# Publication regression — 2026-11-03

Full Python suite: **1523 passed, 50 failed, 19 skipped**. Windows local environment; not a green full-suite result. Separate targeted candidate checks: **42 passed**. Full run took 95.68s. No real paid inference was requested by this test command.

Failure classifications describe observed symptoms, not proven root causes or pre-existing/new regression attribution.

- Unresolved contract / fixture assertion: 20
- Windows symlink privilege: 13
- Blender executable detection: 8
- Encoding: 9

## Unresolved tests

- `tests.test_api_intent_and_strategy::test_api_intent_honors_same_durable_budget_without_dispatch` — Unresolved contract / fixture assertion
- `tests.test_api_intent_and_strategy::test_transport_diagnostics_distinguish_connection_and_stream_stall[failure0-connecting]` — Unresolved contract / fixture assertion
- `tests.test_blender_api_readback::test_rejects_symlinks[image]` — Windows symlink privilege
- `tests.test_blender_api_readback::test_rejects_symlinks[scene]` — Windows symlink privilege
- `tests.test_blender_api_readback::test_rejects_symlinks[directory]` — Windows symlink privilege
- `tests.test_blender_backend::test_timeout_preserves_last_committed_state` — Blender executable detection
- `tests.test_blender_backend::test_symlink_workspace_rejected` — Windows symlink privilege
- `tests.test_blender_backend::test_plan_failure_invalidates_old_plan_and_reconnect_is_idempotent` — Unresolved contract / fixture assertion
- `tests.test_blender_backend::test_ui_blender_is_explicit_and_does_not_open_su_dialog` — Encoding
- `tests.test_blender_backend::test_readonly_turn_cannot_dispatch_blender_write` — Blender executable detection
- `tests.test_blender_backend::test_failed_provider_after_commit_recovers_native_artifact` — Blender executable detection
- `tests.test_blender_backend::test_real_mesh_material_edit_preserves_roof` — Blender executable detection
- `tests.test_blender_backend::test_blender_progress_reports_committed_geometry_without_claiming_quality` — Unresolved contract / fixture assertion
- `tests.test_blender_backend::test_safe_named_delete_preserves_other_objects_and_history` — Blender executable detection
- `tests.test_blender_component_integration::test_tool_signature_and_policy_expose_inference_limits` — Encoding
- `tests.test_blender_edit_contract::test_bad_revision_and_symlink_rejected` — Windows symlink privilege
- `tests.test_blender_wire_context::test_backend_default_detailed_and_symlink` — Windows symlink privilege
- `tests.test_contextual_turn::test_external_plan_symlink_rejected_before_interpreter[False]` — Windows symlink privilege
- `tests.test_contextual_turn::test_external_plan_symlink_rejected_before_interpreter[True]` — Windows symlink privilege
- `tests.test_conversation_receipts::test_api_duplicate_replay_does_not_corrupt_receipt` — Encoding
- `tests.test_imported_research::test_upload_reaches_actual_conversation_provider_without_write_tools` — Unresolved contract / fixture assertion
- `tests.test_imported_research::test_reject_link` — Windows symlink privilege
- `tests.test_imported_research::test_bad_note_blocks_provider_and_unknown_image_role_still_blocks` — Unresolved contract / fixture assertion
- `tests.test_modeling_quality::test_litellm_host_requires_visual_review_before_final_reply` — Unresolved contract / fixture assertion
- `tests.test_native_terminal_host::test_blender_host_interrupted_preserves_real_revision_truth[False]` — Unresolved contract / fixture assertion
- `tests.test_native_terminal_host::test_blender_host_interrupted_preserves_real_revision_truth[True]` — Unresolved contract / fixture assertion
- `tests.test_quality_lift::test_committed_revision_survives_interrupted_capture` — Unresolved contract / fixture assertion
- `tests.test_quality_lift::test_capture_guid_refresh_keeps_next_owned_inspection_working` — Unresolved contract / fixture assertion
- `tests.test_quality_lift::test_capture_refresh_still_rejects_a_different_document` — Unresolved contract / fixture assertion
- `tests.test_quality_lift::test_same_project_script_revisions_reuse_model_root_and_return_screenshots` — Unresolved contract / fixture assertion
- `tests.test_reconstruction_integration::test_first_api_plan_interruption_resumes_written_card_and_tool_history` — Unresolved contract / fixture assertion
- `tests.test_reconstruction_integration::test_litellm_reconstruction_retains_history_and_uploaded_evidence` — Unresolved contract / fixture assertion
- `tests.test_research_tool_context::test_no_policy_preserves_toolless_planning` — Blender executable detection
- `tests.test_research_tool_context::test_explicit_policy_exposes_only_research_and_untrusted_output_cannot_grant_write` — Blender executable detection
- `tests.test_research_tool_context::test_policy_and_receipt_symlinks_are_rejected[policy]` — Windows symlink privilege
- `tests.test_research_tool_context::test_policy_and_receipt_symlinks_are_rejected[state]` — Windows symlink privilege
- `tests.test_research_tool_context::test_policy_and_receipt_symlinks_are_rejected[receipt]` — Windows symlink privilege
- `tests.test_research_tool_context::test_policy_and_receipt_symlinks_are_rejected[runtime]` — Windows symlink privilege
- `tests.test_research_tool_context::test_native_readonly_registration_filters_every_nonresearch_tool[False-False]` — Encoding
- `tests.test_research_tool_context::test_native_readonly_registration_filters_every_nonresearch_tool[True-False]` — Encoding
- `tests.test_research_tool_context::test_native_readonly_registration_filters_every_nonresearch_tool[False-True]` — Encoding
- `tests.test_research_tool_context::test_native_readonly_registration_filters_every_nonresearch_tool[True-True]` — Encoding
- `tests.test_responses_runtime::test_full_shared_harness_tool_error_resume_and_project_context` — Unresolved contract / fixture assertion
- `tests.test_responses_runtime::test_dedicated_critic_has_images_and_no_writer_tools` — Unresolved contract / fixture assertion
- `tests.test_run_usage_audit::test_fresh_run_records_code_identity_and_end_status` — Unresolved contract / fixture assertion
- `tests.test_shared_review_contract::test_native_and_api_use_identical_shared_context` — Unresolved contract / fixture assertion
- `tests.test_shared_review_contract::test_invalid_scope_never_leaks_stale_plan_text_into_review_prompt` — Encoding
- `tests.test_stage_quality::test_real_blender_budget_identical_no_progress_and_retained_candidate` — Blender executable detection
- `tests.test_su_connection_recovery::test_offline_bridge_does_not_consume_approval` — Encoding
- `tests.test_ui_contextual_composer::test_contextual_composer_ui_contracts` — Unresolved contract / fixture assertion

Raw logs contain machine paths and remain local. Public release remains blocked pending diagnosis and rerun. The desktop/SU24 live loop results are documented independently in the release notes.
