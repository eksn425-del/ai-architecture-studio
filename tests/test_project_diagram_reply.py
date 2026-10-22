from app.main import _sanitize_agent_reply


def test_windows_slash_prefixed_project_screenshot_link(tmp_path):
    import os
    import pytest
    if os.name != 'nt':
        pytest.skip('Windows drive-path spelling needs a real Windows filesystem.')
    image = tmp_path / 'outputs/renders/balcony.png'
    image.parent.mkdir(parents=True); image.write_bytes(b'current capture')
    assert _sanitize_agent_reply(f'[查看阳台](</{image.as_posix()}>)', tmp_path) == '[查看阳台](outputs/renders/balcony.png)'
    outside = tmp_path.parent / 'unrelated-private.png'; outside.write_bytes(b'private')
    assert 'outputs/renders' not in _sanitize_agent_reply(f'[外部](</{outside.as_posix()}>)', tmp_path)


def test_actual_project_diagram_keeps_safe_relative_link(tmp_path):
    sketch = tmp_path / "runtime/agent_workspace/notes/direction_sketch.png"
    sketch.parent.mkdir(parents=True)
    sketch.write_bytes(b"owned diagram")
    assert _sanitize_agent_reply(f"![空间草图](<{sketch}>)", tmp_path) == "![空间草图](notes/direction_sketch.png)"
    assert _sanitize_agent_reply(f"[草图]({sketch})", tmp_path) == "[草图](notes/direction_sketch.png)"


def test_other_project_or_private_inputs_are_not_promoted_to_artifact_links(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    private = project / "inputs/reference.png"
    private.parent.mkdir()
    private.write_bytes(b"private")
    unrelated = tmp_path / "notes/other.png"
    unrelated.parent.mkdir()
    unrelated.write_bytes(b"other project")
    for target in (private, unrelated):
        reply = _sanitize_agent_reply(f"![图]({target})", project)
        assert "![图](notes/" not in reply
        assert "![图](outputs/" not in reply
