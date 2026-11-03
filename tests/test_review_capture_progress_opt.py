"""Synthetic six-view receipt regression; no local user history required."""
import copy
import json
from app.capture_progress import ReviewCaptureTracker


def capture():
    revisions = {"b1027_primary": 5}
    views = {view: f"views/{view}.png" for view in ReviewCaptureTracker.VIEWS}
    evidence = {}
    for view, path in views.items():
        camera = {"fov_deg": 35, "view": view}
        identity = {"model_guid": "fixture-guid", "model_path": "fixture.skp", "camera": camera}
        evidence[view] = {
            "canonical_view": view, "model_revisions": revisions,
            "path": path, "native_camera_before": copy.deepcopy(identity),
            "native_camera_after": copy.deepcopy(identity), "native_camera": copy.deepcopy(camera),
            "camera_verified_during_capture": True, "width": 640, "height": 480,
        }
    receipt = {"views": views, "evidence": evidence, "model_revisions": revisions}
    return {"script_id": "b1027_primary"}, {"success": True, "views": views,
        "model_revisions": revisions, "contentItems": [{"type": "inputText", "text": json.dumps(receipt)}]}


def test_review_advisory_identity_camera_revision_and_action_boundaries():
    last = [capture() for _ in range(3)]
    tracker = ReviewCaptureTracker()
    assert not tracker.observe("sketchup_capture_review_views", *last[0])
    assert not tracker.observe("sketchup_inspect_owned", {}, {"success": True})
    assert not tracker.observe("workspace_read", {}, {"success": True})
    assert tracker.observe("sketchup_capture_review_views", *last[1])
    assert not tracker.observe("workspace_write", {}, {"success": True})
    assert tracker.observe("sketchup_capture_review_views", *last[2])

    def changed_receipt(mutator):
        args, output = copy.deepcopy(last[0])
        receipt = json.loads(output["contentItems"][0]["text"])
        mutator(args, output, receipt)
        output["contentItems"][0]["text"] = json.dumps(receipt, ensure_ascii=False)
        return args, output

    def change_camera(args, output, receipt):
        row = receipt["evidence"]["front"]
        for value in (row["native_camera_before"]["camera"], row["native_camera_after"]["camera"], row["native_camera"]):
            value["fov_deg"] += 1

    def change_model(args, output, receipt):
        for row in receipt["evidence"].values():
            row["native_camera_before"]["model_guid"] = "another-guid"
            row["native_camera_after"]["model_guid"] = "another-guid"

    def change_revision(args, output, receipt):
        output["model_revisions"] = {"b1027_primary": 6}
        receipt["model_revisions"] = {"b1027_primary": 6}
        for row in receipt["evidence"].values():
            row["model_revisions"] = {"b1027_primary": 6}

    def corrupt_capture(args, output, receipt):
        receipt["evidence"]["front"]["camera_verified_during_capture"] = False

    def missing_view(args, output, receipt):
        del receipt["evidence"]["front"]

    for mutation in (change_camera, change_model, change_revision, corrupt_capture, missing_view):
        current = ReviewCaptureTracker()
        assert not current.observe("sketchup_capture_review_views", *last[0])
        assert not current.observe("sketchup_capture_review_views", *changed_receipt(mutation))

    tracker = ReviewCaptureTracker()
    assert not tracker.observe("sketchup_capture_review_views", *last[0])
    assert not tracker.observe("sketchup_run_workspace_ruby", {}, {"success": True})
    assert not tracker.observe("sketchup_capture_review_views", *last[1])
    assert not tracker.observe("sketchup_submit_visual_review", {}, {"success": True})
    assert not tracker.observe("sketchup_capture_review_views", *last[2])
