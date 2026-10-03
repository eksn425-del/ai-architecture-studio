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
    tokenizer_cache = Path(getattr(sys, "_MEIPASS", root)) / "tokenizer-cache"
    if tokenizer_cache.is_dir():
        os.environ["TIKTOKEN_CACHE_DIR"] = str(tokenizer_cache)
    sys.path.insert(0, str(root))
    parser = argparse.ArgumentParser()
    parser.add_argument("--attach", type=int, help="Reuse an already running local workbench port for UI validation")
    parser.add_argument("--data-dir", type=Path, help="Use a separate local application profile")
    parser.add_argument("--standalone", action="store_true", help="Use an API and an explicit bridge.json; no Codex config fallback")
    parser.add_argument("--diagnose-provider", type=Path, help="Write a credential-free packaged provider import check and exit")
    parser.add_argument("--api-provider", choices=("glm", "glm-international", "deepseek"), default="glm")
    args = parser.parse_args()
    if args.diagnose_provider:
        import json
        import traceback
        try:
            from litellm import completion
            result = {"ok": callable(completion)}
        except Exception:
            result = {"ok": False, "traceback": traceback.format_exc()}
        args.diagnose_provider.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return
    import webview
    webview.settings["ALLOW_DOWNLOADS"] = True
    server = None
    if args.attach:
        port = args.attach
    else:
        import uvicorn
        from app.main import create_app
        data = args.data_dir.resolve() if args.data_dir else Path(os.environ.get("LOCALAPPDATA", Path.home())) / "KStudio"
        data.mkdir(parents=True, exist_ok=True)
        runtime = data / "runtime"
        bridge = data / "bridge.json"
        if args.standalone:
            os.environ["ARCH_STUDIO_STANDALONE"] = "1"
            os.environ["ARCH_STUDIO_ECONOMY_PROVIDER"] = "litellm"
            if args.api_provider == "deepseek":
                os.environ["ARCH_STUDIO_API_MODEL"] = "deepseek/deepseek-flash"
                os.environ["ARCH_STUDIO_API_KEY_ENV"] = "DEEPSEEK_API_KEY"
                os.environ["ARCH_STUDIO_API_BASE"] = "https://api.deepseek.com"
            else:
                os.environ["ARCH_STUDIO_API_MODEL"] = "zai/glm-5.3-flash"
                os.environ["ARCH_STUDIO_API_KEY_ENV"] = "ZAI_API_KEY"
                os.environ["ARCH_STUDIO_API_BASE"] = ("https://api.z.ai/api/paas/v4" if args.api_provider == "glm-international"
                                                    else "https://open.bigmodel.cn/api/paas/v4")
            os.environ["ARCH_STUDIO_ECONOMY_REASONING_EFFORT"] = "low" if args.api_provider == "deepseek" else "high"
            # Even missing config must fail explicitly rather than borrow Codex's installation.
            os.environ["ARCH_STUDIO_MCP_CONFIG"] = str(bridge)
        elif bridge.is_file():
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
