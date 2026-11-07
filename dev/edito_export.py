"""Convert saved OpenDrift positions into regular CF-style grids for MyOcean."""
from pathlib import Path
from datetime import datetime, timezone
import re
import numpy as np
import xarray as xr
from pyproj import Geod


def export_edito_density(trajectories, path, source_names, bounds,
                         resolution_deg=0.1, max_age_days=30, depth_m=1.0):
    """Snapshot counts/density of active particles, never residence-time sums.

    Grid-cell counts conserve all valid active positions at each saved time.
    The fixed horizontal grid is WGS84. Density is particles/km2 at the model's
    fixed depth, not abundance, recruitment, or a volumetric concentration.
    """
    west, east, south, north = map(float, bounds)
    if not (np.isfinite(resolution_deg) and resolution_deg > 0
            and -180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError('Provide increasing geographic bounds and positive grid resolution.')
    if max_age_days <= 0 or not source_names:
        raise ValueError('Provide positive max_age_days and source names.')
    nlon = int(np.ceil((east-west) / resolution_deg - 1e-10))
    nlat = int(np.ceil((north-south) / resolution_deg - 1e-10))
    xedges = np.linspace(west, east, nlon+1)
    yedges = np.linspace(south, north, nlat+1)
    lon = trajectories.lon.transpose('trajectory', 'time').values
    lat = trajectories.lat.transpose('trajectory', 'time').values
    status = trajectories.status.transpose('trajectory', 'time').values
    age = trajectories.age_seconds.transpose('trajectory', 'time').values / 86400
    marker = trajectories.origin_marker.transpose('trajectory', 'time').values
    times = np.asarray(trajectories.time.values, dtype='datetime64[ns]')
    if times.ndim != 1 or len(times) == 0 or np.isnat(times).any() or not np.all(times[1:] > times[:-1]):
        raise ValueError('Saved time coordinates must be finite and strictly increasing.')
    # Fail before allocating an unexpectedly large in-memory visualization grid.
    estimated_bytes = len(times)*nlat*nlon*4*(2+len(source_names))
    if estimated_bytes > 1_000_000_000:
        raise ValueError('Visualization grid exceeds 1 GB in memory; increase resolution_deg.')
    total = np.zeros((len(times), nlat, nlon), dtype='float32')
    source_counts = [np.zeros_like(total) for _ in source_names]
    valid_counts = []
    for j in range(len(times)):
        keep = (np.isfinite(lon[:, j]) & np.isfinite(lat[:, j])
                & np.isfinite(age[:, j]) & (status[:, j] == 0)
                & (age[:, j] >= 0) & (age[:, j] <= max_age_days))
        x, y, sources = lon[keep, j], lat[keep, j], marker[keep, j]
        if np.any((x < west) | (x > east) | (y < south) | (y > north)):
            raise ValueError('Active particles fall outside the export grid. Widen bounds.')
        if np.any(~np.isfinite(sources) | (sources != np.floor(sources))
                  | (sources < 0) | (sources >= len(source_names))):
            raise ValueError('An active particle has an unknown source marker.')
        for source, counts in enumerate(source_counts):
            selected = sources == source
            counts[j] = np.histogram2d(y[selected], x[selected], bins=(yedges, xedges))[0]
            total[j] += counts[j]
        valid_counts.append(int(keep.sum()))
    if not np.array_equal(total.sum(axis=(1, 2)), valid_counts):
        raise ValueError('Export grid did not conserve active particle counts.')
    geod = Geod(ellps='WGS84')
    row_area = []
    for low, high in zip(yedges[:-1], yedges[1:]):
        area, _ = geod.polygon_area_perimeter(
            [xedges[0], xedges[1], xedges[1], xedges[0]], [low, low, high, high])
        row_area.append(abs(area)/1e6)
    area_km2 = np.asarray(row_area)[:, None] * np.ones((1, nlon))
    coords = dict(time=times, latitude=(yedges[:-1]+yedges[1:])/2,
                  longitude=(xedges[:-1]+xedges[1:])/2)
    density_attrs = dict(units='km-2',
        comment='Equal-weight numerical particles per horizontal square kilometre at fixed depth; not observed larval abundance.',
        cell_methods='time: point')
    data = {'particle_count': (('time', 'latitude', 'longitude'), total,
                               dict(units='1', long_name='Active model particles per grid cell',
                                    cell_methods='time: point latitude: longitude: sum')),
            'particle_density': (('time', 'latitude', 'longitude'),
                                 (total/area_km2).astype('float32'),
                                 dict(density_attrs, long_name='Active model particle density, all sources'))}
    for source, name in enumerate(source_names):
        slug = re.sub('[^a-z0-9]+', '_', str(name).lower()).strip('_')
        key = f'particle_density_source_{source}_{slug}'
        data[key] = (('time', 'latitude', 'longitude'),
                     (source_counts[source]/area_km2).astype('float32'),
                     dict(density_attrs, long_name=f'Active model particle density from {name}',
                          source_index=source))
    ds = xr.Dataset(data, coords=coords, attrs={
        'Conventions': 'CF-1.8', 'title': 'Ogasawara passive larval-drift particle density',
        'summary': 'Regular-grid snapshot density derived from OpenDrift trajectories; illustrative passive transport, not species-calibrated recruitment.',
        'source': 'OpenDrift OceanDrift numerical particles',
        'history': f'{datetime.now(timezone.utc).isoformat()}: binned active saved positions on a WGS84 grid',
        'geospatial_lon_min': west, 'geospatial_lon_max': east,
        'geospatial_lat_min': south, 'geospatial_lat_max': north,
        'geospatial_bounds_crs': 'EPSG:4326', 'model_particle_depth_m': float(depth_m),
        'maximum_particle_age_days': float(max_age_days),
        'time_coverage_start': np.datetime_as_string(times[0], unit='s')+'Z',
        'time_coverage_end': np.datetime_as_string(times[-1], unit='s')+'Z',
        'comment': 'Zero means no valid active particles in that cell at that saved time. No land mask is applied; cells may overlap land. Grid resolution does not increase the forcing resolution. No biological mortality weighting.'})
    ds.time.attrs = dict(standard_name='time', long_name='Time', axis='T')
    ds.latitude.attrs = dict(standard_name='latitude', long_name='Latitude', units='degrees_north', axis='Y')
    ds.longitude.attrs = dict(standard_name='longitude', long_name='Longitude', units='degrees_east', axis='X')
    # Keep only viewer-supported time/latitude/longitude dimensions in this file.
    # Cell area is exported separately to support independent density integration.
    area_path = Path(path).with_name(Path(path).stem+'_cell_area.nc')
    xr.Dataset({'cell_area': (('latitude', 'longitude'), area_km2,
                              dict(standard_name='cell_area', units='km2'))},
               coords={k: ds.coords[k] for k in ['latitude', 'longitude']},
               attrs={'Conventions': 'CF-1.8'}).to_netcdf(area_path)
    encoding = {name: dict(zlib=True, complevel=4, dtype='float32',
                           chunksizes=(1, min(nlat, 128), min(nlon, 128)),
                           _FillValue=np.float32(-9999)) for name in ds.data_vars}
    encoding.update({name: {'_FillValue': None} for name in coords})
    encoding['time'].update(units='seconds since 1970-01-01 00:00:00', calendar='standard', dtype='float64')
    path = Path(path)
    ds.to_netcdf(path, engine='netcdf4', format='NETCDF4', encoding=encoding)
    with xr.open_dataset(path) as reopened:
        if not np.array_equal(reopened.particle_count.sum(('latitude', 'longitude')).values, valid_counts):
            raise ValueError('NetCDF round-trip count check failed.')
    return {'path': str(path), 'cell_area_path': str(area_path),
            'bytes': path.stat().st_size, 'dimensions': dict(ds.sizes),
            'variables': list(ds.data_vars), 'active_particles_per_time': valid_counts,
            'count_conservation': 'passed', 'viewer_import_tested': False}


import json
from pathlib import Path
import numpy as np


def export_trajectory_geojson(trajectories, path, source_names,
                              max_per_source=30, output_stride=6, max_age_days=30):
    """Static sampled paths for map import; full-resolution tracks stay in NetCDF.

    Split at missing/inactive positions and longitude jumps over 180 degrees.
    Sample each contiguous segment, retaining its first and last positions.
    """
    if max_per_source < 1 or output_stride < 1 or max_age_days <= 0:
        raise ValueError('Use positive sample size, output stride and maximum age.')
    if int(max_per_source) != max_per_source or int(output_stride) != output_stride:
        raise ValueError('Sample size and output stride must be integers.')
    lon = trajectories.lon.transpose('trajectory', 'time').values
    lat = trajectories.lat.transpose('trajectory', 'time').values
    status = trajectories.status.transpose('trajectory', 'time').values
    age = trajectories.age_seconds.transpose('trajectory', 'time').values / 86400
    marker = trajectories.origin_marker.transpose('trajectory', 'time').values
    times = np.asarray(trajectories.time.values, dtype='datetime64[s]')
    if np.isnat(times).any() or not np.all(times[1:] > times[:-1]):
        raise ValueError('Time must be finite and strictly increasing.')
    sources = np.full(lon.shape[0], -1, dtype=int)
    for i, values in enumerate(marker):
        finite = values[np.isfinite(values)]
        if not len(finite) or not np.all(finite == finite[0]):
            raise ValueError('Missing or changing source marker.')
        value = finite[0]
        if value != int(value) or not 0 <= value < len(source_names):
            raise ValueError('Unknown source marker.')
        sources[i] = int(value)
    features = []
    selected_counts = []
    colors = ['#e76f51', '#277da8', '#7b2cbf']
    for source, name in enumerate(source_names):
        candidates = np.flatnonzero(sources == source)
        selected = candidates[np.linspace(0, len(candidates)-1,
                              min(len(candidates), int(max_per_source)), dtype=int)]
        selected_counts.append(len(selected))
        for i in selected:
            valid = (np.isfinite(lon[i]) & np.isfinite(lat[i])
                     & (np.abs(lon[i]) <= 180) & (np.abs(lat[i]) <= 90)
                     & (status[i] == 0) & np.isfinite(age[i])
                     & (age[i] >= 0) & (age[i] <= max_age_days))
            indices = np.flatnonzero(valid)
            cuts = np.flatnonzero((np.diff(indices) != 1)
                                  | (np.abs(np.diff(lon[i, indices])) > 180)) + 1
            for segment, idx in enumerate(np.split(indices, cuts)):
                if len(idx) < 2:
                    continue
                take = np.unique(np.r_[idx[::int(output_stride)], idx[-1]])
                coordinates = np.column_stack((lon[i, take], lat[i, take])).astype(float).round(6).tolist()
                features.append({'type': 'Feature', 'properties': {
                    'name': f'{name} — particle {i}, segment {segment}',
                    'source': str(name), 'source_index': source,
                    'trajectory_index': int(i), 'segment': segment,
                    'start_utc': str(times[take[0]])+'Z',
                    'end_utc': str(times[take[-1]])+'Z',
                    'display': 'Static full-period sampled trajectory; not time filtered',
                    'stroke': colors[source % len(colors)], 'stroke-width': 1.5,
                    'stroke-opacity': 0.6},
                    'geometry': {'type': 'LineString', 'coordinates': coordinates}})
    if not features:
        raise ValueError('No valid trajectory segments with at least two positions.')
    # One MultiLineString per source keeps the viewer's labels manageable.
    grouped = []
    for source, name in enumerate(source_names):
        parts = [f for f in features if f['properties']['source_index'] == source]
        if not parts:
            continue
        particles = len({f['properties']['trajectory_index'] for f in parts})
        grouped.append({'type': 'Feature', 'properties': {
            'name': f'{name} — {particles} sampled drift paths (static)',
            'source': str(name), 'source_index': source,
            'sampled_particles': particles, 'output_stride': int(output_stride),
            'start_utc': min(f['properties']['start_utc'] for f in parts),
            'end_utc': max(f['properties']['end_utc'] for f in parts),
            'display': 'Static full-period sampled trajectories; not time filtered',
            'stroke': colors[source % len(colors)], 'stroke-width': 1.5},
            'geometry': {'type': 'MultiLineString',
                         'coordinates': [f['geometry']['coordinates'] for f in parts]}})
    collection = {'type': 'FeatureCollection',
                  'name': 'Ogasawara sampled drift paths (static)',
                  'features': grouped}
    path = Path(path)
    path.write_text(json.dumps(collection, separators=(',', ':'), allow_nan=False))
    return {'path': str(path), 'features': len(grouped), 'line_segments': len(features),
            'selected_particles_per_source': selected_counts,
            'maximum_per_source': int(max_per_source), 'output_stride': int(output_stride),
            'bytes': path.stat().st_size, 'time_animation': False}
