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
            (project_dir/'state/modeling_backend.json').write_text(json.dumps({'backend':'blender','capability':'bounded boxes and indexed meshes'}), encoding="utf-8")
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
    from .imported_research import imported_research_context
    try:
        research_context = imported_research_context(project_dir, context)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    from .reference_defaults import resolve_pending_reference_defaults
    from .reference_roles import current_model_revisions
    if resolve_pending_reference_defaults(project_dir,context,request.message,current_model_revisions(project_dir)):
        store.save(context,project_dir/'state/project_context.json')
    from .reconstruction_runtime import resolve_reconstruction_action, next_reconstruction_state
    from .contextual_turn import resolve_host_action
    try:
        contextual=resolve_host_action(app.state.model_router,project=project_dir,session=session,request=request,context=context)
    except (ValueError, RuntimeError) as error:
        raise HTTPException(409,str(error)) from error
    if contextual and contextual[1].get('attachment_roles_changed'):
        store.save(context,project_dir/'state/project_context.json');store.save_state(project_id,session,'agent_session.json')
    action=contextual[0] if contextual else resolve_reconstruction_action(session,request)
    if app.state.active_turns.get(project_id,{}).get('cancel_requested'):
        raise HTTPException(409,'本轮已请求停止，未开启下一步建模。')
    execute=action=='execute'
    if execute and session.reconstruction_state not in ('planned','building'):
        raise HTTPException(409,'Generate and review a plan before Blender execution')
    if (execute or action == 'plan') and any(ref.type == 'image' and ref.evidence_role == 'unknown' for ref in context.references):
        raise HTTPException(409, '请先确认每张图片是目标建筑图还是待修问题截图，再整理计划。')
    from .design_scope_approval import invalidate_stale_design_scope, capture_pending_design_plan, approve_pending_design_plan
    invalidate_stale_design_scope(project_dir)
    baseline=backend.dispatch('blender_inspect_scene',{}).get('revision',0)
    if project_id in app.state.active_turns:
        app.state.active_turns[project_id].update(action=action,blender_baseline=baseline)
    if action=='plan':
        capture_pending_design_plan(project_dir,'',is_followup=False)
        session.reconstruction_state='clarifying'
        store.save_state(project_id,session,'agent_session.json')
    submitted=datetime.now(timezone.utc).isoformat()
    turn_id=contextual[1]["user_message_id"] if contextual else "message:"+uuid.uuid4().hex
    attachments=[]
    for ref in context.references:
        source=(project_dir/ref.source).resolve()
        if ref.source.startswith('inputs/') and not ref.submitted_at and source.is_relative_to((project_dir/'inputs').resolve()) and source.is_file():
            ref.role_clarification_pending=ref.evidence_role=='unknown' and ref.role_origin=='awaiting_context'
            attachments.append(ref.source);ref.submitted_at=submitted;ref.evidence_turn_id=turn_id
    context.conversation.append(ConversationMessage(role='user',phase='agent',content=request.message,created_at=submitted,metadata={'attachments':attachments,'evidence_turn_id':turn_id}))
    store.save(context,project_dir/'state/project_context.json')
    if execute and session.reconstruction_state == 'planned':
        card=project_dir/'runtime/agent_workspace/notes/reconstruction_card.md'
        pending=project_dir/'runtime/pending_design_scope.json'
        snapshot=json.loads(pending.read_text(encoding="utf-8")) if pending.exists() else {}
        if request.approved_plan_sha256 or snapshot.get('features'):
            try:
                approve_pending_design_plan(project_dir,turn_id,card.read_text(encoding='utf-8'),request.approved_plan_sha256)
            except (ValueError,OSError) as error:
                raise HTTPException(409,str(error)) from error
    prompt='Blender project. Supported capability: bounded named boxes and indexed meshes with simple materials in metres; do not claim full architecture fidelity.\n'+context.model_dump_json()+'\nCurrent request: '+request.message
    prompt += research_context
    if action == 'plan' and baseline:
        prompt += '\nInclude a <design_scope> JSON array </design_scope> in the plan, entries exactly feature_id (stable prior requirement ID) and requested_state. Scope only the requested design changes; KEEP objects stay protected. Approval is required before reversing earlier design intent.'
    if contextual and execute and session.reconstruction_state=='planned':
        from .design_scope_approval import consume_pending_design_plan
        consume_pending_design_plan(project_dir,request.approved_pending_plan_id)
    from .native_agent import CodexAppServerRuntime
    progress_kwargs = ({'progress_callback':app.state.native_progress_callback(project_id)}
        if isinstance(app.state.model_router.codex_runtime,CodexAppServerRuntime)
        and app.state.model_router.route(request.tier).provider=='codex-app-server' else {})
    try:
        result=app.state.model_router.respond(**progress_kwargs,tier=request.tier,project_dir=project_dir,thread_id=session.thread_id or None,prompt=prompt,mcp_enabled=execute,model_path=None,model_guid='',ruby_enabled=False,ruby_state={},workflow_mode=request.workflow_mode,tool_profile='full',developer_instructions='Use only Blender tools. No arbitrary code, external APIs or SketchUp. Preserve unrelated named objects. Planning has no modeling tools. When explicitly registered, search_web and fetch_url are read-only public research tools; use actual returned citations and acknowledge retrieval errors. Imported notes are external assistance, not autonomous web search. Only target_building images define target appearance; defect_location images show historical problems, never target truth; unknown roles require clarification. Preserve image turn and revision provenance. Within approved scope, complete coherent unseen sides and interior as explicitly inferred design. Additional true views constrain the same model; preserve satisfied geometry. Prioritize roof-wall-window-corner joins and circulation before decoration. For observed connection defects, use blender_plan_relation_repair to map priorities to exact components and planned edits; use its measured checks after each commit. Do not replace high-priority unresolved connections with decoration, do not claim visual acceptance from relation tests. Use blender_audit_connections for declared intended joints; positive gaps, penetrations and misalignment require interpretation, and mesh-bound hints require native/view verification. Use prepare_component with exact owned component_ids; component replacement/removal must cover its complete saved receipt, including legs, frames and other children, not only the visible top. For legacy geometry verify each owned child before removal; do not guess ownership from prefixes. inspect fitted six views and interior perspectives; clearance checks are not navigation or compliance. Correct deterministic issues inside finite stage budget, stop destructive or no-progress loops. First-turn quality is judged separately; later wishes must not hide first-turn defects. Intentional touching partition faces are not automatically defects. Report actual limitations.')
        receipt=backend.dispatch('blender_inspect_scene',{})
        if execute and result.status=='completed' and receipt.get('revision',0)<=baseline:
            raise ValueError('Agent returned without committing Blender geometry')
    except Exception as e:
        recovered=backend.dispatch('blender_inspect_scene',{})
        if recovered.get('revision',0)>baseline:
            checkpoint(store,project_id,session,recovered)
            session.status='ready';session.reconstruction_state='building'
        session.error=str(e)[:1200]
        store.save_state(project_id,session,'agent_session.json')
        raise HTTPException(502,str(e)) from e
    if result.status!='completed':
        committed=receipt.get('revision',0)>baseline
        if committed:
            checkpoint(store,project_id,session,receipt)
            session.status='ready';session.reconstruction_state='building'
        status='interrupted' if result.status=='interrupted' else 'failed'
        reply=('本轮已停止。' if status=='interrupted' else '本轮未完成。')+('已保存已提交修改，质量未验收。' if committed else '已有模型保持，未新建交付。')
        session.error='本轮未完成全部任务。';session.last_reply=reply
        metadata={'execution_status':status,'geometry_committed':committed,'checkpoint_saved':committed,'turn_id':getattr(result,'turn_id','')}
        context.conversation.append(ConversationMessage(role='assistant',phase='agent',content=reply,metadata=metadata))
        store.save(context,project_dir/'state/project_context.json');store.save_state(project_id,session,'agent_session.json')
        return {'phase':'agent','reply':reply,'agent':{**metadata,'backend':'blender','agent_action':action},'project':store.load_project(project_id)}
    if action=='plan':
        card=project_dir/'runtime/agent_workspace/notes/reconstruction_card.md'
        card.parent.mkdir(parents=True,exist_ok=True)
        card.write_text('# Blender 建模计划\n\n'+result.reply,encoding='utf-8')
        capture_pending_design_plan(project_dir,card.read_text(encoding='utf-8'),is_followup=bool(baseline))
    session.thread_id=result.thread_id;session.last_reply=result.reply
    session.provider=result.provider_name;session.model=result.model_name;session.last_tool_calls=result.tool_calls
    session.status='ready' if receipt.get('revision') else 'conversation'
    session.reconstruction_state=next_reconstruction_state(session,action)
    session.error=''
    geometry_committed=receipt.get('revision',0)>baseline
    if geometry_committed:checkpoint(store,project_id,session,receipt)
    context.conversation.append(ConversationMessage(role='assistant',phase='agent',content=result.reply,metadata={'backend':'blender','provider':result.provider_name,'model':result.model_name,'reasoning_effort':result.reasoning_effort,'geometry_committed':geometry_committed,'checkpoint_saved':geometry_committed,'agent_action':action,'native_reopen':receipt.get('native_reopen','NOT_RUN')}))
    store.save(context,project_dir/'state/project_context.json');store.save_state(project_id,session,'agent_session.json')
    return {'phase':'agent','reply':result.reply,'agent':{'agent_action':'execute' if execute else ('plan' if action=='plan' else 'clarify'),'backend':'blender','geometry_committed':geometry_committed,'checkpoint_saved':geometry_committed,'execution_status':'committed' if geometry_committed else 'read_only','session_status':session.status,'reconstruction_state':session.reconstruction_state,'provider':session.provider,'model':session.model,'model_info':receipt},'project':store.load_project(project_id)}

def checkpoint(store,project_id,session,receipt):
    if receipt.get('model_path'):
        session.model_path=receipt['model_path'];session.last_model_info=receipt
        state=store.load_state(project_id,'model_state.json',ModelState)
        state.model_path=receipt['model_path'];state.status='agentic';state.connector_readback=receipt
        store.save_state(project_id,state,'model_state.json')
        manifest=store.load_state(project_id,'output_manifest.json',OutputManifest)
        cutaway_paths={r['image_path'] for r in receipt.get('renders',{}).values() if r.get('cutaway') or r.get('hidden_ids')}
        # Cutaways remain labeled in the native receipt; never promote them to the default full-model viewport.
        manifest.model_captures=[item for item in manifest.model_captures if item.path not in cutaway_paths]
        for view,render in receipt.get('renders',{}).items():
            if render.get('cutaway') or render.get('hidden_ids'):continue
            path=render['image_path']
            if render.get('revision')==receipt['revision'] and not any(item.path==path for item in manifest.model_captures):
                manifest.model_captures.append(Artifact(id='blender-view-'+str(receipt['revision'])+'-'+view,type='viewport',path=path,url=f'/api/projects/{project_id}/files/'+path,created_at=datetime.now(timezone.utc).isoformat()))
        if any(item.path == receipt['model_path'] for item in manifest.presentation):
            store.save_state(project_id,manifest,'output_manifest.json')
            return
        manifest.presentation.append(Artifact(id='blender-'+str(receipt['revision']),type='blend',path=receipt['model_path'],url=f'/api/projects/{project_id}/files/'+receipt['model_path'],created_at=datetime.now(timezone.utc).isoformat()))
        store.save_state(project_id,manifest,'output_manifest.json')
