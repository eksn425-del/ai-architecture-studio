from app.harness_parity_policy import decide_codex_baseline


def test_original_codex_is_not_run_while_saved_skp_delivery_is_unproven():
    result = decide_codex_baseline(delivery="FAIL", first_pass_source="FAIL",
        local_edit="FAIL", natural_ux="PASS")
    assert result["decision"] == "P0_DELIVERY_FIRST"
    assert result["original_codex"] == "NOT_RUN"
    pending = decide_codex_baseline(delivery="NOT_RUN", first_pass_source="PASS",
        local_edit="PASS", natural_ux="PASS")
    assert pending["decision"] == "P0_DELIVERY_FIRST"


def test_original_codex_is_skipped_when_k_studio_passes_every_real_gate():
    result = decide_codex_baseline(delivery="PASS", first_pass_source="PASS",
        local_edit="PASS", natural_ux="PASS")
    assert result["decision"] == "KEEP_K_STUDIO"
    assert result["original_codex"] == "NOT_NEEDED"


def test_original_codex_runs_only_after_reliable_delivery_and_site_quality_fail():
    result = decide_codex_baseline(delivery="PASS", first_pass_source="FAIL",
        local_edit="PASS", natural_ux="PASS")
    assert result["decision"] == "RUN_SAME_SOURCE_NATIVE_CODEX_CONTROL"
    assert result["original_codex"] == "CONDITIONAL"


def test_capacity_outage_never_counts_as_bad_agent_quality():
    result = decide_codex_baseline(delivery="PASS", first_pass_source="FAIL",
        local_edit="BLOCKED", natural_ux="PASS", model_capacity_available=False)
    assert result["decision"] == "CONTINUE_SITE_ONCE_AVAILABLE"
    assert result["original_codex"] == "NOT_RUN"
