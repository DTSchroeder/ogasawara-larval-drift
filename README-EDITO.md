# Run the Ogasawara notebook on EDITO

The repository includes `ogasawara_larval_drift_edito.ipynb`, a self-contained
Jupyter version without Google Colab dependencies. The same model, source
islands, current download, MPA analysis and export logic are retained.
It has not yet been executed in an EDITO account. Its export logic was checked
locally and in Colab; platform acceptance must be confirmed in your session.

## 1. Start a Jupyter workspace

Sign in to [EDITO Datalab](https://datalab.dive.edito.eu/) with your EDITO
account. In the service catalogue, find **Jupyter / JupyterLab**, configure a
CPU service in your personal or project workspace, and launch it. Open JupyterLab
when the service is ready. You need an account with computing resources enabled;
if launching is unavailable, check your EDITO resource allocation.

No GPU is required. As a starting point for this small example, 2 CPUs and
8 GB RAM are reasonable; this is a suggested configuration, not an EDITO-tested
minimum. Keep enough disk space for the environment and downloaded currents.

Your **EDITO account** opens the workspace. Your separate **Copernicus Marine
account** downloads the model currents from Copernicus. Both are needed for a
fresh run; this repository supplies neither account's credentials.

## 2. Get this repository

In JupyterLab, select **File → New → Terminal** (or **Terminal** in the Launcher).
Run these commands in that terminal, not in a Python cell:

```bash
git clone https://github.com/DTSchroeder/ogasawara-larval-drift.git
cd ogasawara-larval-drift
```

If you prefer uploads, use **Code → Download ZIP** on GitHub, extract it locally,
and upload the files to JupyterLab. Keep `environment.yml` in the same working
folder as the notebook. The EDITO notebook embeds its helpers and site table,
so no companion Python modules need to be uploaded to execute it.

## 3. Install dependencies and register the kernel

In the same terminal and repository folder:

```bash
mamba env create -f environment.yml
conda run -n ogasawara-larval-drift python -m ipykernel install --user --name ogasawara-larval-drift --display-name "Ogasawara OpenDrift"
```

This can take several minutes. If `mamba` is unavailable but `conda` is installed,
use `conda env create -f environment.yml` for the first command. If the named
environment already exists, reuse it; to update it from this repository, run
`mamba env update -n ogasawara-larval-drift -f environment.yml`.

OpenDrift also [documents installation in EDITO's JupyterHub](https://opendrift.github.io/install.html#install-and-use-on-wekeo-and-edito).
This repository uses its own environment to pin the OpenDrift version used here.

## 4. Open and configure the notebook

1. In JupyterLab's file browser, open the cloned repository and double-click
   **`ogasawara_larval_drift_edito.ipynb`**. Choose this EDITO version, rather than
   the Colab installation notebook.
2. Select **Kernel → Change Kernel → Ogasawara OpenDrift**. Refresh JupyterLab
   if the newly registered kernel is not listed.
3. Run the first dependency-check cell with **Shift+Enter**. It should print
   package versions, including OpenDrift 1.14.12.
4. In the early **Copernicus account configuration** cell, set
   `COPERNICUS_USERNAME` and `COPERNICUS_PASSWORD` to your own login and run it.
   Values entered in code are saved in your notebook copy. Clear them before
   sharing or committing it. Do not put EDITO or S3 credentials in that cell.
5. Find the scenario-settings cell. Use `RUN_PROFILE = 'quick_check'` for a
   24-hour, 90-particle pipeline check first. Use `RUN_PROFILE = '30_day'` for
   the full 2,700-particle scenario. The short check's encounters are not a
   substitute for the 30-day connectivity analysis.
6. Run the remaining cells in order, or use **Run → Run All Cells** after
   choosing your settings. The first current download and coastline setup need
   network access. Reuse of the cached current file avoids repeat downloads.

When changing the run profile, rerun the scenario-settings cell and all cells
after it. This rebuilds the releases, selects matching currents and creates a
new results folder. Do not rerun just the simulation cell on an already-used
OpenDrift object.

## 5. Find the result files

The notebook prints the full path to its run folder. It is under:

```text
ogasawara-larval-drift/results/<timestamp>-<run-id>/
```

Paths are relative to the notebook kernel's current working directory. Browse
that folder in JupyterLab to inspect CSV tables, PNG figures, the HTML map,
`trajectories.nc` and `edito_larval_density.nc`. The final cell must complete to
produce the density export. It should print **count conservation: passed**.

Set `DOWNLOAD_RESULTS = True` in the final cell to create a ZIP and display a
Jupyter download link. You can also download individual files by right-clicking
them in JupyterLab's file browser and selecting **Download**. A ZIP contains
results, not the current forcing cache or the notebook's credential variables.

## Visualize the result

The simulation already writes **`trajectories.nc`** with particle positions and
status. This trajectory-shaped file is for scientific analysis and OpenDrift;
it is not the regular map grid intended for MyOcean's gridded upload.

The final cell additionally creates:

- **`edito_larval_density.nc`**: compressed NetCDF4 with CF-style metadata and
  dimensions `time`, `latitude`, `longitude`. The default 0.1° grid has an
  all-source particle count and particle density, plus one density variable per
  source island group. Time snapshots follow the saved model output interval.
- **`edito_larval_density_cell_area.nc`**: grid-cell areas in km², useful for
  checking that integrating density reproduces the particle counts. This is a
  scientific companion, not the primary viewer upload.
- **`edito_export_checks.json`**: export dimensions and per-time count checks.

In [EDITO MyOcean](https://my-ocean.dive.edito.eu/), open **Personal Catalogue →
Upload**, select `edito_larval_density.nc`, and wait for preprocessing. Select
`particle_density`, or a source-specific density variable, and use the time
slider to view dispersal. This follows the currently documented user-data
import route; the generated file has not yet been imported in EDITO itself.

The export checks particle-count conservation before writing and after
reopening the file. It excludes inactive, missing, not-yet-released and
older-than-maximum-age positions. Counts refer to equal-weight numerical
particles, not measured larval abundance. Density is particles per horizontal
km² at the fixed model depth. No land mask is applied to the grid, so coastal
cells can overlap land. Zero means no valid active particle in a cell.

The 0.1° grid is a visualization binning choice, not an increase in model or
current resolution. The existing connectivity matrix remains a separate
source–destination product; the density grid does not represent connectivity
probabilities or ecological settlement.

## Keep the data

EDITO notebook service files are temporary. Copy the notebook and results to
personal or project S3 storage before stopping the service. Copying to storage
does not automatically register a dataset in the EDITO Data Catalogue. Private
viewer upload and shared catalogue publication are different workflows.
Do not include a notebook containing credentials when publishing results.

Relevant current EDITO documentation:

- [Viewer user-data upload](https://help.edito.eu/en/articles/16918517-what-s-new-in-the-latest-version-of-edito-myocean-viewer-v-17)
- [Onboarding formats and metadata](https://help.edito.eu/en/articles/15339950-onboard-your-data-on-edito)
- [Temporary versus permanent storage](https://help.edito.eu/en/articles/16641024-understand-edito-storage)

## Troubleshooting

| Symptom | What to do |
| --- | --- |
| `ModuleNotFoundError` | Check that the selected kernel is **Ogasawara OpenDrift**, then rerun the dependency check. Installing into a different terminal environment does not change the notebook kernel. |
| Authentication fails | Check the Copernicus username/password variables, rerun the account cell and rerun the download. Your EDITO password is a different login. |
| `CURRENT_FILE` or scenario variables are missing | Run the imports and scenario settings, then download/validate currents before starting the model. Use Run All when starting a fresh kernel. |
| No density NetCDF appears | Run the final export cell after the trajectory-analysis cells. Read its error before proceeding. |
| The viewer rejects a file | Upload `edito_larval_density.nc`, rather than `trajectories.nc` or the cell-area companion. Record the viewer's error; actual EDITO import remains unverified. |
| Files disappear after service restart | Restore them from permanent S3 storage or Git. Notebook working files are not automatically saved back to S3. |

## Optional: open the notebook using EDITO's init script

EDITO also documents an [init-script route](https://help.edito.eu/en/articles/13715151-open-a-jupyter-notebook-with-an-init-script).
In the JupyterLab service's **Init** configuration, use:

- `PersonalInit`: `https://gitlab.mercator-ocean.fr/pub/edito-infra/configuration/-/raw/main/scripts/open-jupyter-notebook-url.sh`
- `PersonalInitArgs`: `https://raw.githubusercontent.com/DTSchroeder/ogasawara-larval-drift/main/ogasawara_larval_drift_edito.ipynb`

This opens the notebook; it does not create the pinned environment. Complete the
environment installation above, obtaining `environment.yml` from this repository.
The clone-and-open route is the recommended starting point for this project.
