# Run the Ogasawara notebook on EDITO

The repository includes `ogasawara_larval_drift_edito.ipynb`, a self-contained
Jupyter version without Google Colab dependencies. The same model, source
islands, current download, MPA analysis and export logic are retained.
It has not yet been executed in an EDITO account. Its export logic was checked
locally and in Colab; platform acceptance must be confirmed in your session.

## Set up the notebook

1. Start an EDITO Jupyter service and upload the notebook and `environment.yml`.
2. In the Jupyter terminal, create its environment and register a kernel:

   ```bash
   mamba env create -f environment.yml
   conda run -n ogasawara-larval-drift python -m ipykernel install --user --name ogasawara-larval-drift --display-name "Ogasawara OpenDrift"
   ```

3. Open the EDITO notebook, select **Ogasawara OpenDrift**, and run the dependency
   check. If the kernel is not listed, refresh Jupyter's kernel selection.
4. Fill in the early Copernicus username/password variables and choose the
   scenario settings. Credentials in code are saved with the notebook.
5. Run the remaining cells. A standard CPU environment is sufficient. Downloads
   and the initial coastline setup need network access.

OpenDrift documents installation on EDITO's JupyterHub directly:
https://opendrift.github.io/install.html#install-and-use-on-wekeo-and-edito

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
