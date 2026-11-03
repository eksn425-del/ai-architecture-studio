"""Focused regression checks for the non-blocking capture progress notice."""

import unittest

from app.capture_progress import CaptureProgressTracker
from app.litellm_runtime import _tool_result_parts


def capture(revision=1, guid="model-a"):
    return {
        "success": True,
        "visual_evidence": {
            "native_camera_after": {"model_guid": guid},
            "model_revisions": {"building": revision},
        },
        "contentItems": [{"type": "inputImage", "imageUrl": "data:image/png;base64,AA=="}],
    }


class CaptureProgressTests(unittest.TestCase):
    def test_camera_adjustments_remain_allowed_and_notice_is_periodic(self):
        tracker = CaptureProgressTracker()
        for index in range(8):
            self.assertFalse(tracker.observe("sketchup_set_camera", {"success": True}))
            self.assertEqual(tracker.observe("sketchup_export_view_image", capture()), index in (2, 5))

    def test_new_revision_model_and_meaningful_action_restart_sequence(self):
        tracker = CaptureProgressTracker()
        for _ in range(3):
            tracker.observe("sketchup_export_view_image", capture())
        self.assertFalse(tracker.observe("sketchup_export_view_image", capture(2)))
        self.assertFalse(tracker.observe("sketchup_export_view_image", capture(2, "model-b")))
        tracker.observe("sketchup_run_workspace_ruby", {"success": True})
        for _ in range(2):
            self.assertFalse(tracker.observe("sketchup_export_view_image", capture(2, "model-b")))
        self.assertTrue(tracker.observe("sketchup_export_view_image", capture(2, "model-b")))

    def test_failed_or_unverified_captures_do_not_prove_same_revision(self):
        tracker = CaptureProgressTracker()
        for _ in range(3):
            tracker.observe("sketchup_export_view_image", capture())
        for unknown in ({"success": False}, {"success": True}, capture(guid=""), capture(revision=True)):
            self.assertFalse(tracker.observe("sketchup_export_view_image", unknown))
        for _ in range(2):
            self.assertFalse(tracker.observe("sketchup_export_view_image", capture()))
        self.assertTrue(tracker.observe("sketchup_export_view_image", capture()))

    def test_notice_preserves_visual_payload_and_receipt(self):
        output = capture()
        output["host_notice"] = "advisory"
        text, images = _tool_result_parts(output)
        self.assertIn('"success": true', text)
        self.assertIn('"host_notice": "advisory"', text)
        self.assertEqual(images, ["data:image/png;base64,AA=="])


if __name__ == "__main__":
    unittest.main()
