import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from app.runtime_safety import LocalRuntimeLease, release_readiness


def test_second_process_cannot_open_same_store_and_exit_releases(tmp_path):
    code = ('from pathlib import Path; from app.runtime_safety import LocalRuntimeLease; '
            'import sys; lease=LocalRuntimeLease(Path(sys.argv[1])); lease.acquire(); lease.release()')
    env = {**os.environ, 'WEB_CONCURRENCY': '1', 'K_STUDIO_DEPLOYMENT_MODE': 'local'}
    with LocalRuntimeLease(tmp_path):
        denied = subprocess.run([sys.executable, '-c', code, str(tmp_path)], capture_output=True, env=env)
        assert denied.returncode != 0
        assert b'Another K Studio service' in denied.stderr
    allowed = subprocess.run([sys.executable, '-c', code, str(tmp_path)], capture_output=True, env=env)
    assert allowed.returncode == 0, allowed.stderr


def test_independent_stores_can_run_and_release_is_idempotent(tmp_path):
    with LocalRuntimeLease(tmp_path/'a'), LocalRuntimeLease(tmp_path/'b'):
        pass
    lease = LocalRuntimeLease(tmp_path/'a')
    lease.acquire(); lease.release(); lease.release()
    with lease:
        with pytest.raises(RuntimeError, match='already held'):
            lease.acquire()


def test_os_releases_lease_after_owned_helper_crash(tmp_path):
    ready = tmp_path/'helper-ready'
    code = ('from pathlib import Path; import sys,time; from app.runtime_safety import LocalRuntimeLease; '
            'lease=LocalRuntimeLease(Path(sys.argv[1])).acquire(); Path(sys.argv[2]).touch(); time.sleep(20)')
    env = {**os.environ, 'WEB_CONCURRENCY':'1', 'K_STUDIO_DEPLOYMENT_MODE':'local'}
    child = subprocess.Popen([sys.executable, '-c', code, str(tmp_path/'store'), str(ready)],
                             env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        deadline = time.monotonic()+5
        while not ready.exists() and child.poll() is None and time.monotonic()<deadline:
            time.sleep(.02)
        assert ready.exists()
        with pytest.raises(RuntimeError, match='Another K Studio service'):
            LocalRuntimeLease(tmp_path/'store').acquire()
        child.terminate(); child.wait(timeout=5)
        with LocalRuntimeLease(tmp_path/'store'):
            pass
    finally:
        if child.poll() is None:
            child.kill(); child.wait(timeout=5)
        child.stderr.close()


@pytest.mark.parametrize('workers', ['2', '8', '0', 'invalid'])
def test_multiworker_json_store_rejected_before_opening_project(tmp_path, monkeypatch, workers):
    monkeypatch.setenv('WEB_CONCURRENCY', workers)
    with pytest.raises(RuntimeError, match='worker|CONCURRENCY'):
        LocalRuntimeLease(tmp_path/'new').acquire()
    assert not (tmp_path/'new').exists()


def test_cloud_flag_cannot_enable_unimplemented_auth(tmp_path, monkeypatch):
    monkeypatch.setenv('K_STUDIO_DEPLOYMENT_MODE', 'cloud')
    with pytest.raises(RuntimeError, match='authenticated control plane'):
        LocalRuntimeLease(tmp_path).acquire()
    assert release_readiness()['paid_multi_user_release_ready'] is False


def test_lifespan_owns_lease_and_readiness_has_no_secrets(tmp_path, fake_components, monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import create_app
    monkeypatch.setenv('K_STUDIO_OPERATOR_API_KEY', 'do-not-serialize-this')
    brain, adapter = fake_components
    app = create_app(tmp_path, brain=brain, sketchup=adapter)
    with TestClient(app) as client:
        data = client.get('/api/release-readiness').json()
        assert data['paid_multi_user_release_ready'] is False
        assert 'do-not-serialize-this' not in str(data)
        with pytest.raises(RuntimeError, match='Another K Studio service'):
            LocalRuntimeLease(tmp_path).acquire()
    with LocalRuntimeLease(tmp_path):
        pass
