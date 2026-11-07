# Larval drift between the Ogasawara Islands

A student tutorial using OpenDrift and EDITO to explore how virtual fish larvae
move between three island groups in Japan.

**Start with [tutorial.ipynb](tutorial.ipynb).** This is the only notebook students
need on EDITO. It contains all helper code and source locations.

### Plan your time

Allow approximately **15–30 minutes for a first walkthrough**, depending on Jupyter experience, computing resources and download speed. This is a guide for completing the workflow, not a guarantee or enough time for a full study of the model. Initial environment installation and downloads may take additional time.

For a **20-minute classroom slot**, instructors should prepare and check the environment beforehand. Students can follow the default scenario through to the outputs, waiting for each cell to finish and checking for errors. Return to the notebook later to study the currents, assumptions, encounter matrices and sensitivity experiments in detail.

## Run the tutorial on EDITO

1. Open a JupyterLab service in [EDITO Datalab](https://datalab.dive.edito.eu/).
2. In its terminal, clone the repository and install the notebook environment:

   ```bash
   git clone https://github.com/DTSchroeder/ogasawara-larval-drift.git
   cd ogasawara-larval-drift
   python -m pip install --user uv
   python -m uv venv --python 3.12 .venv
   python -m uv pip install --python .venv/bin/python -r requirements.txt
   .venv/bin/python -m ipykernel install --user --name ogasawara-larval-drift --display-name "Ogasawara OpenDrift"
   ```

   Run the commands one at a time and wait for each to finish. Stop if any fails.
   Complete installation in the same EDITO service where you open the notebook.

3. Open **`tutorial.ipynb`**, choose **Kernel → Change Kernel → Ogasawara OpenDrift**, and run
   cells in order with **Shift+Enter**. Leave credentials blank: the default
   current-data route uses public EDITO catalogue links.
   If the first cell reports `PackageNotFoundError` for OpenDrift, check the
   selected kernel: the default Python kernel does not contain the tutorial packages.

4. Review the settings before running the simulation. The default follows 2,700
   particles for 30 days per cohort. Use `quick_check` for a short setup check.
5. At **5. Run and retain provenance**, allow several minutes or longer. Wait for
   the simulation cell to finish and display output before proceeding: `[*]`
   means it is still running. Resolve any error before continuing.

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

After the final export cell reports **count conservation: passed**, open the
results folder printed by the notebook, under
`runs/ogasawara-larval-drift/results/<timestamp>-<run-id>/`.
In the JupyterLab file browser, right-click **`edito_larval_density.nc`** and
choose **Download**. Then open [EDITO MyOcean](https://my-ocean.dive.edito.eu/),
choose **Add layer → Personal Catalogue → Upload**, and select the downloaded
file. Wait for processing, add **Active model particle density, all sources**
(`particle_density`), and move the time slider. If the automatic colour range shows 0–0, set the layer's
minimum to **0** and maximum to **0.5** particles/km² as a starting point.
If you see only a grey rectangle, follow the [viewer display walkthrough](docs/EDITO.md#if-the-viewer-shows-only-a-grey-rectangle).

Generated outputs and credentials are excluded from this repository. Save your
results to permanent EDITO storage before stopping the notebook service.

## Optional material

- [Google Colab version](https://colab.research.google.com/github/DTSchroeder/ogasawara-larval-drift/blob/main/extras/colab.ipynb), for students using Colab instead of EDITO.
- [Development and validation](dev/README.md), for instructors and maintainers.

The tutorial also exports `edito_trajectories.geojson` for **Import → GeoJSON** in the MyOcean map. It contains static sampled drift paths grouped by source island; the time slider animates the density layer, not these full-period lines.
