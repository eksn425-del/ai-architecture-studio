"""Run production-JavaScript reference-role regressions in the normal pytest suite."""
from pathlib import Path
import shutil
import subprocess

import pytest


def test_reference_default_ui_contracts():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is required for production JavaScript regression checks")
    result = subprocess.run(
        [node, "--test", str(Path(__file__).with_suffix(".js"))],
        capture_output=True, text=True, encoding="utf-8", timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
