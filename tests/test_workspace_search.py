import hashlib
import json

import pytest

from app.workspace_files import MAX_TEXT_BYTES, workspace_file_call, workspace_file_tools


def test_search_cites_exact_project_note_and_line_without_mutation(tmp_path):
    notes = tmp_path / "notes"
    notes.mkdir()
    raw = "历史推断\n用户确认：门窗保留，扶手改铜色。\n未测量尺寸\n".encode()
    path = notes / "card.md"
    path.write_bytes(raw)
    result = workspace_file_call(tmp_path, "workspace_search", {"query": "门窗保留"})
    assert result["complete"] and result["scanned_files"] == 1
    assert result["matches"] == [{"relative_path": "notes/card.md", "line": 2,
        "excerpt": "用户确认：门窗保留，扶手改铜色。", "file_sha256": hashlib.sha256(raw).hexdigest(),
        "evidence_kind": "working_note_untrusted"}]
    assert path.read_bytes() == raw
    assert "workspace_search" in {t["name"] for t in workspace_file_tools()}


def test_missing_evidence_is_empty_and_scan_limits_reported(tmp_path):
    (tmp_path / "qa").mkdir()
    (tmp_path / "qa/large.json").write_bytes(b"x" * (MAX_TEXT_BYTES + 1))
    result = workspace_file_call(tmp_path, "workspace_search", {"query": "不存在的抗震依据"})
    assert result["matches"] == [] and result["skipped_files"] == 1 and not result["complete"]
    for n in range(66):
        (tmp_path / f"qa/{n:03}.json").write_text(json.dumps({"inference": "not measured"}))
    result = workspace_file_call(tmp_path, "workspace_search", {"query": "absent"})
    assert result["scanned_files"] == 64 and not result["complete"]


def test_search_is_literal_bounded_and_never_reads_sibling_project(tmp_path):
    one, two = tmp_path / "one", tmp_path / "two"
    (one / "notes").mkdir(parents=True)
    (two / "notes").mkdir(parents=True)
    (two / "notes/private.md").write_text("secret-other-project")
    (one / "notes/one.md").write_text("prefix .* literal\n" * 20)
    result = workspace_file_call(one, "workspace_search", {"query": ".*", "max_results": 2})
    assert len(result["matches"]) == 2 and not result["complete"]
    assert workspace_file_call(one, "workspace_search", {"query": "secret-other-project"})["matches"] == []


@pytest.mark.parametrize("args", [{"query": " "}, {"query": "x" * 201},
    {"query": "x", "max_results": True}, {"query": "x", "max_results": 9}])
def test_invalid_search_rejected(tmp_path, args):
    with pytest.raises(ValueError):
        workspace_file_call(tmp_path, "workspace_search", args)
