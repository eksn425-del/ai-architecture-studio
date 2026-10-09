import json

from app.context_compaction import (
    build_reconstruction_checkpoint,
    compact_active_reconstruction_context,
)


def _workspace(tmp_path):
    root = tmp_path / "project"
    notes = root / "runtime" / "agent_workspace" / "notes"
    qa = root / "runtime" / "agent_workspace" / "qa"
    notes.mkdir(parents=True)
    qa.mkdir(parents=True)
    return root, notes, qa


def test_checkpoint_waits_until_structured_schedule_has_signal(tmp_path):
    root, notes, _ = _workspace(tmp_path)
    (notes / "reconstruction_card.md").write_text("approved card", encoding="utf-8")
    (notes / "facade_schedule.json").write_text(json.dumps({
        "schema_version": 1,
        "dimensions_mm": {"overall_width": None},
        "views": {"front": {"provenance": "pending", "opening_count": None}},
        "roof": {"provenance": "pending", "type": "pending", "parapet": "pending"},
        "user_confirmed": [],
        "inferred": [],
    }), encoding="utf-8")
    assert build_reconstruction_checkpoint(root, {}) == ""


def test_checkpoint_contains_durable_card_schedule_review_and_writer_state(tmp_path):
    root, notes, qa = _workspace(tmp_path)
    (notes / "reconstruction_card.md").write_text("rear openings confirmed by user", encoding="utf-8")
    (notes / "facade_schedule.json").write_text(json.dumps({
        "schema_version": 1,
        "dimensions_mm": {"overall_width": 10000},
        "views": {"rear": {"provenance": "user_confirmed", "opening_count": 3}},
        "roof": {"provenance": "observed", "type": "flat", "parapet": "thin"},
        "user_confirmed": ["rear opening_count=3"],
        "inferred": [],
    }), encoding="utf-8")
    (qa / "visual_review.json").write_text(json.dumps({
        "needs_fix": True,
        "issues": [{"view": "roof", "problem": "parapet too heavy"}],
    }), encoding="utf-8")
    (notes / "construction_strategy.json").write_text(json.dumps({
        "schema_version": 1,
        "current_stage": "representative_module",
        "stage_order": ["primary_form", "representative_module", "replication", "variants", "finish"],
        "shared_parameters": {
            "floor_height": {"value": 3200, "units": "mm", "provenance": "user_confirmed", "source": "user"}
        },
        "systems": [{
            "id": "front-openings",
            "stage": "primary_form",
            "role": "opening_system",
            "method": "continuous_wall_with_openings",
            "status": "built",
            "depends_on": ["floor_height"],
            "target_paths": [["SHELL", "FRONT_WALL"]],
            "verification_views": ["front", "oblique"],
            "notes": [],
        }],
        "notes": [],
    }), encoding="utf-8")
    checkpoint = build_reconstruction_checkpoint(root, {
        "villa": {
            "revision": 4,
            "root_pid": 701,
            "last_verification": {"verified": True},
            "last_screenshot": "outputs/renders/ruby-villa-r4.png",
        }
    })
    assert "ACTIVE RECONSTRUCTION CHECKPOINT" in checkpoint
    assert "rear openings confirmed by user" in checkpoint
    assert "rear opening_count=3" in checkpoint
    assert '"revision":4' in checkpoint
    assert "parapet too heavy" in checkpoint
    assert "CONSTRUCTION_STRATEGY:" in checkpoint
    assert "continuous_wall_with_openings" in checkpoint


def test_compaction_drops_only_completed_history_and_preserves_current_turn():
    checkpoint = "ACTIVE RECONSTRUCTION CHECKPOINT\ncurrent truth"
    messages = [
        {"role": "system", "content": "builder rules"},
        {"role": "user", "content": "old request " + "x" * 60000},
        {"role": "assistant", "content": "old answer " + "y" * 60000},
        {"role": "user", "content": [{"type": "text", "text": "current request"}, {"type": "image_url", "image_url": {"url": "data:image/png;base64,current"}}]},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "1", "function": {"name": "workspace_read", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "1", "content": "current tool result"},
        {"role": "user", "content": "HOST QUALITY GATE: capture six views"},
        {"role": "user", "content": [{"type": "text", "text": "Visual readback from SketchUp tool capture."}, {"type": "image_url", "image_url": {"url": "data:image/png;base64,view"}}]},
    ]
    compacted, meta = compact_active_reconstruction_context(messages, checkpoint)
    assert meta["compacted"] is True
    assert meta["dropped_messages"] == 2
    assert len(compacted) == 6
    assert "ACTIVE RECONSTRUCTION CHECKPOINT" in compacted[0]["content"]
    assert compacted[1]["content"][0]["text"] == "current request"
    assert compacted[-1]["content"][0]["text"].startswith("Visual readback")
    assert meta["after_chars"] < meta["before_chars"]


def test_compaction_does_not_run_without_large_completed_history():
    messages = [
        {"role": "system", "content": "rules"},
        {"role": "user", "content": "old"},
        {"role": "assistant", "content": "ok"},
        {"role": "user", "content": "current"},
    ]
    compacted, meta = compact_active_reconstruction_context(
        messages,
        "ACTIVE RECONSTRUCTION CHECKPOINT\ntruth",
    )
    assert compacted == messages
    assert meta["compacted"] is False


def test_compaction_never_expands_request_with_an_oversized_checkpoint():
    messages = [
        {"role": "system", "content": "rules"},
        {"role": "user", "content": "old " + "x" * 2000},
        {"role": "assistant", "content": "done"},
        {"role": "user", "content": "current"},
    ]
    result, meta = compact_active_reconstruction_context(
        messages, "ACTIVE RECONSTRUCTION CHECKPOINT\n" + "z" * 10000,
        threshold_chars=1000,
    )
    assert result == messages
    assert meta["compacted"] is False
    assert meta["after_chars"] == meta["before_chars"]



def test_active_visual_filter_keeps_newest_source_copy_for_compaction():
    from app.litellm_runtime import _current_visual_context

    source_url = "data:image/png;base64,same-source"
    messages = [
        {"role": "system", "content": "rules"},
        {"role": "user", "content": [
            {"type": "text", "text": "old request " + "x" * 100000},
            {"type": "text", "text": "Source image 1: inputs/reference/source.png. Verify this view using visible landmarks."},
            {"type": "image_url", "image_url": {"url": source_url}},
        ]},
        {"role": "assistant", "content": "old reply"},
        {"role": "user", "content": [
            {"type": "text", "text": "current request"},
            {"type": "text", "text": "Source image 1: inputs/reference/source.png. Verify this view using visible landmarks."},
            {"type": "image_url", "image_url": {"url": source_url}},
        ]},
    ]
    filtered = _current_visual_context(messages)
    old_images = [
        block for block in filtered[1]["content"]
        if isinstance(block, dict) and block.get("type") == "image_url"
    ]
    current_images = [
        block for block in filtered[-1]["content"]
        if isinstance(block, dict) and block.get("type") == "image_url"
    ]
    assert old_images == []
    assert len(current_images) == 1

    compacted, meta = compact_active_reconstruction_context(
        filtered,
        "ACTIVE RECONSTRUCTION CHECKPOINT\ncurrent source facts",
        threshold_chars=1000,
    )
    assert meta["compacted"] is True
    assert any(
        isinstance(block, dict) and block.get("type") == "image_url"
        for block in compacted[-1]["content"]
    )



def test_checkpoint_rejects_invalid_facade_schedule_contract(tmp_path):
    root, notes, _ = _workspace(tmp_path)
    (notes / "reconstruction_card.md").write_text("approved card", encoding="utf-8")
    (notes / "facade_schedule.json").write_text(json.dumps({
        "schema_version": 1,
        "views": {
            "front": {
                "provenance": "made_up",
                "opening_count": 4,
                "door_count": 1,
                "features": [],
                "notes": [],
            }
        },
    }), encoding="utf-8")
    assert build_reconstruction_checkpoint(root, {}) == ""


def test_checkpoint_preserves_reconstruction_evidence_mode(tmp_path):
    from app.reconstruction_evidence import default_reconstruction_evidence

    root, notes, _ = _workspace(tmp_path)
    (notes / "reconstruction_card.md").write_text("single-view approved", encoding="utf-8")
    (notes / "facade_schedule.json").write_text(json.dumps({
        "schema_version": 1,
        "views": {"front": {"provenance": "observed", "opening_count": 4}},
        "user_confirmed": [],
        "inferred": ["rear inferred"],
    }), encoding="utf-8")
    evidence = default_reconstruction_evidence()
    evidence["fidelity_mode"] = "single_view_inference"
    evidence["primary_source"] = "inputs/reference/front.png"
    evidence["sources"] = [{
        "path": "inputs/reference/front.png",
        "kind": "exterior_image",
        "provenance": "observed",
        "role": "primary",
    }]
    evidence["exterior_views"]["front"] = {
        "provenance": "observed",
        "source_refs": ["inputs/reference/front.png"],
        "notes": [],
    }
    (notes / "reconstruction_evidence.json").write_text(json.dumps(evidence), encoding="utf-8")

    checkpoint = build_reconstruction_checkpoint(root, {})
    assert "RECONSTRUCTION_EVIDENCE:" in checkpoint
    assert "single_view_inference" in checkpoint
    assert "inputs/reference/front.png" in checkpoint
