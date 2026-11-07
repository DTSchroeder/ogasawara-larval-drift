# Data sources and EDITO catalogue alternatives

## Currents: EDITO access is implemented

The notebook now defaults to `CURRENT_SOURCE = 'edito_catalogue'`. It traverses
EDITO's Copernicus Marine product → dataset → variable-item links and opens the
catalogued public Zarr asset for both `uo` and `vo`. No password is needed for
this access route. The data remain **Copernicus Marine's** six-hourly 1/12°
currents: catalogue access does not change their producer or resolution.

- [EDITO product catalogue](https://api.dive.edito.eu/data/catalogs/projects/copernicus-marine-products/copernicus-marine-product-GLOBAL_ANALYSISFORECAST_PHY_001_024)
- [Exact current dataset](https://api.dive.edito.eu/data/catalogs/projects/copernicus-marine-products/copernicus-marine-product-GLOBAL_ANALYSISFORECAST_PHY_001_024/copernicus-marine-dataset-cmems_mod_glo_phy-cur_anfc_0.083deg_PT6H-i)
- [Eastward velocity item](https://api.dive.edito.eu/data/collections/climate_forecast-eastward_sea_water_velocity/items/3177a73a-c993-51c0-885d-1a8ae80da0ec)
- [Northward velocity item](https://api.dive.edito.eu/data/collections/climate_forecast-northward_sea_water_velocity/items/0aba76c4-f72a-5f1f-b7db-cfb6cc4906c6)

`dev/edito_catalogue.py` selects the regional time-series asset, checks that both
velocity components reference the same store, brackets the requested bounds,
and converts native negative elevation to positive-down depth. It records the
resolved catalogue and asset URLs beside the cached NetCDF as `.source.json`.
The usual CF, time/depth/domain, and wet-release checks still run afterward.

Choose `CURRENT_SOURCE = 'copernicus'` to use the existing Toolbox route instead,
or set `LOCAL_CURRENT_FILE` to use a pre-downloaded CF current subset. Enter
Copernicus credentials only when using a route that requires them.

## Other inputs

| Input | Current use | EDITO catalogue option and decision |
| --- | --- | --- |
| Land/coastline mask | OpenDrift's global land mask rejects moves onto land | The catalogue has EMODnet coastline layers. Their Ogasawara geometry and suitability as an OpenDrift numerical mask have not been verified; keep the existing mask. |
| Protected-area polygons | Published ProtectedSeas Ogasawara Ordinary Zone via HUB Ocean | The catalogue has an EMODnet nationally designated protected-areas item, but the same Ogasawara boundary has not been verified there. Keep HUB Ocean's known polygon and its attribution. |
| Bathymetry/background map | Fixed 1 m particles; Esri tiles are visual context | The catalogue includes bathymetry and a global GEBCO record. Bathymetry could provide context or support a future bottom-interaction model after checking the actual asset coverage. It is not a replacement for currents. |
| Source/target locations and biological settings | Illustrative notebook parameters | These are assumptions, not data-service downloads. They need local spawning/habitat/species evidence, not a generic catalogue substitution. |

Catalogue records inspected include [coastlines](https://api.dive.edito.eu/data/collections/emodnet-coastlines/items),
[protected areas](https://api.dive.edito.eu/data/collections/emodnet-protected_areas/items),
and [bathymetry](https://api.dive.edito.eu/data/collections/emodnet-bathymetry/items).
A record's broad metadata bounding box does not prove that its actual files
contain useful data at the Japanese islands. No unverified layer is substituted
silently. Experimental GLONET forecasts are also catalogued, but they are a
different model; switching to them would change the experiment.

If calibrated larval growth or buoyancy is added later, temperature and salinity
are also linked under the same Copernicus product in EDITO. The present passive,
fixed-depth model does not use those variables.

## Longer runs and the viewer

The 30-day scenario follows each of three daily release cohorts for 30 days,
so the complete run covers 32 days. Integration and saved-output intervals are
independent of the biological drift duration. A 10-minute integration with
hourly output uses 4,608 steps; the faster 40-minute/two-hour setup uses 1,152.
Changing the integration interval can materially change encounter matrices.

Each run exports native `trajectories.nc` plus the regular-grid
`edito_larval_density.nc` for EDITO MyOcean. Upload the latter through
**Personal Catalogue → Upload**, then choose `particle_density` or a source
island's density layer and move the time slider. These are numerical particle
densities, not measured larval abundance or settlement probabilities.
