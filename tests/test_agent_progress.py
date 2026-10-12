import json
import os

from app.agent_progress import select_turn_progress_log


def test_nested_critic_does_not_hide_builder_progress(tmp_path):
    builder = tmp_path / "builder.jsonl"
    critic = tmp_path / "critic.jsonl"
    for path, role, mtime in ((builder, True, 110), (critic, False, 120)):
        path.write_text(json.dumps({"event": "project_budget_started", "is_builder": role}) + "\n", encoding="utf8")
        os.utime(path, (mtime, mtime))
    assert select_turn_progress_log([builder, critic], 100) == builder
    assert select_turn_progress_log([builder, critic], 115) == critic
    assert select_turn_progress_log([builder, critic], 125) is None


def test_non_native_log_and_partial_line_fallback(tmp_path):
    log = tmp_path / "provider.jsonl"
    log.write_text('{"event":"provider_started"}\n{"partial":', encoding="utf8")
    assert select_turn_progress_log([log], 0) == log
