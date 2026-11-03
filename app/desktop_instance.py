"""One desktop per profile; authenticated loopback activation, no process killing."""
import hmac
import json
import secrets
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from .runtime_safety import LocalRuntimeLease


class DesktopInstance:
    def __init__(self, data):
        self.root = Path(data) / 'desktop-instance'
        self.lease = LocalRuntimeLease(self.root)
        self.receipt = self.root / 'activation.json'
        self.server = None
        self.window = None
        self.token = secrets.token_urlsafe(32)

    def acquire_or_activate(self):
        try:
            self.lease.acquire()
            return True
        except RuntimeError:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                try:
                    row = json.loads(self.receipt.read_text(encoding='utf-8'))
                    port = row['port']
                    if type(port) is not int or not 1024 <= port <= 65535:
                        raise ValueError('Invalid activation endpoint')
                    request = urllib.request.Request(f'http://127.0.0.1:{port}/activate', data=b'',
                        headers={'Authorization': 'Bearer ' + row['token']}, method='POST')
                    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request, timeout=1) as response:
                        if response.status == 204:
                            return False
                except (OSError, ValueError, KeyError):
                    time.sleep(.2)
            raise RuntimeError('K Studio 正在启动或退出，请稍后再打开；未启动第二个项目写入服务。')

    def publish(self, window):
        if self.server is not None:
            return
        self.window = window
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass
            def do_POST(self):
                if self.path != '/activate' or not hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + owner.token):
                    self.send_error(403)
                    return
                try:
                    owner.window.show()
                    owner.window.restore()
                except Exception:
                    self.send_error(503)
                    return
                self.send_response(204)
                self.end_headers()
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        temporary = self.receipt.with_suffix('.tmp')
        temporary.write_text(json.dumps({'port': self.server.server_port, 'token': self.token}), encoding='utf-8')
        temporary.replace(self.receipt)

    def close(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        if self.lease.handle is not None:
            self.receipt.unlink(missing_ok=True)
        self.lease.release()
