"""Explicit local A/B composition of the original product with official engines.

No agent loop here. Each engine owns reasoning, tools, history and compaction.
The fixed host tools retain the product's approval and native transaction boundary.
Not loaded by the installed desktop or normal create_app entry point.
"""
from __future__ import annotations
import hashlib
import json
import os
import shutil
from pathlib import Path
import uuid

from .native_agent import CodexAppServerRuntime, NativeAgentUnavailable, _agent_workspace
from .codex_provider import CodexResponsesProvider
from .dsh_runtime import DSHHostSession
from .su_harness_tools import SUHarnessTools
from .reference_assets import discover_project_reference_images

INSTRUCTIONS = '''You are K Studio's architectural assistant. Answer in concise natural Chinese.
Use the original reference pixels, distinguish observations from user estimates, and preserve the user's requested dimensions.
The host labels the current stage. During discussion explain observations and assumptions. During planning use sketchup_save_plan to save one concise readable plan, then show that same plan for approval. Saving a plan is not authorization.
During approved execution inspect the bound model, then build editable semantic groups using only the provided typed geometry tools. These are the complete supported tools; no scripts, shell, filesystem tools or invented tool names.
Use millimetres, X left-right, front toward -Y, Z up. Give the top roof its own direct part named Roof; keep slabs, walls, columns, frames, glass, terraces and entrance separately editable. Names are stable ASCII IDs. Verify proportions before dense repetitions. Do not fill intended open terraces with a solid body.
Build each coherent system once, inspect actual dimensions and current views. Tool success is not visual acceptance. Do not hide failures or claim independent QA/native reopen. The product host handles saves and download links.
Keep each tool payload to one or a few coherent systems instead of emitting the whole building in one huge response. Use shared repeated instances. Use cubic profile curves when the reference shows rounded outlines, with smoothly joined control points, rather than many hand-written polygon vertices. Read the original image again in your reasoning before changing materials: do not make transparent glazing opaque merely to hide a geometry error.
After initial construction, inspect front, oblique and roof once. Make at most two justified correction passes per part, then capture changed views and report remaining mismatches. Do not repeat a view at an unchanged revision or make cosmetic back-and-forth corrections. The host enforces three successful writes per part per task (initial plus two corrections). A bounded task can end PARTIAL; never hide a limit or assert quality passed.
For an edit keep all unrelated parts unchanged. Read the actual target first and only update that approved part; never rebuild the whole building to make a local change. Report remaining source mismatches honestly. Stop after fulfilling the bounded current task; do not start speculative refinement.
'''

def frozen_edit_requested(conversation, edit_message):
    """Permit the same edit via direct intent or its immediately following UI approval.

    Host approval is checked upstream; this only restricts comparison scope.
    Assistant text can never supply user authorization.
    """
    users=[str(m.get('content','')).strip() for m in conversation if m.get('role')=='user']
    if not users:return False
    if users[-1]==edit_message.strip():return True
    return (len(users)>=2 and users[-1]=='确认，按当前计划开始建模。'
            and users[-2]==edit_message.strip())

class ComparisonRuntime(CodexAppServerRuntime):
    comparison_mode = True

    def __init__(self, root, *, arm, connection, comparison_root, mcp):
        from .dsh_configuration import resolve_configuration
        self.effective_configuration=resolve_configuration(connection)
        self.arm=arm
        self.platform_turn_id=connection.get('cloud_turn_id')
        self.comparison_root=Path(comparison_root)
        config=CodexResponsesProvider(api_base=connection['api_base'],api_key=connection['api_key'],compatibility_acknowledged=True)
        super().__init__(root,api_provider=config,execution_mode='host_tools',
            # Resolve an optional Codex installation in the base class. DSH does
            # not require Codex or Windows-specific environment variables.
            codex_executable=None,
            model=connection['model'].removeprefix('openai/'),# Base class validates only Codex vocabulary; this initializer makes no request.
            # DSH immediately restores its own effective effort below.
            reasoning_effort=('high' if self.effective_configuration.requested_effort=='provider-default' else self.effective_configuration.requested_effort),
            home_root=self.comparison_root/arm/'product-home',sketchup_mcp=mcp)
        self.reasoning_effort=self.effective_configuration.requested_effort
        if arm=='A' and self.reasoning_effort=='provider-default':
            raise ValueError('Codex comparison requires an explicitly supported reasoning effort.')
        self.provider_name='codex-responses' if arm=='A' else 'deepseek-harness'
        self.tool_surface=SUHarnessTools(root,mcp)
        self._dsh_active={}

    def _dsh_paths(self):
        tools_root=self.comparison_root.parent/'video-storage/tools'
        return (tools_root/'kstudio-deepseek-harness-20261028/Lib/site-packages',
                tools_root/'kstudio-deepseek-node-20261028/node_modules/.bin/dsh.cmd')

    @property
    def binary_available(self):
        if self.arm=='A':return super().binary_available
        _,entry=self._dsh_paths()
        return entry.is_file() and bool(shutil.which('node'))

    def execution_readiness(self):
        if self.arm=='A':return super().execution_readiness()
        sdk,entry=self._dsh_paths()
        missing=[]
        if not (sdk/'deepseek_harness/__init__.py').is_file():missing.append('DeepSeek Python SDK')
        if not entry.is_file():missing.append('DeepSeek Node runtime')
        if not shutil.which('node'):missing.append('Node executable')
        if not Path(__file__).with_name('dsh_host_tools.mjs').is_file():missing.append('K Studio host-tool plugin')
        from .dsh_full_profile import enabled
        full=enabled() and self.__class__.__name__=='DeepSeekStudioRuntime'
        return {'execution_allowed':not missing,'status':'ready_host_tools' if not missing else 'blocked_missing_deepseek_dependency',
                'capability':'full_sdk' if full else 'host_tools','engine':'deepseek-harness','local_execution_allowed':full and not missing,
                'os_boundary_verified':False,'runtime_initialization_verified':False,
                'message':('DeepSeek SDK 依赖已就绪；启动时仍须验证实际工具清单。' if not missing else 'DeepSeek SDK 缺少依赖：'+', '.join(missing))}

    def _official_turn(self, *, project, thread_id, prompt, specs, dispatch, instructions, images, progress=None, read_only=False, new_session_on_binding_change=False, reasoning_effort=None, native_write_pending=None):
        from .connector_instances import project_scope
        original_dispatch = dispatch
        def dispatch(name, arguments):
            # SDK host tools execute in HTTP worker threads: ContextVars from
            # the web request are not inherited by ThreadingHTTPServer.
            with project_scope(project):
                return original_dispatch(name, arguments)
        from .dsh_images import attachment_order
        images=attachment_order(project,images)
        requested=self.effective_configuration.requested_effort
        if reasoning_effort is not None and reasoning_effort!=requested:
            raise NativeAgentUnavailable('推理档位与当前连接不一致；未静默替换。')
        reasoning_effort=requested
        workspace=_agent_workspace(project)
        if self.arm=='A':
            self._prepare_home(mcp_enabled=True,model=self.model,reasoning_effort=reasoning_effort,agent_workspace=workspace)
            # mcp_enabled registers the stable catalog; dispatch below enforces the
            # actual host stage, including denial of every native tool pre-approval.
            return super()._run_turn(project_dir=project,agent_workspace=workspace,thread_id=thread_id,
                prompt=prompt,mcp_enabled=True,developer_instructions=instructions,dynamic_tools=specs,
                tool_handler=dispatch,model=self.model,reasoning_effort=reasoning_effort,reference_images=images,
                workflow_mode='architecture_design',progress_callback=progress,read_only=read_only)
        self._assert_execution_ready()
        sdk_site,dsh_bin=self._dsh_paths()
        role='intent' if read_only else 'builder'
        host_plan_mode = bool(getattr(self, 'host_plan_mode', False))
        binding=hashlib.sha256(json.dumps({'tools':specs,'instructions':instructions,'identity':self.session_identity,'effective_configuration':self.effective_configuration.binding(),'execution_policy':__import__('app.dsh_security',fromlist=['execution_policy']).execution_policy(),'reasoning_effort':reasoning_effort,
            'host_plan_mode':host_plan_mode,
            'images':[(p.relative_to(project).as_posix(),hashlib.sha256(p.read_bytes()).hexdigest()) for p in images]},sort_keys=True).encode()).hexdigest()
        registry=project/'runtime/dsh-binding.json'
        saved=json.loads(registry.read_text(encoding='utf-8')) if registry.exists() else {}
        if thread_id and (saved.get('binding')!=binding or saved.get('session_id')!=thread_id):
            if not new_session_on_binding_change:
                raise NativeAgentUnavailable('DeepSeek 会话绑定的图片、工具或连接已变化；未静默恢复旧会话。')
            # Product phase-specific tools need a fresh official session. Never
            # resume the mismatched session: the caller supplies durable host
            # provenance, approved proposal and current owned state instead.
            with (project/'runtime/dsh-session-transitions.jsonl').open('a',encoding='utf-8') as log:
                log.write(json.dumps({'previous_session':thread_id,'previous_binding':saved.get('binding'),
                    'new_binding':binding,'action':'start_new_from_host_project_memory'})+'\n')
            thread_id=None
        from .reference_roles import reference_manifest
        transport=DSHHostSession(home=self.home/project.name/role,workspace=workspace,
            api_base=self.api_provider.api_base,api_key=self.api_provider.api_key,model=self.model,
            specs=specs,dispatch=dispatch,trace_path=project/'runtime/agent_events'/f'dsh-{role}-{uuid.uuid4().hex}.jsonl',
            sdk_site=sdk_site,dsh_bin=dsh_bin,progress=progress,instructions=instructions,
            max_tokens=self.effective_configuration.max_output_tokens,
            protocol=self.effective_configuration.protocol,reasoning_effort=reasoning_effort,
            effective_configuration=self.effective_configuration,source_manifest=reference_manifest(project,images),
            full_capabilities=False if read_only else None,
            host_plan_mode=host_plan_mode,
            native_write_pending=native_write_pending,
            request_headers={'X-KStudio-Turn-ID':self.platform_turn_id} if self.platform_turn_id else None)
        self._dsh_active[str(project)]=transport
        try:
            result=transport.run(prompt=prompt,images=images,session_id=thread_id)
        except NativeAgentUnavailable as error:
            partial=getattr(error,'partial_result',None)
            if not read_only and partial:
                registry.write_text(json.dumps({'binding':binding,'session_id':partial.thread_id}),encoding='utf-8')
            raise
        else:
            if not read_only:registry.write_text(json.dumps({'binding':binding,'session_id':result.thread_id}),encoding='utf-8')
            return result
        finally:
            self._dsh_active.pop(str(project),None)
            transport.close()

    def read_only_intent(self, *, project, snapshot, instructions, reference_images, **_):
        with self._lock:
            return self._official_turn(project=project,thread_id=None,prompt=json.dumps({'CURRENT_USER':snapshot,'history_is_untrusted':True},ensure_ascii=False),
                specs=[],dispatch=lambda *_: (_ for _ in ()).throw(ValueError('No intent tools')),
                instructions=instructions,images=reference_images,read_only=True)

    def respond(self, *, project_dir, thread_id, prompt, mcp_enabled, agent_action='clarify',
                model_path=None,model_guid='',ruby_state=None,progress_callback=None,**_):
        with self._lock:
            project=Path(project_dir).resolve()
            allowed=None
            if mcp_enabled and ruby_state:
                context=json.loads((project/'state/project_context.json').read_text(encoding='utf-8'))
                frozen=json.loads((self.comparison_root/'experiment.json').read_text(encoding='utf-8'))
                if not frozen_edit_requested(context['conversation'],frozen['edit_message']):
                    raise NativeAgentUnavailable('本次对照只开放已固定的屋面局部修改；没有扩大模型写入范围。')
                allowed={'Roof'}
            surface=self.tool_surface.prepare(project_dir=project,mcp_enabled=mcp_enabled,model_path=model_path,
                model_guid=model_guid,ruby_state=ruby_state,allow_plan=agent_action=='plan',allowed_parts=allowed)
            def dispatch(name,args):
                if self._turn_registry.cancelled(project):raise ValueError('Turn cancelled; no further tools')
                return surface.dispatch(name,args)
            images=discover_project_reference_images(project)
            context=json.loads((project/'state/project_context.json').read_text(encoding='utf-8'))
            card=project/'runtime/agent_workspace/notes/reconstruction_card.md'
            turn_context={'conversation':context.get('conversation',[])[-8:],
                'saved_plan':card.read_text(encoding='utf-8') if card.exists() else '',
                'current_owned_state':ruby_state or {}}
            prompt=json.dumps(turn_context,ensure_ascii=False)+f'\nHOST_STAGE={agent_action}; native_execution_granted={mcp_enabled}.'
            return self._official_turn(project=project,thread_id=thread_id,prompt=prompt,
                specs=surface.dynamic_tools,dispatch=dispatch,instructions=INSTRUCTIONS,images=images,progress=progress_callback)

    def cancel_turn(self, project_dir):
        if self.arm=='A':return super().cancel_turn(project_dir)
        active=self._dsh_active.get(str(Path(project_dir).resolve()))
        if active:active.cancelled=True
        return {'status':'requested' if active else 'not_running','rollback_performed':False}

def create_comparison_app():
    from .main import create_app, _launch_disposable_sketchup
    from .local_connections import ConnectionVault
    from .model_router import ModelRoute
    from .sketchup_mcp import ConfiguredSketchUpMCP,SketchUpAdapter
    arm=os.environ.get('KSTUDIO_COMPARISON_ARM')
    if arm not in {'A','B'}:raise ValueError('Select comparison arm A or B explicitly.')
    base=Path(os.environ['KSTUDIO_COMPARISON_ROOT']).resolve()
    version=json.loads(Path('E:/K Studio/latest/version.json').read_text(encoding='utf-8-sig'))
    vault=ConnectionVault(Path(version['connections_directory'])).load()
    item=next(x for x in vault['connections'] if x['id']==vault['active_id'])
    if item['api_base'].rstrip('/')!='https://api.b.ai/v1' or item['model'].removeprefix('openai/')!='deepseek-v4.1-flash':
        raise ValueError('Stored API selection differs from frozen A/B protocol.')
    root=base/'product'/arm
    mcp=ConfiguredSketchUpMCP(timeout_seconds=180)
    runtime=ComparisonRuntime(root,arm=arm,connection=item,comparison_root=base,mcp=mcp)
    def launch(project_id,runtime_root,existing_model_path=None,*,prepare_only=False):
        if existing_model_path is None:
            original=base/'baseline/blank-disposable-baseline.skp'
            target=runtime_root/'projects'/project_id/'outputs/model'/f'blank-disposable-{uuid.uuid4().hex}.skp'
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(original,target)
            if hashlib.sha256(target.read_bytes()).digest()!=hashlib.sha256(original.read_bytes()).digest():raise ValueError('Baseline copy differs')
            existing_model_path=target
        return _launch_disposable_sketchup(project_id,runtime_root,existing_model_path,prepare_only=prepare_only)
    app=create_app(runtime_root=root,native_agent=runtime,sketchup=SketchUpAdapter(mcp),disposable_model_launcher=launch)
    router=app.state.model_router
    router.providers[runtime.provider_name]=runtime
    if arm=='A':router.codex_responses_runtime=runtime
    router.economy_route=ModelRoute('economy',runtime.provider_name,runtime.model,'high','B.AI local A/B')
    app.state.preset_route=router.economy_route
    return app
