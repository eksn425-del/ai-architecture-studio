"""Native coding extension over the existing owned-model transaction boundary.

The SDK writes/reads project scripts; the host remains the single SU writer.
ADAI methods already injected by ProjectRuby retain their invocation ledger.
"""
from .agent_tools import AgentToolSurface, AgentToolContext


def extend_surface(base, *, runtime_root, mcp, project_dir, model_path, model_guid,
                   ruby_state, allowed_parts):
    original = AgentToolSurface(runtime_root, mcp).prepare(
        project_dir=project_dir, mcp_enabled=True, model_path=model_path,
        model_guid=model_guid, ruby_enabled=True, ruby_state=ruby_state,
        tool_profile='full')
    names = {'sketchup_run_workspace_ruby', 'sketchup_inspect_owned', 'sketchup_inspect_owned_batch'}
    specs = [s for s in original.dynamic_tools if s['name'] in names]
    def dispatch(name, args):
        if name not in names:
            return base.dispatch(name, args)
        if args.get('script_id') != 'harness_building':
            raise ValueError('Use the existing owned script_id harness_building.')
        if name == 'sketchup_run_workspace_ruby':
            if args.get('allow_full_rebuild'):
                raise ValueError('This task does not authorize replacing an existing building.')
            existing = ruby_state.get('harness_building', {}).get('root_pid')
            if existing:
                if args.get('update_mode') != 'edit':
                    raise ValueError('Continue the existing root with edit and exact approved paths.')
                paths = args.get('allowed_mutation_paths')
                if not paths or any(not p or p[0] not in allowed_parts for p in paths):
                    raise ValueError('Every changed path must belong to an approved architectural part.')
            result = original.dispatch(name, args)
            if result.get('success') is not False:
                base.quality_state['writes'].append({'method':'workspace_ruby',
                    'revision':ruby_state.get('harness_building', {}).get('revision',0)})
            return result
        return original.dispatch(name, args)
    return AgentToolContext(dynamic_tools=base.dynamic_tools+specs, dispatch=dispatch,
                            quality_state=base.quality_state)


def add_workspace_proxy(base, workspace):
    from .workspace_files import workspace_file_tools, workspace_file_call
    tools=workspace_file_tools();names={t['name'] for t in tools}
    return AgentToolContext(dynamic_tools=base.dynamic_tools+tools,
        dispatch=lambda name,args:workspace_file_call(workspace,name,args) if name in names else base.dispatch(name,args),
        quality_state=base.quality_state)
