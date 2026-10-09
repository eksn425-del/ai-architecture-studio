"""Deterministic tests of K AI Studio's per-run GitHub evidence contract."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_test_evidence import PNG_SIGNATURE, VIEWS, validate


def _dump(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _fixture(tmp_path: Path, *, geometry: bool) -> Path:
    root = tmp_path / "2026-10-09-kai-evidence-smoke"
    root.mkdir()
    (root / "README.md").write_text("Real evidence smoke fixture. No provider requests.", encoding="utf-8")
    _dump(root / "run.json", {
        "schema_version": 1, "test_id": root.name, "status": "PARTIAL",
        "geometry_committed": geometry, "base_commit": "a" * 40,
        "source_case": "test-assets/cloud-villa/villa-six-view-sheet.png",
        "model": {"requested": "GPT-6 Luna Max", "actual": "fixture-identifier",
                  "runtime": "codex-native-through-K-AI-Studio"},
        "environment": {"sketchup": "2024"}, "qa": {"reviewer_mode": "agent_supplied"},
    })
    _dump(root / "metrics.json", {
        "schema_version": 1, "elapsed_ms": 1, "tool_call_count": 1,
        "failed_tool_calls": 0, "committed_writes": 1 if geometry else 0,
        "full_root_rebuilds": 1 if geometry else 0, "targeted_corrections": 0,
        "input_tokens": None, "output_tokens": None,
        "token_source": "not_available_from_runtime",
    })
    _dump(root / "errors.json", [])
    (root / "review").mkdir()
    (root / "review/review.md").write_text("No real SketchUp execution; synthetic validator fixture.", encoding="utf-8")
    if geometry:
        (root / "views").mkdir()
        for view in VIEWS:
            (root / f"views/{view}.png").write_bytes(PNG_SIGNATURE + b"synthetic png bytes for test")
            _dump(root / f"views/{view}.evidence.json", {
                "canonical_view": view, "model_revisions": {"villa": 1},
                "camera": {"eye_m": [0, 0, 0]},
            })
        (root / "source-perspective.png").write_bytes(PNG_SIGNATURE + b"fixture")
        for artifact in ("model/write-verifications.json", "model/geometry-readback.json",
                         "model/native-reopen.json", "review/critique.json"):
            _dump(root / artifact, {"test_fixture": True})
    return root


def test_complete_six_view_evidence_is_verifiable(tmp_path: Path) -> None:
    folder = _fixture(tmp_path, geometry=True)
    assert not validate(folder, write_manifest=True)
    assert not validate(folder)


def test_mismatched_canonical_view_is_rejected(tmp_path: Path) -> None:
    folder = _fixture(tmp_path, geometry=True)
    _dump(folder / "views/front.evidence.json", {
        "canonical_view": "rear", "model_revisions": {"villa": 1}, "camera": {}
    })
    assert any("Canonical view label mismatch" in x for x in validate(folder, write_manifest=True))


def test_stale_revision_and_missing_png_rejected(tmp_path: Path) -> None:
    folder = _fixture(tmp_path, geometry=True)
    _dump(folder / "views/front.evidence.json", {
        "canonical_view": "front", "model_revisions": {"villa": 0}, "camera": {}
    })
    assert any("mismatched model revisions" in x for x in validate(folder, write_manifest=True))
    (folder / "views/roof.png").unlink()
    assert any("Committed model missing evidence" in x for x in validate(folder, write_manifest=True))


def test_manifest_detects_tampering_and_real_failed_run_can_have_no_screens(tmp_path: Path) -> None:
    folder = _fixture(tmp_path, geometry=False)
    assert not validate(folder, write_manifest=True)
    assert not validate(folder)
    (folder / "README.md").write_text("Modified after snapshot", encoding="utf-8")
    assert any("Manifest mismatch" in x for x in validate(folder))


def test_new_run_requires_real_oss_adoption_evidence(tmp_path: Path) -> None:
    folder = _fixture(tmp_path, geometry=True)
    new_folder = folder.with_name("2026-10-10-kai-new-building")
    folder.rename(new_folder)
    run = json.loads((new_folder / "run.json").read_text(encoding="utf-8"))
    run["test_id"] = new_folder.name
    _dump(new_folder / "run.json", run)
    errors = validate(new_folder, write_manifest=True)
    assert any("oss-method-ledger.json" in e for e in errors)
    assert any("oss-method-adoption.json" in e for e in errors)

    _dump(new_folder / "model/oss-method-ledger.json", {
        "schema_version": 1, "status": "committed_readback",
        "events": [{"method_id": "saie.wall_with_openings", "status": "returned"}],
    })
    _dump(new_folder / "model/oss-method-adoption.json", {
        "schema_version": 1, "ledger_status": "committed_readback",
        "actual_wrapped_calls": {"saie.wall_with_openings": 1},
        "any_oss_product_use": True, "effect_verified": False,
    })
    assert not validate(new_folder, write_manifest=True)
    assert not validate(new_folder)
    adoption_path = new_folder / "model/oss-method-adoption.json"
    changed = json.loads(adoption_path.read_text(encoding="utf-8"))
    changed["any_oss_product_use"] = False
    _dump(adoption_path, changed)
    assert any("contradicts" in e for e in validate(new_folder, write_manifest=True))
