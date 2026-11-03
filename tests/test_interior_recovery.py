import unittest,math
from app.declarative_interior import furniture,u_staircase
from app.blender_clearance import audit_clearance
from app.blender_render_options import validate_render_options
class InteriorRecovery(unittest.TestCase):
 def test_all_furniture_envelopes_and_rotations(self):
  for kind in ('sofa','bed','table','chair','cabinet','desk'):
   for turns in range(4):
    objects=furniture('test',[10,-20,3],2,1,1.5,kind,quarter_turns=turns);self.assertEqual(len(objects),len({o['id'] for o in objects}))
    for o in objects:
     for i,(c,d) in enumerate(zip(o['location'],o['dimensions'])):
      low=[10-(1 if turns%2 else 2)/2,-20-(2 if turns%2 else 1)/2,3][i];high=low+[(1 if turns%2 else 2),(2 if turns%2 else 1),1.5][i];self.assertGreaterEqual(c-d/2,low-1e-9);self.assertLessEqual(c+d/2,high+1e-9)
 def test_furniture_has_no_positive_volume_self_overlap(self):
  for kind in ('sofa','bed','table','chair','cabinet','desk'):
   for turns in range(4):
    objects=furniture('test',[10,-20,3],2,1,1.5,kind,quarter_turns=turns)
    for i,a in enumerate(objects):
     for b in objects[i+1:]:
      lengths=[min(a['location'][j]+a['dimensions'][j]/2,b['location'][j]+b['dimensions'][j]/2)-max(a['location'][j]-a['dimensions'][j]/2,b['location'][j]-b['dimensions'][j]/2) for j in range(3)]
      self.assertLessEqual(min(lengths),1e-9,(kind,a['id'],b['id']))
 def test_stair_top_and_width(self):
  r=u_staircase('stair',[-2.8,1.94,.47],2.2,3.08,3.03,16,1,.2);self.assertAlmostEqual(r['receipt']['top_z'],3.5);self.assertAlmostEqual(r['receipt']['flight_width'],1);self.assertEqual(len(r['objects']),17)
 def test_bad_furniture(self):
  for bad in [0,-1,float('nan'),True]:
   with self.assertRaises(ValueError):furniture('a',[0,0,0],bad,1,1,'chair')
 def test_clearance_touching_vs_containment(self):
  z=dict(name='aisle',location=[0,0,1],dimensions=[1,4,2],ignore_ids=[]);o={'chair':dict(location=[1,0,1],dimensions=[1,1,2])};self.assertEqual(audit_clearance(o,[z])['zones'][0]['status'],'clear');o['chair']['location']=[0,0,1];self.assertEqual(audit_clearance(o,[z])['zones'][0]['status'],'blocked')
 def test_render_validation(self):
  self.assertEqual(validate_render_options({'hide_ids':['roof']},['roof'])['hide_ids'],['roof'])
  for args in [{'hide_ids':['missing']},{'camera':{'position':[0,0,0],'target':[0,0,0],'lens':24}},{'script':'bad'}]:
   with self.assertRaises(ValueError):validate_render_options(args,['roof'])
if __name__=='__main__':unittest.main()
