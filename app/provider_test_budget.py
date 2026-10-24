"""Opt-in, local single-writer API test ceiling. No credentials or cloud credits."""
from __future__ import annotations

import json
import os
import threading
import uuid
from decimal import Decimal
from pathlib import Path

_LOCK = threading.RLock()


def invoke_with_test_budget(model: str, api_base: str, kwargs: dict, invoke, *, attempt_id: str | None = None):
    location = os.environ.get("K_STUDIO_LOCAL_API_TEST_BUDGET", "").strip()
    if not location:
        return invoke()
    path = Path(location)
    with _LOCK:
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
        used = sum((Decimal(r["liability_usd"]) for r in rows), Decimal(0))
        if used + reserve > ceiling:
            raise ValueError("本轮 API 小额测试预算已到安全边界；已有项目和用量保留，未继续请求。")
        kwargs["max_tokens"] = min(kwargs.get("max_tokens", output_max), output_max)
        row = {"id": attempt_id or uuid.uuid4().hex, "status": "reserved", "liability_usd": str(reserve)}
        rows.append(row)

        def save():
            temporary = path.with_suffix(".tmp")
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
