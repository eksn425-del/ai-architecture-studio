"""Optional, pinned ADAI 0.5.39 component distribution and geometry hook.

ADAI is CPAL-1.0. Its unmodified ZIP distributions are installed outside Git,
with upstream LICENSE/NOTICE intact. K Studio does not vendor ADAI CPAL source.
The separate Managed MCP is NOT silently connected to an active SketchUp model.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

UPSTREAM_REVISION = "cd1e02e9f6906945376f73032e9598643fe8eb64"
VERSION = "0.5.39"
TARGET_SU_YEARS = tuple(range(2018, 2027))
COMPONENTS = {
    "skill": {
        "file": "professional-sketchup-modeling-0.5.39-construction-inspection-20261003-r1.zip",
        "sha256": "8e1295724b0b28e4e2045cb80365350ff1f5c51a6bc0d4c0337df45c16e42d7c",
        "required": ("SKILL.md", "scripts/construction_geometry.rb"),
    },
    "mcp": {
        "file": "sketchup-managed-mcp-0.5.39-construction-inspection-20261003-r1.zip",
        "sha256": "f76de1ab85a3edf2705eb8ebc67112c42367b0c57ccd9f7956a9d9ed0a1fc0d5",
        "required": ("launch.cjs", "plugin/su_mcp.rbz"),
    },
}
MAX_ARCHIVE_BYTES = 32 * 1024 * 1024
MAX_EXTRACTED_BYTES = 128 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 6000


def install_root(repo_root: Path) -> Path:
    return repo_root.resolve() / ".local" / "adai" / VERSION


def _sha256(path: Path) -> str:
    hash_value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hash_value.update(block)
    return hash_value.hexdigest()


def _source_url(name: str) -> str:
    return (
        "https://raw.githubusercontent.com/laowang-wy/adai-sketchup-skill-mcp/"
        + UPSTREAM_REVISION + "/dist/" + COMPONENTS[name]["file"]
    )


def _safe_unpack(archive: Path, destination: Path) -> None:
    with zipfile.ZipFile(archive) as source:
        entries = source.infolist()
        if len(entries) > MAX_ARCHIVE_ENTRIES:
            raise ValueError("ADAI distribution contains too many entries.")
        if sum(item.file_size for item in entries) > MAX_EXTRACTED_BYTES:
            raise ValueError("ADAI distribution exceeds extracted size limit.")
        for item in entries:
            name = item.filename
            pure = PurePosixPath(name)
            unix_mode = (item.external_attr >> 16)
            kind = stat.S_IFMT(unix_mode)
            if (
                not name or "\\" in name or pure.is_absolute()
                or ".." in pure.parts or "." in pure.parts
                or ":" in pure.parts[0]
                or kind not in (0, stat.S_IFREG, stat.S_IFDIR)
            ):
                raise ValueError(f"Unsafe ADAI archive member: {name!r}")
            target = destination.joinpath(*pure.parts)
            if not target.resolve().is_relative_to(destination.resolve()):
                raise ValueError("ADAI archive escapes its destination.")
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with source.open(item) as incoming, target.open("wb") as output:
                    shutil.copyfileobj(incoming, output)


def _find_single(base: Path, ending: str) -> Path:
    candidates = sorted(p for p in base.rglob(Path(ending).name)
                        if p.is_file() and p.as_posix().endswith(ending))
    if len(candidates) != 1:
        raise ValueError(f"Expected one {ending} in ADAI component, found {len(candidates)}.")
    return candidates[0]


def install_component(repo_root: Path, name: str) -> dict:
    """Install a pinned official ZIP without executing its contents.

    This is explicitly opt-in. No SketchUp plugin is installed into an SU user
    profile and no MCP config is changed.
    """
    if name not in COMPONENTS:
        raise ValueError("Unknown ADAI component.")
    base = install_root(repo_root)
    base.mkdir(parents=True, exist_ok=True)
    destination = base / name
    with tempfile.TemporaryDirectory(prefix=".adai-stage-", dir=base) as staging:
        staging_path = Path(staging)
        archive = staging_path / COMPONENTS[name]["file"]
        request = urllib.request.Request(
            _source_url(name), headers={"User-Agent": "KStudio-ADAI-Pinned-Installer"}
        )
        with urllib.request.urlopen(request, timeout=60) as response, archive.open("wb") as output:
            while block := response.read(1024 * 1024):
                output.write(block)
                if output.tell() > MAX_ARCHIVE_BYTES:
                    raise ValueError("ADAI ZIP exceeds download size limit.")
        if _sha256(archive) != COMPONENTS[name]["sha256"]:
            raise ValueError("ADAI ZIP SHA-256 mismatch. Nothing installed.")
        unpacked = staging_path / "unpacked"
        unpacked.mkdir()
        _safe_unpack(archive, unpacked)
        required = [_find_single(unpacked, item) for item in COMPONENTS[name]["required"]]
        # Keep the original upstream license and attribution in the installed package.
        if not list(unpacked.rglob("LICENSE")) or not list(unpacked.rglob("NOTICE")):
            raise ValueError("ADAI distribution is missing LICENSE or NOTICE.")
        metadata = {
            "upstream": "laowang-wy/adai-sketchup-skill-mcp",
            "revision": UPSTREAM_REVISION,
            "version": VERSION,
            "component": name,
            "archive_sha256": COMPONENTS[name]["sha256"],
            "files": {str(p.relative_to(unpacked)).replace("\\", "/"): _sha256(p)
                      for p in required},
        }
        (unpacked / "kstudio-install-manifest.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        # Never delete/overwrite an existing installation; user data is preserved.
        if destination.exists():
            raise FileExistsError(f"ADAI {name} already exists at {destination}; inspect it first.")
        shutil.move(str(unpacked), str(destination))
    return {"component": name, "directory": str(destination),
            "sha256": COMPONENTS[name]["sha256"], "status": "installed_isolated"}


def geometry_helper(repo_root: Path) -> Path | None:
    """Return a verified path only when the user explicitly opts in."""
    if os.getenv("ARCH_STUDIO_ENABLE_ADAI_GEOMETRY") != "1":
        return None
    base = install_root(repo_root) / "skill"
    manifest = base / "kstudio-install-manifest.json"
    if not manifest.is_file() or manifest.is_symlink():
        raise RuntimeError("ADAI Skill not installed. Run scripts/install_adai_components.py.")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if (data.get("revision") != UPSTREAM_REVISION
            or data.get("archive_sha256") != COMPONENTS["skill"]["sha256"]
            or data.get("component") != "skill"):
        raise RuntimeError("ADAI Skill manifest does not match pinned version.")
    candidates = [(name, digest) for name, digest in data.get("files", {}).items()
                  if name.endswith("/scripts/construction_geometry.rb")
                  or name == "scripts/construction_geometry.rb"]
    if len(candidates) != 1:
        raise RuntimeError("ADAI construction helper is absent from the validated installation.")
    relative, digest = candidates[0]
    path = (base / relative).resolve()
    if (not path.is_relative_to(base.resolve()) or not path.is_file()
            or path.is_symlink() or _sha256(path) != digest):
        raise RuntimeError("ADAI geometry helper changed since verified installation.")
    return path



def standalone_mcp_connection(repo_root: Path) -> dict:
    """Expose a verified *separate* MCP configuration; never activate it.

    Caller must use an isolated SU plugin/profile and manually approve a Codex
    configuration change. Do not use in parallel with the production bridge.
    """
    base = install_root(repo_root) / "mcp"
    manifest = base / "kstudio-install-manifest.json"
    if not manifest.is_file() or manifest.is_symlink():
        raise RuntimeError("ADAI MCP is not installed. Install it explicitly first.")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if (data.get("component") != "mcp"
            or data.get("revision") != UPSTREAM_REVISION
            or data.get("archive_sha256") != COMPONENTS["mcp"]["sha256"]):
        raise RuntimeError("ADAI MCP installation manifest does not match pin.")
    located = {}
    for label, suffix in (("launch", "launch.cjs"), ("rbz", "plugin/su_mcp.rbz")):
        candidates = [(name, digest) for name, digest in data.get("files", {}).items()
                      if name == suffix or name.endswith("/" + suffix)]
        if len(candidates) != 1:
            raise RuntimeError(f"ADAI MCP missing verified {label}.")
        relative, digest = candidates[0]
        path = (base / relative).resolve()
        if (not path.is_relative_to(base.resolve()) or not path.is_file()
                or path.is_symlink() or _sha256(path) != digest):
            raise RuntimeError(f"ADAI MCP {label} changed after install.")
        located[label] = str(path)
    return {
        "mcp_server_name": "adai_sketchup_isolated",
        "command": "node",
        "args": [located["launch"]],
        "plugin_rbz": located["rbz"],
        "connected": False,
        "requires_separate_sketchup_plugin_profile": True,
        "version_certification": "none",
    }


def detect_sketchup_installations() -> list[dict]:
    """Locate candidate SketchUp versions; discovery is NOT a compatibility PASS."""
    roots = []
    if os.name == "nt":
        for key in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)"):
            value = os.getenv(key)
            if value and Path(value) not in roots:
                roots.append(Path(value))
    found = []
    for year in TARGET_SU_YEARS:
        override = os.getenv(f"SKETCHUP_{year}_EXE")
        paths = ([Path(override)] if override else []) + [
            root / "SketchUp" / f"SketchUp {year}" / "SketchUp.exe" for root in roots
        ]
        existing = next((p for p in paths if p.is_file()), None)
        roaming = os.getenv("APPDATA") if os.name == "nt" else None
        plugin_path = (
            Path(roaming) / "SketchUp" / f"SketchUp {year}" / "SketchUp"
            / "Plugins" / "kongxing_ai_sketchup" / "main.rb"
            if roaming else None
        )
        found.append({
            "year": year, "installed": existing is not None,
            "executable": str(existing) if existing else None,
            "kongxing_bridge_plugin_present": bool(plugin_path and plugin_path.is_file()),
            "kstudio_real_su_validation": "2024_legacy_bridge_only" if year == 2024 else "not_run",
            "adai_upstream_validation": "2019_targeted_only" if year == 2019 else "not_run",
            "adai_geometry_in_kstudio": "not_run",
        })
    return found
