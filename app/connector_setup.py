"""Local-only connector onboarding. Never copies credentials or installs into SketchUp."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import uuid
import sys
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_FILE = "KStudio-SketchUp-Connector.rbz"
PAYLOADS = {PLUGIN_FILE, "node.exe", "kongxing_sketchup_mcp.mjs", "LICENSE.Node.txt", "README.txt"}
CANDIDATE_YEARS = tuple(range(2019, 2028))


def platform_supported() -> bool:
    return os.name == "nt"


def managed_root() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        raise ValueError("当前环境没有 Windows 用户安装目录。")
    return Path(base) / "KStudio" / "connectors" / "kongxing"


def managed_config_path() -> Path:
    return managed_root() / "bridge.json"


def target_config() -> Path:
    explicit = os.environ.get("ARCH_STUDIO_MCP_CONFIG")
    return Path(explicit).resolve() if explicit else managed_config_path()


def _package(verify: bool = False) -> tuple[Path, dict]:
    configured = os.environ.get("ARCH_STUDIO_CONNECTOR_PACKAGE")
    packaged = ROOT / "connector-distribution"
    root = Path(configured) if configured else (packaged if packaged.is_dir() else ROOT / "runtime/connector-distribution")
    if root.is_symlink():
        raise ValueError("连接器安装包目录无效。")
    root = root.resolve()
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema") not in {1, 2} or not re.fullmatch(r"[A-Za-z0-9.-]{1,64}", manifest.get("version", "")):
        raise ValueError("连接器安装包清单无效。")
    entries = manifest.get("files", {})
    expected = {PLUGIN_FILE} if manifest.get('schema') == 2 and manifest.get('kind') == 'kstudio-public' else PAYLOADS
    if set(entries) != expected:
        raise ValueError("连接器安装包缺少必要文件，或包含未声明文件。")
    for name, entry in entries.items():
        path = root / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size != entry.get("bytes"):
            raise ValueError("连接器安装包文件缺失或大小不符。")
        if verify and hashlib.sha256(path.read_bytes()).hexdigest() != entry.get("sha256"):
            raise ValueError("连接器安装包校验失败；未进行安装。")
    return root, manifest


def detect_installations() -> list[dict]:
    if os.name != "nt":
        return []
    import winreg
    found = {}
    for hive, subkey in (
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    ):
        try:
            with winreg.OpenKey(hive, subkey) as root:
                for i in range(winreg.QueryInfoKey(root)[0]):
                    try:
                        with winreg.OpenKey(root, winreg.EnumKey(root, i)) as item:
                            name = str(winreg.QueryValueEx(item, "DisplayName")[0])
                            match = re.fullmatch(r"SketchUp(?: Pro)? (20\d{2})", name)
                            if not match:
                                continue
                            location = Path(winreg.QueryValueEx(item, "InstallLocation")[0])
                            if not (location / "SketchUp.exe").is_file():
                                continue
                            year = int(match[1])
                            plugin = Path(os.environ.get("APPDATA", "")) / f"SketchUp/SketchUp {year}/SketchUp/Plugins/kongxing_ai_sketchup/main.rb"
                            public_plugin = plugin.parent.parent / 'kstudio_connector.rb'
                            public_present = public_plugin.is_file() and (plugin.parent.parent / 'kstudio_connector/main.rb').is_file()
                            present = plugin.is_file() or public_present
                            managed = plugin.is_file() and "0.1.0-kstudio-local1" in plugin.read_text(encoding="utf-8", errors="replace")
                            found[(year, str(location.resolve()).casefold())] = {"year": year, "name": name, "executable": str(location / 'SketchUp.exe'), "plugin_present": present,
                                           "plugin_kind": "kstudio-public" if public_present else "managed_trial" if managed else "existing" if present else "missing", "compatibility": "not_verified"}
                    except OSError:
                        continue
        except OSError:
            continue
    return sorted(found.values(), key=lambda entry: entry["year"], reverse=True)


def _configured() -> bool:
    from .sketchup_mcp import _resolve_server, ConnectorUnavailable
    try:
        _resolve_server()
        return True
    except ConnectorUnavailable:
        return False


def setup_status() -> dict:
    package_available, version, publication = False, None, "unavailable"
    package_schema, connector_kind, verified_years = None, 'unavailable', []
    try:
        _, manifest = _package()
        package_available = True
        version = manifest["version"]
        publication = manifest.get("publication", "unverified")
        package_schema = manifest.get('schema')
        connector_kind = manifest.get('kind', 'legacy_local')
        verified_years = manifest.get('native_verified_years', [])
    except (OSError, ValueError, TypeError):
        pass
    configured = _configured()
    managed = False
    try:
        settings = json.loads(target_config().read_text(encoding="utf-8"))
        managed = Path(settings.get("command", "")).resolve().is_relative_to((managed_root() / "versions").resolve())
    except (OSError, ValueError, TypeError):
        pass
    return {"platform_supported": platform_supported(), "package_available": package_available,
            "package_version": version, "publication": publication,
            "package_schema": package_schema, "connector_kind": connector_kind,
            "configured": configured, "configuration_kind": "managed" if configured and managed else "existing" if configured else "missing",
            "installations": detect_installations(),
            "compatibility_policy": {"candidate_years": list(CANDIDATE_YEARS), "native_trial_years": verified_years, "all_versions_verified": False},
            "native_reachability": "not_checked", "clean_machine_acceptance": "not_run"}


def verify_runtime(node: Path, server: Path) -> None:
    # Stdio discovery only: no tools/call and no connection to SketchUp.
    from .sketchup_mcp import _frame, _read_frames
    request = _frame({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    request += _frame({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    result = subprocess.run([str(node), str(server)], input=request, capture_output=True, timeout=15,
                            cwd=server.parent, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    replies = {message.get("id"): message for message in _read_frames(result.stdout)}
    tools = replies.get(2, {}).get("result", {}).get("tools", [])
    if result.returncode or not replies.get(1, {}).get("result", {}).get("serverInfo") or "sketchup_health" not in {tool.get("name") for tool in tools}:
        raise ValueError("本机连接程序自检未通过；未启用配置。")


def install_runtime(year: int, *, manual_version: bool = False) -> dict:
    if not platform_supported():
        raise ValueError("此连接器安装流程目前只适用于 Windows。")
    if type(year) is not int or (not manual_version and year not in {entry["year"] for entry in detect_installations()}):
        raise ValueError("请先选择检测到的 SketchUp 版本；未安装或未识别的版本不会被替代。")
    if year not in CANDIDATE_YEARS:
        raise ValueError("此版本尚不满足当前插件要求；请查看兼容性说明，未进行安装。")
    if _configured():
        return {"status": "existing_configuration_preserved", "configured": True,
                "native_reachability": "not_checked", "plugin_installed_by_setup": False}
    source, manifest = _package(verify=True)
    if manifest.get('schema') == 2 and manifest.get('kind') == 'kstudio-public':
        return install_public_runtime(source, manifest, year)
    root = managed_root()
    if root.is_symlink() or (root / "versions").is_symlink():
        raise ValueError("用户连接器目录不能指向其他安装位置。")
    root.mkdir(parents=True, exist_ok=True)
    config = target_config()
    if config.exists() or config.is_symlink():
        raise ValueError("已有连接配置尚未通过检查；安装器不会覆盖它。请保留配置并检查原因。")
    version = root / "versions" / manifest["version"]
    if not version.exists():
        stage = root / "versions" / ("staging-" + uuid.uuid4().hex)
        stage.mkdir(parents=True)
        for name in PAYLOADS:
            shutil.copyfile(source / name, stage / name)
        for name, entry in manifest["files"].items():
            if hashlib.sha256((stage / name).read_bytes()).hexdigest() != entry["sha256"]:
                raise ValueError("复制后的安装文件校验失败；未运行程序或启用配置。")
        verify_runtime(stage / "node.exe", stage / "kongxing_sketchup_mcp.mjs")
        stage.rename(version)
    else:
        if version.is_symlink():
            raise ValueError("连接器版本目录无效。")
        for name, entry in manifest["files"].items():
            payload = version / name
            if payload.is_symlink() or not payload.is_file() or hashlib.sha256(payload.read_bytes()).hexdigest() != entry["sha256"]:
                raise ValueError("已有连接器版本与安装包不一致；未覆盖文件。")
        verify_runtime(version / "node.exe", version / "kongxing_sketchup_mcp.mjs")
    generated = root / "generated_scripts"
    generated.mkdir(exist_ok=True)
    settings = {"command": str(version / "node.exe"), "args": [str(version / "kongxing_sketchup_mcp.mjs")],
                "cwd": str(root), "env": {"KONGXING_CONNECTION_FILE": str(root / "connection.json"),
                "ARCHFLOW_GENERATED_SCRIPT_DIR": str(generated)}}
    config.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation: do not replace a concurrent install or any existing configuration.
    with config.open("x", encoding="utf-8") as handle:
        json.dump(settings, handle, ensure_ascii=False, indent=2)
    return {"status": "runtime_installed", "configured": True, "selected_year": year,
            "package_version": manifest["version"], "native_reachability": "not_checked",
            "plugin_installed_by_setup": False, "geometry_modified": False}


def install_public_runtime(source, manifest, year):
    from .public_connector import initialize_pairing, authorize_workspace
    config = target_config()
    if config.exists() or config.is_symlink():
        raise ValueError('已有连接配置保留；请先在设置中核对，安装器不会覆盖。')
    root = initialize_pairing()
    workspace = os.environ.get('ARCH_STUDIO_RUNTIME_DIR')
    if not workspace:
        raise ValueError('当前项目运行目录未准备好，请重新打开 K Studio 后配对。')
    authorize_workspace(root, workspace)
    executable = Path(sys.executable).parent / 'KStudioConnector.exe'
    if getattr(sys, 'frozen', False):
        if not executable.is_file():
            raise ValueError('安装包缺少公开连接器程序，请修复安装。')
        command, args = str(executable), []
    else:
        command, args = sys.executable, ['-m', 'app.public_connector']
    settings = {'command': command, 'args': args, 'cwd': str(ROOT),
        'env': {'KSTUDIO_PUBLIC_CONNECTOR_ROOT': str(root),
                'ARCHFLOW_GENERATED_SCRIPT_DIR': str(root / 'generated_scripts')}}
    config.parent.mkdir(parents=True, exist_ok=True)
    with config.open('x', encoding='utf-8') as handle:
        json.dump(settings, handle, ensure_ascii=False, indent=2)
    # The running desktop initially has a private profile path. Switch only its
    # generated-file transport directory to the explicit newly paired location.
    os.environ['ARCHFLOW_GENERATED_SCRIPT_DIR'] = str(root / 'generated_scripts')
    os.environ['ARCH_STUDIO_GENERATED_SCRIPT_DIR'] = str(root / 'generated_scripts')
    return {'status': 'runtime_installed', 'configured': True, 'selected_year': year,
            'package_version': manifest['version'], 'native_reachability': 'not_checked',
            'plugin_installed_by_setup': False, 'geometry_modified': False,
            'connector_kind': 'kstudio-public', 'restart_sketchup_required': True}


def register_routes(app, lock) -> None:
    @app.get("/api/connectors/sketchup/setup")
    def status():
        return setup_status()

    @app.get("/api/connectors/sketchup/plugin")
    def plugin():
        try:
            root, _ = _package(verify=True)
        except (OSError, ValueError, TypeError) as error:
            raise HTTPException(503, "连接器安装包未准备好或校验失败；没有提供虚假的下载链接。") from error
        return FileResponse(root / PLUGIN_FILE, media_type="application/octet-stream", filename=PLUGIN_FILE)

    @app.post("/api/connectors/sketchup/install")
    def install(request: dict):
        if request.get("confirm_install") is not True:
            raise HTTPException(400, "请确认安装本机连接程序。")
        if not lock.acquire(blocking=False):
            raise HTTPException(409, "建模正在执行，请结束后再安装连接器。")
        try:
            return install_runtime(request.get("year"), manual_version=request.get("manual_version") is True)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            raise HTTPException(400, "连接器未启用：" + str(error)) from error
        finally:
            lock.release()
