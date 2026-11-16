"""Choose the active user turn log without replacing it with nested Critic work."""
from pathlib import Path
import json
from threading import Lock


class ProgressLogReader:
    """Count the whole active log incrementally, rather than a lossy tail.

    Keep only counters/stage flags in memory, never transcript/error text. An
    incomplete last JSONL record is left for the next poll. The reader belongs
    to one active turn and is discarded when that turn ends.
    """
    def __init__(self):
        self._lock = Lock()
        self._path = None
        self._offset = 0
        self._reset()

    def _reset(self):
        self._offset = 0
        self._stats = dict(calls=0, failures=0, api_started=False,
                           api_responded=False, script_written=False,
                           stage="正在读取资料与思考")

    def read(self, path: Path) -> dict:
        with self._lock:
            if path != self._path or path.stat().st_size < self._offset:
                self._path = path
                self._reset()
            with path.open("rb") as stream:
                stream.seek(self._offset)
                for line in iter(stream.readline, b""):
                    if not line.endswith(b"\n"):
                        break
                    self._offset += len(line)
                    try:
                        item = json.loads(line)
                    except (ValueError, UnicodeError):
                        continue
                    if not isinstance(item, dict):
                        continue
                    event, tool = item.get("event"), str(item.get("tool", ""))
                    s = self._stats
                    s["api_started"] |= event == "provider_started"
                    s["api_responded"] |= event == "provider_response"
                    s["script_written"] |= event == "tool_result" and tool in {"workspace_write", "workspace_write_file", "codex_fileChange"} and item.get("success") is not False
                    if event in {"tool_started", "tool_result"}:
                        s["calls"] += int(event == "tool_result")
                        s["failures"] += int(event == "tool_result" and item.get("success") is False)
                        s["stage"] = "正在执行建模脚本" if "ruby" in tool else "正在检查模型截图" if "image" in tool or "camera" in tool else "正在读取模型状态"
                    elif item.get("item_type") == "commandExecution":
                        s["stage"] = "正在编写或检查模型脚本"
            return dict(self._stats)


def select_turn_progress_log(paths: list[Path], started: float) -> Path | None:
    recent = sorted((p for p in paths if p.stat().st_mtime >= started),
                    key=lambda p: p.stat().st_mtime, reverse=True)
    for path in recent:
        # Native logs declare the role at the beginning. A newly created
        # read-only Critic log must not reset the Builder's tool count to zero.
        with path.open("rb") as handle:
            header = handle.read(8192).decode("utf-8", errors="replace")
        for line in header.splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if isinstance(event, dict) and event.get("event") == "project_budget_started":
                if event.get("is_builder") is True:
                    return path
                break
    return recent[0] if recent else None
