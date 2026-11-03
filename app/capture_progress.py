"""Advisory progress feedback for consecutive SketchUp visual captures."""

import json


class CaptureProgressTracker:
    """Notice repeated capture cycles without blocking any camera or model action.

    Only receipts with an explicit model identity and revision can be compared.
    Other tools break the sequence, except for camera adjustments, which are
    part of a normal capture cycle. A new tracker is created for every turn.
    """

    def __init__(self):
        self.revision = None
        self.count = 0

    def observe(self, name, output):
        if name == "sketchup_set_camera":
            return False
        if name != "sketchup_export_view_image":
            self.revision = None
            self.count = 0
            return False
        evidence = output.get("visual_evidence") if output.get("success") is True else None
        camera = evidence.get("native_camera_after") if isinstance(evidence, dict) else None
        guid = camera.get("model_guid") if isinstance(camera, dict) else None
        revisions = evidence.get("model_revisions") if isinstance(evidence, dict) else None
        if (not isinstance(guid, str) or not guid or not isinstance(revisions, dict)
                or not revisions or any(not isinstance(k, str) or type(v) is not int or v < 0
                                        for k, v in revisions.items())):
            self.revision = None
            self.count = 0
            return False
        revision = (guid, json.dumps(revisions, sort_keys=True, separators=(",", ":")))
        self.count = self.count + 1 if revision == self.revision else 1
        self.revision = revision
        # Three captures permit normal viewpoint refinement; repeat the advisory
        # only after another three, without prohibiting further captures.
        return self.count >= 3 and self.count % 3 == 0


class ReviewCaptureTracker:
    """Advisory only for repeated verified six-view capture parameters.

    No cached images or quality decisions are returned. Only an exact match of
    native model identity, revision, six verified cameras, image sizes and the
    tool arguments can trigger a notice. Unknown tools conservatively reset the
    sequence so that a model mutation can never reuse an earlier observation.
    """

    VIEWS = frozenset({"front", "rear", "left", "right", "roof", "oblique"})
    SAFE_BETWEEN = frozenset({"sketchup_inspect_owned", "sketchup_get_model_context",
                              "workspace_read", "workspace_read_many", "workspace_search",
                              "workspace_write", "workspace_update_strategy"})

    def __init__(self):
        self.signature = None
        self.count = 0

    def observe(self, name, arguments, output):
        if name in self.SAFE_BETWEEN:
            return False
        if name != "sketchup_capture_review_views":
            self.signature = None
            self.count = 0
            return False
        signature = self._signature(arguments, output)
        if signature is None:
            self.signature = None
            self.count = 0
            return False
        self.count = self.count + 1 if signature == self.signature else 1
        self.signature = signature
        return self.count >= 2

    @classmethod
    def _signature(cls, arguments, output):
        if not isinstance(arguments, dict) or not isinstance(output, dict) or output.get("success") is not True:
            return None
        if not isinstance(arguments.get("script_id"), str) or not arguments["script_id"]:
            return None
        revisions = output.get("model_revisions")
        if (not isinstance(revisions, dict) or not revisions
                or any(not isinstance(k, str) or type(v) is not int or v < 0 for k, v in revisions.items())):
            return None
        items = output.get("contentItems")
        if not isinstance(items, list):
            return None
        text_items = [item.get("text") for item in items if isinstance(item, dict)
                      and item.get("type") in {"inputText", "text"} and isinstance(item.get("text"), str)]
        if len(text_items) != 1:
            return None
        try:
            receipt = json.loads(text_items[0])
        except (ValueError, TypeError):
            return None
        if not isinstance(receipt, dict) or receipt.get("model_revisions") != revisions:
            return None
        evidence, views = receipt.get("evidence"), receipt.get("views")
        if (not isinstance(evidence, dict) or set(evidence) != cls.VIEWS
                or not isinstance(views, dict) or set(views) != cls.VIEWS
                or output.get("views") != views):
            return None
        identity = None
        cameras = {}
        for view in sorted(cls.VIEWS):
            row = evidence[view]
            if not isinstance(row, dict) or row.get("canonical_view") != view or row.get("model_revisions") != revisions:
                return None
            if row.get("path") != views[view] or not isinstance(views[view], str) or not views[view]:
                return None
            before, after = row.get("native_camera_before"), row.get("native_camera_after")
            if not isinstance(before, dict) or not isinstance(after, dict) or row.get("camera_verified_during_capture") is not True:
                return None
            model_id = (after.get("model_path"), after.get("model_guid"))
            if (any(not isinstance(x, str) or not x for x in model_id)
                    or (before.get("model_path"), before.get("model_guid")) != model_id
                    or (identity is not None and identity != model_id)):
                return None
            identity = model_id
            camera = after.get("camera")
            if (not isinstance(camera, dict) or not camera or before.get("camera") != camera
                    or row.get("native_camera") != camera
                    or type(row.get("width")) is not int or row["width"] <= 0
                    or type(row.get("height")) is not int or row["height"] <= 0):
                return None
            cameras[view] = {"camera": camera, "width": row["width"], "height": row["height"]}
        try:
            return json.dumps({"arguments": arguments, "model": identity, "revisions": revisions,
                               "cameras": cameras}, sort_keys=True, ensure_ascii=False, allow_nan=False)
        except (ValueError, TypeError):
            return None
