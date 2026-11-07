# Ogasawara larval drift with OpenDrift

Explore passive fish-larval transport between the Hahajima, Chichijima and
Mukojima island groups in Japan's Ogasawara archipelago. The notebooks download
Copernicus Marine currents, simulate particle drift, calculate illustrative
island-group and published-MPA encounter matrices, and export maps and NetCDF.

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/DTSchroeder/ogasawara-larval-drift/blob/main/ogasawara_larval_drift_colab.ipynb)

## Choose a notebook

| Notebook | Environment |
| --- | --- |
| [Google Colab](ogasawara_larval_drift_colab.ipynb) | Self-contained, installs dependencies and embeds helper code |
| [EDITO Jupyter](ogasawara_larval_drift_edito.ipynb) | Self-contained; create the Python 3.12 kernel first; see [EDITO setup](README-EDITO.md) |
| [Standard Jupyter](ogasawara_larval_drift.ipynb) | Uses the Python helpers and `sites.csv` alongside the notebook |

For local Jupyter:

```bash
mamba env create -f environment.yml
conda activate ogasawara-larval-drift
jupyter lab
```

Run cells in order. Leave credentials blank for the default public EDITO
catalogue route, or enter your own Copernicus Marine login if you choose the
Toolbox route. Configure the scenario in the settings cell. **This repository contains
no account credentials.** Values entered in notebook code will be saved in your
copy: clear them and clear outputs before sharing or committing a notebook.
Do not upload Copernicus credential files or runtime data to this repository.

## Run on EDITO

Follow the [step-by-step EDITO guide](README-EDITO.md): launch a JupyterLab
service in [EDITO Datalab](https://datalab.dive.edito.eu/), clone this repository,
install the Python 3.12 environment with `uv` (or Conda on compatible images),
and select the **Ogasawara OpenDrift** kernel.
Open **`ogasawara_larval_drift_edito.ipynb`**, enter your own Copernicus login,
and try `RUN_PROFILE = 'quick_check'` before the full 30-day run.

The guide includes terminal commands, kernel selection, result downloads,
permanent S3 storage, troubleshooting, and import of the density NetCDF into
EDITO MyOcean. The full 30-day scenario was completed on EDITO on 7 November 2026 using
public catalogue-linked currents: 2,700 particles, 4,608 integration steps and
769 hourly export frames. Its NetCDF passed MyOcean import and map rendering.

## EDITO catalogue inputs

The default `CURRENT_SOURCE = 'edito_catalogue'` reads the existing Copernicus
current product through EDITO catalogue asset links without a password.
See [data sources and replacement decisions](DATA-SOURCES.md) for the exact
catalogue entries, provenance, and why the Japanese protection polygons and
global coastline mask are retained.

## Default scenario

- 2,700 equal-weight particles: 300 per source per day, over three daily releases.
- Releases on 1–3 May 2025, each followed for 30 days; run ends 2 June 2025.
- Passive OceanDrift particles at 1 m fixed depth; no species-specific behaviour.
- Copernicus six-hourly 1/12° horizontal currents, with missing-current losses
  reported rather than replaced by zero currents.
- 10-minute integration and hourly saved output: 4,608 integration steps.
- Encounter analysis at ages 7–30 days. Each particle counts once per target;
  denominators include all released particles. Targets are nonexclusive.

**Exploratory model:** species, spawning season, mortality, behaviour and habitat
suitability are not calibrated. Illustrative release locations and 15 km circle
targets are not real spawning/settlement habitat. Published MPA geometry is
separately analysed: derived island sectors belong to one published Ordinary
Zone feature and do not represent three separately designated MPAs. Historical
boundary validity has not been verified.

The faster 40-minute configuration produced substantially different encounter
matrices from the original 10-minute configuration. Use timestep sensitivity
checks before interpreting ecological connectivity. Coastline rejection can
exaggerate retention. The coarse currents do not resolve all inter-island or
nearshore circulation.

## Outputs and EDITO visualization

Each run writes a separate `results/` folder containing native `trajectories.nc`,
release and quality tables, encounter matrices, plots, an interactive HTML map,
and provenance. These generated files are excluded from Git.

The final cell also exports `edito_larval_density.nc`: a regular WGS84
`time × latitude × longitude` NetCDF grid containing particle counts and
all-source/source-specific particle densities. Upload this file through
**Personal Catalogue → Upload** in [EDITO MyOcean](https://my-ocean.dive.edito.eu/).
Use the time slider to animate density. The native trajectory file retains
individual tracks for scientific analysis.

Density means numerical particles per horizontal km², not measured abundance
or recruitment probability. The 0.1° export grid is visualization binning and
does not improve the forcing resolution. No land mask is applied to export
cells. Count conservation is checked before writing and after reopening.

The full 30-day scenario completed on EDITO using current assets resolved
through EDITO catalogue links. Every particle received 30 days of follow-up,
with no missing-current or domain losses. The density NetCDF passed EDITO
MyOcean import and map rendering. See [the full-run record](validation/edito_30day_20261107.json).
Fresh Copernicus authentication is unnecessary for this public asset route; the
optional authenticated Toolbox route remains a separate access option.
See [README-EDITO.md](README-EDITO.md) for setup and permanent-storage instructions.

## Validation

In the notebook environment, run:

```bash
python validate_edito_export.py
python validate_edito_catalogue.py
python validate_notebook.py
```

The exporter checks counts, source sums, density-area integration, boundary
bins, age/status filtering, time encoding and out-of-domain rejection. The
notebook validation runs a small, explicitly synthetic uniform-current case and
compares displacement with an analytic expectation. This verifies software
behaviour, not ecological realism. The GeoJSON snapshot under `validation/` is
public boundary data used for offline checks, not simulated scientific results.

## Data attribution and references

- [ILIAD oil-spill reference notebook](https://github.com/ILIAD-ocean-twin/opendrift-demo/blob/master/notebooks/oilspill.ipynb)
- [ILIAD MPA reference notebooks](https://github.com/ILIAD-ocean-twin/aquaculture-norway/tree/iliad-mpa/notebooks/mpa)
- [OpenDrift](https://opendrift.github.io/)
- [Copernicus Marine current product](https://data.marine.copernicus.eu/product/GLOBAL_ANALYSISFORECAST_PHY_001_024/services)
- [Published Ogasawara MPA dataset, HUB Ocean](https://app.hubocean.earth/catalog/dataset/39e7bf52-8aff-46aa-b4b4-b82a22abc1b7/ogasawara-marine-protected-area-)

MPA data are attributed to ProtectedSeas via HUB Ocean (CC BY 4.0); the snapshot
retains the published geometry and properties. Follow Copernicus Marine's
product-specific citation and attribution requirements when using its data.
