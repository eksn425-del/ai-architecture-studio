# Remote Refactor Handoff — 2026-09-30

## Status

ChatGPT resumed repository ownership after the user paused the previous Codex run.

This remote round intentionally changed product logic before the next local Codex execution. It does **not** claim Windows/SketchUp runtime acceptance.

## Why this refactor was necessary

The user provided additional Building-Xuezhang teaching evidence showing a stronger reconstruction workflow than our earlier simple `plan -> approve -> execute` design:

> inspect image -> ask high-impact questions -> user answers -> AI proposes estimated dimensions / assumptions -> user confirms -> modeling begins -> continued edits reuse the same model.

This matches the broader product lesson from direct Codex, Pylon, ADAI, Supex and Stultus: quality comes from the task method + persistent Agent harness + software bridge, not from exposing more tools or selecting a premium model.

## Remote code changes

### `app/models.py`

- reconstruction lifecycle is now:
  `idle -> clarifying -> planned -> building`;
- added `clarification_rounds`;
- `ConversationRequest.agent_action` now supports:
  `auto | clarify | plan | execute`.

### `app/reconstruction_runtime.py`

Deterministic host policy now resolves:

- idle + auto -> clarify;
- clarifying + auto -> plan;
- planned/building + auto -> execute;
- explicit execute before planned/building -> reject.

The policy exposes a user gate:

- clarification;
- approval;
- none.

### `app/image_to_sketchup_skill.py`

The reconstruction Skill is now explicitly:

> inspect -> clarify -> parameterize -> approve -> persistent Ruby -> execute -> inspect -> revise.

Clarification is limited to high-impact reconstruction questions. Unknown exact dimensions do not block progress; the Agent should propose a coherent estimated modeling baseline.

### `app/codex_parity.py`

`notes/reconstruction_card.md` is now a parameter card containing:

- intended use/views;
- included/excluded scope;
- scale anchors;
- unseen-geometry policy;
- visible detail target;
- KNOWN / ESTIMATED / ASSUMED dimensions;
- form/voids;
- facade depth;
- repeated modules;
- material zones;
- persistent build plan;
- approval status;
- current visual mismatches.

### `app/workflow_context.py`

Added separate developer/prompt behavior for:

- CLARIFICATION turn;
- PARAMETER/PLAN turn;
- EXECUTION turn.

Clarification/planning explicitly withhold SketchUp geometry edits.

### tests

`tests/test_reconstruction_runtime.py` and `tests/test_image_to_sketchup.py` now specify the new clarification-first contract.

These integration tests may intentionally fail until `main.py`, runtimes and UI are locally wired to the new state machine. Codex should fix implementation, not weaken the tests back to the old flow.

## Repository/process guardrails added

Created `docs/EXECUTION_GUARDRAILS.md` and updated `AGENTS.md`.

Key rules:

- user-visible quality is the milestone outcome;
- connectivity/tool count/white-box fixtures are prerequisites only;
- copy/adopt proven patterns before generalizing;
- do not rebuild a weaker Codex;
- do not use Astra to hide a harness problem;
- do not interrupt the user for non-critical engineering probes;
- record non-critical external checks as `pending_external` and continue;
- no taskbook/site/render/PPT expansion before Image -> SketchUp parity.

## Next local work

Use `docs/CURRENT_TASK.md` as the authoritative task.

The main local responsibilities are:

1. wire the new state machine into `main.py`;
2. wire action/tool-profile/reference scope into Codex App Server and LiteLLM;
3. add clarification/parameter/approval UI;
4. keep persistent workspace Ruby primary;
5. optionally inspect Building-Xuezhang desktop/SU plugin behavior if locally available;
6. run the real same-image Sol Low direct-Codex parity benchmark.

## Non-blocking policy

The standalone workspace-write probe is **not** a reason to pause and ask the user during normal implementation.

If Codex cannot run it from a suitable shell itself, record:

`workspace_write_probe: pending_external`

Continue all non-dependent work. Surface it to the user only if real website execution is genuinely blocked by inability to write the persistent workspace.

## Model policy

- parity baseline: GPT-6 Sol Low;
- no Astra call;
- no silent reasoning/model upgrade;
- if website + Sol Low remains much worse than direct Codex + Sol Low, investigate missing harness capability before changing models.
