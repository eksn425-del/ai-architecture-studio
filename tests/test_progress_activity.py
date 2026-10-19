import json
import time

from app.progress_activity import public_events, update_activity
from app.progress_activity import activity_history


def test_public_receipts_hide_arguments_reasoning_and_retain_identical_calls(tmp_path):
    path = tmp_path / "turn.jsonl"
    row = {"event": "tool_started", "tool": "sketchup_run_ruby", "arguments": {"secret": "sk-private"}}
    path.write_text("\n".join(json.dumps(x) for x in [
        {"event": "reasoning", "text": "private reasoning"}, row, row,
        {"event": "tool_result", "tool": "sketchup_run_ruby", "success": False, "error": "private path"}
    ]) + "\n", encoding="utf-8")
    events = public_events(path)
    assert len(events) == 3
    assert len({x["id"] for x in events}) == 3
    assert events[-1]["status"] == "warning"
    assert not any(value in json.dumps(events) for value in ["sk-private", "private reasoning", "private path"])
    first = events[0]["id"]
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")
    assert public_events(path)[0]["id"] == first


def test_progress_persists_append_only_and_finishes_without_quality_claim(tmp_path):
    directory = tmp_path / "runtime/agent_events"
    directory.mkdir(parents=True)
    started = time.time() - 1
    path = directory / "builder.jsonl"
    path.write_text(json.dumps({"event": "project_budget_started", "is_builder": True}) + "\n" +
                    json.dumps({"event": "tool_started", "tool": "camera"}) + "\n", encoding="utf-8")
    active = {"started": started, "message_index": 4, "anchor": "stable-user-message"}
    first = update_activity(tmp_path, active)[0]
    second = update_activity(tmp_path, active)[0]
    assert first["events"] == second["events"]
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"event": "tool_result", "tool": "camera", "success": True}) + "\n")
    finished = update_activity(tmp_path, active, finished=True)[0]
    assert finished["message_index"] == 4 and finished["finished"] is True
    assert finished["anchor"] == "stable-user-message"
    assert finished["events"][:len(first["events"])] == first["events"]
    assert "验收通过" not in str(finished)


def test_uuid_filenames_cannot_reorder_conversation_and_bad_cache_is_ignored(tmp_path):
    folder = tmp_path/'runtime/public_activity'
    folder.mkdir(parents=True)
    for name, started in [('z', 1), ('a', 2), ('m', 3)]:
        (folder/(name+'.json')).write_text(json.dumps({'id':name,'started':started,'events':[]}), 'utf-8')
    (folder/'broken.json').write_text('not json', 'utf-8')
    (folder/'wrong-type.json').write_text('[]', 'utf-8')
    assert [r['id'] for r in activity_history(tmp_path)] == ['z', 'a', 'm']
