"""Controlled public Codex Responses route -> real Blender acceptance.

A separate scripted subprocess speaks App Server JSON-RPC to the UNMODIFIED
CodexAppServerRuntime. It is NOT upstream Codex, real Responses HTTP/SSE, model
reasoning, provider quality, paid inference or a cost benchmark. Every geometry
write crosses the public router/runtime/tool surface; host operations only grant
explicit fixture scope and independently read native evidence.
"""
from __future__ import annotations

import argparse
import base64
import copy
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import tomllib
from unittest.mock import patch
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
MODEL = 'kstudio-controlled-fixture'
API_BASE = 'https://controlled-fixture.invalid/v1'
SYNTHETIC_KEY = 'controlled-test-only-not-a-real-credential'


def dump(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def target_edits(objects):
    edits = []
    for floor in range(3):
        for bay in (2, 3):
            obj = copy.deepcopy(objects[f'bay_{floor}_{bay}_rail'])
            obj['dimensions'][2] = .45
            obj['location'][2] -= .075
            obj['material']['color'] = [.12, .15, .18, 1]
            edits.append(obj)
    return edits


def file_hashes(root: Path):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


def scenarios(objects):
    edits = target_edits({obj['id']: obj for obj in objects})
    def call(call_id, name, arguments, **extra):
        return {'call_id': call_id, 'name': name, 'arguments': arguments, **extra}
    protected = copy.deepcopy(next(obj for obj in objects if obj['id'] == 'KEEP_neighbor'))
    protected['dimensions'][0] += 1
    return {
        'PLAN': [],
        'UNAPPROVED': [call('unapproved-build', 'blender_apply_objects', {'objects': objects})],
        'BUILD': [call('build', 'blender_apply_objects', {'objects': objects}),
                  call('read-build', 'blender_inspect_scene', {})],
        'EDIT': [call('foreign-turn-delete', 'blender_apply_objects', {'objects': [], 'delete_ids': ['KEEP_neighbor']}, foreign=True),
                 call('hostile-delete', 'blender_apply_objects', {'objects': [], 'delete_ids': ['KEEP_neighbor']}),
                 call('hostile-update', 'blender_apply_objects', {'objects': [protected]}),
                 call('hostile-add', 'blender_apply_objects', {'objects': [{'id': 'unapproved', 'location': [0, 0, 0], 'dimensions': [1, 1, 1]}]}),
                 call('edit-six', 'blender_apply_objects', {'objects': edits}),
                 call('read-edit', 'blender_inspect_scene', {}),
                 call('render-edit', 'blender_render_scene', {'view': 'front', 'resolution': 800, 'denoise': False}),
                 call('exact-detail', 'blender_inspect_scene', {'object_ids': [edits[0]['id']], 'include_geometry_detail': True})],
        'STALE': [call('stale-instruction', 'blender_apply_objects', {'objects': edits})],
        'UNKNOWN': [call('unknown-tool', 'execute_python', {'code': 'delete_everything()'})],
        'READ_ONLY': [call('final-inspect', 'blender_inspect_scene', {})],
    }


def fixture_server(root: Path):
    """Deterministic transport peer only; it cannot call Blender or any API."""
    config = tomllib.loads((Path(os.environ['CODEX_HOME']) / 'config.toml').read_text())
    provider_id = config['model_provider']
    provider = config['model_providers'][provider_id]
    assert provider['base_url'] == API_BASE
    assert provider['requires_openai_auth'] is False
    assert config['sandbox_workspace_write']['network_access'] is False
    assert os.environ.get(provider['env_key']) == SYNTHETIC_KEY
    assert not (Path(os.environ['CODEX_HOME']) / 'auth.json').exists()
    script = json.loads((root / 'scenarios.json').read_text())
    log = root / ('transport-' + uuid.uuid4().hex + '.jsonl')
    def record(direction, message):
        with log.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'direction': direction, 'message': message}, ensure_ascii=False) + '\n')
    record('fixture_metadata', {'simulation': True, 'upstream_codex': False,
        'external_requests': 0, 'model': config['model'], 'model_provider': provider_id,
        'api_base': provider['base_url'], 'credential_present_not_logged': True,
        'login_cache_present': False, 'network_access': False})
    def send(message):
        record('fixture_to_runtime', message)
        print(json.dumps(message, ensure_ascii=False), flush=True)
    def receive():
        line = sys.stdin.readline()
        if not line:
            return None
        message = json.loads(line)
        record('runtime_to_fixture', message)
        return message
    thread_id = ''
    thread_state = root / 'thread-usage.json'
    usage_state = json.loads(thread_state.read_text()) if thread_state.exists() else {}
    while (request := receive()) is not None:
        method, params = request.get('method'), request.get('params', {})
        if method == 'initialize':
            send({'id': request['id'], 'result': {'userAgent': 'SCRIPTED_TEST_NOT_CODEX'}})
        elif method == 'initialized':
            continue
        elif method in ('thread/start', 'thread/resume'):
            thread_id = params.get('threadId') or ('controlled-thread-' + uuid.uuid4().hex)
            send({'id': request['id'], 'result': {'thread': {'id': thread_id},
                'model': MODEL, 'modelProvider': provider_id, 'reasoningEffort': 'low'}})
        elif method == 'turn/start':
            prompt = next(item['text'] for item in params['input'] if item['type'] == 'text')
            label = prompt.split('FIXTURE:', 1)[1].split()[0]
            turn_id = 'controlled-turn-' + uuid.uuid4().hex
            send({'id': request['id'], 'result': {'turn': {'id': turn_id, 'status': 'inProgress'}}})
            identity = {'threadId': thread_id, 'turnId': turn_id}
            for call in script[label]:
                call_params = {**identity, 'callId': call['call_id'], 'tool': call['name'], 'arguments': call['arguments']}
                if call.get('foreign'):
                    call_params['turnId'] = 'not-the-active-turn'
                send({'id': call['call_id'], 'method': 'item/tool/call', 'params': call_params})
                result = receive()
                assert result and result.get('id') == call['call_id'], result
                assert 'result' in result
            # Deliberately nonzero historical totals prove only the current-turn
            # delta is attributed; numbers are fixed fixtures, not tokenization.
            prior = usage_state.get(thread_id, {'inputTokens': 10000, 'outputTokens': 1000})
            last = {'inputTokens': 100 + 10 * len(script[label]), 'outputTokens': 20}
            total = {key: prior[key] + last[key] for key in prior}
            usage_state[thread_id] = total
            dump(thread_state, usage_state)
            send({'method': 'thread/tokenUsage/updated', 'params': {**identity, 'tokenUsage': {'total': total, 'last': last}}})
            send({'method': 'item/completed', 'params': {**identity, 'item': {
                'id': 'reply-' + label, 'type': 'agentMessage',
                'text': 'CONTROLLED_' + label + ': scripted fixture; independent visual quality NOT_RUN.'}}})
            send({'method': 'turn/completed', 'params': {**identity, 'turn': {'id': turn_id, 'status': 'completed'}}})
        else:
            raise AssertionError(f'Unexpected fixture method: {method}')


def make_fixture_executable(root: Path, script):
    root.mkdir(parents=True, exist_ok=True)
    dump(root / 'scenarios.json', script)
    bootstrap = '#!' + sys.executable + '\nimport runpy, sys\n' \
        + 'sys.argv = ' + repr([str(Path(__file__).resolve()), '--fixture-server', str(root)]) + '\n'
    bootstrap += 'runpy.run_path(' + repr(str(Path(__file__).resolve())) + ', run_name="__main__")\n'
    if os.name == 'nt':
        # Keep the same real subprocess/runtime on Windows; only the scripted
        # transport peer is synthetic. No shell launch is added to the product.
        peer = root / 'scripted-app-server.py'
        peer.write_text(bootstrap, encoding='utf-8')
        launcher = root / 'scripted-app-server.cmd'
        quote = lambda path: '"' + str(path).replace('%', '%%') + '"'
        launcher.write_text('@echo off\nchcp 65001 >nul\n' + quote(sys.executable)
                            + ' ' + quote(peer) + '\n', encoding='utf-8')
        return launcher
    launcher = root / 'scripted-app-server'
    launcher.write_text(bootstrap, encoding='utf-8')
    launcher.chmod(0o700)
    return launcher


def collect_transport(root: Path):
    records = [json.loads(line) for path in sorted(root.glob('transport-*.jsonl'))
               for line in path.read_text().splitlines()]
    replies = {row['message']['id']: row['message']['result'] for row in records
               if row['direction'] == 'runtime_to_fixture' and 'result' in row['message']}
    return records, replies


def receipt(reply):
    return json.loads(next(part['text'] for part in reply['contentItems'] if part['type'] == 'inputText'))


def fresh_reopen(project: Path, scene, output: Path, executable: str):
    """Independent host read-only validation, never counted as an Agent call."""
    target = output / f"fresh-reopen-r{scene['revision']}.json"
    command = [executable, '--background', '--disable-autoexec', str(project / scene['model_path']),
        '--python-exit-code', '1', '--python', str(ROOT / 'app/blender_worker.py'), '--', 'inspect', str(target)]
    result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=240)
    (output / f"fresh-reopen-r{scene['revision']}.log").write_text(result.stdout + result.stderr)
    return json.loads(target.read_text())


def run(output: Path):
    from app.blender_backend import BlenderBackend
    from app.model_router import DeterministicModelRouter
    from app.native_agent import CodexAppServerRuntime
    from scripts.verify_cloud_blender_contracts import fixture_objects, bind_instruction
    output = output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use a fresh output directory; prior evidence is immutable')
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    project = output / 'project'
    (project / 'state').mkdir(parents=True)
    dump(project / 'state/modeling_backend.json', {'backend': 'blender'})
    objects = fixture_objects()
    script = scenarios(objects)
    executable = make_fixture_executable(output / 'fixture', script)
    turns = []
    with patch.dict(os.environ, {'HOME': str(output / 'home'),
            'CODEX_HOME': str(output / 'unused-login-home'),
            'ARCH_STUDIO_CODEX_HOME': str(output / 'isolated-codex-home'),
            'ARCH_STUDIO_ECONOMY_PROVIDER': 'codex', 'ARCH_STUDIO_STANDALONE': '1',
            'ARCH_STUDIO_ECONOMY_MODEL': MODEL, 'ARCH_STUDIO_ECONOMY_REASONING_EFFORT': 'low',
            'ARCH_STUDIO_CODEX_TIMEOUT_SECONDS': '300', 'LITELLM_LOCAL_MODEL_COST_MAP': 'True'}, clear=False):
        native = CodexAppServerRuntime(output / 'runtime', codex_executable=str(executable))
        router = DeterministicModelRouter(native, runtime_root=output / 'runtime')
        # Public configuration and dispatch. No monkeypatch of runtime, tools,
        # _prepare_home, _run_turn, _request or native subprocess creation.
        router.configure_codex_responses(model=MODEL, api_base=API_BASE, api_key=SYNTHETIC_KEY,
            reasoning_effort='low', protocol='responses', compatibility_acknowledged=True)
        runtime = router.codex_responses_runtime
        assert type(runtime) is CodexAppServerRuntime
        assert runtime is router.providers['codex-responses']
        backend = BlenderBackend(project)
        def turn(label, approved, thread=None, readonly=False):
            result = router.respond(tier='economy', project_dir=project, thread_id=thread,
                prompt='FIXTURE:' + label + ' Controlled synthetic contract test only.',
                mcp_enabled=approved, ruby_enabled=False,
                developer_instructions='Synthetic 74-object test. Host execution permission and exact edit scope are authoritative. KEEP all other objects.',
                workflow_mode='architecture_design', tool_profile='full',
                blender_readonly_tools=readonly)
            turns.append({'label': label, 'host_execution_granted': approved, **asdict(result)})
            assert result.status == 'completed'
            assert result.provider_name == 'codex-responses' and result.model_name == MODEL
            assert result.input_tokens == 100 + 10 * len(script[label])
            assert result.output_tokens == 20
            return result
        plan = turn('PLAN', False)
        assert not backend.state.exists()
        unapproved = turn('UNAPPROVED', False, plan.thread_id)
        assert not backend.state.exists() and unapproved.failed_tool_calls == 1
        built = turn('BUILD', True)
        first = backend.dispatch('blender_inspect_scene', {})
        dump(output / 'revision-1.json', first)
        assert first['revision'] == 1 and len(first['objects']) == 74
        instruction = 'Change only central six rail panels to dark gray and 0.45m height; preserve lower edges and KEEP_neighbor.'
        bind_instruction(project, instruction, 'unified-fixture-edit')
        ids = [obj['id'] for obj in target_edits(first['objects'])]
        keep = sorted(set(first['objects']) - set(ids))
        backend.install_edit_contract(allowed_ids=ids, keep_ids=keep, expected_revision=1)
        changed = turn('EDIT', True, built.thread_id)
        second = backend.dispatch('blender_inspect_scene', {})
        dump(output / 'revision-2.json', second)
        assert changed.failed_tool_calls == 3
        bind_instruction(project, 'Stop changes. Inspect only; keep existing geometry.', 'unified-fixture-inspect')
        before = file_hashes(backend.root)
        stale = turn('STALE', True, changed.thread_id)
        assert stale.failed_tool_calls == 1 and file_hashes(backend.root) == before
        unknown = turn('UNKNOWN', True, stale.thread_id)
        assert unknown.failed_tool_calls == 1 and file_hashes(backend.root) == before
        inspected = turn('READ_ONLY', False, unknown.thread_id, readonly=True)
        assert inspected.failed_tool_calls == 0 and file_hashes(backend.root) == before
        config_text = (runtime.home / 'config.toml').read_text()
        config = tomllib.loads(config_text)
        route = router.route('economy').as_dict()
        assert not (runtime.home / 'auth.json').exists()
        assert not (output / 'unused-login-home').exists()
    records, replies = collect_transport(output / 'fixture')
    expected_denials = {'unapproved-build', 'foreign-turn-delete', 'hostile-delete',
        'hostile-update', 'hostile-add', 'stale-instruction', 'unknown-tool'}
    assert all(replies[key]['success'] is False for key in expected_denials)
    events = [json.loads(line) for path in (project / 'runtime/agent_events').glob('*.jsonl') for line in path.read_text().splitlines()]
    raw_receipts = {event['call_id']: event['output'] for event in events if event['event'] == 'tool_receipt'}
    native_receipts = {}
    for key, revision in [('build', 1), ('read-build', 1), ('edit-six', 2), ('read-edit', 2), ('final-inspect', 2)]:
        result = receipt(replies[key])
        assert replies[key]['success'] is True
        assert result['revision'] == revision and result['native_reopen'] == 'PASS'
        original = first if revision == 1 else second
        assert result['objects'] == original['objects']
        assert raw_receipts[key]['geometry'] == original['geometry']
        for object_id, geometry in result['geometry'].items():
            native_geometry = original['geometry'][object_id]
            arrays = {field: native_geometry[field] for field in ('vertices', 'faces')}
            omission = geometry['wire_geometry_omission']
            assert omission['counts'] == {'vertices': 8, 'faces': 6}
            assert omission['sha256'] == hashlib.sha256(json.dumps(arrays, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
            assert all(geometry[field] == value for field, value in native_geometry.items() if field not in arrays)
            assert 'vertices' not in geometry and 'faces' not in geometry
        assert result['wire_geometry_projection']['retrieve']
        native_receipts[key] = {'revision': revision, 'native_reopen': result['native_reopen'],
            'geometry_objects': len(result['geometry']), 'raw_geometry_matches_native': True,
            'wire_topology_omissions_sha_match_native': True}
    detail = receipt(replies['exact-detail'])
    assert set(detail['geometry']) == {ids[0]}
    assert detail['geometry'][ids[0]] == second['geometry'][ids[0]]
    render = receipt(replies['render-edit'])
    render_path = project / render['image_path']
    render_hash = hashlib.sha256(render_path.read_bytes()).hexdigest()
    forwarded_images = []
    for item in replies['render-edit']['contentItems']:
        if item['type'] != 'inputImage':
            continue
        url = item['imageUrl']
        assert url.startswith('data:image/png;base64,')
        forwarded_images.append(hashlib.sha256(base64.b64decode(url.split(',', 1)[1], validate=True)).hexdigest())
    fresh = {str(scene['revision']): fresh_reopen(project, scene, output, backend.executable) for scene in (first, second)}
    tool_starts = [row['message'] for row in records if row['direction'] == 'fixture_to_runtime'
                   and row['message'].get('method') == 'item/tool/call']
    thread_requests = [row['message'] for row in records if row['direction'] == 'runtime_to_fixture'
                       and row['message'].get('method') in ('thread/start', 'thread/resume')]
    input_requests = [row['message'] for row in records if row['direction'] == 'runtime_to_fixture'
                      and row['message'].get('method') == 'turn/start']
    checks = {
        'public_router_selects_same_codex_runtime': route['provider'] == 'codex-responses' and route['agent_engine'] == 'codex-app-server',
        'explicit_api_config_without_login_auth': config['model_provider'] == 'kstudio_api' and SYNTHETIC_KEY not in config_text,
        'no_geometry_before_host_execution': plan.tool_call_count == 0 and unapproved.failed_tool_calls == 1,
        'all_seven_guard_attempts_denied': len(expected_denials) == 7 and all(replies[key]['success'] is False for key in expected_denials),
        'same_render_pixels_returned_to_scripted_app_server': forwarded_images == [render_hash],
        'native_receipts_and_hashed_topology_returned_to_scripted_app_server': len(native_receipts) == 5,
        'full_raw_native_geometry_retained_in_runtime_events': all(row['raw_geometry_matches_native'] for row in native_receipts.values()),
        'target_height_and_color': second['revision'] == 2 and all(abs(second['geometry'][key]['dimensions'][2] - .45) < 1e-5
            and all(abs(a - b) < 1e-5 for a, b in zip(second['geometry'][key]['material'][0]['color'], [.12, .15, .18, 1])) for key in ids),
        'six_lower_edges_preserved': all(abs(first['geometry'][key]['location'][2] - first['geometry'][key]['dimensions'][2] / 2
            - second['geometry'][key]['location'][2] + second['geometry'][key]['dimensions'][2] / 2) < 1e-5 for key in ids),
        'all_68_keep_geometry_material_topology_preserved': len(keep) == 68 and all(first['geometry'][key] == second['geometry'][key] for key in keep),
        'native_save_reopen_and_independent_fresh_reopens': first['native_reopen'] == second['native_reopen'] == 'PASS'
            and fresh['1'] == first['geometry'] and fresh['2'] == second['geometry'],
        'original_blend_immutable': hashlib.sha256((project / first['model_path']).read_bytes()).hexdigest() == first['sha256'],
        'source_reference_reaches_turn_input': any(any(item['type'] == 'localImage' for item in request['params']['input']) for request in input_requests),
        'provider_bound_thread_resume': any(request['method'] == 'thread/resume' for request in thread_requests)
            and all(request['params']['modelProvider'] == 'kstudio_api' for request in thread_requests),
        'synthetic_usage_turn_delta_not_historical_total': all(turn['input_tokens'] == 100 + 10 * len(script[turn['label']]) and turn['output_tokens'] == 20 for turn in turns),
        'inspect_only_round_does_not_mutate_model': file_hashes(backend.root) == before,
    }
    evidence = {
        'test_kind': 'controlled scripted App Server subprocess + public Codex Responses router/runtime + actual Blender',
        'route': route, 'checks': checks, 'turns': turns, 'native_wire_receipts': native_receipts,
        'raw_journal_receipt_count': len(raw_receipts),
        'guard_denials': {key: replies[key] for key in sorted(expected_denials)},
        'native_render_path': str(render_path.relative_to(output)), 'native_render_sha256': render_hash,
        'returned_image_sha256': forwarded_images, 'native_render_attachment_count': len(forwarded_images),
        'operations': {'native_revisions': [first['revision'], second['revision']], 'objects': 74, 'edited': 6, 'preserved': 68,
            'tool_requests_at_transport': len(tool_starts), 'runtime_tool_calls': sum(turn['tool_call_count'] for turn in turns),
            'failed_runtime_tool_calls': sum(turn['failed_tool_calls'] for turn in turns), 'scripted_turns': len(turns)},
        'usage': {'input_tokens': sum(turn['input_tokens'] for turn in turns), 'output_tokens': sum(turn['output_tokens'] for turn in turns),
            'basis': 'DETERMINISTIC_FIXTURE_NUMBERS_NOT_TOKENIZER_OR_BILLING'},
        'upstream_codex_app_server': 'NOT_RUN_BY_THIS_SCRIPT',
        'responses_http_sse': 'NOT_TESTED_BY_THIS_SCRIPT', 'paid_cost': 'NOT_INCURRED',
        'blender_version': subprocess.check_output([backend.executable, '--version'], text=True).splitlines()[0],
        'runtime_seconds': time.monotonic() - started,
        'limitations': [
            'Only the App Server peer is scripted; production runtime and Blender are real. This is not actual Codex internal reasoning.',
            'The fixture never contacts the configured .invalid URL and makes no HTTP inference request.',
            'No autonomous planning, visual understanding, provider fidelity, provider billing or monetary savings demonstrated.',
            'Host explicitly grants execution and exact allowed/KEEP IDs; natural-language authorization inference is not tested.',
            'No independent LLM Critic, owner source reconstruction, SketchUp, browser GUI or user computer acceptance.',
            'Independent fresh native reopens are host read-only checks, not Agent operations.'],
    }
    dump(output / 'events.json', events)
    dump(output / 'transport.json', records)
    dump(output / 'evidence.json', evidence)
    assert all(checks.values()), checks
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--fixture-server', type=Path)
    args = parser.parse_args()
    if args.fixture_server:
        fixture_server(args.fixture_server)
    elif args.output:
        evidence = run(args.output)
        print(json.dumps({key: evidence[key] for key in ('test_kind', 'route', 'checks', 'operations', 'usage', 'paid_cost', 'runtime_seconds')}, indent=2))
    else:
        parser.error('--output is required')


if __name__ == '__main__':
    main()
