import unittest,math
from collections import Counter
from app.declarative_architecture import window_wall,sloped_closure,floor_opening,leaf_rosette,scoped_replacement_patch
from app.blender_views import fitted_axis_camera
class ArchitectureRecovery(unittest.TestCase):
 def test_closed_roof_solid(self):
  o=sloped_closure('cap',-4,1,3.8,4,3.5,6.5,7.8,{})
  e=Counter(tuple(sorted((f[i],f[(i+1)%len(f)]))) for f in o['faces'] for i in range(len(f)));self.assertEqual(set(e.values()),{2})
 def test_window_volume(self):
  o=window_wall('wall',-4,4,3,.2,0,3,[[-1,1,1,2]],{},{},{})
  self.assertAlmostEqual(sum(math.prod(x['dimensions']) for x in o if '_wall_' in x['id']),4.4)
 def test_two_one_zero_cleanup_and_keep(self):
  scene={'KEEP':{'id':'KEEP'}};ids=[]
  for openings in [[[-3,-2,1,2],[1,2,1,2]],[[-1,1,1,2]],[]]:
   objects=window_wall('wall',-4,4,3,.2,0,3,openings,{},{},{})
   p=scoped_replacement_patch(objects,ids,scene)
   for n in p['delete_ids']:scene.pop(n)
   scene.update({o['id']:o for o in objects});ids=[o['id'] for o in objects]
   self.assertEqual(set(scene),set(ids)|{'KEEP'});self.assertEqual(scene['KEEP'],{'id':'KEEP'})
 def test_collision_rejected(self):
  objects=window_wall('wall',-4,4,3,.2,0,3,[],{},{},{})
  with self.assertRaises(ValueError):scoped_replacement_patch(objects,[],{'wall_wall_0_0'})
 def test_missing_prior_rejected(self):
  with self.assertRaises(ValueError):scoped_replacement_patch([],['missing'],set())
 def test_fitted_translated_large_cameras(self):
  for bounds in [[(100,110),(-200,-190),(20,30)],[(-500,500),(-1,1),(-20,20)]]:
   for view in ['front_elevation','rear_elevation','left','right','top','bottom']:
    pos,center,scale,clip=fitted_axis_camera(view,bounds);self.assertEqual(center,tuple((a+b)/2 for a,b in bounds));self.assertGreater(scale,max(b-a for a,b in bounds))
 def test_floor_void(self):
  o=floor_opening('floor',-4,4,-4,4,3,.4,[-3,-1,0,3],{});self.assertAlmostEqual(sum(math.prod(x['dimensions']) for x in o),58*.4)
 def test_rosette_closed_seeded(self):
  o=leaf_rosette('plant',[0,0,0]);self.assertEqual(o,leaf_rosette('plant',[0,0,0]));self.assertEqual(len(o['faces']),144)
  for f in o['faces']:
   p,q,r=[o['vertices'][i] for i in f];u=[q[i]-p[i] for i in range(3)];v=[r[i]-p[i] for i in range(3)];cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];self.assertGreater(sum(x*x for x in cross),1e-12)
 def test_bad_openings(self):
  for openings in [[[-5,1,1,2]],[[-1,1,1,2],[0,2,1,2]],[[float('nan'),1,1,2]]]:
   with self.assertRaises(ValueError):window_wall('wall',-4,4,3,.2,0,3,openings,{},{},{})
if __name__=='__main__':unittest.main()
