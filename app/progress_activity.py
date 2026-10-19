"""Public, append-only execution receipts. Never expose model reasoning or arguments."""
from __future__ import annotations

import json
import threading

_ACTIVITY_LOCK = threading.RLock()
from pathlib import Path

from .agent_progress import select_turn_progress_log


def _label(tool: str) -> str:
    labels = {
        "sketchup_get_model_context": "核对当前模型的构件与版本",
        "sketchup_inspect_owned": "检查当前建筑构件及连接",
        "sketchup_read_workspace_ruby": "读取当前版本的建模记录",
        "sketchup_get_workspace_ruby_state": "核对项目模型状态",
        "sketchup_list_groups": "查看模型分组层级",
        "sketchup_verify_keep": "核对需要保留的构件",
        "sketchup_capture_canonical_view": "采集当前版本的模型视角",
        "sketchup_submit_visual_review": "独立对照参考图与模型结果",
    }
    if tool in labels:
        return labels[tool]
    if tool == "codex_commandExecution":
        return "检查本轮工作文件与模型资料"
    if tool == "codex_fileChange":
        return "更新本轮工作文件"
    if "ruby" in tool:
        return "执行有范围的模型修改"
    if "camera" in tool or "image" in tool or "screenshot" in tool:
        return "查看模型视角与截图"
    if "material" in tool:
        return "检查建筑材质"
    if "write" in tool:
        return "准备本轮工作文件"
    if "save" in tool or "checkpoint" in tool:
        return "保存项目检查点"
    return "读取并核对项目资料"


def public_events(path: Path | None, limit: int = 524288) -> list[dict]:
    """Stable byte-offset IDs survive tail polling and repeated identical tools."""
    if path is None:
        return []
    events = []
    with path.open("rb") as handle:
        offset = max(0, path.stat().st_size - limit)
        handle.seek(offset)
        if offset:
            handle.readline()
        while True:
            offset = handle.tell()
            raw = handle.readline()
            if not raw:
                break
            try:
                item = json.loads(raw)
            except (ValueError, UnicodeDecodeError):
                continue
            kind = item.get("event")
            if kind not in {"tool_started", "tool_result"}:
                continue
            label = _label(str(item.get("tool", "")))
            failed = kind == "tool_result" and item.get("success") is False
            events.append({"id": f"{path.stem}:{offset}",
                           "text": label + ("，正在处理返回的问题" if failed else "，已收到执行结果" if kind == "tool_result" else ""),
                           "status": "warning" if failed else "done" if kind == "tool_result" else "running"})
    return events


def activity_history(project_dir: Path) -> list[dict]:
    directory = project_dir / "runtime/public_activity"
    runs = []
    for path in sorted(directory.glob("*.json"), key=lambda p: p.stat().st_mtime)[-100:]:
        try:
            run = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(run, dict) and isinstance(run.get('started'), (int, float)) and isinstance(run.get('events'), list):
                runs.append(run)
        except (ValueError, OSError):
            continue
    return sorted(runs, key=lambda run: run['started'])[-30:]


def _update_activity(project_dir: Path, active: dict, *, finished: bool = False) -> list[dict]:
    started = active["started"]
    turn_id = str(active.get("request_id") or int(started * 1000))
    directory = project_dir / "runtime/public_activity"
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{turn_id}.json"
    run = {"id": turn_id, "message_index": active.get("message_index", 0),
           "anchor": active.get("anchor", active.get("request_id", turn_id)),
           "started": started, "finished": False,
           "events": [{"id": turn_id + ":start", "text": "已收到要求，开始核对资料和模型", "status": "done"}]}
    if target.exists():
        try:
            run = json.loads(target.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            pass
    log = select_turn_progress_log(list((project_dir / "runtime/agent_events").glob("*.jsonl")), started)
    known = {event["id"] for event in run["events"]}
    run["events"].extend(event for event in public_events(log) if event["id"] not in known)
    if finished and turn_id + ":end" not in known:
        run["events"].append({"id": turn_id + ":end", "text": "本轮处理已结束，请查看回复与模型结果", "status": "done"})
    run["finished"] = run.get("finished", False) or finished
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(run, ensure_ascii=False), encoding="utf-8")
    temporary.replace(target)
    return activity_history(project_dir)


def update_activity(project_dir: Path, active: dict, *, finished: bool = False) -> list[dict]:
    with _ACTIVITY_LOCK:
        return _update_activity(project_dir, active, finished=finished)
