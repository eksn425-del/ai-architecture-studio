import json
from app.blender_backend import BlenderBackend
import pytest

def test_component_preparation_is_read_only_and_rejects_unrelated_collision(tmp_path,monkeypatch):
 monkeypatch.setattr('app.blender_backend.shutil.which',lambda _: '/usr/bin/blender')
 b=BlenderBackend(tmp_path);args={'kind':'window_wall','parameters':dict(name='wall',start=-4,end=4,plane=3,thickness=.2,base=0,height=3,openings=[],wall_material={},glass_material={},frame_material={}), 'previous_ids':[]}
 q=b.dispatch('blender_prepare_component',args);assert q['writes_performed']==0 and not b.state.exists()
 original={'objects':{'wall_wall_0_0':{'id':'wall_wall_0_0','location':[99,99,0],'dimensions':[1,1,1]}},'revision':1};b.state.write_text(json.dumps(original))
 with pytest.raises(ValueError,match='collision'):b.dispatch('blender_prepare_component',args)
 assert json.loads(b.state.read_text())==original
 args['previous_ids']=['wall_wall_0_0'];assert b.dispatch('blender_prepare_component',args)['component_ids']==['wall_wall_0_0']

def test_tool_signature_and_policy_expose_inference_limits(tmp_path,monkeypatch):
 monkeypatch.setattr('app.blender_backend.shutil.which',lambda _: '/usr/bin/blender')
 b=BlenderBackend(tmp_path);d=next(t for t in b.tools() if t['name']=='blender_prepare_component')['description']
 for term in ['window_wall(name,start,end,plane','floor_opening(name','quarter_turns','component_ids','metres']:assert term in d
 from pathlib import Path
 text=Path('app/blender_workflow.py').read_text()
 for term in ['First-turn quality is judged separately','inferred design','same model','finite stage budget']:assert term in text

def test_complete_furniture_receipt_removes_top_and_all_legs():
 from app.declarative_interior import furniture
 from app.declarative_architecture import scoped_replacement_patch
 table=furniture('table',[0,0,0],2,1,.8,'table');ids=[o['id'] for o in table]
 assert 'table_top' in ids and len([n for n in ids if '_leg_' in n])==4
 scene={o['id']:o for o in table};scene['KEEP']={'id':'KEEP'}
 patch=scoped_replacement_patch([],ids,scene)
 for name in patch['delete_ids']:scene.pop(name)
 assert scene=={'KEEP':{'id':'KEEP'}}

def test_furniture_kind_change_does_not_leave_old_parts():
 from app.declarative_interior import furniture
 from app.declarative_architecture import scoped_replacement_patch
 old=furniture('piece',[0,0,0],2,1,.8,'desk');new=furniture('piece',[0,0,0],2,1,.8,'chair');scene={o['id']:o for o in old};scene['KEEP']={'id':'KEEP'}
 patch=scoped_replacement_patch(new,[o['id'] for o in old],scene)
 for name in patch['delete_ids']:scene.pop(name)
 scene.update({o['id']:o for o in new})
 assert set(scene)=={'KEEP'}|{o['id'] for o in new}
