"""The website Sol Low proxy is real Codex inference, never fake API credit."""
from app.modeling_test_profile import assess_sol_low_surrogate


def test_surrogate_requires_actual_proven_model_identity():
    args = dict(route_provider="codex-app-server", requested_model="gpt-6.1-sol", requested_effort="low")
    before = assess_sol_low_surrogate(**args)
    assert before["status"] == "CONFIGURED_NOT_EXECUTED"
    assert not before["real_inference_if_executed"]
    after = assess_sol_low_surrogate(**args, actual_model="gpt-6.1-sol", actual_effort="low")
    assert after["status"] == "REAL_SURROGATE_IDENTITY_VERIFIED"
    assert after["real_inference_if_executed"]
    assert after["paid_gateway_requests_proven"] is False
    assert after["official_or_bai_responses_parity_proven"] is False


def test_selection_never_silently_overrides_user_requested_model_or_effort():
    for provider,model,effort in [
        ("codex-app-server","gpt-6-astra","high"),
        ("codex-app-server","gpt-6.1-sol","high"),
        ("managed-responses","gpt-6.1-sol","low"),
    ]:
        outcome = assess_sol_low_surrogate(route_provider=provider, requested_model=model,
                 requested_effort=effort, actual_model=model, actual_effort=effort)
        assert outcome["status"] == "NOT_THIS_TEST_PROFILE"
        assert outcome["requested_model"] == model
        assert outcome["does_not_override_any_selected_model"]
    wrong = assess_sol_low_surrogate(route_provider="codex-app-server",
          requested_model="gpt-6.1-sol",requested_effort="low",
          actual_model="gpt-6-luna",actual_effort="max")
    assert wrong["status"] == "MODEL_IDENTITY_MISMATCH"
