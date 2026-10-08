from app.modeling_quality import (
    CANONICAL_REVIEW_VIEWS,
    build_visual_critic_prompt,
    parse_visual_critique_response,
    require_post_write_verification,
)


def test_visual_critic_prompt_is_bounded_and_read_only():
    prompt = build_visual_critic_prompt(["source.png"], CANONICAL_REVIEW_VIEWS)
    assert "at most 3" in prompt
    assert "Do not write Ruby" in prompt
    assert "NEEDS_FIX: YES|NO" in prompt
    for view in CANONICAL_REVIEW_VIEWS:
        assert view in prompt


def test_visual_critique_parser_keeps_top_three_and_keep_list():
    result = parse_visual_critique_response(
        """NEEDS_FIX: YES
<assessment>Facade is close but three large mismatches remain.</assessment>
<issue priority="2" view="roof">problem: roof grid is too coarse
action: refine the current roof group only</issue>
<issue priority="1" view="front">problem: upper opening count is wrong
action: patch the named opening group</issue>
<issue priority="4" view="left">problem: tiny trim mismatch
action: defer</issue>
<issue priority="3" view="rear">problem: rear recess is too shallow
action: deepen only the rear recess</issue>
<keep>
overall massing
balcony slab positions
</keep>"""
    )
    assert result.needs_fix is True
    assert result.malformed is False
    assert [issue.priority for issue in result.issues] == [1, 2, 3]
    assert result.issues[0].view == "front"
    assert result.keep == ("overall massing", "balcony slab positions")


def test_visual_critique_done_does_not_require_issues():
    result = parse_visual_critique_response(
        "NEEDS_FIX: NO\n<assessment>No blocking mismatch remains.</assessment>\n<keep>roof\nopenings</keep>"
    )
    assert result.needs_fix is False
    assert result.malformed is False
    assert not result.issues


def test_post_write_verification_returns_expected_actual_receipt():
    transaction = {
        "status": "committed",
        "owned_after": {
            "objects_total": 4,
            "bounds_mm": {"min": [0, 0, 0], "max": [12000, 8000, 6800]},
        },
    }
    readback = {
        "persistent_id": 701,
        "revision": 3,
        "objects_total": 4,
        "bounds_mm": {"min": [0.0, 0.0, 0.0], "max": [12000.005, 8000.0, 6800.0]},
    }
    receipt = require_post_write_verification(
        transaction, readback, expected_root_pid=701, expected_revision=3
    )
    assert receipt["verified"] is True
    assert all("expected" in check and "actual" in check for check in receipt["checks"])


def test_post_write_verification_rejects_silent_mismatch():
    transaction = {"status": "committed", "owned_after": {"objects_total": 4}}
    readback = {"persistent_id": 701, "revision": 3, "objects_total": 3}
    try:
        require_post_write_verification(
            transaction, readback, expected_root_pid=701, expected_revision=3
        )
    except ValueError as error:
        assert "objects_total" in str(error)
    else:
        raise AssertionError("A mismatched post-write readback must fail.")
