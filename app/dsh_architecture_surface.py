"""Native coding extension over the existing owned-model transaction boundary.

The SDK writes/reads project scripts; the host remains the single SU writer.
ADAI methods already injected by ProjectRuby retain their invocation ledger.
"""
from .agent_tools import AgentToolSurface, AgentToolContext
from copy import deepcopy
import json
from pathlib import Path
from datetime import datetime, timezone

STAGES = ('structure', 'enclosure', 'sample', 'repetition', 'circulation', 'finish', 'correction')


def extend_surface(base, *, runtime_root, mcp, project_dir, model_path, model_guid,
                   ruby_state, allowed_parts):
    original = AgentToolSurface(runtime_root, mcp).prepare(
        project_dir=project_dir, mcp_enabled=True, model_path=model_path,
        model_guid=model_guid, ruby_enabled=True, ruby_state=ruby_state,
        tool_profile='full')
    names = {'sketchup_run_workspace_ruby', 'sketchup_inspect_owned', 'sketchup_inspect_owned_batch'}
    specs = [deepcopy(s) for s in original.dynamic_tools if s['name'] in names]
    for spec in specs:
        if spec['name'] == 'sketchup_run_workspace_ruby' and 'inputSchema' in spec:
            spec['inputSchema']['properties']['construction_stage'] = {
                'type': 'string', 'enum': list(STAGES),
                'description': 'Label this bounded architectural construction step. Submit real incremental geometry, not an entire prebuilt building. A label does not certify completion.'}
    def dispatch(name, args):
        if name not in names:
            result = base.dispatch(name, args)
            if name == 'sketchup_model_state' and result.get('success') is not False:
                ledger = Path(project_dir) / 'runtime' / 'construction_steps.jsonl'
                if ledger.is_file() and not ledger.is_symlink():
                    try:
                        rows = [json.loads(line) for line in ledger.read_text(encoding='utf-8').splitlines()]
                        result = {**result, 'construction_steps': rows[-32:]}
                    except (OSError, ValueError):
                        result = {**result, 'construction_steps_error': 'unreadable; inspect native state before continuation'}
            return result
        if args.get('script_id') != 'harness_building':
            raise ValueError('Use the existing owned script_id harness_building.')
        if name == 'sketchup_run_workspace_ruby':
            args = dict(args)
            stage = args.pop('construction_stage', None)
            if stage is not None and stage not in STAGES:
                raise ValueError('Unknown construction stage.')
            if args.get('allow_full_rebuild'):
                raise ValueError('This task does not authorize replacing an existing building.')
            existing = ruby_state.get('harness_building', {}).get('root_pid')
            if existing:
                if args.get('update_mode') != 'edit':
                    raise ValueError('Continue the existing root with edit and exact approved paths.')
                paths = args.get('allowed_mutation_paths')
                if not paths or any(not p or p[0] not in allowed_parts for p in paths):
                    raise ValueError('Every changed path must belong to an approved architectural part.')
            previous_revision = ruby_state.get('harness_building', {}).get('revision', 0)
            result = original.dispatch(name, args)
            if result.get('success') is not False:
                base.quality_state['writes'].append({'method':'workspace_ruby',
                    'revision':ruby_state.get('harness_building', {}).get('revision',0)})
                native = ruby_state.get('harness_building', {})
                if stage and native.get('revision', 0) > previous_revision and not native.get('write_in_flight') and native.get('durability_status') != 'unconfirmed':
                    receipt = {'stage': stage, 'revision': native['revision'],
                        'root_pid': native.get('root_pid'), 'at': datetime.now(timezone.utc).isoformat(),
                        'status': 'native_revision_committed', 'system_complete': False}
                    result = {**result, 'construction_step': receipt}
                    # Recording failure must never transform a committed write into a retry.
                    try:
                        ledger = Path(project_dir) / 'runtime' / 'construction_steps.jsonl'
                        if ledger.is_symlink() or ledger.parent.is_symlink():
                            raise ValueError('Construction ledger must not redirect')
                        ledger.parent.mkdir(parents=True, exist_ok=True)
                        with ledger.open('a', encoding='utf-8') as stream:
                            stream.write(json.dumps(receipt, ensure_ascii=False) + '\n')
                    except (OSError, ValueError):
                        result['construction_step_recording'] = 'failed_after_commit_do_not_replay'
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
