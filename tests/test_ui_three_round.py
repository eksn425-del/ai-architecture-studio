"""Run bounded production-JavaScript regressions in the normal pytest suite."""
from pathlib import Path
import shutil
import subprocess

import pytest


def test_three_round_ui_contracts():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is required for production JavaScript regression checks")
    suite = Path(__file__).with_suffix(".js")
    result = subprocess.run(
        [node, "--test", str(suite)], capture_output=True, text=True, encoding="utf-8", timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
