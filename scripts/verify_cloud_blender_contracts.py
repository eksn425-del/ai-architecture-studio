"""Cloud-native regression evidence; deterministic fixture, not independent LLM QA.

Run with the product's Python environment. Native model creation, serialization,
reopen and renders use the unmodified production BlenderBackend/worker boundary.
No owner assets, paid provider or local desktop are accessed.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.blender_backend import BlenderBackend


def fixture_objects():
    """Six repeated bays, intentional central recess, separate protected neighbor."""
    result = []
    def box(name, loc, dims, color):
        result.append(dict(id=name, location=loc, dimensions=dims,
                           material=dict(color=[*color, 1], roughness=.65)))
    cream=[.72,.66,.55]; dark=[.10,.16,.20]
    box('base', [0,1,-.15], [12,5,.3], [.32,.33,.34])
    for floor in range(3):
        z=floor*2.5
        for bay,x in enumerate([-4.5,-2.7,-.9,.9,2.7,4.5]):
            y=.9 if bay in [2,3] else 0
            prefix=f'bay_{floor}_{bay}'
            box(prefix+'_back',[x,y+.6,z+1.15],[1.7,.22,2.3],cream)
            box(prefix+'_glass',[x,y+.46,z+1.3],[1.18,.08,1.65],dark)
            box(prefix+'_slab',[x,y,z],[1.78,1.6,.18],cream)
            box(prefix+'_rail',[x,y-.71,z+.55],[1.65,.07,.60],cream)
    box('KEEP_neighbor',[7,1,2.5],[1.8,3,5],[.25,.34,.26])
    return result


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def run_native(output: Path):
    started=time.time()
    output.mkdir(parents=True, exist_ok=True)
    project=output/'project'
    if (project/'runtime/blender/scene.json').exists():
        raise ValueError('Use a fresh evidence directory; prior native evidence is immutable')
    (project/'state').mkdir(parents=True, exist_ok=True)
    dump(project/'state/modeling_backend.json', {'backend':'blender'})
    backend=BlenderBackend(project)
    first=backend.dispatch('blender_apply_objects', {'objects':fixture_objects()})
    dump(output/'revision-1.json',first)
    before=backend.dispatch('blender_render_scene', {'view':'front','resolution':800,'denoise':False})
    dump(output/'render-before.json',before)
    return {'started_epoch':started,'project':str(project),'first':first,'before':before}


def bind_instruction(project, message, turn_id):
    """Explicit deterministic host fixture, NOT NLP or owner approval inference."""
    from app.design_scope_approval import current_reference_fingerprint
    from app.reference_roles import current_model_revisions
    source='inputs/reference/synthetic-contract-target.png'
    image=project/source
    if not image.exists():
        from PIL import Image, ImageDraw
        image.parent.mkdir(parents=True,exist_ok=True)
        canvas=Image.new('RGB',(800,800),'white'); draw=ImageDraw.Draw(canvas)
        draw.text((20,20),'SYNTHETIC CONTRACT FIXTURE - NOT AN OWNER SOURCE PHOTO',fill='black')
        draw.text((20,45),'Central six rails: dark gray, height 0.45m. Other objects KEEP.',fill='black')
        for floor in range(3):
            for bay in range(6):
                x=30+bay*95; y=120+floor*170
                draw.rectangle((x,y,x+80,y+150),outline='gray',width=3)
                draw.rectangle((x,y+110,x+80,y+145),fill='#263039' if bay in [2,3] else '#bbb6a8')
        draw.rectangle((640,120,760,620),fill='#506950')
        draw.text((640,640),'KEEP_neighbor',fill='black')
        canvas.save(image)
    context={'references':[{'source':source,'evidence_role':'target_building','evidence_turn_id':'synthetic-fixture'}], 'conversation':[{'role':'user', 'content':message,
        'metadata':{'evidence_turn_id':turn_id}}]}
    dump(project/'state/project_context.json',context)
    row={'user_message_id':turn_id,'user_message':message,'execution_granted':True,
         'action':'execute','model_revisions':current_model_revisions(project),
         'reference_fingerprint':current_reference_fingerprint(project)}
    with (project/'runtime/contextual_intent.jsonl').open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(row)+'\n')


def reject_without_mutation(backend, action):
    before=backend.state.read_bytes()
    files={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in backend.root.rglob('*') if p.is_file()}
    try:
        action()
    except ValueError as error:
        assert backend.state.read_bytes()==before
        assert files=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in backend.root.rglob('*') if p.is_file()}
        return {'rejected':True, 'error':str(error), 'scene_and_native_files_unchanged':True}
    raise AssertionError('Expected product denial before mutation')


def review_before_edit(output, initial):
    from app.review_context import prepare_review_context,validate_review_context_current
    from app.reference_roles import current_model_revisions
    project=Path(initial['project'])
    original='Change only central six rail panels to dark gray and 0.45m height; preserve lower edges and KEEP_neighbor.'
    bind_instruction(project,original,'fixture-goal-1')
    context=prepare_review_context(project,current_model_revisions(project),
        {'front':project/initial['before']['image_path']},[])
    assert original in context.prompt
    assert project/initial['before']['image_path'] in context.images
    bind_instruction(project,'Pause geometry; inspect neighbor only.','fixture-goal-2')
    backend=BlenderBackend(project)
    changed=reject_without_mutation(backend,lambda:validate_review_context_current(context))
    bind_instruction(project,original,'fixture-goal-1-restored')
    context=prepare_review_context(project,current_model_revisions(project),
        {'front':project/initial['before']['image_path']},[])
    return context,changed


def progress_observation(receipt,targets):
    states=[]
    for target in targets:
        height=receipt['geometry'][target]['dimensions'][2]
        distance=abs(height-.45)
        states.append({'feature_id':target,'desired_state':'height 0.45 m',
            'observed_state':{'height_m':height},'distance_to_target':distance,
            'status':'satisfied' if distance < 1e-5 else 'unsatisfied'})
    return {'model_revisions':{'blender_scene':receipt['revision']},
            'needs_fix':any(s['status']=='unsatisfied' for s in states),'feature_states':states}


def finish_native(output, initial):
    backend=BlenderBackend(Path(initial['project']))
    first=initial['first']
    targets=[f'bay_{floor}_{bay}_rail' for floor in range(3) for bay in [2,3]]
    context,instruction_denial=review_before_edit(output,initial)
    keep=sorted(set(first['objects'])-set(targets))
    backend.install_edit_contract(allowed_ids=targets,keep_ids=keep,expected_revision=1)
    protected=copy.deepcopy(first['objects']['KEEP_neighbor']);protected['dimensions'][0]+=1
    denials={'keep_update':reject_without_mutation(backend,lambda:backend.dispatch('blender_apply_objects',{'objects':[protected]})),
             'keep_delete':reject_without_mutation(backend,lambda:backend.dispatch('blender_apply_objects',{'objects':[],'delete_ids':['KEEP_neighbor']})),
             'unknown_scope':reject_without_mutation(backend,lambda:backend.dispatch('blender_apply_objects',{'objects':[{'id':'unapproved','location':[0,0,0],'dimensions':[1,1,1]}]})),
             'current_instruction_changed':instruction_denial}
    from app.stage_quality import ReviewProgress
    progress_path=Path(initial['project'])/'runtime/cloud_regression_progress.json'
    fingerprint=context.metadata['review_context_fingerprint']
    progress=ReviewProgress(progress_path,context_fingerprint=fingerprint)
    from app.review_context import finalize_review_context
    requirement={'feature_id':'facade.central.rails','desired_state':'Central six rails dark gray and height 0.45m',
        'source_ref':'inputs/reference/synthetic-contract-target.png','model_revisions':{'blender_scene':1},
        'intent':{'property':'height_m','value':.45},'evidence':'Native r1 dimensions are 0.60m; scripted measurements, not LLM judgment.'}
    first_metadata=finalize_review_context(context,'NEEDS_FIX: YES\n<assessment>Scripted dimensional check.</assessment>\n<issue priority="1" view="front">problem: central rails exceed target height\naction: edit only six central rails</issue>\n<review_requirements>'+json.dumps([requirement])+'</review_requirements>')
    dump(output/'review-before.json',{'metadata':first_metadata,'measurements':progress_observation(first,targets),'synthetic_reply':True})
    progress.observe({'model_revisions':{'blender_scene':1},'needs_fix':True,'reviewer':first_metadata})
    assert len(ReviewProgress(progress_path,context_fingerprint=fingerprint).records)==1
    edits=[]
    for name in targets:
        obj=copy.deepcopy(first['objects'][name])
        obj['material']['color']=[.12,.15,.18,1]
        obj['dimensions'][2]=.45
        obj['location'][2]-=.075  # Preserve lower edge.
        edits.append(obj)
    second=backend.dispatch('blender_apply_objects', {'objects':edits})
    assert all(abs(second['geometry'][k]['dimensions'][2]-.45)<1e-5 for k in targets)
    assert all(all(abs(a-b)<1e-5 for a,b in zip(second['geometry'][k]['material'][0]['color'],[.12,.15,.18,1])) for k in targets)
    assert all(abs((first['geometry'][k]['location'][2]-first['geometry'][k]['dimensions'][2]/2)-(second['geometry'][k]['location'][2]-second['geometry'][k]['dimensions'][2]/2))<1e-5 for k in targets)
    dump(output/'revision-2.json',second)
    after=backend.dispatch('blender_render_scene', {'view':'front','resolution':800,'denoise':False})
    dump(output/'render-after.json',after)
    from app.review_context import prepare_review_context,validate_review_context_current,finalize_review_context
    denials['stale_review_revision']=reject_without_mutation(backend,lambda:validate_review_context_current(context))
    current=prepare_review_context(Path(initial['project']),{'blender_scene':2},
        {'front':Path(initial['project'])/after['image_path']},[])
    assert current.metadata['review_context_fingerprint']==fingerprint
    validate_review_context_current(current)
    resolution={'feature_id':'facade.central.rails','prior_requirement_id':first_metadata['review_requirements'][0]['requirement_id'],
        'status':'resolved','source_ref':requirement['source_ref'],'model_revisions':{'blender_scene':2},
        'evidence':'All six native heights measured 0.45m, dark gray; deterministic native check only.'}
    metadata=finalize_review_context(current,'NEEDS_FIX: NO\n<assessment>Deterministic contract fixture only; no independent visual quality claim.</assessment>\n<review_requirements>[]</review_requirements><requirement_resolutions>'+json.dumps([resolution])+'</requirement_resolutions>')
    dump(output/'review-context.json',{'metadata':metadata,'prompt':current.prompt,
        'image_hashes':current.image_hashes,'model_revisions':current.revisions,
        'synthetic_reply':True,'source_photo_fidelity':'NOT_TESTED'})
    progress=ReviewProgress(progress_path,context_fingerprint=fingerprint)
    progress.observe({'model_revisions':{'blender_scene':2},'needs_fix':False,'reviewer':metadata})
    progress=ReviewProgress(progress_path,context_fingerprint=fingerprint)
    assert len(progress.records)==2 and not progress.blocked
    progress.observe({'model_revisions':{'blender_scene':2},'needs_fix':False,'reviewer':metadata})
    assert len(progress.records)==2
    bind_instruction(Path(initial['project']),'Keep dark rails; inspect only.','fixture-goal-3')
    stale_edit=copy.deepcopy(edits[0]);stale_edit['dimensions'][2]=.44
    denials['stale_write_intent']=reject_without_mutation(backend,lambda:backend.dispatch('blender_apply_objects',{'objects':[stale_edit]}))
    changed_context=prepare_review_context(Path(initial['project']),{'blender_scene':2},
        {'front':Path(initial['project'])/after['image_path']},[])
    changed_progress=ReviewProgress(progress_path,context_fingerprint=changed_context.metadata['review_context_fingerprint'])
    assert not changed_progress.records and not changed_progress.blocked
    unchanged=set(first['geometry'])-set(targets)
    checks={'both_native_reopen':first['native_reopen']==second['native_reopen']=='PASS',
            'actual_revisions':[first['revision'],second['revision']]==[1,2],
            'all_untargeted_geometry_and_material_preserved':all(first['geometry'][k]==second['geometry'][k] for k in unchanged),
            'target_height_color_and_lower_edge_checked':True,
            'targeted_geometry_changed':all(first['geometry'][k]!=second['geometry'][k] for k in targets),
            'protected_neighbor_preserved':first['geometry']['KEEP_neighbor']==second['geometry']['KEEP_neighbor'],
            'original_blend_immutable':hashlib.sha256((Path(initial['project'])/first['model_path']).read_bytes()).hexdigest()==first['sha256']}
    evidence={'test_kind':'deterministic product-contract fixture with real cloud Blender execution',
              'provider_calls':0,'independent_llm_visual_quality':'NOT_RUN','paid_cost':'NOT_INCURRED',
              'blender_version':subprocess.check_output([backend.executable,'--version'],text=True).splitlines()[0],
              'runtime_seconds':time.time()-initial['started_epoch'],'project':initial['project'],
              'contract_denials':denials,'durable_progress':{'actual_revisions':[1,2],'persisted_records':len(progress.records),'same_revision_not_recounted':True,'changed_instruction_new_goal':True},'checks':checks,'renders':[initial['before'],after], 'revisions':[1,2],
              'limitations':['Synthetic fixture, not a source-photo reconstruction or independent Critic quality result.',
                             'No end-to-end real provider quality, token cost, SketchUp or user PC test.']}
    dump(output/'evidence.json',evidence)
    assert all(checks.values()),checks
    return evidence


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--initial-only',action='store_true')
    parser.add_argument('--resume-initial',action='store_true')
    args=parser.parse_args()
    initial=json.loads((args.output/'initial.json').read_text()) if args.resume_initial else run_native(args.output)
    dump(args.output/'initial.json',initial)
    if not args.initial_only:
        print(json.dumps(finish_native(args.output,initial),indent=2))

if __name__=='__main__': main()
