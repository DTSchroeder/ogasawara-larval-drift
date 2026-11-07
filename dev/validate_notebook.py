"""Offline checks with real OpenDrift and explicitly SYNTHETIC currents.

Run in the notebook environment: python validate_notebook.py
No Copernicus credentials, ocean data, or scientific conclusions are involved.
"""
from pathlib import Path
import contextlib
import json
import os
import shutil
import tempfile

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "ogasawara-matplotlib"))

import nbformat
import numpy as np
import pandas as pd
import xarray as xr

from drift_analysis import encounter_matrix

ROOT = Path(__file__).resolve().parent


def check_encounters():
    # Particle 0 visits B repeatedly after competence: count once. Particle 1
    # visits B only too early. Particle 2 is inactive there and must not count.
    # Origins are A, A, B: unequal denominators exercise source normalization.
    sites = pd.DataFrame({"name": ["A", "B"], "target_lon": [140., 142.],
                          "target_lat": [27., 27.], "target_radius_km": [5., 5.]})
    ds = xr.Dataset(
        {"lon": (("trajectory", "time"), [[140, 142, 142], [142, 140, 140], [142, 142, 142]]),
         "lat": (("trajectory", "time"), np.full((3, 3), 27.)),
         "origin_marker": (("trajectory", "time"), [[0, 0, 0], [0, 0, 0], [1, 1, 1]]),
         "status": (("trajectory", "time"), [[0, 0, 0], [0, 0, 0], [1, 1, 1]]),
         "age_seconds": (("trajectory", "time"), np.tile([0, 86400, 172800], (3, 1)))},
        coords={"trajectory": [0, 1, 2], "time": pd.date_range("2025-05-01", periods=3)})
    counts, fractions, events = encounter_matrix(ds, sites, [2, 1], 1, 2)
    assert counts.values.tolist() == [[1, 1], [0, 0]]
    assert fractions.values.tolist() == [[0.5, 0.5], [0., 0.]]
    assert len(events) == 2 and (events.first_encounter_age_days == 1).all()
    try:
        encounter_matrix(ds, sites, [3, 1], 1, 2)
    except ValueError:
        pass
    else:
        raise AssertionError("Incorrect release denominators were accepted")


def main():
    check_encounters()
    nb = nbformat.read(ROOT / "ogasawara_larval_drift.ipynb", as_version=4)
    nbformat.validate(nb)
    for i, cell in enumerate(nb.cells):
        if cell.cell_type == "code":
            compile(cell.source, f"cell_{i}", "exec")
    with tempfile.TemporaryDirectory(prefix="ogasawara-SYNTHETIC-check-") as directory:
        scratch = Path(directory)
        shutil.copy(ROOT / "sites.csv", scratch)
        (scratch / "data").mkdir()
        shutil.copy(ROOT / "validation/ogasawara_mpa_snapshot.geojson",
                    scratch / "data/ogasawara_mpa_hubocean.geojson")
        # Analytic uniform current field; not real ocean data.
        time = pd.date_range("2025-04-30", "2025-05-04", freq="6h")
        lat, lon, depth = np.linspace(22, 33, 111), np.linspace(137, 148, 111), [0.5, 10., 30.]
        shape = (len(time), len(depth), len(lat), len(lon))
        field = xr.Dataset(
            {"uo": (("time", "depth", "latitude", "longitude"), np.full(shape, 0.08, dtype="float32")),
             "vo": (("time", "depth", "latitude", "longitude"), np.full(shape, 0.02, dtype="float32"))},
            coords={"time": time, "depth": depth, "latitude": lat, "longitude": lon},
            attrs={"title": "SYNTHETIC uniform currents for software validation only", "Conventions": "CF-1.8"})
        field.uo.attrs = {"standard_name": "eastward_sea_water_velocity", "units": "m s-1"}
        field.vo.attrs = {"standard_name": "northward_sea_water_velocity", "units": "m s-1"}
        field.depth.attrs = {"standard_name": "depth", "units": "m", "positive": "down", "axis": "Z"}
        field.latitude.attrs = {"standard_name": "latitude", "units": "degrees_north", "axis": "Y"}
        field.longitude.attrs = {"standard_name": "longitude", "units": "degrees_east", "axis": "X"}
        field.time.attrs = {"standard_name": "time", "axis": "T"}
        forcing = scratch / "SYNTHETIC_currents.nc"
        field.to_netcdf(forcing)
        previous = Path.cwd()
        namespace = {"__name__": "__notebook_validation__"}
        try:
            os.chdir(scratch)
            with (scratch / "validation.log").open("w") as log, contextlib.redirect_stdout(log):
                for i, cell in enumerate(nb.cells):
                    if cell.cell_type != "code":
                        continue
                    print(f"Executing notebook cell {i}", flush=True)
                    source = cell.source
                    if cell.get("id") == "colab-login":
                        # Synthetic validation uses a local file and needs no account.
                        source = source.replace("CONFIGURE_COPERNICUS = True", "CONFIGURE_COPERNICUS = False")
                    exec(compile(source, f"cell_{i}", "exec"), namespace)
                    if "LOCAL_CURRENT_FILE" in cell.source and "START =" in cell.source:
                        # Override only parameters; execute every other cell unchanged.
                        namespace.update(SCENARIO_LABEL="SYNTHETIC currents — software check",
                                         RELEASE_DAYS=2, PARTICLES_PER_SITE_PER_DAY=4,
                                         MAX_AGE_DAYS=1, MIN_ENCOUNTER_AGE_DAYS=0,
                                         LOCAL_CURRENT_FILE=str(forcing), HORIZONTAL_DIFFUSIVITY_M2_S=0.)
                        namespace["RELEASE_TIMES"] = pd.date_range("2025-05-01", periods=2).to_pydatetime().tolist()
                        namespace["END"] = pd.Timestamp("2025-05-03").to_pydatetime()
            run_dir = namespace["RUN_DIR"]
            expected = ["trajectories.nc", "release_manifest.csv", "provenance.json",
                        "trajectory_quality.csv", "encounter_counts.csv", "encounter_fractions.csv",
                        "first_encounters.csv", "trajectories.png", "release_locations.png",
                        "encounter_matrix.png", "interactive_trajectories.html",
                        "edito_larval_density.nc", "edito_larval_density_cell_area.nc",
                        "edito_export_checks.json"]
            assert all((run_dir / name).stat().st_size > 0 for name in expected)
            ds = namespace["trajectories"]
            assert ds.sizes["trajectory"] == 24
            assert (namespace["fractions"].values >= 0).all()
            assert (namespace["fractions"].values <= 1).all()
            # Independent analytic displacement check, away from coastlines.
            from pyproj import Geod
            geod = Geod(ellps="WGS84")
            measured = []
            for i in range(ds.sizes["trajectory"]):
                t = ds.isel(trajectory=i)
                idx = np.flatnonzero(np.isfinite(t.lon.values) & (t.status.values == 0))
                first, last = idx[0], idx[-1]
                seconds = float(t.age_seconds.values[last] - t.age_seconds.values[first])
                _, _, distance = geod.inv(float(t.lon.values[first]), float(t.lat.values[first]),
                                           float(t.lon.values[last]), float(t.lat.values[last]))
                expected_distance = np.hypot(0.08, 0.02) * seconds
                assert np.isclose(distance, expected_distance, rtol=0.02), (distance, expected_distance)
                measured.append(float(distance))
            # Retain only clearly labelled software-check previews, not synthetic results.
            preview = ROOT / "validation"
            preview.mkdir(exist_ok=True)
            for name in ["release_locations.png", "encounter_matrix.png", "trajectories.png"]:
                shutil.copy(run_dir / name, preview / ("SYNTHETIC_" + name))
            summary = {"forcing": "SYNTHETIC uniform 0.08 m/s east, 0.02 m/s north; not ocean observations",
                       "notebook_schema_valid": True, "all_code_cells_executed": True,
                       "opendrift_version": namespace["version"]("opendrift"),
                       "trajectories": 24, "daily_release_cohorts": 2,
                       "analytic_displacement_check": "passed within 2%",
                       "encounter_edge_cases": "passed",
                       "outputs_checked": expected,
                       "real_copernicus_simulation_run": False}
            (preview / "validation.json").write_text(json.dumps(summary, indent=2) + "\n")
            print(json.dumps(summary, indent=2))
        except BaseException:
            log_file = scratch / "validation.log"
            if log_file.exists():
                print(log_file.read_text()[-5000:])
            for model_log in scratch.glob("results/*/opendrift.log"):
                print(model_log.read_text()[-6000:])
            raise
        finally:
            os.chdir(previous)


if __name__ == "__main__":
    main()
