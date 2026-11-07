"""Geodesic island-group encounters from OpenDrift trajectory output.

This measures potential physical encounters, not biological settlement.
"""
import numpy as np
import pandas as pd
from pyproj import Geod

GEOD = Geod(ellps="WGS84")


def circle(lon, lat, radius_km, n=120):
    azimuths = np.linspace(0, 360, n + 1)
    x, y, _ = GEOD.fwd(np.full(n + 1, lon), np.full(n + 1, lat),
                       azimuths, np.full(n + 1, radius_km * 1000))
    return x, y


def release_cloud(lon, lat, radius_m, number, rng):
    """Uniform area sampling in a geodesic disc, rather than degree offsets."""
    x, y, _ = GEOD.fwd(np.full(number, lon), np.full(number, lat),
                       rng.uniform(0, 360, number), radius_m * np.sqrt(rng.random(number)))
    return x, y


def encounter_matrix(ds, sites, released_per_source, min_age_days, max_age_days):
    """Rows are sources, columns destinations; count each particle once per target.

    Only active, finite positions in the inclusive age window count. Separate
    destinations are nonexclusive, so row sums of fractions can exceed one.
    Denominators include all released particles, including subsequently lost ones.
    """
    if not 0 <= min_age_days <= max_age_days:
        raise ValueError("Encounter age window must satisfy 0 <= min <= max.")
    names = sites["name"].tolist()
    denominators = np.asarray(released_per_source, dtype=int)
    if denominators.shape != (len(names),) or (denominators <= 0).any():
        raise ValueError("Provide a positive released count for every source.")
    required = {"lon", "lat", "origin_marker", "status", "age_seconds"}
    if not required.issubset(ds.variables):
        raise ValueError(f"Missing output variables: {required - set(ds.variables)}")
    counts = np.zeros((len(names), len(names)), dtype=int)
    records = []
    observed = np.zeros(len(names), dtype=int)
    for index in range(ds.sizes["trajectory"]):
        t = ds.isel(trajectory=index)
        marker = np.asarray(t.origin_marker.values).ravel()
        finite_marker = marker[np.isfinite(marker)]
        if not len(finite_marker):
            raise ValueError(f"Trajectory {index} has no source marker.")
        if not np.all(finite_marker == finite_marker[0]):
            raise ValueError("Source marker changed within a trajectory.")
        source = int(finite_marker[0])
        if source != finite_marker[0] or not 0 <= source < len(names):
            raise ValueError(f"Unknown source marker {finite_marker[0]}")
        observed[source] += 1
        lon, lat = np.asarray(t.lon), np.asarray(t.lat)
        age = np.asarray(t.age_seconds) / 86400
        valid = (np.isfinite(lon) & np.isfinite(lat) & np.isfinite(age)
                 & (np.asarray(t.status) == 0)
                 & (age >= min_age_days) & (age <= max_age_days))
        for dest, site in enumerate(sites.itertuples(index=False)):
            if not valid.any():
                continue
            _, _, distance = GEOD.inv(lon[valid], lat[valid],
                                      np.full(valid.sum(), site.target_lon),
                                      np.full(valid.sum(), site.target_lat))
            hits = distance <= site.target_radius_km * 1000
            if hits.any():
                counts[source, dest] += 1
                first = np.flatnonzero(valid)[np.flatnonzero(hits)[0]]
                records.append({"trajectory": ds.trajectory.values[index].item(),
                                "source": names[source], "destination": names[dest],
                                "first_encounter_age_days": float(age[first]),
                                "first_encounter_time": str(t.time.values[first])})
    if not np.array_equal(observed, denominators):
        raise ValueError(f"Expected released trajectories {denominators.tolist()}, "
                         f"found {observed.tolist()}. Check output before interpreting fractions.")
    count_df = pd.DataFrame(counts, index=names, columns=names)
    fraction_df = count_df.div(denominators, axis=0)
    events = pd.DataFrame(records, columns=["trajectory", "source", "destination",
                                           "first_encounter_age_days", "first_encounter_time"])
    count_df.index.name = fraction_df.index.name = "source"
    return count_df, fraction_df, events
