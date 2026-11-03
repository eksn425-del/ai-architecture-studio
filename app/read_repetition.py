"""Detect repeated identical, successful workspace file reads within one turn."""
import hashlib
import json
import re


class ReadRepetitionTracker:
    """Advisory only: never suppress a read, alter history or authorize writes."""

    def __init__(self):
        self.counts = {}

    def before_tool(self, name):
        # Even a failed write is treated as a possible revision boundary.
        if name in {"workspace_write", "workspace_update_strategy"}:
            self.counts.clear()

    def observe(self, name, arguments, output):
        if name not in {"workspace_read", "workspace_read_many"} or output.get("success") is not True:
            return False
        rows = [output] if name == "workspace_read" else output.get("results")
        if not isinstance(rows, list) or not rows:
            return False
        if any(not isinstance(row, dict) or row.get("success") is not True
               or not isinstance(row.get("file_sha256"), str)
               or re.fullmatch(r"[0-9a-f]{64}", row["file_sha256"]) is None for row in rows):
            return False
        # The actual returned result is included: paths, pagination, hash,
        # completeness and content all distinguish one observation from another.
        value = json.dumps([name, arguments, output], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        key = hashlib.sha256(value.encode("utf-8")).hexdigest()
        count = self.counts.get(key, 0) + 1
        self.counts[key] = count
        return count == 3
