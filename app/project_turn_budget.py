"""Append-only cumulative Native Builder usage; not API billing.

Only recorded integer telemetry in a finished host run counts. Unknown, interrupted-without-usage or legacy
Builder logs are explicitly uncertain, never reset or estimated as zero.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class ProjectBuilderUsage:
    input_tokens: int
    output_tokens: int
    uncertain_files: tuple[str, ...]


def read_project_builder_usage(events_dir: Path) -> ProjectBuilderUsage:
    input_total = output_total = 0
    uncertain: list[str] = []
    if not events_dir.exists():
        return ProjectBuilderUsage(0, 0, ())
    for path in sorted(events_dir.glob("*.jsonl")):
        if path.is_symlink() or not path.is_file():
            uncertain.append(path.name)
            continue
        try:
            events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        except (OSError, ValueError, TypeError):
            uncertain.append(path.name)
            continue
        start = next((e for e in events if isinstance(e, dict) and e.get("event") == "project_budget_started"), None)
        if start is None:
            if any(isinstance(e, dict) and e.get("event") in {
                "token_usage", "tool_started", "turn_interrupted", "native_budget_exhausted"
            } for e in events):
                uncertain.append(path.name)
            continue
        if start.get("is_builder") is not True:
            continue
        receipt = next((e for e in reversed(events) if isinstance(e, dict) and e.get("event") == "project_budget_finished"), None)
        if (receipt is None or receipt.get("is_builder") is not True
                or receipt.get("status") not in {"completed", "interrupted", "failed"}
                or type(receipt.get("input_tokens")) is not int
                or type(receipt.get("output_tokens")) is not int
                or min(receipt["input_tokens"], receipt["output_tokens"]) < 0):
            uncertain.append(path.name)
            continue
        input_total += receipt["input_tokens"]
        output_total += receipt["output_tokens"]
    return ProjectBuilderUsage(input_total, output_total, tuple(uncertain))
