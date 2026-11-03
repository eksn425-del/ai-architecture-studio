"""Upgrade this owner's existing E-drive source installation without project/key migration.

No services, inference, downloads or native model writes. Requires a committed
source checkout and preserves the previous launcher/config/shortcut for rollback.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--latest", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--storage-script", type=Path, required=True)
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1]
    latest = args.latest.resolve(strict=True)
    old = json.loads((latest / "version.json").read_text(encoding="utf-8-sig"))
    if old.get("api_test_budget"):
        raise SystemExit("An existing budgeted test profile cannot be converted by removing its budget.")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    tracked_changes = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=source, text=True)
    if tracked_changes.strip():
        raise SystemExit("Commit reviewed source changes before installation.")
    if os.name != "nt" or not (Path(old["runtime_directory"]) / "projects").is_dir():
        raise SystemExit("An existing Windows installation with project data is required.")
    if not args.storage_script.is_file():
        raise SystemExit("The owner project storage workspace script is unavailable.")
    # Do not interrupt an active or idle service during installation.
    import socket
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1", int(old["port"]))) == 0:
            raise SystemExit("Close the owned local backend normally before installation.")
    prior = Path(old["code_directory"])
    prior_manifest = json.loads((prior / "release-source.json").read_text(encoding="utf-8-sig"))
    for relative, expected in prior_manifest["files"].items():
        assert digest(prior / relative) == expected, "Previous release verification failed"
    destination = latest.parent / "versions" / (datetime.now().strftime("%Y%m%d-") + commit[:8] + "-personal")
    destination.mkdir(exist_ok=False)
    paths = set(prior_manifest["files"])
    paths.update(subprocess.check_output(["git", "ls-files", "app", "scripts", "examples"], cwd=source, text=True, encoding="utf-8").splitlines())
    files = {}
    for relative in sorted(paths):
        candidate = source / relative
        if not candidate.is_file():
            assert relative.startswith("connector-distribution/"), relative
            candidate = prior / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(candidate, target)
        files[relative] = digest(target)
    manifest = {"commit": commit, "branch": "codex/mcp-selector-20261025", "files": files,
                "desktop_mode": "personal-byok", "inherited_connector_distribution": old["commit"]}
    (destination / "release-source.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    for relative, expected in files.items():
        assert digest(destination / relative) == expected
    audit = args.audit.resolve()
    audit.mkdir(exist_ok=False, parents=True)
    for name in ("version.json", "Open-KStudio.ps1", "Open-KStudio-v2.ps1", "Start-KStudioBackend.ps1", "Rollback-KStudio.ps1", "last-launch.json", "desktop-install-receipt.json"):
        path = latest / name
        if path.is_file():
            shutil.copy2(path, audit / ("previous-" + name))
    shutil.copy2(latest / "version.json", audit / "rollback-version.json")
    # Local settings belong to this Windows account, with no plaintext Key or
    # copied historic provider credential. Existing project history stays in place.
    sid = subprocess.check_output(["whoami", "/user", "/fo", "csv", "/nh"], text=True, errors="replace").strip().split(",")[-1].strip('"')
    profile = latest.parent / "data" / "profiles" / ("windows-" + hashlib.sha256(sid.encode()).hexdigest()[:16])
    connections = profile / "settings"
    connections.mkdir(parents=True, exist_ok=True)
    config = {**old, "commit": commit, "code_directory": str(destination), "desktop_mode": "personal-byok",
              "desktop_data_directory": str(profile), "connections_directory": str(connections),
              "storage_workspace_script": str(args.storage_script.resolve()), "upgrade_audit": str(audit),
              "api_test_mode": False, "initial_api": "none", "account_scope": "current_windows_user"}
    for field in ("local_model", "local_reasoning_effort", "api_test_budget", "backend_script"):
        config.pop(field, None)
    temporary = latest / "version.update.json"
    temporary.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    # Stable desktop entry can dispatch old rollback configurations too.
    (latest / "Open-KStudio.ps1").write_text(
        "$ErrorActionPreference='Stop'\n"
        "$cfg=Join-Path $PSScriptRoot 'version.json'\n"
        "$version=Get-Content -LiteralPath $cfg -Raw -Encoding UTF8 | ConvertFrom-Json\n"
        "if($version.desktop_mode -eq 'personal-byok'){ & (Join-Path $version.code_directory 'scripts\\Open-KStudioPersonal.ps1') -ConfigFile $cfg }"
        "else{ & (Join-Path $PSScriptRoot 'Open-KStudio-v2.ps1') -ConfigFile $cfg }\n",
        encoding="utf-8-sig")
    temporary.replace(latest / "version.json")
    receipt = {"commit": commit, "previous_commit": old["commit"], "files_verified": len(files),
               "code_directory": str(destination), "runtime_directory": old["runtime_directory"],
               "settings_directory": str(connections), "account_scope": "current_windows_user",
               "desktop_mode": "personal-byok", "initial_api": "none", "service_started": False,
               "paid_inference": False, "installed_at": datetime.now(timezone.utc).isoformat()}
    (audit / "installation.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    (latest / "desktop-install-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=True))


if __name__ == "__main__":
    main()
