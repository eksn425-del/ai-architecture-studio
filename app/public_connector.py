"""User-paired, local filesystem transport for the public SketchUp extension.

No network listener, developer configuration or proprietary plugin is required.
The extension runs requests on SketchUp's main thread. Uncertain operations are
never submitted again automatically; callers retain their durable operation ID.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sys
import time
import uuid
from pathlib import Path

VERSION = '2026.11.05-r2'
TOOL_NAMES = ('sketchup_health', 'sketchup_get_model_context', 'sketchup_eval_project_file',
              'sketchup_set_camera', 'sketchup_export_view_image')
DOCUMENT_BINDING = {'expected_model_path':{'type':'string'}, 'expected_model_guid':{'type':'string'}}
TOOL_PROPERTIES = {
    'sketchup_eval_project_file': {'script_path': {'type': 'string'},
        'operation_name': {'type': 'string'}, 'operation_id': {'type': 'string'}},
    'sketchup_set_camera': {**DOCUMENT_BINDING, **{key: {'type': 'array', 'items': {'type': 'number'}, 'minItems': 3, 'maxItems': 3}
                           for key in ('eye_m', 'target_m', 'up')}},
    'sketchup_export_view_image': {**DOCUMENT_BINDING, 'output_path': {'type': 'string'}, 'width': {'type': 'integer'},
        'height': {'type': 'integer'}, 'zoom_extents': {'type': 'boolean'}},
}


def root_dir():
    return Path(os.environ.get('KSTUDIO_PUBLIC_CONNECTOR_ROOT') or
                Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'KStudio' / 'connectors' / 'public')


def atomic_write(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    with temporary.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, separators=(',', ':'))
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def initialize_pairing(root=None):
    root = Path(root or root_dir())
    for part in (root, *root.parents):
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise ValueError('Connector directory must not redirect')
    root.mkdir(parents=True, exist_ok=True)
    for name in ('requests', 'responses', 'journal', 'generated_scripts'):
        (root / name).mkdir(exist_ok=True)
    config = root / 'pairing.json'
    if not config.exists():
        # Directory is per-user LOCALAPPDATA; restrict it to that Windows user
        # and SYSTEM, never grant a browser/network identity access.
        if os.name == 'nt':
            import subprocess
            identity = subprocess.check_output(['whoami', '/user', '/fo', 'csv', '/nh'], text=True, encoding='mbcs',
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            import csv
            sid = next(csv.reader([identity.strip()]))[1]
            result = subprocess.run(['icacls', str(root), '/inheritance:r', '/grant:r',
                f'*{sid}:(OI)(CI)F', '*S-1-5-18:(OI)(CI)F'], capture_output=True,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            if result.returncode:
                raise ValueError('Could not protect connector pairing directory')
        with config.open('x', encoding='utf-8') as stream:
            json.dump({'schema': 1, 'token': secrets.token_hex(32),
                       'script_root': str((root / 'generated_scripts').resolve()),
                       'workspace_roots': [str(Path(os.environ['ARCH_STUDIO_RUNTIME_DIR']).resolve())]
                           if os.environ.get('ARCH_STUDIO_RUNTIME_DIR') else [],
                       'enabled': True}, stream)
    return root


def authorize_workspace(root, workspace):
    """Register a host-verified local workspace; never called by model tools."""
    root, workspace = Path(root), Path(workspace).absolute()
    for part in (workspace, *workspace.parents):
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise ValueError('Connector workspace must not redirect')
    if not workspace.is_dir() or workspace == Path(workspace.anchor):
        raise ValueError('Connector workspace must be an existing project runtime directory')
    if workspace.resolve() != workspace:
        raise ValueError('Connector workspace must not redirect')
    config = json.loads((root / 'pairing.json').read_text(encoding='utf-8'))
    if not config.get('enabled'):
        raise ValueError('Connector pairing is disabled; explicitly re-pair before use')
    folders = config.setdefault('workspace_roots', [])
    path = str(workspace.resolve())
    if path not in folders:
        folders.append(path)
        atomic_write(root / 'pairing.json', config)


def signed(body, token):
    data = json.dumps(body, ensure_ascii=False, separators=(',', ':'))
    return {'body': data, 'mac': hmac.new(token.encode(), data.encode(), hashlib.sha256).hexdigest()}


def verified(envelope, token):
    expected = hmac.new(token.encode(), envelope['body'].encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, envelope['mac']):
        raise ValueError('Invalid connector receipt signature')
    return json.loads(envelope['body'])


def call(name, arguments=None, *, root=None, timeout=None):
    from .connector_deadlines import native_response_timeout
    if timeout is None:timeout=native_response_timeout(name)
    if name not in TOOL_NAMES:
        raise ValueError('Unsupported public connector tool')
    root = Path(root or root_dir())
    config = json.loads((root / 'pairing.json').read_text(encoding='utf-8'))
    if not config.get('enabled'):
        raise ValueError('Connector pairing is disabled')
    args = dict(arguments or {})
    from .connector_instances import target_for_request
    project = args.pop('_kstudio_project', '')
    target = target_for_request(root, project,
        identity_only=name in {'sketchup_health', 'sketchup_get_model_context'},
        wait_for_read=name in {'sketchup_health', 'sketchup_get_model_context', 'sketchup_get_model_info',
                               'sketchup_get_entities', 'sketchup_export_view_image', 'sketchup_set_camera'})
    if name in {'sketchup_set_camera','sketchup_export_view_image'}:
        if any(not isinstance(args.get(key),str) or not args[key].strip() for key in DOCUMENT_BINDING):
            raise ValueError('Camera and image capture require an explicit document path and GUID')
    if name == 'sketchup_eval_project_file':
        script = Path(args['script_path']).resolve(strict=True)
        if script.suffix.lower() != '.rb' or not script.is_relative_to(Path(config['script_root']).resolve()):
            raise ValueError('Script is outside the paired generated-script directory')
        args['script_sha256'] = hashlib.sha256(script.read_bytes()).hexdigest()
        args['script_path'] = str(script)
    # This transport only deduplicates operations. ProjectRuby persists intent
    # BEFORE dispatch and blocks ALL further geometry writes while any owned
    # revision is unconfirmed, including a new script/operation ID. RETURNED
    # here is not a native commit/save receipt; that separate host gate remains.
    # Same generated script/contents cannot be replayed after an uncertain reply.
    explicit_id = args.pop('operation_id', None)
    request_digest = hashlib.sha256(json.dumps([name, args, target] if target else [name, args], sort_keys=True).encode()).hexdigest()
    # A changed document token must not create a new write operation for the
    # same script after an unknown reply. Return a digest conflict, never replay.
    write_identity = hashlib.sha256(json.dumps([name, args, project, target['instance_id']], sort_keys=True).encode()).hexdigest() if target else request_digest
    op = explicit_id or (write_identity
                        if name == 'sketchup_eval_project_file' else uuid.uuid4().hex)
    if not isinstance(op, str) or not op.isalnum() or len(op) > 80:
        raise ValueError('Invalid operation ID')
    receipt = root / 'responses' / (op + '.json')
    # Modern traffic never enters the legacy shared queue: an older installed
    # plugin cannot understand a target field and would otherwise steal it.
    request_dir = root / 'instance-requests' / target['instance_id'] if target else root / 'requests'
    request_dir.mkdir(parents=True, exist_ok=True)
    request = request_dir / (op + '.json')
    if not receipt.exists() and not request.exists() and not (root / 'journal' / (op + '.json')).exists():
        atomic_write(request, signed({'operation_id': op, 'name': name, 'arguments': args,
            'request_digest': request_digest, 'target': target, 'expires_at': time.time() + timeout}, config['token']))
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if receipt.exists():
            result = verified(json.loads(receipt.read_text(encoding='utf-8')), config['token'])
            if result.get('operation_id') != op:
                raise ValueError('Connector operation identity changed')
            if result.get('request_digest') != request_digest:
                raise ValueError('Operation ID was reused with different arguments')
            if target and result.get('instance_id') != target['instance_id']:
                raise ValueError('Connector replied from a different SketchUp instance')
            if result.get('error'):
                raise RuntimeError(result['error'])
            return result['result']
        time.sleep(0.05)
    raise TimeoutError(f'Native outcome unknown; do not replay. Operation {op}. Open SketchUp and reconcile its journal.')


def stdio_main():
    def _frame(value):
        body = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        return f'Content-Length: {len(body)}\r\n\r\n'.encode('ascii') + body
    while True:
        line = sys.stdin.buffer.readline(8192)
        if not line:
            break
        if not line.strip():
            continue
        framed = line.lower().startswith(b'content-length:')
        if framed:
            size = int(line.split(b':', 1)[1])
            if not 0 < size <= 8 * 1024 * 1024:
                return
            while sys.stdin.buffer.readline(8192).strip():
                pass
            body = sys.stdin.buffer.read(size)
        else:
            body = line
        message = json.loads(body)
        if 'id' not in message:
            continue
        response = {'jsonrpc': '2.0', 'id': message['id']}
        try:
            method = message.get('method')
            if method == 'initialize':
                result = {'protocolVersion': '2024-11-05', 'capabilities': {'tools': {}},
                          'serverInfo': {'name': 'kstudio-public-sketchup', 'version': VERSION}}
            elif method == 'tools/list':
                result = {'tools': [{'name': name, 'description': 'Paired local SketchUp ' + name,
                    'inputSchema': {'type': 'object', 'properties': TOOL_PROPERTIES.get(name, {}),
                    'required': {'sketchup_eval_project_file': ['script_path'],
                        'sketchup_set_camera': ['eye_m', 'target_m', *DOCUMENT_BINDING],
                        'sketchup_export_view_image': ['output_path', *DOCUMENT_BINDING]}.get(name, [])}}
                    for name in TOOL_NAMES]}
            elif method == 'tools/call':
                value = call(message['params']['name'], message['params'].get('arguments'))
                result = {'content': [{'type': 'text', 'text': json.dumps(value, ensure_ascii=False)}]}
            else:
                raise ValueError('Unsupported MCP method')
            response['result'] = result
        except Exception as error:
            response['error'] = {'code': -32000, 'message': str(error)}
        sys.stdout.buffer.write(_frame(response) if framed else json.dumps(response).encode() + b'\n')
        sys.stdout.buffer.flush()


if __name__ == '__main__':
    stdio_main()
