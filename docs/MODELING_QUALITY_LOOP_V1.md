# Modeling Quality Loop v1

This is the next local acceptance task after the remote GitHub implementation.

## Why this change

The product can already generate and revise real editable SketchUp geometry, but the remaining failure pattern is quality confidence: an Agent can report success after a tool call even when the visible building still differs from the source. This milestone adopts two proven open-source patterns without replacing the existing DeepSeek + persistent Ruby + Kongxing stack:

- 3DCodeBench: bounded visual self-critique with an explicit NEEDS_FIX decision.
- dcc-mcp-sketchup: mutating work is not trusted until a post-write expected/actual read-back receipt exists.

The Builder remains the only writer. The critic is read-only. The deterministic verification receipt and real SketchUp views are higher-trust evidence than the Agent's prose.

## Codex local execution

1. Pull and inspect:
   git pull --ff-only
   git status --short
   git log -5 --oneline

2. Read AGENTS.md, this file, docs/CURRENT_TASK.md and docs/EXECUTION_GUARDRAILS.md.

3. Run:
   python -m pytest tests/test_modeling_quality.py tests/test_quality_lift.py tests/test_codex_parity.py tests/test_image_to_sketchup.py tests/test_owned_inspection.py tests/test_visual_revision.py
   python -m pytest
   powershell -ExecutionPolicy Bypass -File scripts/check.ps1

4. Fix any failing test without weakening the assertion. Keep the existing disposable-model boundary and current provider/bridge architecture.

5. Rebuild/restart the current K Studio source or desktop package as appropriate. Preserve local data and the saved DeepSeek key. Open SketchUp and Kongxing, then use a fresh dedicated blank project copy.

6. Run one fresh single-image reconstruction and one fresh whole-six-view reconstruction with the current DeepSeek route. Use ordinary user interaction: upload, clarify/plan, approve once, then let execution finish without manual geometry edits.

7. For every project-Ruby mutation, inspect write_verification. It must be verified=true and contain actual read-back checks for transaction status, root persistent ID and revision; where available, object count and mm bounds must also match.

8. After the primary build, require current front/rear/left/right/roof/oblique screenshots and update qa/visual_qa.md. The review must contain NEEDS_FIX, no more than three highest-impact mismatches, a KEEP list, current revision and deterministic receipt status.

9. If NEEDS_FIX is YES, perform only targeted edits against the named affected groups. Preserve KEEP geometry. Recapture current views and review again. Stop after at most two correction rounds in one turn. If blocking mismatches remain, report partial instead of forcing a false PASS.

10. Replay the integrated persistent baseline into a new blank disposable model. Verify the model family actually reappears, then save/download, reopen in native SketchUp, edit one guarded object, save again and re-read IDs/bounds.

11. Record actual provider/tool-call/token data, screenshots, verification receipts, remaining visual defects and any manual intervention under a sanitized test-results folder. Never commit API keys, private user files, personal paths or private SKP/DWG assets.

12. Update docs/HANDOFF.md and docs/CURRENT_TASK.md with the real result. Commit and push to origin/main. Confirm remote main contains the commit.

## Acceptance

Technical PASS requires green tests, valid writer receipts, working recovery/checkpoints, fresh-blank replay and native reopen/edit.

Visual PASS requires current final-revision six-view evidence, no unresolved high-impact mismatch, and no contradiction of source-defining silhouette, storeys/bays/opening counts, recess/projection depth or roof/parapet. Old screenshots and Agent prose do not count as final evidence.

If technical PASS succeeds but visual PASS fails, keep the milestone partial and continue improving the modeling method rather than adding unrelated features.
