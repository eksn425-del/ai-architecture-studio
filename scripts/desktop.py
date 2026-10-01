"""Thin BSD pywebview shell around the existing localhost workbench."""
from __future__ import annotations

import argparse
import os
import socket
import sys
import threading
import time
from pathlib import Path


def main() -> None:
    os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    parser = argparse.ArgumentParser()
    parser.add_argument("--attach", type=int, help="Reuse an already running local workbench port for UI validation")
    args = parser.parse_args()
    import webview
    webview.settings["ALLOW_DOWNLOADS"] = True
    server = None
    if args.attach:
        port = args.attach
    else:
        import uvicorn
        from app.main import create_app
        data = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "KStudio"
        data.mkdir(parents=True, exist_ok=True)
        runtime = data / "runtime"
        bridge = data / "bridge.json"
        if bridge.is_file():
            os.environ["ARCH_STUDIO_MCP_CONFIG"] = str(bridge)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(create_app(runtime), host="127.0.0.1", port=port, log_level="warning"))
        threading.Thread(target=server.run, daemon=True).start()
        deadline = time.monotonic() + 20
        while not server.started:
            if time.monotonic() > deadline:
                raise RuntimeError("K Studio local service could not start.")
            time.sleep(0.1)
    webview.create_window("K Studio · AI 建模", f"http://127.0.0.1:{port}/", width=1280, height=850, min_size=(760, 600))
    try:
        webview.start(gui="edgechromium")
    finally:
        if server:
            server.should_exit = True


if __name__ == "__main__":
    main()
