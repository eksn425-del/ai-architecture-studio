import json
from pathlib import Path
import shutil
import subprocess

import pytest


def test_ruby_backtrace_line_is_not_provider_http_status():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node unavailable for actual frontend function check")
    source = (Path(__file__).parents[1] / "app/static/studio.js").read_text(encoding="utf-8")
    start = source.index("function friendlyError(")
    end = source.index("\nfunction ", start + 1)
    inputs = ["Cannot save copy to current model file. geometry_tools.rb:401",
              "geometry_tools.rb:402", "geometry_tools.rb:429",
              "AuthenticationError: invalid API key", "请求失败（401）",
              "HTTP 402", 'status_code: 429', "workspace routing discovery unauthorized (401)"]
    program = source[start:end] + "\nconsole.log(JSON.stringify(" + json.dumps(inputs) + ".map(message => friendlyError({message}))));"
    result = subprocess.run([node, "-e", program], capture_output=True, text=True, encoding="utf-8", check=True)
    outputs = json.loads(result.stdout)
    assert all("API Key" not in x and "额度不足" not in x and "限流" not in x for x in outputs[:3])
    assert all("API Key 无效" in x for x in outputs[3:5])
    assert "额度不足" in outputs[5]
    assert "限流" in outputs[6]
    assert "Codex 本机登录缓存" in outputs[7]
