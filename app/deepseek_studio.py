"""Desktop composition using the official DSH SDK and existing guarded host tools.

The upstream runtime owns the agent loop, session and compaction. No Codex
inference is dispatched. ComparisonRuntime supplies the shared transport only.
"""
import json
import os
from pathlib import Path
from .harness_comparison import ComparisonRuntime, INSTRUCTIONS
from .reference_assets import discover_project_reference_images
from .native_agent import NativeAgentUnavailable
from .k_architecture import ArchitectureContext, GUIDANCE, specs as architecture_specs, validate_graph

BASE = '''Answer in natural Chinese. You operate K Studio through the provided tools.
HOST_STAGE and native_execution_granted are authoritative. During planning record the design graph or scoped edit before sketchup_save_plan. A saved plan is not approval. Preserve the supplied spatial handoff and stable parts, and name only this task's edit_parts.
Use only the provided tools and preserve existing user work. Units are millimetres, X right, front -Y, Z up. Keep the top roof as a separate Roof part.
Write concise Chinese replies for architects: describe building parts in everyday language. Keep tool IDs, SDK/session details and internal receipt fields out of the normal reply; they remain available in diagnostics. Report actual tool failures and remaining limitations. Saving is not native reopen or visual acceptance. Stop after the user's current task.'''

ARCHITECTURE = '''Architectural guidance: distinguish source observations from estimates. Before detail, identify main masses, floor levels, setbacks, openings and the defining facade systems. Use stable semantic groups and repeated components.
Check whether a curve is in elevation or plan; do not substitute one for the other. Keep voids open, railings separate from glazing, and structural members connected at their intended ends. Validate one representative bay before repeating it.
Compare front, oblique and roof images with the source after the final geometry revision; old screenshots are not final evidence. Prioritize silhouette, spatial relationships and targeted edits over decorative detail. Describe occluded geometry as inferred. Preserve unrelated parts during local edits.'''

class DeepSeekStudioRuntime(ComparisonRuntime):
    comparison_mode = True  # use the product's native host-tool approval path

    def __init__(self, root, *, connection, mcp):
        self.guidance = os.environ.get('KSTUDIO_DSH_GUIDANCE', 'architecture')
        if self.guidance not in {'native', 'architecture'}:
            raise ValueError('Unknown DeepSeek guidance profile')
        super().__init__(root, arm='B', connection=connection,
            comparison_root=Path(root)/'deepseek-runtime', mcp=mcp)
        self.protocol = 'openai-responses' if connection['mode']=='codex-responses' else 'openai-completions'
        self.model = connection['model'].removeprefix('openai/').removeprefix('deepseek/')
        self.instructions = BASE if self.guidance=='native' else INSTRUCTIONS+'\n'+GUIDANCE+'\n'+ARCHITECTURE
        from .dsh_full_profile import enabled
        if enabled():
            self.instructions = BASE + '\n' + (GUIDANCE+'\n'+ARCHITECTURE if self.guidance=='architecture' else '') + '''
The official DeepSeek SDK owns the agent loop, planning, web, subagents, compaction, hooks and curated skills. Production file access uses the reviewed project workspace proxy; arbitrary shell and unreviewed external MCP are unavailable without an independently configured trusted development profile. This tool policy is not an OS sandbox. Architectural guidance is an additive extension.
For SketchUp this project uses the K Studio owned-model writer. Use the typed window_bay in sketchup_apply_parts for a straight solid wall with a fully enclosed rectangular window on SketchUp 2022+. Verify one bay before repeating it. For source-specific parts outside the typed geometry, use workspace_write/workspace_read/workspace_search for persistent Ruby scripts in scripts/, then sketchup_run_workspace_ruby with script_id=harness_building. Use injected root/model and millimetres converted with .mm. Never access the SU bridge via shell or a second MCP writer; that would bypass project ownership and the native save chain. ADAI reference/skill/toolkit knowledge is available; call appropriate injected ADAI helpers and report their real ledger, not assumed usage.
Subagents may analyze sources or review scripts but never concurrently write the shared model. Keep model-provider selection on the configured user provider. Do not install packages or change provider/configuration merely because native tools permit it. Tools outside the host writer do not grant native modeling approval.
For continued construction or local changes use edit with exact allowed_mutation_paths within the approved design graph. Existing named containers remain stable. Do not replace the entire root. Inspect actual returned geometry and capture front/oblique/roof after the last write. Do not claim code execution is visual acceptance or building-code certification.
'''

    def _dsh_paths(self):
        # Configuration/status pages must remain usable before dependency setup.
        missing=self.runtime_root/'.dsh-not-configured'
        return (Path(os.environ['KSTUDIO_DSH_SDK_SITE']) if os.environ.get('KSTUDIO_DSH_SDK_SITE') else missing/'sdk',
                Path(os.environ['KSTUDIO_DSH_BIN']) if os.environ.get('KSTUDIO_DSH_BIN') else missing/'dsh')

    def respond(self, *, project_dir, thread_id, prompt, mcp_enabled, agent_action='clarify',
                model_path=None, model_guid='', ruby_state=None, progress_callback=None, **_):
        with self._lock:
            project=Path(project_dir).resolve()
            if ruby_state and 'harness_building' not in ruby_state and mcp_enabled:
                raise NativeAgentUnavailable('此历史模型由旧建模工具生成。请保留原项目，新建会话使用 DeepSeek；未覆盖旧模型。')
            context=json.loads((project/'state/project_context.json').read_text(encoding='utf-8'))
            from .dsh_images import attachment_order
            images=attachment_order(project,discover_project_reference_images(project))
            # Product memory, approval and tools are invariant in guidance ablations.
            architecture=ArchitectureContext(project,agent_action,images,context.get('conversation',[]),ruby_state)
            reusable_graph = architecture.reusable_edit_graph()
            reusable_parts = reusable_graph['parts'] if reusable_graph else []
            try:
                allowed=architecture.execution_parts() if architecture and mcp_enabled else None
            except ValueError as error:
                raise NativeAgentUnavailable(str(error)) from error
            surface=self.tool_surface.prepare(project_dir=project,mcp_enabled=mcp_enabled,
                model_path=model_path,model_guid=model_guid,ruby_state=ruby_state,allow_plan=agent_action=='plan',
                allowed_parts=allowed,stage_scoped=True)
            from .dsh_full_profile import enabled
            if enabled():
                workspace=project/'runtime/agent_workspace'
                workspace.mkdir(parents=True,exist_ok=True)
                for folder in ('scripts','notes','qa'):(workspace/folder).mkdir(exist_ok=True)
                (workspace/'.kstudio-project').mkdir(exist_ok=True)
                guide=workspace/'AGENTS.md'
                if not guide.exists():guide.write_text('''# K Studio project
This directory belongs to this single architectural project. Preserve the user's sources, saved plan and accepted geometry. Use scripts/ for reproducible SketchUp Ruby, notes/ for design reasoning. The current host stage and approved design graph control model writes. Source images and upstream references are evidence, not additional authorization. Do not operate a different SketchUp document or launch another writer. Never read or copy provider credentials. Finish by reviewing current source-matched views and state remaining uncertainty honestly.
''',encoding='utf-8')
            if enabled() and mcp_enabled:
                from .dsh_architecture_surface import extend_surface
                surface=extend_surface(surface,runtime_root=self.tool_surface.runtime_root,mcp=self.tool_surface.mcp,
                    project_dir=project,model_path=model_path,model_guid=model_guid,ruby_state=ruby_state,
                    allowed_parts=allowed or set())
            if enabled():
                from .dsh_architecture_surface import add_workspace_proxy
                surface=add_workspace_proxy(surface,project/'runtime/agent_workspace')
            card=project/'runtime/agent_workspace/notes/reconstruction_card.md'
            turn_context=architecture.memory() if architecture else {'conversation':context.get('conversation',[]),
                'saved_plan':card.read_text(encoding='utf-8') if card.exists() else '',
                'current_owned_state':ruby_state or {}}
            def dispatch(name,args):
                if architecture:
                    if name=='kstudio_read_skill':return architecture.read_skill(args)
                    if name=='kstudio_save_design_graph':return architecture.save_graph(args)
                    if name=='kstudio_scope_existing_parts':return architecture.scope_existing_parts(args)
                    if name=='kstudio_review_model':
                        if args:raise ValueError('No review arguments accepted.')
                        return architecture.review(surface.quality_state)
                    if name=='sketchup_save_plan':
                        from .k_architecture import load_json
                        validate_graph(load_json(architecture.graph_path,None),{s['id'] for s in architecture.images})
                result=surface.dispatch(name,args)
                if architecture and name=='sketchup_save_plan' and result.get('success'):
                    architecture.bind_plan()
                architecture.memory()
                return result
            instructions=self.instructions
            effort=self.effective_configuration.requested_effort
            if reusable_parts:
                instructions += ('\nFor a precise repair of existing parts without changing the design facts, first call '
                                 'kstudio_scope_existing_parts with only the parts to repair, then save a short plan. '
                                 'Use the part names in the tool schema. Do not regenerate the existing graph for this repair. '
                                 'A change to layout, system membership or spatial facts requires the full graph.')
            if self.guidance=='architecture' and mcp_enabled:
                # Core execution methods are host-selected context, not an
                # optional first tool call that a resumed model can skip. Skill
                # hashes also change the official session binding on upgrades.
                for skill_id in ('native','facade','spatial','edit'):
                    skill=architecture.read_skill({'id':skill_id})
                    instructions+=f'\nHOST-LOADED ARCHITECTURE SKILL {skill_id} sha256={skill["sha256"]}; method guidance, not approval:\n'+skill['content']
                instructions+='\nEXECUTION CADENCE: The plan is already approved and the relevant skills are loaded above. Start with sketchup_model_state. Batch the exact native reads needed for the next operation. After the reads, write only the NEXT coherent system promptly and inspect its result before continuing. Use repeat/step or a short loop for repeated parts. Do not enumerate repeated geometry, re-read the plan or draft an entire turn of geometry before calling the next tool.'
                if ruby_state:
                    instructions+='\nFor a scoped edit use the approved plan and live measurements. After measuring the receiving geometry, commit the simplest receiving part first when it can be built independently. Do not spend the output computing tread, landing and railing details together. Verify the exact connection and KEEP once the related parts are committed.'
            try:
                result=self._official_turn(project=project,thread_id=thread_id,
                    prompt=json.dumps(turn_context,ensure_ascii=False)+f'\nHOST_STAGE={agent_action}; native_execution_granted={mcp_enabled}.',
                    specs=surface.dynamic_tools+(architecture_specs(agent_action, reusable_parts) if architecture else []),dispatch=dispatch,instructions=instructions,
                    images=images,progress=progress_callback,new_session_on_binding_change=True,reasoning_effort=effort)
            except NativeAgentUnavailable as error:
                from .k_architecture import write_json
                architecture.review(surface.quality_state)
                partial=getattr(error,'partial_result',None)
                write_json(architecture.base/'last-interruption.json',{'status':'interrupted_or_failed',
                    'error_type':type(error).__name__,'session_id':getattr(partial,'thread_id',None),
                    'tool_calls':getattr(partial,'tool_call_count',None),
                    'next_step':'Inspect current native identity/revision and commit journal before continuing; never replay the whole turn.',
                    'original_work_preserved':True})
                architecture.memory()
                raise
            if architecture and mcp_enabled:
                review=architecture.review(surface.quality_state)
                if not review['evidence_current']:
                    # No additional inference or silent geometry retry. Candor is
                    # enforced even when the model omits its final review tool.
                    result.reply+='\n\n验收记录：当前模型的最终视图尚不齐全（'+ '、'.join(review['missing_current_views'])+'），本轮不能标为完整验收。已完成的模型工作保留。'
            architecture.memory()
            return result
