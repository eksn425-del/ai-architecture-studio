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
    parser.add_argument("--runtime-dir", type=Path, help="Explicitly retain an existing local project store")
    parser.add_argument("--connections-dir", type=Path, help="Explicitly retain an existing encrypted connection store")
    parser.add_argument("--bridge-config", type=Path, help="Explicitly retain the owner's local connector")
    parser.add_argument("--generated-dir", type=Path, help="Use the existing connector's approved script directory")
    parser.add_argument("--standalone", action="store_true", help="Use an API and an explicit bridge.json; no Codex config fallback")
    parser.add_argument("--diagnose-provider", type=Path, help="Write a credential-free packaged provider import check and exit")
    parser.add_argument("--diagnose-bundle", type=Path, help="Check bundled Harness without inference and exit")
    parser.add_argument("--diagnose-harness", action="store_true", help="With --diagnose-bundle, initialize the official tool catalog without inference")
    parser.add_argument("--api-provider", choices=("glm", "glm-international", "deepseek"), default="deepseek")
    args = parser.parse_args()
    if args.diagnose_bundle:
        import json
        import subprocess
        import traceback
        try:
            from app.desktop_bootstrap import configure
            import deepseek_harness
            profile = args.data_dir or args.diagnose_bundle.parent / 'diagnostic-profile'
            configured = configure(Path(getattr(sys, '_MEIPASS', root)), profile)
            probe = subprocess.run([str(configured['node']), '--version'], capture_output=True, text=True, timeout=20,
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            result = {'ok': probe.returncode == 0, 'node_version': probe.stdout.strip(),
                      'sdk_import': True, 'engine': os.environ['KSTUDIO_AGENT_ENGINE'],
                      'capabilities': os.environ['KSTUDIO_DSH_CAPABILITIES'], 'inference_called': False}
            if args.diagnose_harness:
                from app.dsh_runtime import DSHHostSession
                workspace = profile / 'diagnostic-workspace'
                workspace.mkdir(parents=True, exist_ok=True)
                session = DSHHostSession(home=profile / 'diagnostic-harness', workspace=workspace,
                    api_base='https://example.invalid/v1', api_key='offline-fixture-no-provider-access', model='fixture-model',
                    specs=[], dispatch=lambda *args: None, trace_path=profile / 'diagnostic-events.jsonl',
                    sdk_site=Path(os.environ['KSTUDIO_DSH_SDK_SITE']), dsh_bin=configured['launcher'], full_capabilities=True)
                try:
                    session.start()
                    result['native_tools'] = session.inventory
                finally:
                    session.close()
        except Exception:
            result = {'ok': False, 'traceback': traceback.format_exc(), 'inference_called': False}
        args.diagnose_bundle.parent.mkdir(parents=True, exist_ok=True)
        args.diagnose_bundle.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        return
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
    application = None
    server_thread = None
    closing_lock = None
    instance = None
    if args.attach:
        port = args.attach
    else:
        import uvicorn
        data = args.data_dir.resolve() if args.data_dir else Path(os.environ.get("LOCALAPPDATA", Path.home())) / "KStudio"
        data.mkdir(parents=True, exist_ok=True)
        from app.desktop_instance import DesktopInstance
        instance = DesktopInstance(data)
        if not instance.acquire_or_activate():
            return
        import atexit
        atexit.register(instance.close)
        runtime = args.runtime_dir.resolve() if args.runtime_dir else data / "runtime"
        bridge = data / "bridge.json"
        if getattr(sys, 'frozen', False):
            from app.desktop_bootstrap import configure
            configure(Path(sys._MEIPASS), data)
        elif args.standalone:
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
        os.environ['ARCH_STUDIO_RUNTIME_DIR'] = str(runtime)
        if args.connections_dir:
            os.environ['KSTUDIO_CONNECTIONS_DIR'] = str(args.connections_dir.resolve())
        if args.bridge_config:
            if not args.bridge_config.is_file():
                raise RuntimeError('所选本机连接配置不存在；没有改动原设置。')
            os.environ['ARCH_STUDIO_MCP_CONFIG'] = str(args.bridge_config.resolve())
        if args.generated_dir:
            os.environ['ARCHFLOW_GENERATED_SCRIPT_DIR'] = str(args.generated_dir.resolve())
            os.environ['ARCH_STUDIO_GENERATED_SCRIPT_DIR'] = str(args.generated_dir.resolve())
        from app.main import create_app
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        application = create_app(runtime)
        server = uvicorn.Server(uvicorn.Config(application, host="127.0.0.1", port=port, log_level="warning"))
        server_thread = threading.Thread(target=server.run, daemon=True)
        server_thread.start()
        deadline = time.monotonic() + 20
        while not server.started:
            if time.monotonic() > deadline:
                raise RuntimeError("K Studio local service could not start.")
            time.sleep(0.1)
    window = webview.create_window("K Studio · AI 建模", f"http://127.0.0.1:{port}/", width=1100, height=720, min_size=(760, 600), maximized=True, text_select=True)
    def on_closing():
        nonlocal closing_lock
        if application is None:
            return True
        if not application.state.agent_lock.acquire(blocking=False):
            from app.desktop_lifecycle import notify_busy_close
            notify_busy_close(window)
            return False
        # Exclude newly submitted writes until the loopback server has exited.
        closing_lock = application.state.agent_lock
        server.should_exit = True
        return True
    window.events.closing += on_closing
    if instance:
        window.events.loaded += lambda: instance.publish(window)
    try:
        if args.data_dir:
            browser_storage = args.data_dir.resolve() / "webview"
            browser_storage.mkdir(parents=True, exist_ok=True)
            webview.start(gui="edgechromium", private_mode=False, storage_path=str(browser_storage))
        else:
            webview.start(gui="edgechromium")
    finally:
        if server:
            server.should_exit = True
            if server_thread:
                server_thread.join(timeout=30)
        if closing_lock:
            closing_lock.release()
        if instance:
            instance.close()
            atexit.unregister(instance.close)


if __name__ == "__main__":
    main()
