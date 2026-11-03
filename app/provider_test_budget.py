"""Opt-in, local single-writer API test ceiling. No credentials or cloud credits."""
from __future__ import annotations

import json
import hashlib
import os
import threading
import uuid
from decimal import Decimal, DecimalException
from pathlib import Path
from .runtime_safety import LocalRuntimeLease

_LOCK = threading.RLock()


def invoke_with_test_budget(model: str, api_base: str, kwargs: dict, invoke, *, attempt_id: str | None = None):
    location = os.environ.get("K_STUDIO_LOCAL_API_TEST_BUDGET", "").strip()
    if not location:
        return invoke()
    path = Path(location).resolve()
    owner_root = path.parent / (".api-budget-" + hashlib.sha256(os.path.normcase(path.name).encode()).hexdigest()[:16])
    # The process lock spans reading, pre-dispatch reservation, provider call,
    # and settlement. A second process fails before reading stale state or
    # dispatching. RLock alone cannot uphold a shared monetary ceiling.
    with _LOCK, LocalRuntimeLease(owner_root):
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if model != data["model"] or api_base.rstrip("/") != data["api_base"].rstrip("/"):
            raise ValueError("本轮测试预算只允许已指定的供应商和模型；未发送请求。")
        ceiling = Decimal(data["limit_usd"])
        input_rate, output_rate = Decimal(data["input_usd_per_million"]), Decimal(data["output_usd_per_million"])
        input_max, output_max = data["max_input_tokens"], data["max_output_tokens"]
        if (not all(type(n) is int and n > 0 for n in (input_max, output_max))
                or not all(n.is_finite() and n > 0 for n in (ceiling, input_rate, output_rate))):
            raise ValueError("测试预算配置无效；未发送请求。")
        reserve = (input_rate * input_max + output_rate * output_max) / 1000000
        rows = data.setdefault("requests", [])
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise ValueError("测试预算账本格式无效；未发送请求。")
        # An interrupted or partially accounted request has an unknown real
        # liability. Do not let a later turn silently continue merely because
        # the nominal ledger still appears to have spare capacity.
        if any(r.get("status") != "settled_upper_bound" for r in rows):
            raise ValueError("前次请求费用尚未核实；保留预算并停止，请先查看服务商账单。")
        try:
            liabilities = [Decimal(str(row["liability_usd"])) for row in rows]
            if any(not value.is_finite() or value < 0 for value in liabilities):
                raise ValueError("invalid historical liability")
            used = sum(liabilities, Decimal(0))
        except (KeyError, ValueError, DecimalException) as error:
            raise ValueError("测试预算历史费用无效；保留原账本，未发送请求。") from error
        if used + reserve > ceiling:
            raise ValueError("本轮 API 小额测试预算已到安全边界；已有项目和用量保留，未继续请求。")
        requested_output = kwargs.get("max_tokens", output_max)
        if type(requested_output) is not int or requested_output <= 0:
            raise ValueError("测试请求输出上限无效；未发送请求。")
        kwargs["max_tokens"] = min(requested_output, output_max)
        row = {"id": attempt_id or uuid.uuid4().hex, "status": "reserved", "liability_usd": str(reserve)}
        rows.append(row)

        def save():
            temporary = path.with_suffix(f".{uuid.uuid4().hex}.tmp")
            temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            temporary.replace(path)

        # Persist before network dispatch. Unknown failures keep their reservation.
        save()
        try:
            response = invoke()
            actual = response.get("model") if isinstance(response, dict) else getattr(response, "model", None)
            usage = response.get("usage") if isinstance(response, dict) else getattr(response, "usage", None)
            if hasattr(usage, "model_dump"):
                usage = usage.model_dump()
            def wire(value):
                return value.split("/", 1)[1] if isinstance(value, str) and value.startswith(("openai/", "deepseek/")) else value
            counts = [usage.get("prompt_tokens"), usage.get("completion_tokens")] if isinstance(usage, dict) else [None, None]
            if (wire(actual) != wire(model) or any(type(n) is not int or n < 0 for n in counts)
                    or counts[0] > input_max or counts[1] > output_max):
                raise ValueError("供应商返回的模型或用量超出测试预算约定；保留预留额度并停止。")
            amount = (input_rate * counts[0] + output_rate * counts[1]) / 1000000
            row.update(status="settled_upper_bound", input_tokens=counts[0], output_tokens=counts[1], liability_usd=str(amount))
            save()
            return response
        except BaseException:
            # Cancellation (including asyncio.CancelledError/KeyboardInterrupt)
            # cannot erase a request's unknown billing liability.
            row["status"] = "unresolved"
            save()
            raise
