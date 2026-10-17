"""Explicit Blender opt-in on the existing project/conversation/router pipeline."""
import json
import uuid
from datetime import datetime, timezone
from fastapi import HTTPException
from .blender_backend import BlenderBackend, enabled
from .models import AgentSession, ModelState, ConversationMessage, OutputManifest, Artifact

def install(app, store):
    @app.post('/api/projects/{project_id}/blender/session')
    def start(project_id: str):
        if not app.state.agent_lock.acquire(blocking=False):
            raise HTTPException(409, 'Another turn is running')
        try:
            store.load_context(project_id)
            project_dir=store.project_dir(project_id)
            session=store.load_state(project_id,'agent_session.json',AgentSession)
            if (session.model_path or session.ruby_state) and session.modeling_backend != 'blender':
                raise HTTPException(409,'Existing SketchUp session is protected; use a separate project for Blender')
            backend=BlenderBackend(project_dir)
            if enabled(project_dir):
                return {'backend':'blender','project':store.load_project(project_id),'executable_available':True}
            (project_dir/'state/modeling_backend.json').write_text(json.dumps({'backend':'blender','capability':'bounded boxes and indexed meshes'}))
            session.modeling_backend='blender';session.status='conversation';session.thread_id='';session.reconstruction_state='idle'
            store.save_state(project_id,session,'agent_session.json')
            return {'backend':'blender','project':store.load_project(project_id),'executable_available':bool(backend.executable)}
        except (ValueError,FileNotFoundError) as e:
            raise HTTPException(409,str(e)) from e
        finally:
            app.state.agent_lock.release()

def converse(app,store,project_id,request):
    project_dir=store.project_dir(project_id)
    backend=BlenderBackend(project_dir)
    context=store.load_context(project_id)
    session=store.load_state(project_id,'agent_session.json',AgentSession)
    execute=request.agent_action=='execute' or (request.agent_action=='auto' and session.reconstruction_state=='building')
    if execute and session.reconstruction_state not in ('planned','building'):
        raise HTTPException(409,'Generate and review a plan before Blender execution')
    if (execute or request.agent_action == 'plan') and any(ref.type == 'image' and ref.evidence_role == 'unknown' for ref in context.references):
        raise HTTPException(409, '请先确认每张图片是目标建筑图还是待修问题截图，再整理计划。')
    baseline=backend.dispatch('blender_inspect_scene',{}).get('revision',0)
    if project_id in app.state.active_turns:
        app.state.active_turns[project_id].update(action='execute' if execute else request.agent_action,blender_baseline=baseline)
    if request.agent_action=='plan':
        session.reconstruction_state='clarifying'
        store.save_state(project_id,session,'agent_session.json')
    submitted=datetime.now(timezone.utc).isoformat()
    turn_id="message:"+uuid.uuid4().hex
    attachments=[]
    for ref in context.references:
        source=(project_dir/ref.source).resolve()
        if ref.source.startswith('inputs/') and not ref.submitted_at and source.is_relative_to((project_dir/'inputs').resolve()) and source.is_file():
            attachments.append(ref.source);ref.submitted_at=submitted;ref.evidence_turn_id=turn_id
    context.conversation.append(ConversationMessage(role='user',phase='agent',content=request.message,created_at=submitted,metadata={'attachments':attachments,'evidence_turn_id':turn_id}))
    store.save(context,project_dir/'state/project_context.json')
    prompt='Blender project. Supported capability: bounded named boxes and indexed meshes with simple materials in metres; do not claim full architecture fidelity.\n'+context.model_dump_json()+'\nCurrent request: '+request.message
    try:
        result=app.state.model_router.respond(tier=request.tier,project_dir=project_dir,thread_id=session.thread_id or None,prompt=prompt,mcp_enabled=execute,model_path=None,model_guid='',ruby_enabled=False,ruby_state={},workflow_mode=request.workflow_mode,tool_profile='full',developer_instructions='Use only Blender tools. No arbitrary code, external APIs or SketchUp. Preserve unrelated named objects. Planning has no modeling tools. Only target_building images define target appearance; defect_location images show historical problems, never target truth; unknown roles require clarification. Preserve image turn and revision provenance. Report actual limitations.')
        receipt=backend.dispatch('blender_inspect_scene',{})
        if execute and receipt.get('revision',0)<=baseline:
            raise ValueError('Agent returned without committing Blender geometry')
    except Exception as e:
        recovered=backend.dispatch('blender_inspect_scene',{})
        if recovered.get('revision',0)>baseline:
            checkpoint(store,project_id,session,recovered)
            session.status='ready';session.reconstruction_state='building'
        session.error=str(e)[:1200]
        store.save_state(project_id,session,'agent_session.json')
        raise HTTPException(502,str(e)) from e
    if request.agent_action=='plan':
        card=project_dir/'runtime/agent_workspace/notes/reconstruction_card.md'
        card.parent.mkdir(parents=True,exist_ok=True)
        card.write_text('# Blender 建模计划\n\n'+result.reply,encoding='utf-8')
    session.thread_id=result.thread_id;session.last_reply=result.reply
    session.provider=result.provider_name;session.model=result.model_name;session.last_tool_calls=result.tool_calls
    session.status='ready' if receipt.get('revision') else 'conversation'
    session.reconstruction_state='building' if execute else ('planned' if request.agent_action=='plan' else 'clarifying')
    session.error=''
    checkpoint(store,project_id,session,receipt)
    context.conversation.append(ConversationMessage(role='assistant',phase='agent',content=result.reply,metadata={'backend':'blender','provider':result.provider_name,'native_reopen':receipt.get('native_reopen','NOT_RUN')}))
    store.save(context,project_dir/'state/project_context.json');store.save_state(project_id,session,'agent_session.json')
    return {'phase':'agent','reply':result.reply,'agent':{'agent_action':'execute' if execute else ('plan' if request.agent_action=='plan' else 'clarify'),'backend':'blender','session_status':session.status,'reconstruction_state':session.reconstruction_state,'provider':session.provider,'model':session.model,'model_info':receipt},'project':store.load_project(project_id)}

def checkpoint(store,project_id,session,receipt):
    if receipt.get('model_path'):
        session.model_path=receipt['model_path'];session.last_model_info=receipt
        state=store.load_state(project_id,'model_state.json',ModelState)
        state.model_path=receipt['model_path'];state.status='agentic';state.connector_readback=receipt
        store.save_state(project_id,state,'model_state.json')
        manifest=store.load_state(project_id,'output_manifest.json',OutputManifest)
        for view,render in receipt.get('renders',{}).items():
            path=render['image_path']
            if render.get('revision')==receipt['revision'] and not any(item.path==path for item in manifest.model_captures):
                manifest.model_captures.append(Artifact(id='blender-view-'+str(receipt['revision'])+'-'+view,type='viewport',path=path,url=f'/api/projects/{project_id}/files/'+path,created_at=datetime.now(timezone.utc).isoformat()))
        if any(item.path == receipt['model_path'] for item in manifest.presentation):
            store.save_state(project_id,manifest,'output_manifest.json')
            return
        manifest.presentation.append(Artifact(id='blender-'+str(receipt['revision']),type='blend',path=receipt['model_path'],url=f'/api/projects/{project_id}/files/'+receipt['model_path'],created_at=datetime.now(timezone.utc).isoformat()))
        store.save_state(project_id,manifest,'output_manifest.json')
