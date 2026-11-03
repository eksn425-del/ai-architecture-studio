"""Exercise actual subprocess decoding without Blender, provider, or credentials."""
import subprocess
import sys
import pytest
from app.blender_backend import BlenderBackend


def test_utf8_worker_paths_survive_windows_locale(tmp_path):
    script = "import sys; sys.stdout.buffer.write('E:/测试工程/渲染完成'.encode('utf-8'))"
    BlenderBackend._run(tmp_path, "fixture", [sys.executable, "-c", script])
    assert "测试工程/渲染完成" in (tmp_path/"fixture.log").read_text(encoding="utf-8")


def test_bad_log_byte_does_not_hide_worker_failure(tmp_path):
    script = "import sys; sys.stderr.buffer.write(bytes([255])); sys.exit(9)"
    with pytest.raises(subprocess.CalledProcessError) as error:
        BlenderBackend._run(tmp_path, "fixture", [sys.executable, "-c", script])
    assert error.value.returncode == 9
    assert (tmp_path/"fixture-failure.txt").is_file()
    assert not (tmp_path/"fixture.log").exists()
