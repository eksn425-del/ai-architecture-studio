"""Install the workbench dependencies and start the local API-powered studio."""
from pathlib import Path
import argparse
import hashlib
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import venv
import webbrowser


def main() -> None:
    if sys.version_info < (3, 11):
        raise SystemExit("Please install Python 3.11 or newer and run Start K Studio again.")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    environment = root / ".venv"
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.is_file():
        print("Creating the local Python environment...", flush=True)
        venv.EnvBuilder(with_pip=True).create(environment)
    requirements = [root / "requirements.txt", root / "requirements-model-providers.txt"]
    fingerprint = hashlib.sha256(b"".join(p.read_bytes() for p in requirements)).hexdigest()
    marker = environment / ".kstudio-requirements"
    if not marker.is_file() or marker.read_text().strip() != fingerprint:
        print("Installing K Studio and the DeepSeek / GLM adapter. First launch may take several minutes.", flush=True)
        subprocess.run([str(python), "-m", "pip", "install", "--quiet", "-r", str(requirements[0]), "-r", str(requirements[1])], check=True)
        marker.write_text(fingerprint)
    port = None
    for candidate in range(args.port, min(args.port + 10, 65536)):
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", candidate))
                port = candidate
                break
            except OSError:
                continue
    if port is None:
        raise SystemExit("No free local port. Close the previous workbench or choose --port.")
    url = f"http://127.0.0.1:{port}/"
    if not args.no_browser:
        def open_when_ready() -> None:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            for _ in range(60):
                try:
                    with opener.open(url + "api/status", timeout=1) as response:
                        if response.status == 200:
                            webbrowser.open(url)
                            return
                except OSError:
                    time.sleep(0.5)
        threading.Thread(target=open_when_ready, daemon=True).start()
    config = os.environ.copy()
    config.setdefault("ARCH_STUDIO_ECONOMY_PROVIDER", "litellm")
    config.setdefault("ARCH_STUDIO_API_MODEL", "deepseek/deepseek-flash")
    config.setdefault("ARCH_STUDIO_ECONOMY_REASONING_EFFORT", "low")
    print(f"K Studio: {url}\nChoose your AI provider and enter its API Key in the browser. Keep this window open.", flush=True)
    try:
        subprocess.run([str(python), str(root / "scripts/dev.py"), "--port", str(port)], cwd=root, env=config, check=True)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
