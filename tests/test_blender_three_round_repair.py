"""Real Blender mechanics with deterministic assistant/critic fixtures, not vision QA."""
import hashlib
import io
import json
import shutil
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from app.main import create_app
from app.native_agent import AgentTurnResult
from app.agent_tools import AgentToolSurface
from app.reference_roles import (reference_manifest,current_model_revisions,validate_review_requirements,
                                load_approved_design_scope,requirement_id)

@pytest.mark.skipif(not shutil.which('blender'),reason='real Blender required')
def test_actual_three_round_scoped_edits_and_keep(tmp_path):
    class Simulation:
        available=True;model='deterministic-three-round-fixture';reasoning_effort='low'
        history=[];calls=0
        def respond(self,**kw):
            self.calls+=1
            project=kw['project_dir']
            surface=AgentToolSurface(tmp_path,None,oss_backends={})
            tools=surface.prepare(project_dir=project,mcp_enabled=kw['mcp_enabled'],model_path=None,model_guid='',ruby_enabled=False,ruby_state={})
            from app.blender_backend import BlenderBackend
            state=BlenderBackend(project).dispatch('blender_inspect_scene',{})
            rev=state['revision']
            if not kw['mcp_enabled']:
                scope=[] if rev==0 else [{'feature_id':'terrace.rails' if rev==1 else 'street.window',
                    'requested_state':'dark gray metal bars' if rev==1 else 'height 2.192 metres, lower edge fixed'}]
                return AgentTurnResult(thread_id='sim',reply='尺寸单位米。仅改变指定构件，其余保持。\n<design_scope>'+json.dumps(scope)+'</design_scope>' if scope else '初始构件计划：八段栏杆、一扇窗、保护墙。',provider_name='simulation',model_name=self.model,reasoning_effort='low')
            if rev==0:
                objects=[{'id':f'rail_{i}','location':[i*1.5,0,1.5],'dimensions':[1,.08,1],'material':{'color':[.8,.8,.8,1]}} for i in range(8)]
                objects += [{'id':'window','location':[0,3,2.37],'dimensions':[1.2,.08,2.74]}, {'id':'KEEP_wall','location':[0,5,2],'dimensions':[12,.2,4]}]
            elif rev==1:
                objects=[]
                # Three separated vertical metal bars per segment, same outer bounds.
                vertices=[];faces=[]
                cube_faces=[[0,1,3,2],[2,3,7,6],[6,7,5,4],[4,5,1,0],[2,6,4,0],[7,3,1,5]]
                for x in [-.45,0,.45]:
                    offset=len(vertices)
                    vertices += [[x+dx,dy,z] for dx in [-.05,.05] for dy in [-.04,.04] for z in [-.5,.5]]
                    faces += [[offset+j for j in face] for face in cube_faces]
                for i in range(8):
                    old=state['objects'][f'rail_{i}']
                    objects.append({'id':old['id'],'location':old['location'],'vertices':vertices,'faces':faces,'material':{'color':[.12,.12,.12,1],'roughness':.25}})
            else:
                objects=[{**state['objects']['window'],'location':[0,3,2.096],'dimensions':[1.2,.08,2.192]},
                         {'id':'window_upper_infill','location':[0,3,3.466],'dimensions':[1.2,.08,.548]}]
            receipt=tools.dispatch('blender_apply_objects',{'objects':objects})
            # A simulated Critic envelope is validated by production lifecycle logic.
            manifest=reference_manifest(project,list((project/'inputs/reference').glob('*')))
            source=next(x['source'] for x in manifest if x['role']=='target_building')
            revisions=current_model_revisions(project)
            if rev==0:
                requirements=[{'feature_id':feature,'desired_state':text,'source_ref':source,'model_revisions':revisions,'intent':{'property':prop,'value':value}}
                    for feature,text,prop,value in [('terrace.rails','white rails','color','white'),('street.window','height 2.74','height',2.74)]]
            else:
                feature='terrace.rails' if rev==1 else 'street.window'
                old=next(r for row in self.history for r in row['requirements'] if r['feature_id']==feature)
                scope=load_approved_design_scope(project)
                requested=next(x['requested_state'] for x in scope['features'] if x['feature_id']==feature)
                requirements=[{'feature_id':feature,'desired_state':requested,'source_ref':source,'model_revisions':revisions,
                    'intent':{'property':'color' if rev==1 else 'height','value':'dark gray' if rev==1 else 2.192},
                    'relation':'supersedes','prior_requirement_id':requirement_id(old),'evidence':'Explicit displayed-plan approval; deterministic dimensions checked.',
                    'design_scope_version':scope['version'],'approved_requested_state':requested}]
            checked=validate_review_requirements('<review_requirements>'+json.dumps(requirements)+'</review_requirements>',manifest=manifest,revisions=revisions,issue_count=len(requirements),history=self.history,approved_scope=load_approved_design_scope(project))
            self.history.append({'requirements':checked})
            return AgentTurnResult(thread_id='sim',reply='模拟响应：几何已提交，真实 Blender 保存重开。视觉质量未验证。',provider_name='simulation',model_name=self.model,reasoning_effort='low',tool_calls=[{'name':'blender_apply_objects'}])
    sim=Simulation();app=create_app(runtime_root=tmp_path,native_agent=sim);client=TestClient(app)
    pid=client.post('/api/projects',json={'project_name':'Three round technical fixture'}).json()['project_id'];base='/api/projects/'+pid
    assert client.post(base+'/blender/session').status_code==200
    image=io.BytesIO();Image.new('RGB',(16,16),'white').save(image,format='PNG')
    upload=client.post(base+'/inputs/reference?filename=technical-fixture.png&evidence_role=target_building',content=image.getvalue())
    assert upload.status_code==200,upload.text
    receipts=[]
    for round_number in range(3):
        message=['先制定初始计划','栏杆改成深灰金属竖杆，先给我计划，确认后再执行。','先说明窗户降低20%的衔接方案，等我确认。'][round_number]
        planned=client.post(base+'/conversation',json={'message':message,'agent_action':'auto' if round_number else 'plan'})
        assert planned.status_code==200,planned.text
        assert planned.json()['agent']['agent_action']=='plan'
        assert planned.json()['agent']['geometry_committed'] is False
        project=app.state.store.project_dir(pid)
        card=project/'runtime/agent_workspace/notes/reconstruction_card.md'
        digest=hashlib.sha256(card.read_text(encoding='utf-8').encode()).hexdigest()
        if round_number:
            before_calls=sim.calls
            rejected=client.post(base+'/conversation',json={'message':'确认执行','agent_action':'execute','approved_plan_sha256':'0'*64})
            assert rejected.status_code==409,rejected.text
            assert sim.calls==before_calls
        result=client.post(base+'/conversation',json={'message':'确认执行','agent_action':'execute','approved_plan_sha256':digest})
        assert result.status_code==200,result.text
        receipt=result.json()['agent']['model_info'];receipts.append(receipt)
        assert receipt['revision']==round_number+1 and receipt['native_reopen']=='PASS'
        assert result.json()['agent']['geometry_committed'] is True
        assert client.get(base+'/files/'+receipt['model_path']).status_code==200
    a,b,c=receipts
    assert a['geometry']['KEEP_wall']==b['geometry']['KEEP_wall']==c['geometry']['KEEP_wall']
    assert a['geometry']['window']==b['geometry']['window']
    for i in range(8):
        key=f'rail_{i}'
        assert a['objects'][key]['location']==b['objects'][key]['location']
        assert a['geometry'][key]['dimensions']==pytest.approx(b['geometry'][key]['dimensions'])
        assert len(b['objects'][key]['vertices'])==24 and len(b['objects'][key]['faces'])==18
        assert b['objects'][key]==c['objects'][key]
    assert c['objects']['window']['dimensions'][2]==2.192
    assert c['objects']['window']['location'][2]-2.192/2==pytest.approx(1)
    assert c['objects']['window_upper_infill']['dimensions'][2]==.548
    pause=client.post(base+'/conversation',json={'message':'暂停，不要修改模型。','agent_action':'auto'})
    assert pause.status_code==200 and pause.json()['agent']['geometry_committed'] is False
    (tmp_path/'three-round-results.json').write_text(json.dumps({'provider':'deterministic simulation','receipts':receipts,'history':sim.history},indent=2))
