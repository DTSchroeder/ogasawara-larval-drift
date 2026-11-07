import sys,json,tempfile
from pathlib import Path
import numpy as np
import xarray as xr
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edito_export import export_edito_density
# Include both upper-edge positions, a retired particle and an over-age particle.
ds=xr.Dataset({
 'lon':(('trajectory','time'),[[0.,1.],[0.5,0.5],[0.5,0.5]]),
 'lat':(('trajectory','time'),[[0.,1.],[0.5,0.5],[0.5,0.5]]),
 'status':(('trajectory','time'),[[0,0],[0,1],[0,0]]),
 'age_seconds':(('trajectory','time'),np.array([[0,86400],[0,86400],[0,2*86400]])),
 'origin_marker':(('trajectory','time'),[[0,0],[1,1],[1,1]])},
 coords={'time':np.array(['2025-05-01','2025-05-02'],dtype='datetime64[ns]'),'trajectory':[0,1,2]})
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)/'grid.nc';report=export_edito_density(ds,p,['a','b'],[0,1,0,1],0.5,max_age_days=1)
 assert report['active_particles_per_time']==[3,1]
 with xr.open_dataset(p) as grid,xr.open_dataset(report['cell_area_path']) as area:
  assert grid.particle_count.dims==('time','latitude','longitude')
  np.testing.assert_allclose((grid.particle_density*area.cell_area).sum(('latitude','longitude')),[3,1],rtol=1e-6)
  np.testing.assert_allclose(grid.particle_density,grid.particle_density_source_0_a+grid.particle_density_source_1_b,rtol=1e-6)
  assert grid.latitude.attrs['units']=='degrees_north'
 with xr.open_dataset(p,decode_times=False) as grid:
  assert grid.time.attrs['calendar']=='standard' and 'since 1970' in grid.time.attrs['units']
 outside=ds.copy(deep=True);outside.lon.values[0,0]=2
 try:export_edito_density(outside,p,['a','b'],[0,1,0,1],0.5)
 except ValueError as e:assert 'outside' in str(e)
 else:raise AssertionError('Outside particles silently lost')
print('Passed count conservation, source sums, density-area integration, boundary bins, retirement/age exclusion, time encoding, and domain rejection.')
