"""No-network tests for pinned ADAI component installation and isolation."""
from __future__ import annotations

import hashlib
import io
import json
import os
import zipfile
from pathlib import Path

import pytest

from app import adai_components as subject


def _zip_bytes(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, value in files.items():
            item = zipfile.ZipInfo(path)
            # Preserve deliberately malformed ZIP names in negative fixtures;
            # the constructor otherwise normalizes Windows backslashes.
            item.filename = path
            archive.writestr(item, value)
    return buffer.getvalue()


def _mock_skill_download(monkeypatch, data: bytes) -> None:
    monkeypatch.setitem(subject.COMPONENTS["skill"], "sha256", hashlib.sha256(data).hexdigest())
    monkeypatch.setattr(subject.urllib.request, "urlopen",
                        lambda *args, **kwargs: io.BytesIO(data))


def test_install_verified_skill_isolated_and_enable_guard(tmp_path: Path, monkeypatch) -> None:
    data = _zip_bytes({
        "professional-sketchup-modeling/SKILL.md": b"test skill",
        "professional-sketchup-modeling/LICENSE": b"CPAL-1.0",
        "professional-sketchup-modeling/NOTICE": b"ADAI attribution",
        "professional-sketchup-modeling/scripts/construction_geometry.rb": b"module ADAIConstructionGeometry; end",
    })
    _mock_skill_download(monkeypatch, data)
    result = subject.install_component(tmp_path, "skill")
    assert result["status"] == "installed_isolated"
    assert not (tmp_path / "runtime").exists()
    monkeypatch.delenv("ARCH_STUDIO_ENABLE_ADAI_GEOMETRY", raising=False)
    assert subject.geometry_helper(tmp_path) is None
    monkeypatch.setenv("ARCH_STUDIO_ENABLE_ADAI_GEOMETRY", "1")
    helper = subject.geometry_helper(tmp_path)
    assert helper is not None
    assert helper.read_bytes().startswith(b"module ADAIConstructionGeometry")
    with pytest.raises(FileExistsError):
        subject.install_component(tmp_path, "skill")


def test_helper_modification_fails_closed(tmp_path: Path, monkeypatch) -> None:
    data = _zip_bytes({
        "professional-sketchup-modeling/SKILL.md": b"test",
        "professional-sketchup-modeling/LICENSE": b"CPAL-1.0",
        "professional-sketchup-modeling/NOTICE": b"attribution",
        "professional-sketchup-modeling/scripts/construction_geometry.rb": b"valid",
    })
    _mock_skill_download(monkeypatch, data)
    subject.install_component(tmp_path, "skill")
    monkeypatch.setenv("ARCH_STUDIO_ENABLE_ADAI_GEOMETRY", "1")
    path = subject.geometry_helper(tmp_path)
    assert path
    path.write_text("tampered", encoding="utf-8")
    with pytest.raises(RuntimeError, match="changed"):
        subject.geometry_helper(tmp_path)


def test_archive_traversal_and_symlink_are_rejected(tmp_path: Path) -> None:
    for name in ("../escape", "/etc/escape", "C:/escape", "x\\evil"):
        src = tmp_path / "test.zip"
        src.write_bytes(_zip_bytes({name: b"x"}))
        with pytest.raises(ValueError, match="Unsafe"):
            subject._safe_unpack(src, tmp_path / "target")
    link_zip = tmp_path / "link.zip"
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as z:
        item = zipfile.ZipInfo("malicious-link")
        item.create_system = 3
        item.external_attr = (0o120777 << 16)
        z.writestr(item, "target")
    link_zip.write_bytes(data.getvalue())
    with pytest.raises(ValueError, match="Unsafe"):
        subject._safe_unpack(link_zip, tmp_path / "target")


def test_zip_checksum_mismatch_never_installs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(subject.urllib.request, "urlopen",
                        lambda *args, **kwargs: io.BytesIO(b"untrusted bytes"))
    with pytest.raises(ValueError, match="SHA-256"):
        subject.install_component(tmp_path, "skill")
    assert not (subject.install_root(tmp_path) / "skill").exists()


def test_detect_versions_never_claims_support(tmp_path: Path, monkeypatch) -> None:
    exe = tmp_path / "SketchUp.exe"
    exe.write_bytes(b"")
    monkeypatch.setenv("SKETCHUP_2026_EXE", str(exe))
    values = subject.detect_sketchup_installations()
    assert [v["year"] for v in values] == list(range(2018, 2027))
    assert next(v for v in values if v["year"] == 2026)["installed"] is True
    assert all(v["adai_geometry_in_kstudio"] == "not_run" for v in values)


def test_separate_mcp_is_verified_but_never_auto_connected(tmp_path: Path, monkeypatch) -> None:
    data = _zip_bytes({
        "sketchup-managed-mcp/launch.cjs": b"process.exit(0);",
        "sketchup-managed-mcp/plugin/su_mcp.rbz": b"plugin bytes",
        "sketchup-managed-mcp/LICENSE": b"CPAL-1.0",
        "sketchup-managed-mcp/NOTICE": b"ADAI attribution",
    })
    monkeypatch.setitem(subject.COMPONENTS["mcp"], "sha256", hashlib.sha256(data).hexdigest())
    monkeypatch.setattr(subject.urllib.request, "urlopen",
                        lambda *args, **kwargs: io.BytesIO(data))
    subject.install_component(tmp_path, "mcp")
    info = subject.standalone_mcp_connection(tmp_path)
    assert info["mcp_server_name"] == "adai_sketchup_isolated"
    assert info["connected"] is False
    assert info["args"][0].endswith("launch.cjs")
    assert info["plugin_rbz"].endswith(".rbz")
    Path(info["plugin_rbz"]).write_bytes(b"tampered")
    with pytest.raises(RuntimeError, match="changed"):
        subject.standalone_mcp_connection(tmp_path)

def test_guarded_project_ruby_injects_verified_helper_only_when_enabled(tmp_path: Path, monkeypatch) -> None:
    from app import project_ruby

    executor = object.__new__(project_ruby.ProjectRubyExecutor)
    executor.project_id = "test-project"
    executor.expected_model_path = tmp_path / "blank-disposable-test.skp"
    executor.expected_model_guid = "GUID"

    def script() -> str:
        return executor._build_transport_script(
            tmp_path / "project.rb", tmp_path / "report.json",
            expected_revision=0, root_pid=None,
            keep_expectations=[{"path": ["BALCONY"], "persistent_id": 123}],
        )

    monkeypatch.setattr(project_ruby, "geometry_helper", lambda *_: None)
    default_code = script()
    assert "adai_geometry = ADAIConstructionGeometry" not in default_code
    assert "verify_owned_fingerprints!" in default_code
    assert "KStudioProfessionalHelpers.wall_with_openings" in default_code

    helper = tmp_path / "installed-official-helper.rb"
    helper.write_text("module ADAIConstructionGeometry; end", encoding="utf-8")
    monkeypatch.setattr(project_ruby, "geometry_helper", lambda *_: helper)
    enabled_code = script()
    assert "adai_geometry = ADAIConstructionGeometry" in enabled_code
    assert f"load {executor._ruby_string(str(helper))}" in enabled_code
    assert "CodexSketchupArchitect.run" in enabled_code
    assert "verify_owned_fingerprints!" in enabled_code
    assert "SKETCHUP" not in enabled_code or "18..26" in enabled_code


def test_zip_duplicate_and_size_guard(tmp_path: Path) -> None:
    archive = tmp_path / "oversize.zip"
    huge_meta = _zip_bytes({"x.bin": b"x" * 100})
    archive.write_bytes(huge_meta)
    old_limit = subject.MAX_EXTRACTED_BYTES
    try:
        subject.MAX_EXTRACTED_BYTES = 10
        with pytest.raises(ValueError, match="size limit"):
            subject._safe_unpack(archive, tmp_path / "unpack")
    finally:
        subject.MAX_EXTRACTED_BYTES = old_limit
def test_blank_launcher_parses_in_windows_powershell():
    """PowerShell 5.1 reads BOM-less scripts as ANSI; source must still parse."""
    import os
    import subprocess
    from pathlib import Path
    import pytest

    if os.name != "nt":
        pytest.skip("Windows PowerShell 5.1 parser regression")
    launcher = Path(__file__).resolve().parents[1] / "scripts/open_blank_sketchup.ps1"
    command = (
        "$errorsFound=$null; $tokensFound=$null; "
        "[System.Management.Automation.Language.Parser]::ParseFile('"
        + str(launcher).replace("'", "''")
        + "',[ref]$tokensFound,[ref]$errorsFound) | Out-Null; "
        "if($errorsFound.Count){$errorsFound | Out-String | Write-Output; exit 1}"
    )
    result = subprocess.run(["powershell", "-NoProfile", "-Command", command],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr


def test_blank_launcher_prefers_architecture_template_without_scale_figure():
    from pathlib import Path
    source = (Path(__file__).resolve().parents[1] / "scripts/open_blank_sketchup.ps1").read_text(encoding="utf-8")
    assert source.index("'Temp03b - AEC.skp'") < source.index("'Temp01a - Simple.skp'")
    assert "if ($found) { $found; break }" in source
