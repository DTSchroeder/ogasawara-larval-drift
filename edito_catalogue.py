"""Read the exact Copernicus current product through EDITO's public STAC links."""
from pathlib import Path
import json
import urllib.request
import numpy as np
import xarray as xr

EDITO_CURRENT_PRODUCT = (
    'https://api.dive.edito.eu/data/catalogs/projects/copernicus-marine-products/'
    'copernicus-marine-product-GLOBAL_ANALYSISFORECAST_PHY_001_024'
)


def _json(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


def resolve_edito_current_asset(dataset_id):
    """Traverse catalogue links, checking that both velocity items share a store."""
    product = _json(EDITO_CURRENT_PRODUCT)
    dataset_link = next((link for link in product['links']
                         if link.get('rel') == 'child'
                         and link['href'].rsplit('/', 1)[-1] == 'copernicus-marine-dataset-' + dataset_id), None)
    if dataset_link is None:
        raise ValueError(f'Current dataset is not linked from the EDITO product: {dataset_id}')
    dataset = _json(dataset_link['href'])
    assets = {}
    for link in dataset.get('links', []):
        if link.get('rel') != 'item':
            continue
        variable = ('uo' if '/climate_forecast-eastward_sea_water_velocity/' in link['href']
                    else 'vo' if '/climate_forecast-northward_sea_water_velocity/' in link['href'] else None)
        if variable is None or variable in assets:
            continue
        item = _json(link['href'])
        # This service is spatially chunked and efficient for a regional time series.
        asset = item.get('assets', {}).get('arco-time-series')
        if asset is not None:
            assets[variable] = {'item_url': link['href'], 'asset_url': asset['href']}
    if set(assets) != {'uo', 'vo'}:
        raise ValueError('EDITO does not expose both expected current components as time-series assets.')
    if assets['uo']['asset_url'] != assets['vo']['asset_url']:
        raise ValueError('Velocity component assets differ; inspect before combining.')
    return {'provider': 'Copernicus Marine via EDITO Data Catalogue',
            'product_catalogue_url': EDITO_CURRENT_PRODUCT,
            'dataset_catalogue_url': dataset_link['href'], 'dataset_id': dataset_id,
            'components': assets, 'asset_url': assets['uo']['asset_url']}


def _outside(ds, coordinate, low, high):
    values = np.asarray(ds[coordinate].values)
    if values.ndim != 1 or not np.all(values[1:] > values[:-1]):
        raise ValueError(f'{coordinate} must increase strictly.')
    if np.issubdtype(values.dtype, np.number):
        if np.isclose(values[0], low, rtol=0, atol=1e-6):
            low = values[0]
        if np.isclose(values[-1], high, rtol=0, atol=1e-6):
            high = values[-1]
    if values[0] > low or values[-1] < high:
        raise ValueError(f'EDITO asset does not cover requested {coordinate} bounds.')
    first = max(0, int(np.searchsorted(values, low, side='right')) - 1)
    last = min(len(values), int(np.searchsorted(values, high, side='left')) + 1)
    return ds.isel({coordinate: slice(first, last)})


def download_edito_currents(request, output_path):
    """Subset a public catalogue-linked Zarr asset and normalize its CF depth."""
    source = resolve_edito_current_asset(request['dataset_id'])
    remote = xr.open_zarr(source['asset_url'], consolidated=True, zarr_format=2, chunks=None)
    try:
        subset = remote[['uo', 'vo']]
        if 'elevation' in subset.coords:
            # Native Zarr elevation is negative below sea level. OpenDrift's
            # existing notebook validation expects positive-down depth in metres.
            subset = subset.rename({'elevation': 'depth'})
            subset = subset.assign_coords(depth=-subset.depth).sortby('depth')
        if 'depth' not in subset.coords:
            raise ValueError('Current asset has no depth/elevation coordinate.')
        subset.depth.attrs = dict(standard_name='depth', long_name='Depth',
                                  units='m', positive='down', axis='Z')
        subset = _outside(subset, 'longitude', request['minimum_longitude'], request['maximum_longitude'])
        subset = _outside(subset, 'latitude', request['minimum_latitude'], request['maximum_latitude'])
        subset = _outside(subset, 'time', np.datetime64(request['start_datetime']),
                          np.datetime64(request['end_datetime']))
        # Include the shallower and deeper adjacent levels around the requested range.
        subset = _outside(subset, 'depth', request['minimum_depth'], request['maximum_depth'])
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = output_path.with_suffix('.partial.nc')
        subset.attrs = dict(subset.attrs, current_access_provider=source['provider'],
                            edito_dataset_catalogue=source['dataset_catalogue_url'])
        print('Reading catalogue current subset:', dict(subset.sizes), flush=True)
        subset.to_netcdf(temporary)
        temporary.replace(output_path)
        source['subset_dimensions'] = dict(subset.sizes)
        source['subset_request'] = request
        output_path.with_suffix('.source.json').write_text(json.dumps(source, indent=2) + '\n')
    finally:
        remote.close()
    return source
