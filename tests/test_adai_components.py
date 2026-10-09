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
            archive.writestr(path, value)
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
