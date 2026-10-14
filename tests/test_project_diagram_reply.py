from app.main import _sanitize_agent_reply


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
