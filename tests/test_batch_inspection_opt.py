"""Synthetic native bridge regression; never contacts SketchUp."""
import json
from pathlib import Path
from app.project_ruby import ProjectRubyExecutor
from app.sketchup_mcp import MCPCallError


def test_batch_inspection_preserves_identity_and_guards(tmp_path, monkeypatch):
    fixture = tmp_path
    model = fixture / "projects" / "batch-test" / "outputs" / "model" / "blank-disposable-test.skp"
    model.parent.mkdir(parents=True)
    model.write_bytes(b"offline fixture")
    monkeypatch.setenv("ARCHFLOW_GENERATED_SCRIPT_DIR", str(fixture / "transport"))


    class Adapter:
        def __init__(self):
            self.guid = "fixture-guid"
            self.active_context = False

        def get_active_model_identity(self):
            return {"model_path": str(model.resolve()), "model_guid": self.guid,
                    "active_context": self.active_context, "main_thread": True}


    class Bridge:
        def __init__(self):
            self.calls = []

        def call(self, name, arguments):
            source = Path(arguments["script_path"]).read_text(encoding="utf-8")
            self.calls.append((name, source))
            assert name == "sketchup_eval_project_file"
            assert "Read owned groups" in arguments["operation_name"]
            assert "root.get_attribute(CodexSketchupArchitect::DICT, 'revision') == 3" in source
            assert "Project identity mismatch" in source and "Active model GUID changed" in source
            if "snapshot = {snapshots:" in source:
                assert 'FINS_FRONT' in source and 'TOWER_SCREEN' in source
                return {"result": {"revision": 3, "snapshots": [
                    {"path": ["FINS_FRONT"], "persistent_id": 101, "objects": [{"id": 1}], "next_offset": 1},
                    {"path": ["TOWER_SCREEN"], "persistent_id": 202, "objects": [{"id": 2}], "next_offset": None},
                ]}}
            if '"FINS_FRONT"' in source:
                return {"result": {"revision": 3, "path": ["FINS_FRONT"], "persistent_id": 101,
                                   "objects": [{"id": 1}, {"id": 3}], "next_offset": None}}
            return {"result": {"revision": 3, "path": ["TOWER_SCREEN"], "persistent_id": 202,
                               "objects": [{"id": 2}], "next_offset": None}}


    adapter, bridge = Adapter(), Bridge()
    executor = ProjectRubyExecutor(fixture, "batch-test", expected_model_path=model,
                                   expected_model_guid=adapter.guid, mcp=bridge,
                                   ruby_state={"main": {"root_pid": 17, "revision": 3}}, adapter=adapter)
    def payload(result):
        return json.loads(result["contentItems"][0]["text"])

    batch = payload(executor.inspect_owned({"script_id": "main", "paths": [["FINS_FRONT"], ["TOWER_SCREEN"]]}))
    assert batch["read_only"] and batch["revision"] == 3 and len(bridge.calls) == 1
    assert [item["persistent_id"] for item in batch["snapshots"]] == [101, 202]
    assert batch["snapshots"][0]["next_offset"] == 1  # preview is not complete evidence
    first = payload(executor.inspect_owned({"script_id": "main", "path": ["FINS_FRONT"], "limit": 50}))
    second = payload(executor.inspect_owned({"script_id": "main", "path": ["TOWER_SCREEN"], "limit": 50}))
    assert [first["persistent_id"], second["persistent_id"]] == [101, 202]
    assert first["next_offset"] is None and len(first["objects"]) == 2 and len(bridge.calls) == 3
    for arguments in (
        {"script_id": "main", "paths": [["FINS_FRONT"], ["FINS_FRONT"]]},
        {"script_id": "main", "path": ["FINS_FRONT"], "paths": [["TOWER_SCREEN"]]},
        {"script_id": "main", "paths": [[str(i)] for i in range(49)]},
    ):
        try:
            executor.inspect_owned(arguments)
            raise AssertionError("invalid batch was accepted")
        except ValueError:
            pass
    assert len(bridge.calls) == 3
    adapter.guid = "different-guid"
    adapter.active_context = True
    try:
        executor.inspect_owned({"script_id": "main", "paths": [["FINS_FRONT"]]})
        raise AssertionError("changed identity was accepted without native proof")
    except MCPCallError:
        pass
    assert len(bridge.calls) == 3
    print("PASS: batch inspection preserves identities, preview limits, validation, and identity guards")
