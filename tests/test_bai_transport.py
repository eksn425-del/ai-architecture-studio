import json

import httpx
import pytest

from app.bai_transport import complete_bai
from app.provider_test_budget import invoke_with_test_budget


MODEL = "deepseek-v4.1-flash"


def event(delta=None, finish=None, usage=None, model=MODEL):
    return {"model": model, "choices": [] if delta is None and finish is None else [
        {"index": 0, "delta": delta or {}, "finish_reason": finish}],
        **({"usage": usage} if usage is not None else {})}


USAGE = event(usage={"prompt_tokens": 30, "completion_tokens": 10})
FINISH = event(finish="tool_calls")


def perform(events, *, done=True):
    requests = []
    def serve(request):
        requests.append(json.loads(request.content))
        wire = "".join("data: " + json.dumps(e) + "\n\n" for e in events)
        wire += "data: [DONE]\n\n" if done else ""
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=wire)
    kwargs = dict(model="openai/" + MODEL, api_base="https://api.b.ai/v1",
                  api_key="fixture-only", timeout=240, max_retries=0, num_retries=0,
                  messages=[{"role": "user", "content": "fixture"}], max_tokens=32768)
    return lambda: complete_bai(kwargs, transport=httpx.MockTransport(serve)), requests, kwargs


def test_fragmented_tool_reasoning_and_actual_usage_survive():
    first = {"index": 0, "id": "tool-1", "type": "function",
             "function": {"name": "workspace_write", "arguments": '{"path":'}}
    tail = {"index": 0, "function": {"arguments": '"model/plan.md"}'}}
    invoke, requests, _ = perform([
        event({"reasoning_content": "private fixture"}),
        event({"tool_calls": [first]}), event({"tool_calls": [tail]}), FINISH, USAGE])
    result = invoke()
    message = result.choices[0].message
    assert message["reasoning_content"] == "private fixture"
    assert json.loads(message["tool_calls"][0]["function"]["arguments"]) == {"path": "model/plan.md"}
    assert result.usage == USAGE["usage"]
    assert len(requests) == 1
    body = requests[0]
    assert body["model"] == MODEL and body["stream"] is True
    assert body["stream_options"] == {"include_usage": True}
    assert not {"api_key", "api_base", "timeout", "max_retries", "num_retries"} & body.keys()


@pytest.mark.parametrize("events,done", [
    ([event({"content": "partial"}), USAGE], False),
    ([event(finish="length"), USAGE], True),
    ([event(finish="content_filter"), USAGE], True),
    ([FINISH], True),
    ([FINISH, event(usage={"prompt_tokens": True, "completion_tokens": 1})], True),
    ([event({"content": "wrong"}, model="another-model"), FINISH, USAGE], True),
    ([FINISH, event({"content": "late"}), USAGE], True),
])
def test_incomplete_unmetered_or_mixed_stream_never_returns_tools(events, done):
    invoke, requests, _ = perform(events, done=done)
    with pytest.raises(ValueError):
        invoke()
    assert len(requests) == 1


def test_stream_disconnect_keeps_test_budget_reservation(tmp_path, monkeypatch):
    path = tmp_path / "budget.json"
    path.write_text(json.dumps(dict(model="openai/" + MODEL, api_base="https://api.b.ai/v1",
        limit_usd="1", input_usd_per_million="0.30", output_usd_per_million="1.20",
        max_input_tokens=1048576, max_output_tokens=32768, requests=[])))
    monkeypatch.setenv("K_STUDIO_LOCAL_API_TEST_BUDGET", str(path))
    invoke, requests, kwargs = perform([FINISH, USAGE], done=False)
    with pytest.raises(ValueError):
        invoke_with_test_budget(kwargs["model"], kwargs["api_base"], kwargs, invoke)
    rows = json.loads(path.read_text())["requests"]
    assert len(rows) == len(requests) == 1
    assert rows[0]["status"] == "unresolved"
    assert rows[0]["liability_usd"] == "0.3538944"
