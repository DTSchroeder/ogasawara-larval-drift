# Development and validation

Students should use the self-contained [tutorial](../tutorial.ipynb) in the
repository root. This folder contains the modular notebook, shared helper
sources, offline checks, and verification records for instructors/maintainers.

The standard Jupyter notebook `ogasawara_larval_drift.ipynb` expects its kernel's
working directory to be this `dev/` folder, beside `sites.csv` and the helpers.
It uses the same model and export logic as the student tutorial.

From the repository root, in the installed notebook environment:

```bash
python dev/validate_edito_catalogue.py
python dev/validate_edito_export.py
python dev/validate_trajectory_export.py
python dev/validate_notebook.py
```

`validate_notebook.py` runs a small synthetic uniform-current case and compares
its displacement with an analytic expectation. This checks software behaviour,
not ecological realism. The public GeoJSON snapshot under `validation/` enables
offline boundary checks. It is attributed to ProtectedSeas via HUB Ocean,
CC BY 4.0. JSON verification records describe the real EDITO runs separately.

For Conda/Mamba instead of `uv`, use `dev/environment.yml` from the root:

```bash
mamba env create -f dev/environment.yml
conda run -n ogasawara-larval-drift python -m ipykernel install --user --name ogasawara-larval-drift --display-name "Ogasawara OpenDrift"
```

The self-contained student and Colab notebooks embed the helpers. When changing
model code, keep their embedded copies synchronized with the modules here.
Clear notebook outputs and credential values before committing.
