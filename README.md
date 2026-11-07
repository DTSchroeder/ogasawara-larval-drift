# Larval drift between the Ogasawara Islands

A student tutorial using OpenDrift and EDITO to explore how virtual fish larvae
move between three island groups in Japan.

**Start with [tutorial.ipynb](tutorial.ipynb).** This is the only notebook students
need on EDITO. It contains all helper code and source locations.

## Run the tutorial on EDITO

1. Open a JupyterLab service in [EDITO Datalab](https://datalab.dive.edito.eu/).
2. In its terminal, clone the repository and install the notebook environment:

   ```bash
   git clone https://github.com/DTSchroeder/ogasawara-larval-drift.git
   cd ogasawara-larval-drift
   uv venv --python 3.12 .venv
   uv pip install --python .venv/bin/python -r requirements.txt
   .venv/bin/python -m ipykernel install --user --name ogasawara-larval-drift --display-name "Ogasawara OpenDrift"
   ```

3. Open **`tutorial.ipynb`**, select the **Ogasawara OpenDrift** kernel, and run
   cells in order with **Shift+Enter**. Leave credentials blank: the default
   current-data route uses public EDITO catalogue links.
4. Review the settings before running the simulation. The default follows 2,700
   particles for 30 days per cohort. Use `quick_check` for a short setup check.

See the [detailed EDITO guide](docs/EDITO.md) for workspace setup, troubleshooting,
and saving results to permanent storage.

## What students will explore

- Release virtual larvae and follow their trajectories.
- Compare potential encounters between island groups and protected-area sectors.
- Export a density NetCDF and visualize its time series in EDITO MyOcean.
- Discuss how currents, model assumptions and numerical settings affect results.

The currents are too coarse to resolve narrow channels and nearshore habitat.
Particles have no calibrated species-specific behaviour or mortality, so the
results describe potential physical transport, not biological recruitment.
See [model notes and attribution](docs/MODEL-NOTES.md) and [data sources](docs/DATA-SOURCES.md).

## View the results

The notebook saves each run under `runs/ogasawara-larval-drift/results/`.
Upload **`edito_larval_density.nc`** through **Personal Catalogue → Upload** in
[EDITO MyOcean](https://my-ocean.dive.edito.eu/). Choose `particle_density` and
move the time slider. If the automatic colour range shows 0–0, set the layer's
minimum to **0** and maximum to **0.5** particles/km² as a starting point.

Generated outputs and credentials are excluded from this repository. Save your
results to permanent EDITO storage before stopping the notebook service.

## Optional material

- [Google Colab version](https://colab.research.google.com/github/DTSchroeder/ogasawara-larval-drift/blob/main/extras/colab.ipynb), for students using Colab instead of EDITO.
- [Development and validation](dev/README.md), for instructors and maintainers.
