import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from app.blender_workflow import checkpoint
from app.models import AgentSession,ModelState,OutputManifest,Artifact
class FakeStore:
 def __init__(self):self.states={}
 def load_state(self,pid,name,kind):
  if name not in self.states:self.states[name]=kind(project_id=pid)
  return self.states[name]
 def save_state(self,pid,value,name):self.states[name]=value
class CutawayRecovery(unittest.TestCase):
 def test_cutaway_never_becomes_normal_viewport(self):
  store=FakeStore();session=AgentSession(project_id='case');manifest=OutputManifest(project_id='case');manifest.model_captures.append(Artifact(id='old',type='viewport',path='cut.png',created_at='now'));store.states['output_manifest.json']=manifest
  receipt={'model_path':'model.blend','revision':1,'renders':{'front':{'image_path':'full.png','revision':1},'cut':{'image_path':'cut.png','revision':1,'cutaway':True,'hidden_ids':['roof']}}}
  checkpoint(store,'case',session,receipt)
  self.assertEqual([a.path for a in store.states['output_manifest.json'].model_captures],['full.png'])
if __name__=='__main__':unittest.main()
