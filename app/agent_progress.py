"""Choose the active user turn log without replacing it with nested Critic work."""
from pathlib import Path
import json


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
