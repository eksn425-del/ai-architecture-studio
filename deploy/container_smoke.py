"""Real offline HTTP/SQLite smoke for the built cloud image, without live credentials.

CI passes --require-container to verify Linux nonroot/ro-root/tmpfs/network-none
boundaries. A local run without that flag verifies the same service assertions but
explicitly cannot certify container isolation. No test login or provider mock exists.
"""
from __future__ import annotations
import argparse
from contextlib import closing
import importlib.metadata
import json
import os
import platform
import re
import secrets
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import httpx


def isolation(required: bool) -> dict:
    if not required:
        return {'status': 'NOT_CHECKED_LOCAL_SCRIPT_ONLY'}
    assert sys.platform == 'linux', 'Container check requires Linux'
    assert os.getuid() == 10001 and os.getgid() == 10001, 'Expected image nonroot UID/GID 10001'
    status = dict(line.split(':', 1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
    assert status['NoNewPrivs'].strip() == '1', 'no-new-privileges missing'
    assert int(status['CapEff'].strip(), 16) == 0, 'Effective capabilities must be empty'
    mounts = [line.split() for line in Path('/proc/mounts').read_text().splitlines()]
    root = next(row for row in mounts if row[1] == '/')
    tmp = next(row for row in mounts if row[1] == '/tmp')
    assert 'ro' in root[3].split(','), 'Root filesystem must be read-only'
    assert tmp[2] == 'tmpfs' and {'rw', 'nosuid', 'nodev', 'noexec'} <= set(tmp[3].split(',')), 'Restricted tmpfs missing'
    interfaces = [name for _, name in socket.if_nameindex()]
    assert interfaces and set(interfaces) == {'lo'}, 'External network interface present'
    return {'status': 'PASS', 'uid': os.getuid(), 'gid': os.getgid(),
            'root_read_only': True, 'tmpfs': True, 'tmp_noexec_nosuid_nodev': True,
            'no_new_privileges': True, 'effective_capabilities': 0, 'interfaces': interfaces}


def run(root: Path, require_container: bool) -> dict:
    result = {'scope': ('BUILT_IMAGE_REAL_OFFLINE_HTTP_SQLITE_ENGINEERING_SMOKE' if require_container
                        else 'LOCAL_SCRIPT_REAL_HTTP_SQLITE_ENGINEERING_SMOKE'),
              'status': 'RUNNING', 'python': platform.python_version(),
              'os': platform.system(), 'architecture': platform.machine(),
              'isolation': isolation(require_container), 'live_credentials': False,
              'paid_inference': False, 'public_deployment': 'NOT_RUN',
              'real_oidc_payment_provider': 'NOT_RUN', 'postgresql_in_this_check': 'NOT_RUN'}
    direct = []
    for line in (root / 'requirements-cloud.txt').read_text(encoding='utf-8-sig').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        match = re.fullmatch(r'([A-Za-z0-9_.-]+)(?:\[[^]]+\])?==([^\s]+)', line.strip())
        assert match, 'Direct cloud requirements must remain exactly pinned'
        actual = importlib.metadata.version(match[1])
        assert actual == match[2], f'Direct dependency version mismatch: {match[1]}'
        direct.append({'name': match[1], 'version': actual})
    result['direct_dependencies'] = direct
    result['installed_distributions'] = sorted(
        [{'name': d.metadata['Name'], 'version': d.version} for d in importlib.metadata.distributions()],
        key=lambda x: x['name'].lower())
    # Do not inherit API credentials, HTTP proxies, cloud config, or machine secrets.
    environment = {k: v for k, v in os.environ.items() if k.upper() in ('PATH', 'SYSTEMROOT', 'WINDIR', 'LANG', 'LC_ALL', 'TEMP', 'TMP', 'TMPDIR')}
    environment.update(PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
    with tempfile.TemporaryDirectory(prefix='kstudio-cloud-smoke-') as temporary:
        work = Path(temporary)
        db = work / 'cloud.sqlite'
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0))
            port = probe.getsockname()[1]
        base = f'http://127.0.0.1:{port}'
        environment.update(KSTUDIO_CLOUD_DATABASE_URL='sqlite:///' + str(db),
                           KSTUDIO_CLOUD_SESSION_SECRET=secrets.token_urlsafe(48),
                           KSTUDIO_CLOUD_PUBLIC_URL=base, KSTUDIO_CLOUD_ENV='test',
                           KSTUDIO_WEBSITE_DIR=str(root / 'website'),
                           KSTUDIO_PRICES_CONFIRMED='0', KSTUDIO_CLOUD_PRICES='{}',
                           KSTUDIO_CLOUD_MODELS='{}', KSTUDIO_CLOUD_RELEASE='{}')
        commands = []
        for arguments in (['-m', 'pip', 'check'], ['-m', 'cloud.cli', 'migrate'],
                          ['-m', 'cloud.cli', 'migrate'], ['-m', 'cloud.cli', 'audit'],
                          ['-m', 'cloud.cli', 'recover-stale']):
            proc = subprocess.run([sys.executable, *arguments], cwd=root, env=environment,
                                  capture_output=True, text=True, timeout=40)
            assert proc.returncode == 0, f'Command failed: {arguments}: {proc.stderr[-1600:]}'
            if arguments[-1] == 'audit':
                assert json.loads(proc.stdout)['consistent'] is True
            commands.append({'arguments': arguments, 'exit_code': proc.returncode, 'stdout': proc.stdout.strip()})
        result['commands'] = commands
        log = (work / 'server.log').open('w', encoding='utf-8')
        server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'cloud.main:create_app', '--factory',
                                   '--host', '127.0.0.1', '--port', str(port), '--workers', '1', '--no-access-log'],
                                  cwd=root, env=environment, stdout=log, stderr=log)
        try:
            with httpx.Client(base_url=base, trust_env=False, timeout=5, follow_redirects=False) as client:
                deadline = time.monotonic() + 20
                ready = False
                while time.monotonic() < deadline:
                    assert server.poll() is None, 'Real cloud HTTP process exited during startup'
                    try:
                        ready = client.get('/health/ready').status_code == 200
                        if ready:
                            break
                    except httpx.TransportError:
                        pass
                    time.sleep(.1)
                assert ready, 'Real cloud HTTP readiness timed out'
                paths = ['/health/live', '/health/ready', '/api/status', '/', '/download',
                         '/docs/start', '/docs/connect', '/account/device', '/assets/site.js', '/assets/site.css']
                for path in paths:
                    response = client.get(path)
                    assert response.status_code == 200, f'HTTP failed: {path}: {response.status_code}'
                    assert response.headers.get('x-content-type-options') == 'nosniff'
                assert client.get('/assets/site.js').content == (root/'website/assets/site.js').read_bytes()
                config = client.get('/api/public/config').json()
                assert config['auth']['available'] is False
                assert config['payment']['available'] is False
                assert config['release']['download_available'] is False
                assert config['pricing']['confirmed'] is False
                assert config['models'] == []
                assert client.get('/api/auth/me').json() == {'authenticated': False}
                assert client.get('/api/auth/login').status_code == 503
                assert client.get('/api/account/usage').status_code == 401
                assert client.post('/api/account/orders', json={'package_id': 'unconfigured'}).status_code == 401
                assert client.post('/api/payments/stripe/webhook', content=b'{}').status_code == 400
                feedback = 'Offline container engineering check: no customer data or external identity.'
                submitted = client.post('/api/feedback', json={'message': feedback})
                assert submitted.status_code == 200 and submitted.json()['received'] is True
                with closing(sqlite3.connect(db)) as connection:
                    assert connection.execute('SELECT version FROM schema_version').fetchone()[0] == 2
                    assert connection.execute('SELECT message FROM feedback').fetchall() == [(feedback,)]
                    counts = {table: connection.execute('SELECT count(*) FROM ' + table).fetchone()[0]
                              for table in ('users', 'sessions', 'wallets', 'tasks', 'orders', 'ledger_events', 'payment_events')}
                    assert all(count == 0 for count in counts.values())
                result.update(status='PASS', http_routes=paths, static_asset_exact_match=True,
                              disabled_services=['authentication', 'payment', 'public_download', 'platform_models'],
                              feedback_rows_persisted=1, account_billing_table_counts=counts,
                              no_fake_identity=True, server_transport='real uvicorn HTTP on loopback')
        finally:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)
            log.close()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-container', action='store_true')
    parser.add_argument('--source-root', type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        result = run(args.source_root.resolve(), args.require_container)
    except Exception as exc:
        print('KSTUDIO_CONTAINER_RESULT=' + json.dumps({'status': 'FAIL', 'exception': type(exc).__name__,
            'reason': str(exc)[:2000], 'public_deployment': 'NOT_RUN'}, ensure_ascii=False), flush=True)
        raise
    print('KSTUDIO_CONTAINER_RESULT=' + json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
