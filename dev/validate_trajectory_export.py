"""Check grouped trajectory export without ocean-data downloads."""
import json
from pathlib import Path
import numpy as np
from edito_export import export_trajectory_geojson
import tempfile
import xarray as xr
with tempfile.TemporaryDirectory() as tmp:
    lon=np.array([[142.,142.1,np.nan,142.3,142.4,142.5],[141.,141.1,141.2,141.3,141.4,141.5]])
    status=np.zeros((2,6)); status[0,5]=1
    ds=xr.Dataset({
        'lon':(('trajectory','time'),lon),
        'lat':(('trajectory','time'),np.ones((2,6))*27),
        'status':(('trajectory','time'),status),
        'age_seconds':(('trajectory','time'),np.tile(np.arange(6)*3600,(2,1))),
        'origin_marker':(('trajectory','time'),np.array([[0]*6,[1]*6],dtype=float)),
    },coords={'time':np.datetime64('2025-05-01')+np.arange(6)*np.timedelta64(1,'h')})
    p=Path(tmp)/'tracks.geojson'
    report=export_trajectory_geojson(ds,p,['A','B'],output_stride=6)
    result=json.loads(p.read_text())
    assert report['features']==2 and report['line_segments']==3
    assert result['features'][0]['geometry']['coordinates']==[[[142.,27.],[142.1,27.]],[[142.3,27.],[142.4,27.]]]
    assert result['features'][1]['geometry']['coordinates']==[[[141.,27.],[141.5,27.]]]
    ds.origin_marker.values[0,0]=8
    try: export_trajectory_geojson(ds,p,['A','B'])
    except ValueError: pass
    else: raise AssertionError('Changing source was not rejected')
    print('PASSED: finite coordinates, gap/inactive splitting, endpoint retention, grouped sources and invalid source rejection.')
