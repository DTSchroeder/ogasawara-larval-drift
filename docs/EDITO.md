# Run the Ogasawara notebook on EDITO

The repository includes `tutorial.ipynb`, a self-contained
Jupyter version without Google Colab dependencies. The same model, source
islands, current download, MPA analysis and export logic are retained.
A 24-hour verification and the full 30-day scenario both completed on EDITO on
7 November 2026. The full run used 2,700 particles, three daily release cohorts,
4,608 ten-minute steps and hourly outputs. Every particle had a full 30-day
follow-up, without missing-current or domain losses. Currents were resolved
through EDITO catalogue links and read without a password. The exported density
NetCDF passed MyOcean import and final-frame rendering. See the
[full-run check record](../dev/validation/edito_30day_20261107.json).

## 1. Start a Jupyter workspace

Sign in to [EDITO Datalab](https://datalab.dive.edito.eu/) with your EDITO
account. In the service catalogue, find **Jupyter / JupyterLab**, configure a
CPU service in your personal or project workspace, and launch it. Open JupyterLab
when the service is ready. You need an account with computing resources enabled;
if launching is unavailable, check your EDITO resource allocation.

No GPU is required. As a starting point for this small example, 2 CPUs and
8 GB RAM are reasonable; this is a suggested configuration, not an EDITO-tested
minimum. Keep enough disk space for the environment and downloaded currents.

Your **EDITO account** opens the workspace. The default **EDITO catalogue** current-access route uses public Copernicus
assets and requires no Copernicus login. A separate Copernicus Marine account
is needed only if you choose an access route requiring authentication. This
repository supplies no account credentials.

## 2. Get this repository

In JupyterLab, select **File → New → Terminal** (or **Terminal** in the Launcher).
Run these commands in that terminal, not in a Python cell:

```bash
git clone https://github.com/DTSchroeder/ogasawara-larval-drift.git
cd ogasawara-larval-drift
```

If you prefer uploads, use **Code → Download ZIP** on GitHub, extract it locally,
and upload the files to JupyterLab. Keep `requirements.txt` (or
`dev/environment.yml` for Conda) in the same working folder as the notebook. The EDITO notebook embeds its helpers and site table,
so no companion Python modules need to be uploaded to execute it.

## 3. Install dependencies and register the kernel

EDITO service images differ: some provide `uv`, while others show a Conda
`(base)` prompt and have no `uv` command. The default notebook kernel may use
Python 3.13 without OpenDrift. Create a separate Python 3.12 environment using
the following steps, then explicitly select its notebook kernel.

Run each command **one at a time in the JupyterLab terminal**, waiting for it to
finish. If a command fails, stop and resolve that error before continuing.

First install `uv` if it is missing, and check that Python can run it:

```bash
python -m pip install --user uv
python -m uv --version
```

Create the environment inside the repository folder:

```bash
python -m uv venv --python 3.12 .venv
```

Install the tutorial packages and wait until the terminal prompt returns:

```bash
python -m uv pip install --python .venv/bin/python -r requirements.txt
```

Register the notebook kernel:

```bash
.venv/bin/python -m ipykernel install --user --name ogasawara-larval-drift --display-name "Ogasawara OpenDrift"
```

Using `python -m uv` avoids relying on the `uv` executable being on the shell's
search path. Dependencies are installed into `.venv`; the service's default
Python environment is unchanged. Do not move this folder after registering the
kernel, because its registration refers to the environment's full path.

Complete these steps in the **same EDITO service where you open the notebook**.
A kernel installed in another service is not automatically available here.

### Alternative for an image with Conda/Mamba

For users who prefer Conda/Mamba, the original environment file is also available:

```bash
mamba env create -f dev/environment.yml
conda run -n ogasawara-larval-drift python -m ipykernel install --user --name ogasawara-larval-drift --display-name "Ogasawara OpenDrift"
```

Use `conda env create -f dev/environment.yml` if only Conda is installed. Reuse an
existing environment rather than trying to create it again. OpenDrift also
[documents installation in EDITO's JupyterHub](https://opendrift.github.io/install.html#install-and-use-on-wekeo-and-edito),
but the available installation tools depend on the service image you choose.

Check `conda env list` after installation: `ogasawara-larval-drift` must appear
before running `conda run -n ogasawara-larval-drift ...`. A `(base)` prompt does
not mean that the tutorial environment exists. If Conda returns to the prompt
while solving without creating the environment, use the `python -m uv` route
above. This symptom can indicate a resource limit; it does not confirm the cause.

## 4. Open and configure the notebook

1. In JupyterLab's file browser, open the cloned repository and double-click
   **`tutorial.ipynb`**. Choose this EDITO version, rather than
   the Colab installation notebook.
2. Select **Kernel → Change Kernel → Ogasawara OpenDrift**. Refresh JupyterLab
   if the newly registered kernel is not listed.
3. Confirm the notebook's upper-right kernel selector says **Ogasawara OpenDrift**.
   Installing packages in a terminal does not switch an already-open notebook's kernel.
4. Run the first dependency-check cell with **Shift+Enter**. It should print
   package versions, including OpenDrift 1.14.12.
5. For the default `CURRENT_SOURCE = 'edito_catalogue'`, leave the early
   Copernicus username/password variables blank. If you choose
   `CURRENT_SOURCE = 'copernicus'`, enter your own login and run that account cell.
   Values entered in code are saved in your notebook copy. Clear them before
   sharing or committing it. Do not put EDITO or S3 credentials in that cell.
6. Find the scenario-settings cell. Use `RUN_PROFILE = 'quick_check'` for a
   24-hour, 90-particle pipeline check first. Use `RUN_PROFILE = '30_day'` for
   the full 2,700-particle scenario. The short check's encounters are not a
   substitute for the 30-day connectivity analysis.
7. Run the remaining cells in order, or use **Run → Run All Cells** after
   choosing your settings. The first current download and coastline setup need
   network access. Reuse of the cached current file avoids repeat downloads.

When changing the run profile, rerun the scenario-settings cell and all cells
after it. This rebuilds the releases, selects matching currents and creates a
new results folder. Do not rerun just the simulation cell on an already-used
OpenDrift object.

## 5. Find the result files

The notebook prints the full path to its run folder. It is under:

```text
runs/ogasawara-larval-drift/results/<timestamp>-<run-id>/
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
import route. Both the 24-hour and full 30-day exports passed this import and rendered
correctly on 7 November 2026. Check each new export after uploading it.

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

During verification, the viewer displayed an automatic deletion date one week
after upload. Keep your original NetCDF in permanent storage and check the
retention date shown for each Personal Catalogue upload.
Do not include a notebook containing credentials when publishing results.

Relevant current EDITO documentation:

- [Viewer user-data upload](https://help.edito.eu/en/articles/16918517-what-s-new-in-the-latest-version-of-edito-myocean-viewer-v-17)
- [Onboarding formats and metadata](https://help.edito.eu/en/articles/15339950-onboard-your-data-on-edito)
- [Temporary versus permanent storage](https://help.edito.eu/en/articles/16641024-understand-edito-storage)

## Troubleshooting

| Symptom | What to do |
| --- | --- |
| `uv: command not found` | Install with `python -m pip install --user uv`, then use `python -m uv` as shown above. |
| `EnvironmentLocationNotFound` | The named Conda environment was not created. Check `conda env list`; finish installation or use the `python -m uv` route before registering the kernel. |
| `PackageNotFoundError: No package metadata was found for opendrift` | Select **Kernel → Change Kernel → Ogasawara OpenDrift**, then rerun the first cell. A traceback under `/opt/conda/lib/python3.13` indicates the default Python environment is being used rather than the tutorial's Python 3.12 environment. |
| `.venv/bin/python` does not exist | Complete the environment setup in this repository folder, in this same EDITO service. |
| `ModuleNotFoundError` | Check that the selected kernel is **Ogasawara OpenDrift**, then rerun the dependency check. Installing into a different terminal environment does not change the notebook kernel. |
| Authentication fails | Check the Copernicus username/password variables, rerun the account cell and rerun the download. Your EDITO password is a different login. |
| `CURRENT_FILE` or scenario variables are missing | Run the imports and scenario settings, then download/validate currents before starting the model. Use Run All when starting a fresh kernel. |
| No density NetCDF appears | Run the final export cell after the trajectory-analysis cells. Read its error before proceeding. |
| The viewer rejects a file | Upload `edito_larval_density.nc`, rather than `trajectories.nc` or the cell-area companion. The 24-hour example passed import; record any error from your new export. |
| Files disappear after service restart | Restore them from permanent S3 storage or Git. Notebook working files are not automatically saved back to S3. |

## Optional: open the notebook using EDITO's init script

EDITO also documents an [init-script route](https://help.edito.eu/en/articles/13715151-open-a-jupyter-notebook-with-an-init-script).
In the JupyterLab service's **Init** configuration, use:

- `PersonalInit`: `https://gitlab.mercator-ocean.fr/pub/edito-infra/configuration/-/raw/main/scripts/open-jupyter-notebook-url.sh`
- `PersonalInitArgs`: `https://raw.githubusercontent.com/DTSchroeder/ogasawara-larval-drift/main/tutorial.ipynb`

This opens the notebook; it does not create the pinned environment. Complete the
environment installation above, obtaining `requirements.txt` (or
`dev/environment.yml` for Conda) from this repository.
The clone-and-open route is the recommended starting point for this project.

See [DATA-SOURCES.md](DATA-SOURCES.md) for catalogue input alternatives and
longer-run configuration. Public Zarr access requires the `fsspec[http]`
dependency included in `requirements.txt`.

### Colour range for sparse particle grids

Most cells contain zero particles. MyOcean's automatic colour range can
therefore collapse to **0–0**, producing an apparently empty map despite valid
nonzero cells. Open the density layer's gear/settings control and set **Min = 0**
and **Max = 0.5** particles/km² as a useful starting point for this scenario.
Select a sequential palette (for example purple–green–yellow) and adjust the
upper limit for the frame being inspected. This changes display only; it does
not alter counts, trajectories or connectivity. The tested full-run view uses
this manual range. Remove the old one-day layer from the map when comparing
longer dates, or it will show an out-of-range warning.

## Show individual drift paths on the map

The trajectory-export cell in the notebook creates **`edito_trajectories.geojson`**, with up to 30 particles per source island group, sampled every sixth saved output (six hours with the default hourly output). First/last positions are retained, and missing or inactive gaps are split. Each source is one multi-part geometry to avoid dozens of labels.

1. Download `edito_trajectories.geojson` from the run folder (right-click the file in JupyterLab → **Download**).
2. In the MyOcean **map**, choose **Import → GeoJSON**, select the file, select all three island groups, and press **Import 3**. Leave **Split multi-part geometries** off. This uses the geometry-import tool, separate from the NetCDF Personal Catalogue upload.
3. The paths show the **entire run** and remain static when the time slider moves. The density NetCDF layer still follows the selected time. The viewer may apply its own line colours; click a path's label to identify its source. Collapse label details or drag labels aside to uncover the lines.

This is a display sample, not all 2,700 tracks. The complete hourly trajectories remain in `trajectories.nc`; encounter matrices still use every particle and saved output. Adjust `TRACKS_PER_SOURCE` or `TRACK_OUTPUT_STRIDE` for map readability; these settings do not rerun or change the simulation.
