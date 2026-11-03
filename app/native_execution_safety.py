"""Capability checks for the official runtime; never an OS-sandbox certificate.

host_tools uses the upstream no-environment protocol. It exposes only the
existing bounded host tool surface. It does not enable arbitrary shell/bpy.
The supported binary is pinned because this is an experimental protocol.
"""
import hashlib
from functools import lru_cache
from pathlib import Path
import shutil
import sys
import tomllib

HOST_TOOLS_REVISION = "codex-no-environment-v1"
SUPPORTED_CODEX_SHA256 = {
    "dd4adf302b112fdc30fce509a5e261a0a6f1118dc58ac2da636eb84e0a6b3e3e": "0.130.0-alpha.5",
}
HOST_TOOL_NAMES = frozenset({
    "blender_inspect_scene", "blender_render_scene", "blender_apply_objects",
    "blender_prepare_component", "blender_audit_connections", "blender_audit_clearance",
    "blender_plan_relation_repair", "blender_check_relation_repair",
    "blender_audit_spatial_clearance", "search_web", "fetch_url",
    "sketchup_model_state", "sketchup_apply_parts", "sketchup_inspect_part", "sketchup_view",
    "sketchup_save_plan",
})
HOST_TOOLS_DISABLED_FEATURES = (
    "shell_tool", "unified_exec", "shell_zsh_fork", "shell_snapshot",
    "apply_patch_freeform", "js_repl", "code_mode", "code_mode_only",
    "js_repl_tools_only", "multi_agent", "multi_agent_v2", "enable_fanout",
    "apps", "enable_mcp_apps", "builtin_mcp", "plugins", "remote_plugin",
    "hooks", "plugin_hooks", "tool_suggest", "request_permissions_tool",
    "in_app_browser", "browser_use", "browser_use_external", "computer_use",
    "image_generation", "skill_mcp_dependency_install", "external_migration",
    "remote_models", "memories", "chronicle", "goals",
)


@lru_cache(maxsize=8)
def _binary_digest(path, size, mtime_ns):
    # Stat values invalidate a replaced installation; no credential/config reads.
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def host_tools_runtime_identity(executable):
    candidate = shutil.which(str(executable)) if executable else None
    if not candidate:
        return None
    try:
        path = Path(candidate).resolve(strict=True)
        stat = path.stat()
        digest = _binary_digest(str(path), stat.st_size, stat.st_mtime_ns)
    except OSError:
        return None
    version = SUPPORTED_CODEX_SHA256.get(digest)
    return {"version": version, "sha256": digest} if version else None


def execution_readiness(platform_name=None, *, capability="native_local", executable=None):
    name = sys.platform if platform_name is None else platform_name
    if capability == "host_tools":
        identity = host_tools_runtime_identity(executable)
        return {"execution_allowed": bool(identity),
                "status": "ready_host_tools" if identity else "blocked_unsupported_host_tools_runtime",
                "reason": "upstream_no_environment" if identity else "unsupported_no_environment_protocol",
                "message": ("Codex 官方引擎可用：仅使用受控宿主工具；本机 shell、任意文件工具和 bpy 执行未启用。"
                            if identity else "当前 Codex 安装未验证无本机环境协议；未启动模型或其他运行时。"),
                "capability": capability, "local_execution_allowed": False,
                "os_boundary_verified": False, "policy_text_is_proof": False,
                "protocol_revision": HOST_TOOLS_REVISION, "runtime_identity": identity}
    if capability != "native_local":
        raise ValueError("Unknown native execution capability.")
    if name == "win32":
        return {"execution_allowed": False, "status": "blocked_unverified_windows",
                "reason": "windows_os_boundary_not_verified", "capability": capability,
                "message": "Windows 本地执行隔离尚未验证；原生命令/文件执行能力暂停。API 可选择官方引擎的受控宿主工具模式。",
                "local_execution_allowed": False, "policy_text_is_proof": False,
                "verification_enable_path_implemented": False}
    return {"execution_allowed": True, "status": "existing_platform_path",
            "capability": capability, "windows_gate_applies": False, "policy_text_is_proof": False}


def validate_host_tools(tools):
    names = [tool.get("name") for tool in tools]
    if any(name not in HOST_TOOL_NAMES for name in names) or len(names) != len(set(names)):
        raise ValueError("This native capability only supports bounded Blender/SketchUp geometry and approved research tools; no shell, Ruby or Python execution tools.")


def validate_host_tools_config(home):
    """Internal entrypoints also require the generated, restricted API profile."""
    try:
        config=tomllib.loads((Path(home) / "config.toml").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError("Host-tools runtime configuration is missing or invalid.") from error
    if (config.get("sandbox_mode") != "read-only" or config.get("approval_policy") != "never"
            or config.get("web_search") != "disabled"
            or any(config.get("features",{}).get(name) is not False for name in HOST_TOOLS_DISABLED_FEATURES)
            or any(config.get(key) for key in ("mcp_servers", "hooks", "windows", "permissions"))):
        raise ValueError("Host-tools runtime configuration changed; local execution remains blocked.")
