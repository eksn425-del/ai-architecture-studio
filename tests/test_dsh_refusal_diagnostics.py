import json
import os
from pathlib import Path
import socket
import sqlite3
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from app.dsh_configuration import resolve_configuration
from app.dsh_runtime import DSHHostSession, host_refusal
from app.native_agent import NativeAgentUnavailable
from tests.test_official_dsh_local import enable_budget


def test_host_refusal_does_not_echo_unknown_exception_or_request_path():
    secret = 'private-canary-not-a-real-key'
    for error in (ValueError(secret), KeyError(secret), TypeError(secret)):
        result = host_refusal(error, '/'+secret)
        assert result['code'] == 'INVALID_HOST_REQUEST'
        assert result['retryable'] is False
        assert secret not in json.dumps(result)


def test_real_loopback_returns_safe_refusal_code_and_records_it(tmp_path, monkeypatch):
    monkeypatch.delenv('KSTUDIO_TEST_BATCH_CONFIG', raising=False)
    monkeypatch.setitem(sys.modules, 'deepseek_harness', SimpleNamespace(
        DeepSeekHarness=lambda **kwargs: SimpleNamespace(close=lambda: None)))
    cfg = resolve_configuration({'api_base': 'https://example.invalid/v1', 'model': 'fixture'})
    log = tmp_path/'trace.jsonl'
    host = DSHHostSession(home=tmp_path/'home', workspace=tmp_path, api_base=cfg.endpoint,
        api_key='private-canary-not-a-real-key', model=cfg.model, specs=[], dispatch=lambda *_: None,
        trace_path=log, sdk_site=tmp_path, dsh_bin='unused', effective_configuration=cfg,
        reasoning_effort=cfg.requested_effort, protocol=cfg.protocol)
    def refused(_):
        raise ValueError('Test batch has unknown provider liability; no new request dispatched')
    host.test_budget = SimpleNamespace(reserve=refused, close=lambda: None)
    try:
        req = Request(f'http://127.0.0.1:{host.server.server_port}/test-budget/reserve',
            data=b'{"request_secret":"private-canary-not-a-real-key"}',
            headers={'Authorization': 'Bearer '+host.token, 'Content-Type': 'application/json'})
        with pytest.raises(HTTPError) as caught:
            urlopen(req, timeout=3)
        assert caught.value.code == 400
        result = json.load(caught.value)
        assert result['code'] == 'USAGE_RECONCILIATION_REQUIRED'
        assert result['operation'] == 'provider_reservation' and result['retryable'] is False
        assert '用量待核对' in result['error'] and '已有模型' in result['error']
        trace = log.read_text(encoding='utf8')
        assert 'host_request_refused' in trace and result['code'] in trace
        assert host.token not in trace and 'private-canary-not-a-real-key' not in trace
    finally:
        host.close()


@pytest.mark.parametrize('protocol', ['openai-completions', 'openai-responses'])
def test_official_transport_failure_reports_reconciliation_without_provider_retry(tmp_path, monkeypatch, protocol):
    """Actual official SDK + a local socket failure; never calls BAI or SketchUp."""
    sdk = os.environ.get('KSTUDIO_TEST_DSH_SDK_SITE')
    binary = os.environ.get('KSTUDIO_TEST_DSH_BIN')
    if not sdk or not binary:
        pytest.skip('Explicit pinned SDK paths required for offline real transport test')
    requests = []
    class BrokenProvider(BaseHTTPRequestHandler):
        def log_message(self, *_): pass
        def do_POST(self):
            requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()
    server = ThreadingHTTPServer(('127.0.0.1', 0), BrokenProvider)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    cfg = resolve_configuration({'api_base': f'http://127.0.0.1:{server.server_port}/v1',
        'model': 'fixture-model', 'request_retries': 2,
        'mode': 'codex-responses' if protocol == 'openai-responses' else 'compatible',
        'capabilities_json': json.dumps({'tools': True, 'streaming': True, 'context_window': 65536, 'max_output_tokens': 4096})})
    enable_budget(monkeypatch, tmp_path, cfg, 3)
    monkeypatch.setenv('KSTUDIO_DSH_EXECUTION_POLICY', 'production-file-proxy')
    monkeypatch.delenv('KSTUDIO_DSH_MCP_CONFIG', raising=False)
    log = tmp_path/'events.jsonl'
    host = DSHHostSession(home=tmp_path/'home', workspace=tmp_path, api_base=cfg.endpoint,
        api_key='offline-no-provider-key', model=cfg.model, specs=[], dispatch=lambda *_: pytest.fail('No geometry tools'),
        trace_path=log, sdk_site=Path(sdk), dsh_bin=Path(binary), effective_configuration=cfg,
        reasoning_effort=cfg.requested_effort, protocol=cfg.protocol, full_capabilities=True)
    try:
        with pytest.raises(NativeAgentUnavailable) as caught:
            host.run(prompt='Offline connection failure fixture.', images=[])
        text = str(caught.value)
        assert 'USAGE_RECONCILIATION_REQUIRED' in text and '用量待核对' in text
        assert '已有模型' in text and '自动再次发送付费请求' in text
        assert len(requests) == 1
        with sqlite3.connect(tmp_path/'dsh-test-batches.sqlite3') as db:
            rows = db.execute('SELECT status,usage_json FROM attempts').fetchall()
        assert len(rows) == 1 and rows[0][0] == 'unknown'
        events = [json.loads(line) for line in log.read_text(encoding='utf8').splitlines()]
        refusals = [e for e in events if e.get('event') == 'host_request_refused']
        assert refusals[-1]['code'] == 'USAGE_RECONCILIATION_REQUIRED'
        assert refusals[-1]['operation'] == 'provider_reservation'
        assert any(e.get('type') == 'llm/retry' for e in events)
        assert 'offline-no-provider-key' not in log.read_text(encoding='utf8')
        (tmp_path/'offline-refusal-receipt.json').write_text(json.dumps({
            'protocol': protocol, 'provider_http_requests': len(requests), 'ledger_rows': len(rows),
            'ledger_state': rows[0][0], 'error_code': refusals[-1]['code'], 'paid_calls': 0,
            'native_operations': 0}, indent=2), encoding='utf8')
    finally:
        host.close(); server.shutdown(); server.server_close()
