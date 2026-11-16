from app.native_agent import _usage_breakdown_delta


def test_resumed_thread_counts_only_current_turn_cache_and_reasoning():
    first, baseline = _usage_breakdown_delta(
        {"cachedInputTokens": 95000, "cacheWriteInputTokens": 3000, "reasoningOutputTokens": 800},
        {"cachedInputTokens": 15000, "cacheWriteInputTokens": 0, "reasoningOutputTokens": 100}, None)
    assert first == {"cached_input_tokens": 15000, "cache_write_input_tokens": 0, "reasoning_output_tokens": 100}
    second, _ = _usage_breakdown_delta(
        {"cachedInputTokens": 125000, "cacheWriteInputTokens": 5000, "reasoningOutputTokens": 1100}, {}, baseline)
    assert second == {"cached_input_tokens": 45000, "cache_write_input_tokens": 2000, "reasoning_output_tokens": 400}


def test_missing_first_sample_cannot_be_reconstructed_as_zero_or_previous_thread_cost():
    result, baseline = _usage_breakdown_delta({}, {}, None)
    assert all(value is None for value in result.values())
    result, _ = _usage_breakdown_delta({"cachedInputTokens": 900000}, {"cachedInputTokens": 1000}, baseline)
    assert result["cached_input_tokens"] is None


def test_zero_is_reported_but_reset_and_invalid_counters_remain_unknown():
    result, baseline = _usage_breakdown_delta({"cached_input_tokens": 100}, {"cached_input_tokens": 0}, None)
    assert result["cached_input_tokens"] == 0
    result, _ = _usage_breakdown_delta({"cached_input_tokens": 50}, {}, baseline)
    assert result["cached_input_tokens"] is None
    result, _ = _usage_breakdown_delta({"cachedInputTokens": True, "reasoningOutputTokens": -1}, {}, None)
    assert all(value is None for value in result.values())
