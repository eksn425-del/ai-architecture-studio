import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase, main
from unittest.mock import patch
from uuid import uuid4

from app.interrupted_build_recovery import recover_interrupted_first_build
from app.reference_roles import canonical_plan_text
from app.sketchup_mcp import MCPCallError


class RecoveryTest(TestCase):
    def setUp(self):
        self._temp = __import__("tempfile").TemporaryDirectory(prefix="kstudio-recovery-")
        self.addCleanup(self._temp.cleanup)
        self.root = Path(self._temp.name).resolve()
        (self.root / "outputs/model").mkdir(parents=True)
        (self.root / "runtime/scripts/reports").mkdir(parents=True)
        (self.root / "runtime/agent_workspace/notes").mkdir(parents=True)
        self.model = self.root / "outputs/model/blank-disposable-test.skp"
        self.model.write_bytes(b"test")
        self.card = self.root / "runtime/agent_workspace/notes/reconstruction_card.md"
        self.card.write_text("plan", encoding="utf-8")
        self.pending = {"pending_plan_id":"abc", "project_identity":str(self.root), "model_revisions":{},
                        "consumed":True, "is_followup":False, "reference_manifest_fingerprint":"ref",
                        "plan_sha256":hashlib.sha256(canonical_plan_text("plan").encode()).hexdigest()}
        self.write("runtime/pending_design_scope.json", self.pending)
        self.write("runtime/relation_execution_epoch.json", {"pending_plan_id":"abc"})
        self.state = {"revision":1, "root_pid":7, "last_verification":{"verified":True},
                      "last_report":"runtime/scripts/reports/a.json"}
        self.write("runtime/project_ruby_state.json", {"model_path":str(self.model),"scripts":{"a":self.state}})
        self.report = {"project_id":self.root.name, "model_path":str(self.model), "revision":1,"root_pid":7,"status":"committed"}
        self.write("runtime/scripts/reports/a.json",self.report)
        self.session = SimpleNamespace(reconstruction_state="planned",model_path="outputs/model/blank-disposable-test.skp",ruby_state={})
        self.identity = {"model_path":str(self.model),"model_guid":"guid","active_context":False,"main_thread":True}
        self.adapter = SimpleNamespace(get_active_model_identity=lambda:dict(self.identity))
        self.executor = SimpleNamespace(ruby_state={"a":self.state}, inspect_owned=lambda _: {"contentItems":[{"text":json.dumps({"revision":1,"read_only":True})}]})

    def write(self, path, data):
        (self.root / path).write_text(json.dumps(data),encoding="utf-8")

    def run_recovery(self):
        with patch("app.interrupted_build_recovery.current_reference_fingerprint",return_value="ref"):
            return recover_interrupted_first_build(self.root,self.session,self.adapter,lambda *_:self.executor)

    def test_matching_root_recovers_session_without_authorizing_writer(self):
        self.assertTrue(self.run_recovery())
        self.assertEqual(self.session.reconstruction_state,"building")
        self.assertEqual(self.session.ruby_state["a"]["revision"],1)

    def test_unconsumed_or_changed_plan_never_recovers(self):
        self.pending["consumed"] = False
        self.write("runtime/pending_design_scope.json",self.pending)
        self.assertFalse(self.run_recovery())
        self.assertEqual(self.session.reconstruction_state,"planned")

    def test_unconfirmed_write_never_recovers(self):
        self.state["durability_status"] = "unconfirmed"
        self.write("runtime/project_ruby_state.json",{"model_path":str(self.model),"scripts":{"a":self.state}})
        self.assertFalse(self.run_recovery())

    def test_different_native_revision_never_recovers(self):
        self.executor.inspect_owned=lambda _: {"contentItems":[{"text":json.dumps({"revision":2,"read_only":True})}]}
        self.assertFalse(self.run_recovery())

    def test_wrong_document_never_recovers(self):
        self.identity["model_path"] = str(self.root / "other.skp")
        self.assertFalse(self.run_recovery())

    def test_missing_owned_root_never_recovers(self):
        def no_root(_):
            raise MCPCallError("Owned root missing")
        self.executor.inspect_owned = no_root
        self.assertFalse(self.run_recovery())
        self.assertEqual(self.session.reconstruction_state, "planned")

    def test_malformed_disk_envelopes_do_not_crash_or_recover(self):
        for filename in ("runtime/pending_design_scope.json", "runtime/relation_execution_epoch.json",
                         "runtime/project_ruby_state.json", "runtime/scripts/reports/a.json"):
            path = self.root / filename
            original = path.read_bytes()
            for malformed in ([], None, "interrupted"):
                with self.subTest(filename=filename, malformed=malformed):
                    self.write(filename, malformed)
                    self.assertFalse(self.run_recovery())
                    self.assertEqual(self.session.reconstruction_state, "planned")
                    self.assertEqual(self.session.ruby_state, {})
            path.write_bytes(original)

    def test_malformed_native_receipt_does_not_recover(self):
        for malformed in (None, {}, {"contentItems": []}, {"contentItems": [None]},
                          {"contentItems": [{"text": "[]"}]}, {"contentItems": [{"text": "null"}]}):
            with self.subTest(receipt=malformed):
                self.executor.inspect_owned = lambda _, value=malformed: value
                self.assertFalse(self.run_recovery())
                self.assertEqual(self.session.reconstruction_state, "planned")

if __name__ == "__main__":
    main()
