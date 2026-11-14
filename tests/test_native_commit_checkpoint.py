import json
import re
from pathlib import Path
import unittest
import uuid
from unittest.mock import patch

from app.native_commit_checkpoint import persist_committed_revision
from app.project_ruby import ProjectRubyExecutor
from app.sketchup_mcp import MCPCallError


class FakeMCP:
    def __init__(self, *, failure=False, receipt=True):
        self.failure, self.receipt = failure, receipt
        self.script = None
        self.calls = 0

    def call(self, name, args):
        self.calls += 1
        self.script = Path(args["script_path"]).read_text(encoding="utf-8")
        if self.failure:
            raise RuntimeError("disconnected")
        line = next(line for line in self.script.splitlines() if line.startswith("target = "))
        target = Path(json.loads(line[len("target = "):]))
        target.write_bytes(b"fake saved SKP")
        target.with_suffix(".status.json").write_text(json.dumps({"finished": True, "ok": self.receipt}), encoding="utf-8")
        return {"result": {"checkpoint_scheduled": True}}


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self._temp = __import__("tempfile").TemporaryDirectory(prefix="kstudio-checkpoint-")
        self.addCleanup(self._temp.cleanup)
        self.root = Path(self._temp.name)
        self.project = self.root / "runtime" / "projects" / "case"
        self.model = self.project / "outputs" / "model" / "blank-disposable-test.skp"
        self.model.parent.mkdir(parents=True)
        self.model.write_bytes(b"original blank")
        self.transport = self.root / "transport"
        self.mcp = FakeMCP()
        self.guard = patch("app.native_commit_checkpoint._generated_script_dir", return_value=self.transport)
        self.guard.start()

    def tearDown(self):
        self.guard.stop()

    def save(self, **extra):
        args = dict(project_dir=self.project, project_id="case", model_path=self.model,
                    model_guid="guid-1", script_id="building", revision=1, root_pid=321, mcp=self.mcp)
        args.update(extra)
        return persist_committed_revision(**args)

    def test_saves_immutable_copy_after_native_identity_guards(self):
        receipt = self.save()
        text = self.mcp.script
        self.assertLess(text.index("UI.start_timer(0.1, false) do"), text.index("model.save_copy(target)"))
        for guard in ("Active model path changed", "Active model GUID changed", "Active edit context changed",
                      "Owned root missing or empty", "Owned project changed", "Owned revision changed"):
            self.assertEqual(text.count(guard), 2)
            self.assertLess(text.rindex(guard), text.index("model.save_copy(target)"))
        self.assertLess(text.index("model.save_copy(target)"), text.index("unless model.save\n"))
        self.assertEqual(receipt["status"], "saved_unverified_reopen")
        self.assertTrue((self.project / receipt["path"]).is_file())
        self.assertEqual(self.model.read_bytes(), b"original blank")  # mocked SU does not edit it
        self.assertFalse(list(self.transport.glob("*.rb")))

    def test_fresh_names_do_not_overwrite_older_checkpoint(self):
        first, second = self.save(), self.save()
        self.assertNotEqual(first["path"], second["path"])
        self.assertTrue((self.project / first["path"]).is_file())

    def test_bad_identity_fails_before_call(self):
        for options in ({"model_guid": ""}, {"script_id": "../other"}, {"revision": 0}, {"root_pid": True},
                        {"model_path": self.root / "elsewhere.skp"}):
            with self.subTest(options=options), self.assertRaises(MCPCallError):
                self.save(**options)
        self.assertEqual(self.mcp.calls, 0)

    def test_failed_or_ambiguous_save_does_not_claim_success_or_retry(self):
        for fake in (FakeMCP(failure=True), FakeMCP(receipt=False)):
            with self.subTest(failure=fake.failure), self.assertRaisesRegex(MCPCallError, "committed.*unconfirmed"):
                self.save(mcp=fake)
            self.assertEqual(fake.calls, 1)
            self.assertFalse(list(self.transport.glob("*.rb")))

    def test_unconfirmed_revision_blocks_further_writes(self):
        executor = ProjectRubyExecutor(self.root / "runtime", "case", expected_model_path=self.model,
                                      expected_model_guid="guid", mcp=self.mcp,
                                      ruby_state={"building": {"durability_status": "unconfirmed"}})
        with self.assertRaisesRegex(MCPCallError, "checkpoint is unconfirmed"):
            executor.run({"script_id": "building", "ruby_source": "true"})
        self.assertEqual(self.mcp.calls, 0)

    def test_unconfirmed_state_survives_restart_when_session_has_same_revision(self):
        state_path = self.project / "runtime" / "project_ruby_state.json"
        state_path.parent.mkdir(parents=True)
        state_path.write_text(json.dumps({"model_path": str(self.model.resolve()), "scripts": {
            "building": {"revision": 2, "durability_status": "unconfirmed"}}}), encoding="utf-8")
        executor = ProjectRubyExecutor(self.root / "runtime", "case", expected_model_path=self.model,
                                      expected_model_guid="guid", mcp=self.mcp,
                                      ruby_state={"building": {"revision": 2}})
        with self.assertRaisesRegex(MCPCallError, "checkpoint is unconfirmed"):
            executor.run({"script_id": "building", "ruby_source": "true"})
        self.assertEqual(self.mcp.calls, 0)

    def test_unconfirmed_disk_state_blocks_newer_session_state(self):
        state_path = self.project / "runtime" / "project_ruby_state.json"
        state_path.parent.mkdir(parents=True)
        state_path.write_text(json.dumps({"model_path": str(self.model.resolve()), "scripts": {
            "building": {"revision": 1, "durability_status": "unconfirmed"}}}), encoding="utf-8")
        executor = ProjectRubyExecutor(self.root / "runtime", "case", expected_model_path=self.model,
                                      expected_model_guid="guid", mcp=self.mcp,
                                      ruby_state={"building": {"revision": 2}})
        with self.assertRaisesRegex(MCPCallError, "checkpoint is unconfirmed"):
            executor.run({"script_id": "building", "ruby_source": "true"})
        self.assertEqual(self.mcp.calls, 0)

    def test_timeout_committed_report_quarantines_before_retry_and_restart(self):
        class Adapter:
            def get_active_model_identity(inner):
                return {"model_path": str(self.model), "model_guid": "guid", "active_context": False, "main_thread": True}

        class LostReply:
            def call(inner, name, args):
                state_path = self.project / "runtime" / "project_ruby_state.json"
                before_call = json.loads(state_path.read_text(encoding="utf-8"))["scripts"]["building"]
                self.assertEqual(before_call["durability_status"], "unconfirmed")
                code = Path(args["script_path"]).read_text(encoding="utf-8")
                match = re.search(r'report_path: ("(?:\\.|[^"\\])*")', code)
                self.assertIsNotNone(match)
                report = Path(json.loads(match.group(1)))
                report.write_text(json.dumps({"status": "committed", "project_id": "case", "revision": 1, "root_pid": 321}), encoding="utf-8")
                raise TimeoutError("lost reply after commit")

        executor = ProjectRubyExecutor(self.root / "runtime", "case", expected_model_path=self.model,
                                      expected_model_guid="guid", mcp=LostReply(), adapter=Adapter())
        with patch("app.project_ruby._generated_script_dir", return_value=self.transport):
            with self.assertRaisesRegex(MCPCallError, "may have committed"):
                executor.run({"script_id": "building", "ruby_source": "root.entities.add_group"})
        state = json.loads((self.project / "runtime" / "project_ruby_state.json").read_text(encoding="utf-8"))["scripts"]["building"]
        self.assertEqual((state["revision"], state["root_pid"], state["durability_status"]), (1, 321, "unconfirmed"))
        self.assertEqual(len(list(self.transport.glob("*.rb"))), 1)
        self.assertTrue((self.project / "runtime" / "scripts" / "building.rb").is_file())
        resumed = ProjectRubyExecutor(self.root / "runtime", "case", expected_model_path=self.model,
                                     expected_model_guid="guid", mcp=LostReply(), adapter=Adapter(),
                                     ruby_state={"building": {"revision": 1}})
        with self.assertRaisesRegex(MCPCallError, "checkpoint is unconfirmed"):
            resumed.run({"script_id": "building", "ruby_source": "root.entities.add_group"})

    def test_timeout_without_report_retains_intent_and_source(self):
        class Adapter:
            def get_active_model_identity(inner):
                return {"model_path": str(self.model), "model_guid": "guid", "active_context": False, "main_thread": True}

        class LostReply:
            def call(inner, name, args):
                raise TimeoutError("no native report")

        executor = ProjectRubyExecutor(self.root / "runtime", "case", expected_model_path=self.model,
                                      expected_model_guid="guid", mcp=LostReply(), adapter=Adapter())
        with patch("app.project_ruby._generated_script_dir", return_value=self.transport):
            with self.assertRaisesRegex(MCPCallError, "may have committed"):
                executor.run({"script_id": "building", "ruby_source": "root.entities.add_group"})
        state = json.loads((self.project / "runtime" / "project_ruby_state.json").read_text(encoding="utf-8"))["scripts"]["building"]
        self.assertEqual((state["durability_status"], state["outcome"]), ("unconfirmed", "unknown"))
        self.assertEqual(len(list(self.transport.glob("*.rb"))), 1)
        self.assertTrue((self.project / "runtime" / "scripts" / "building.rb").is_file())

    def test_explicit_rollback_clears_write_intent(self):
        class Adapter:
            def get_active_model_identity(inner):
                return {"model_path": str(self.model), "model_guid": "guid", "active_context": False, "main_thread": True}

        class Aborted:
            def call(inner, name, args):
                code = Path(args["script_path"]).read_text(encoding="utf-8")
                match = re.search(r'report_path: ("(?:\\.|[^"\\])*")', code)
                Path(json.loads(match.group(1))).write_text(json.dumps({"status": "aborted"}), encoding="utf-8")
                raise RuntimeError("native transaction rolled back")

        executor = ProjectRubyExecutor(self.root / "runtime", "case", expected_model_path=self.model,
                                      expected_model_guid="guid", mcp=Aborted(), adapter=Adapter())
        with patch("app.project_ruby._generated_script_dir", return_value=self.transport):
            with self.assertRaisesRegex(RuntimeError, "rolled back"):
                executor.run({"script_id": "building", "ruby_source": "root.entities.add_group"})
        state = json.loads((self.project / "runtime" / "project_ruby_state.json").read_text(encoding="utf-8"))["scripts"]
        self.assertNotIn("building", state)
        self.assertFalse(list(self.transport.glob("*.rb")))

    def test_lost_preview_preserves_verified_commit_and_returns_no_image(self):
        bounds = {"min": [0, 0, 0], "max": [100, 100, 100], "size": [100, 100, 100]}
        owned = {"persistent_id": 321, "objects_total": 1, "bounds_mm": bounds}
        identity = {"model_path": str(self.model), "model_guid": "guid", "active_context": False}

        class Adapter:
            def get_active_model_identity(inner):
                return identity

            def get_model_info(inner):
                return {"entity_count": 1}

            def capture_view(inner, path):
                raise MCPCallError("Image destination is outside paired workspaces")

        class Commit:
            def call(inner, name, args):
                code = Path(args["script_path"]).read_text(encoding="utf-8")
                match = re.search(r'report_path: ("(?:\\.|[^"\\])*")', code)
                report = {"status": "committed", "project_id": "case", "revision": 1,
                          "root_pid": 321, "owned_after": owned}
                Path(json.loads(match.group(1))).write_text(json.dumps(report), encoding="utf-8")
                return {}

        executor = ProjectRubyExecutor(self.root / "runtime", "case", expected_model_path=self.model,
                                      expected_model_guid="guid", mcp=Commit(), adapter=Adapter())
        readback = {"contentItems": [{"text": json.dumps({**owned, "revision": 1})}]}
        with (patch("app.project_ruby._generated_script_dir", return_value=self.transport),
              patch("app.project_ruby.persist_committed_revision", return_value={"status": "saved_unverified_reopen"}),
              patch.object(executor, "inspect_owned", return_value=readback)):
            result = executor.run({"script_id": "building", "ruby_source": "root.entities.add_group"})

        self.assertTrue(result["success"])
        self.assertEqual(len(result["contentItems"]), 1)
        summary = json.loads(result["contentItems"][0]["text"])
        self.assertTrue(summary["write_verification"]["verified"])
        self.assertEqual(summary["capture_status"], "PENDING")
        self.assertIsNone(summary["screenshot"])
        saved = json.loads(executor.state_path.read_text(encoding="utf-8"))["scripts"]["building"]
        self.assertEqual((saved["revision"], saved["durability_status"]), (1, "saved_unverified_reopen"))


if __name__ == "__main__":
    unittest.main()
