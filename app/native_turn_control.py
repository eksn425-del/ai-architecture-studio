"""Small host adapter for actual App Server turn identity and cancellation.

This is transport glue, not a second agent loop. The runtime owns all event reads
and tool dispatch; cancellation only writes turn/interrupt on that same stream.
"""
from __future__ import annotations

import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable


class NativeTurnControl:
    def __init__(self, send: Callable[[dict[str, Any]], None], wake: Callable[[], None],
                 emit: Callable[[dict[str, Any]], None] | None = None):
        self._send = send
        self._wake = wake
        self._emit = emit or (lambda event: None)
        self._lock = threading.RLock()
        self.thread_id = ""
        self.turn_id = ""
        self.cancel_requested = False
        self.requested_at: float | None = None
        self.wait_started_at: float | None = None
        self.interrupt_attempted = False
        self.interrupt_sent = False
        self.interrupt_acknowledged = False
        self.interrupt_error = ""
        self.terminal_status = ""
        self.in_flight_tool = ""
        self.interrupt_request_id = "kstudio-interrupt-" + uuid.uuid4().hex

    def bind_thread(self, thread_id: str) -> None:
        with self._lock:
            self.thread_id = thread_id

    def bind_turn(self, response: dict[str, Any]) -> None:
        turn = response.get("turn")
        turn_id = turn.get("id") if isinstance(turn, dict) else None
        if not isinstance(turn_id, str) or not turn_id:
            raise ValueError("Codex turn/start returned no turn id.")
        with self._lock:
            self.turn_id = turn_id
            if self.cancel_requested:
                self._interrupt_locked()

    def _interrupt_locked(self) -> None:
        if not self.thread_id or not self.turn_id or self.interrupt_attempted or self.terminal_status:
            return
        # Mark before writing: an uncertain write must never be blindly retried.
        self.interrupt_attempted = True
        try:
            self._send({"id": self.interrupt_request_id, "method": "turn/interrupt",
                        "params": {"threadId": self.thread_id, "turnId": self.turn_id}})
            self.interrupt_sent = True
        except (OSError, RuntimeError) as error:
            self.interrupt_error = str(error)[:500]
        self._wake()

    def request_cancel(self) -> dict[str, Any]:
        with self._lock:
            repeated = self.cancel_requested
            if self.terminal_status:
                return self.receipt("not_running")
            self.cancel_requested = True
            if self.requested_at is None:
                self.requested_at = time.monotonic()
            if not self.in_flight_tool and self.wait_started_at is None:
                self.wait_started_at = self.requested_at
            self._interrupt_locked()
            receipt = self.receipt("already_requested" if repeated else "requested")
        self._wake()
        self._emit({"event": "cancel_requested", **receipt})
        return receipt

    def handle_response(self, message: dict[str, Any]) -> bool:
        if message.get("id") != self.interrupt_request_id:
            return False
        with self._lock:
            self.interrupt_acknowledged = "error" not in message and isinstance(message.get("result"), dict)
            if "error" in message:
                self.interrupt_error = str((message.get("error") or {}).get("message", "Interrupt rejected"))[:500]
            receipt = self.receipt("requested")
        self._emit({"event": "interrupt_acknowledged" if self.interrupt_acknowledged else "interrupt_rejected", **receipt})
        return True

    def begin_tool(self, name: str) -> bool:
        """Linearize dispatch against cancel, without locking across external work."""
        with self._lock:
            if self.cancel_requested or self.terminal_status:
                return False
            self.in_flight_tool = name
            return True

    def end_tool(self) -> None:
        with self._lock:
            self.in_flight_tool = ""
            if self.cancel_requested:
                # The tool has its own timeout. Give its reply/queued terminal
                # events a full bounded drain window after it returns.
                self.wait_started_at = time.monotonic()

    def finish(self, status: str) -> None:
        with self._lock:
            self.terminal_status = status

    def receipt(self, status: str = "running") -> dict[str, Any]:
        with self._lock:
            return {"status": status, "thread_id": self.thread_id, "turn_id": self.turn_id,
                    "cancellation_requested": self.cancel_requested,
                    "interrupt_attempted": self.interrupt_attempted,
                    "interrupt_sent": self.interrupt_sent,
                    "interrupt_acknowledged": self.interrupt_acknowledged,
                    "interrupt_error": self.interrupt_error,
                    "terminal_status": self.terminal_status,
                    "interrupted_confirmed": self.terminal_status == "interrupted",
                    "in_flight_tool": self.in_flight_tool,
                    "rollback_performed": False}

    def matches(self, params: dict[str, Any]) -> bool:
        """Reject explicitly foreign/stale events; tolerate older missing envelopes."""
        thread_id = params.get("threadId")
        turn_id = params.get("turnId") or (params.get("turn") or {}).get("id")
        return (not thread_id or thread_id == self.thread_id) and (not turn_id or turn_id == self.turn_id)


class NativeTurnRegistry:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._active: dict[str, list[NativeTurnControl]] = {}

    @staticmethod
    def _key(project_dir: Path) -> str:
        return str(project_dir.resolve())

    def register(self, project_dir: Path, control: NativeTurnControl) -> None:
        with self._lock:
            turns = self._active.setdefault(self._key(project_dir), [])
            # A nested read-only Critic cannot start after its Builder was stopped.
            if any(turn.cancel_requested for turn in turns):
                control.request_cancel()
            turns.append(control)

    def unregister(self, project_dir: Path, control: NativeTurnControl) -> None:
        with self._lock:
            key = self._key(project_dir)
            turns = self._active.get(key, [])
            if control in turns:
                turns.remove(control)
            if not turns:
                self._active.pop(key, None)

    def cancelled(self, project_dir: Path) -> bool:
        with self._lock:
            return any(turn.cancel_requested for turn in self._active.get(self._key(project_dir), []))

    def cancel(self, project_dir: Path) -> dict[str, Any]:
        # Keep registration atomic with this snapshot so nested turns inherit stop.
        with self._lock:
            turns = list(self._active.get(self._key(project_dir), []))
            if not turns:
                return {"status": "not_running", "thread_id": "", "turn_id": "",
                        "cancellation_requested": False, "interrupt_attempted": False, "interrupt_sent": False,
                        "interrupt_acknowledged": False, "interrupted_confirmed": False,
                        "in_flight_tool": "", "rollback_performed": False, "turns": []}
            receipts = [turn.request_cancel() for turn in turns]
            return {**receipts[0], "turns": receipts}


def native_progress_event(method: str, params: dict[str, Any], *, thread_id: str,
                          turn_id: str) -> dict[str, Any] | None:
    """Public-safe bounded progress. Never return reasoning, commands or arguments."""
    event: dict[str, Any] = {"event": method, "thread_id": thread_id, "turn_id": turn_id}
    if method == "item/agentMessage/delta":
        return {**event, "item_id": str(params.get("itemId") or "")[:200],
                "text": str(params.get("delta") or "")[:4000]}
    if method == "turn/plan/updated":
        plan = params.get("plan")
        return {**event, "plan": [
            {"step": str(step.get("step") or "")[:500], "status": str(step.get("status") or "")[:50]}
            for step in (plan if isinstance(plan, list) else [])[:20] if isinstance(step, dict)]}
    if method in {"item/started", "item/completed"}:
        item = params.get("item") or {}
        kind = item.get("type")
        if kind not in {"agentMessage", "agent_message", "commandExecution", "fileChange", "dynamicToolCall", "mcpToolCall", "mcp_tool_call"}:
            return None
        event.update(item_id=str(item.get("id") or "")[:200], item_type=kind,
                     status=str(item.get("status") or "")[:50])
        if kind in {"agentMessage", "agent_message"}:
            event["text"] = str(item.get("text") or "")[:4000]
        elif kind in {"dynamicToolCall", "mcpToolCall", "mcp_tool_call"}:
            event["tool"] = str(item.get("tool") or "")[:200]
        return event
    if method in {"turn/started", "turn/completed"}:
        return {**event, "status": str((params.get("turn") or {}).get("status") or "")[:50]}
    return None
