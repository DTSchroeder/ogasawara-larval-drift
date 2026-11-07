"""Offline checks for depth conversion, bracketing and source consistency."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import numpy as np
import xarray as xr
import edito_catalogue as catalogue


def main():
    dataset_id = 'test-current'
    dataset_url = 'https://example.org/dataset'
    east = 'https://example.org/climate_forecast-eastward_sea_water_velocity/items/u'
    north = 'https://example.org/climate_forecast-northward_sea_water_velocity/items/v'
    asset_url = 'https://example.org/current.zarr'
    records = {
        catalogue.EDITO_CURRENT_PRODUCT: {'links': [{'rel': 'child', 'href':
            'https://example.org/copernicus-marine-dataset-' + dataset_id}]},
        'https://example.org/copernicus-marine-dataset-' + dataset_id:
            {'links': [{'rel': 'item', 'href': east}, {'rel': 'item', 'href': north}]},
        east: {'assets': {'arco-time-series': {'href': asset_url}}},
        north: {'assets': {'arco-time-series': {'href': asset_url}}},
    }
    shape = (4, 3, 4, 4)
    ds = xr.Dataset({name: (('time', 'elevation', 'latitude', 'longitude'),
                                  np.full(shape, value, dtype='float32'))
                     for name, value in [('uo', 0.1), ('vo', -0.2)]},
                    coords={'time': np.arange('2025-05-01', '2025-05-05', dtype='datetime64[D]'),
                            'elevation': [-3., -1.5, -0.5], 'latitude': [21., 22., 23., 24.],
                            'longitude': [136., 137., 138., 139.]})
    request = dict(dataset_id=dataset_id, minimum_longitude=137.1, maximum_longitude=138.1,
                   minimum_latitude=22.1, maximum_latitude=23.1, minimum_depth=0.5,
                   maximum_depth=2., start_datetime='2025-05-01T12:00:00',
                   end_datetime='2025-05-03T12:00:00')
    with patch.object(catalogue, '_json', side_effect=records.__getitem__):
        assert catalogue.resolve_edito_current_asset(dataset_id)['asset_url'] == asset_url
        with TemporaryDirectory() as tmp, patch.object(catalogue.xr, 'open_zarr', return_value=ds.copy()) as opened:
            path = Path(tmp)/'currents.nc'
            catalogue.download_edito_currents(request, path)
            assert opened.call_args.kwargs['chunks'] is None  # no global Dask graph
            assert opened.call_args.kwargs['zarr_format'] == 2
            with xr.open_dataset(path) as result:
                np.testing.assert_array_equal(result.depth, [0.5, 1.5, 3.])
                assert result.depth.attrs['positive'] == 'down'
                assert result.longitude.min() <= 137.1 and result.longitude.max() >= 138.1
                assert result.latitude.min() <= 22.1 and result.latitude.max() >= 23.1
                assert result.time.values[0] < np.datetime64(request['start_datetime'])
                assert result.time.values[-1] > np.datetime64(request['end_datetime'])
                np.testing.assert_allclose(result.vo, -0.2)
            metadata = json.loads(path.with_suffix('.source.json').read_text())
            assert metadata['components']['uo']['asset_url'] == metadata['components']['vo']['asset_url']
        records[north]['assets']['arco-time-series']['href'] = 'https://example.org/other.zarr'
        try:
            catalogue.resolve_edito_current_asset(dataset_id)
        except ValueError as error:
            assert 'differ' in str(error)
        else:
            raise AssertionError('Different component stores were silently combined')
    try:
        catalogue._outside(ds, 'latitude', 20., 23.)
    except ValueError as error:
        assert 'does not cover' in str(error)
    else:
        raise AssertionError('Unsupported bounds silently accepted')
    print('Passed EDITO source consistency, bounded reads, depth sign/order, bracketing, round-trip, and coverage rejection checks.')


if __name__ == '__main__':
    main()
