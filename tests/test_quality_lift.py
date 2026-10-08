from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

from app.architecture_skill import MAX_CONTEXT_CHARS, UPSTREAM_REVISION, load_architecture_skill_context
from app.models import ProjectContext, QualityBenchmarkRun
from app.native_agent import CodexAppServerRuntime
from app.project_ruby import ProjectRubyExecutor, validate_project_ruby_source
from app.sketchup_mcp import SketchUpAdapter
from app.store import ProjectStore


def test_native_agent_defaults_to_sol_low_and_allows_experiment_override(tmp_path, monkeypatch):
    monkeypatch.delenv("ARCH_STUDIO_CODEX_REASONING_EFFORT", raising=False)
    monkeypatch.delenv("ARCH_STUDIO_ECONOMY_MODEL", raising=False)
    default = CodexAppServerRuntime(tmp_path / "runtime", codex_executable="codex-test")
    assert default.model == "gpt-6.1-sol"
    assert default.reasoning_effort == "low"

    monkeypatch.setenv("ARCH_STUDIO_CODEX_REASONING_EFFORT", "medium")
    experiment = CodexAppServerRuntime(tmp_path / "runtime", codex_executable="codex-test")
    assert experiment.reasoning_effort == "medium"

    monkeypatch.setenv("ARCH_STUDIO_CODEX_REASONING_EFFORT", "ultra")
    with pytest.raises(ValueError, match="must be one of"):
        CodexAppServerRuntime(tmp_path / "runtime", codex_executable="codex-test")


def test_native_runtime_config_records_low_effort_and_hides_raw_eval(tmp_path, monkeypatch):
    source_home = tmp_path / "source-codex"
    source_home.mkdir()
    (source_home / "config.toml").write_text('model = "gpt-6-astra"\n', encoding="utf-8")
    (source_home / "auth.json").write_text("opaque test auth", encoding="utf-8")
    monkeypatch.setenv("CODEX_HOME", str(source_home))

    class ToolClient:
        def list_tools(self):
            return [
                {"name": "sketchup_health", "inputSchema": {"type": "object", "properties": {}}},
                {"name": "sketchup_eval_project_file", "inputSchema": {"type": "object", "properties": {"script_path": {"type": "string"}}}},
            ]

    runtime = CodexAppServerRuntime(tmp_path / "runtime", codex_executable="codex-test", sketchup_mcp=ToolClient(), home_root=tmp_path / "isolated-home", model="gpt-6-astra", reasoning_effort="low")
    runtime._prepare_home(mcp_enabled=True)
    config = (runtime.home / "config.toml").read_text(encoding="utf-8")
    assert 'model_reasoning_effort = "low"' in config
    tools = runtime._dynamic_tools(ruby_enabled=True)
    names = [tool["name"] for tool in tools]
    assert "sketchup_eval_project_file" not in names
    assert "sketchup_run_project_ruby" in names
    assert "script_path" not in tools[-1]["inputSchema"]["properties"]


def test_architecture_skill_context_is_selective_and_bounded():
    context = load_architecture_skill_context()
    assert len(context) <= MAX_CONTEXT_CHARS
    assert UPSTREAM_REVISION in context
    assert "Program and area balance" in context
    assert "Develop plan and section together" in context
    assert "Transaction and revision helper" in context
    assert "Iterate against evidence" in context
    assert "Compatibility and recovery" not in context


def test_camera_adapter_accepts_non_collinear_plan_up_vector():
    class Client:
        call_args = None
        def call(self, name, arguments):
            self.call_args = (name, arguments)
            return {"success": True}

    client = Client()
    SketchUpAdapter(client).set_camera([30, 24, 105], [30, 24, 0], up_m=[0, 1, 0])
    assert client.call_args == ("sketchup_set_camera", {"eye_m": [30, 24, 105], "target_m": [30, 24, 0], "up": [0, 1, 0]})


class FakeRubyAdapter:
    def __init__(self, model_path: Path, guid: str = "guid-live"):
        self.model_path = model_path
        self.guid = guid
        self.captures: list[Path] = []

    def get_active_model_identity(self):
        return {"model_path": str(self.model_path), "model_guid": self.guid, "active_context": False, "main_thread": True}

    def get_model_info(self):
        return {"entity_count": 42, "units": "meters", "model_name": self.model_path.name}

    def capture_view(self, output_path: Path):
        self.captures.append(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"\x89PNG\r\n\x1a\nreview-image")
        return {"success": True}


class FakeRubyMCP:
    def __init__(self):
        self.calls = []
        self.transport_sources: list[str] = []
        self.inspection_sources: list[str] = []

    def call(self, name, arguments):
        self.calls.append((name, arguments))
        assert name == "sketchup_eval_project_file"
        transport_path = Path(arguments["script_path"])
        transport = transport_path.read_text(encoding="utf-8")
        if "inspect_named_owned_group" in transport:
            self.inspection_sources.append(transport)
            root_pid = int(re.search(r"find_entity_by_persistent_id\((\d+)\)", transport).group(1))
            revision = int(re.search(r"Revision mismatch' unless .* == (\d+)", transport).group(1))
            return {"result": {
                "persistent_id": root_pid,
                "revision": revision,
                "objects_total": 1,
                "bounds_mm": {"min": [0.0, 0.0, 0.0], "max": [1000.0, 1000.0, 3000.0]},
                "objects": [],
                "next_offset": None,
            }}

        self.transport_sources.append(transport)
        expected_revision = int(re.search(r"expected_revision: (\d+)", transport).group(1))
        report_literal = re.search(r"report_path: (\"(?:\\.|[^\"])*\")", transport).group(1)
        report_path = Path(json.loads(report_literal))
        root_match = re.search(r"root_pid: (\d+|nil)", transport)
        root_pid = int(root_match.group(1)) if root_match.group(1).isdigit() else 701
        report_path.write_text(json.dumps({
            "status": "committed",
            "revision": expected_revision + 1,
            "root_pid": root_pid,
            "expected_revision": expected_revision,
            "owned_after": {
                "objects_total": 1,
                "bounds_mm": {"min": [0.0, 0.0, 0.0], "max": [1000.0, 1000.0, 3000.0]},
            },
        }), encoding="utf-8")
        return {"success": True, "text": "committed"}


def _executor(tmp_path: Path, *, active_model: Path | None = None, state=None):
    runtime_root = tmp_path / "runtime"
    project_id = "quality-test"
    model_path = runtime_root / "projects" / project_id / "outputs" / "model" / "blank-disposable-test.skp"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_bytes(b"disposable model copy")
    adapter = FakeRubyAdapter(active_model or model_path)
    mcp = FakeRubyMCP()
    executor = ProjectRubyExecutor(
        runtime_root,
        project_id,
        expected_model_path=model_path,
        expected_model_guid="guid-live",
        mcp=mcp,
        ruby_state=state,
        adapter=adapter,
    )
    return executor, adapter, mcp, model_path


def test_committed_revision_survives_interrupted_capture(tmp_path):
    executor, adapter, mcp, model_path = _executor(tmp_path)
    def failed_capture(path):
        raise OSError("capture interrupted")
    adapter.capture_view = failed_capture
    with pytest.raises(OSError, match="interrupted"):
        executor.run({"script_id": "main", "ruby_source": "root.name = 'Restorable'"})
    restored = ProjectRubyExecutor(
        executor.runtime_root, executor.project_id, expected_model_path=model_path,
        expected_model_guid="guid-live", mcp=mcp, ruby_state={}, adapter=adapter,
    )
    assert restored.ruby_state["main"]["revision"] == 1
    assert restored.ruby_state["main"]["root_pid"] == 701


def test_project_ruby_path_and_source_restrictions(tmp_path):
    executor, _adapter, _mcp, model_path = _executor(tmp_path)
    with pytest.raises(ValueError, match="script_id"):
        validate_project_ruby_source("../outside", "root.name = 'bad'")
    with pytest.raises(ValueError, match="blocked"):
        validate_project_ruby_source("main", "File.delete('private.skp')")
    for source in (
        "Object.const_get(:File).delete('private.skp')",
        "model.entities.erase_entities(model.entities.to_a)",
        "root.parent.entities.clear!",
        "receiver.public_send(:system, 'whoami')",
        "model.active_view.write_image('C:/Users/user/private.png')",
        "Sketchup.open_models.each { |m| m.close }",
        "$LOAD_PATH.clear",
    ):
        with pytest.raises(ValueError, match="blocked"):
            validate_project_ruby_source("main", source)
    assert validate_project_ruby_source("main", "box = root.entities.add_group; model.active_view.zoom_extents")
    with pytest.raises(ValueError, match="Remove all active_model"):
        validate_project_ruby_source("main", "model.start_operation('build', true) if model.respond_to?(:start_operation)")
    with pytest.raises(ValueError, match="disposable"):
        ProjectRubyExecutor(
            tmp_path / "runtime", "quality-test",
            expected_model_path=tmp_path / "private-thesis.skp",
            expected_model_guid="guid-live", mcp=FakeRubyMCP(),
        )
    assert not (model_path.parent.parent.parent / "runtime" / "scripts").exists()


def test_project_ruby_active_model_gate_prevents_script_write(tmp_path):
    external = tmp_path / "source-thesis.skp"
    external.write_bytes(b"private source")
    executor, _adapter, mcp, _model_path = _executor(tmp_path, active_model=external)
    with pytest.raises(Exception, match="no longer matches"):
        executor.run({"script_id": "main", "ruby_source": "root.name = 'safe'"})
    assert mcp.calls == []
    project_runtime = tmp_path / "runtime" / "projects" / "quality-test" / "runtime"
    assert not project_runtime.exists()


def test_existing_mcp_edits_can_refresh_ruby_guid_within_same_turn(tmp_path):
    executor, adapter, _mcp, _model_path = _executor(tmp_path)
    adapter.guid = "guid-after-existing-tool-edit"
    identity = executor.refresh_active_model_snapshot()
    assert identity["model_guid"] == "guid-after-existing-tool-edit"
    assert executor.expected_model_guid == "guid-after-existing-tool-edit"


def test_same_project_script_revisions_reuse_model_root_and_return_screenshots(tmp_path, monkeypatch):
    transport_dir = tmp_path / "kongxing-generated"
    monkeypatch.setenv("ARCHFLOW_GENERATED_SCRIPT_DIR", str(transport_dir))
    state = {}
    executor, adapter, mcp, model_path = _executor(tmp_path, state=state)
    first = executor.run({"script_id": "main", "ruby_source": "root.name = 'Cultural center'"})
    second = executor.run({"script_id": "main", "ruby_source": "root.name = 'Cultural center revised'", "allow_full_rebuild": True})

    assert state["main"]["revision"] == 2
    assert state["main"]["root_pid"] == 701
    assert state["main"]["model_guid"] == "guid-live"
    assert Path(mcp.calls[0][1]["script_path"]).parent == transport_dir.resolve()
    assert len(mcp.calls) == 4
    assert len(mcp.inspection_sources) == 2
    assert "expected_revision: 0" in mcp.transport_sources[0]
    assert "expected_revision: 1" in mcp.transport_sources[1]
    assert "root_pid: 701" in mcp.transport_sources[1]
    assert "unless defined?(CodexSketchupArchitect)" not in mcp.transport_sources[1]
    assert "root.entities.to_a.each { |entity| entity.erase! }" in mcp.transport_sources[1]
    assert "root.set_attribute(CodexSketchupArchitect::DICT, 'project_id', \"quality-test\")" in mcp.transport_sources[1]
    assert len(adapter.captures) == 2
    assert first["success"] and second["success"]
    summary = json.loads(second["contentItems"][0]["text"])
    assert summary["write_verification"]["verified"] is True
    assert {item["check"] for item in summary["write_verification"]["checks"]} >= {
        "transaction_status", "root_persistent_id", "revision", "objects_total", "bounds_mm"
    }
    assert second["contentItems"][1]["type"] == "inputImage"
    assert (model_path.parents[2] / "outputs" / "renders" / "ruby-main-r2.png").is_file()
    assert list(transport_dir.iterdir()) == []


def test_ab_benchmark_metadata_persists_same_low_model_and_input(tmp_path):
    store = ProjectStore(tmp_path / "runtime")
    project = store.create_project(ProjectContext(project_name="Quality benchmark fixture"))
    input_hash = hashlib.sha256(b"same sanitized community-center benchmark input").hexdigest()
    for variant in ("A", "B"):
        store.save_benchmark_run(QualityBenchmarkRun(
            benchmark_id="quality-lift-v1",
            variant=variant,
            project_id=project.project_id,
            model="gpt-6-astra",
            reasoning_effort="low",
            input_sha256=input_hash,
            architecture_skill=variant == "B",
            ruby_enabled=variant == "B",
            skill_revision=UPSTREAM_REVISION if variant == "B" else "",
            status="complete",
        ))

    runs = store.load_benchmark_runs(project.project_id)
    assert [run.variant for run in runs] == ["A", "B"]
    assert runs[0].model == runs[1].model == "gpt-6-astra"
    assert runs[0].reasoning_effort == runs[1].reasoning_effort == "low"
    assert runs[0].input_sha256 == runs[1].input_sha256 == input_hash
    assert runs[0].architecture_skill is False and runs[1].architecture_skill is True
