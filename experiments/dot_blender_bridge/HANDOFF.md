# Round handoff: supervised Blender backend experiment

Updated: 2026-10-16 UTC. Read this and README.md before continuing.

## Goal and outcome

Test whether K Studio's real tool pipeline can control Blender in an independent Linux environment without requiring the author's SketchUp desktop. Preserve the product's parser/dispatch where practical; distinguish the adapted backend and supervised decisions from the unported production Agent.

Completed: a six-part synthetic pavilion was planned, built, inspected, rendered, locally edited (roof only), saved and reopened. Slab and four columns were preserved exactly. This supports bounded supervised box-assembly modeling. It does not establish full website/Agent replacement, architectural reconstruction quality or structural safety.

## Repository checkpoints and publication state

- Repository: `eksn425-del/ai-architecture-studio` (visibility verified public).
- Base: `59fa229b5ae8873d05d42aafadfbc61c7af7ec41`.
- Tested implementation/evidence commit: `ec80814f5ed0a934c23b19f5e522b27e837997ae`.
- Isolated branch: `experiment/dot-blender-bridge-20261016`.
- This handoff is a documentation-only successor to the tested implementation. Obtain its exact local commit with `git log -1 --format=%H -- experiments/dot_blender_bridge/HANDOFF.md`; a file cannot contain its own Git commit hash.
- Explicit approval to publish this experiment code, test records and pavilion screenshots to this public repository branch was received on 2026-10-16. The initial attempt was denied before that approval. Publication is pending the authorized retry and remote SHA verification.
- Retry the same branch push after the explicit approval; verify its remote SHA before reporting publication. Never merge into main or alter active SU work as part of this experiment.

## Changes and evidence map

All new files are under `experiments/dot_blender_bridge/`; production files are unchanged.

- `backend_contract.py`: seven bounded tool schemas and explicit adapted instructions.
- `server.py`: isolated stdio MCP, validation, edit allowlist, lock, atomic candidate commit.
- `blender_job.py`: native Blender geometry, identities/digests, KEEP, save/reopen and six cameras.
- `interactive_seam.py`: manual decision exchange through existing K Studio schema/parser/dispatch.
- `replay_supervised.py`: replays saved decisions; it does not generate new decisions.
- `run_checks.py`: 14 transport/integration checks.
- `verify_pavilion.py`: 16 final native/evidence checks.
- `check_guards.py`: stale digest, prohibited edit and partial-failure rollback checks.
- `evidence/`: sanitized JSON results, logs, original failed render log, six final images, before image and SHA256 inventory.

The assistant inspected actual before/after oblique images and observed the enlarged overhang. Test assertions do not substitute for source-matched independent visual review.

## Environment and recovery procedure

Verified runtime: Linux, Python 3.12.14, Blender 4.3.2 (`blender` on PATH), Pillow 12.3.0. Rendering uses CPU Cycles, eight samples, 480x360, denoising disabled. No network listener, model service, API credential or paid inference is required. The MCP transport is the repository's existing Content-Length stdio contract.

On a replacement environment, obtain this experiment from an approved persisted branch or the delivered experiment archive. If it has not been published, GitHub alone cannot recover the local successor commit. Restore the experiment folder onto a checkout of the exact base above; do not overwrite a working production checkout.

Provision Python 3.12 and Blender 4.3.2 from their official sources. Create an isolated Python virtual environment, activate it and install `Pillow==12.3.0` from PyPI. This is the minimum dependency set observed for this bounded pipeline; fresh-host provisioning was not itself performed in this round. Do not install or configure a paid model provider just to run these tests.

From the repository root, with the virtual environment active:

    python --version
    blender --version
    python -c 'import PIL; print(PIL.__version__)'
    python experiments/dot_blender_bridge/run_checks.py /tmp/new-transport
    python experiments/dot_blender_bridge/replay_supervised.py /tmp/new-pavilion
    python experiments/dot_blender_bridge/verify_pavilion.py /tmp/new-pavilion
    python experiments/dot_blender_bridge/check_guards.py /tmp/new-pavilion

Use new output directories so earlier results survive. The actual model will be `/tmp/new-pavilion/scene/scene.blend`; six PNGs are beside it. The before-edit scene is retained separately. Reopen/render checks invoke real Blender. Generated UUIDs differ across fresh runs, so compare within-run identity/KEEP and expected dimensions, not a fixed cross-run mesh digest.

For new decisions, use `interactive_seam.py export <run-directory> <brief>` and `consume <run-directory> <response.json>`. Inspect the exported schema; responses require its exact request SHA and standard tool-call envelope. Configure `DOT_BLENDER_ALLOWED_EDIT_NAMES` in the isolated connector configuration before edits. An assistant response cannot expand that scope. Never publish raw request/response history, since it can contain project context and user text.

## Actual results and failure accounting

The tested implementation passed 14 integration checks, 16 pavilion checks and three negative controls. A separate fresh replay also passed the pavilion and negative-control checks. See JSON files for individual assertions rather than interpreting these counts as a quality benchmark.

Original before-edit geometry SHA: `0472a999d7d82d1022b847b0d6f4590b00e8f0593b1464543cac527f40900ce2`.
Original after-edit geometry SHA: `f42a72f019f57db0f3e5989a06b644a16535fbf1efdbbae728b65e5fb7e0cec3`.
Roof final target dimensions: 6.8 x 4.8 x 0.25 metres; centre (0,0,3.125). Expected world bounds: x +/-3.4, y +/-2.4, z 3.0 to 3.25, tolerance 0.000001 metre. Observed float32 differences are retained in the result JSON. Five other parts keep exact snapshots and IDs.

Initial rendering failed because this Blender build lacked OpenImageDenoise. Denoising was explicitly disabled and rendering rerun; the initial failure log remains separate. Intentional negative-control errors are expected rejections, and saved scene bytes plus reopened geometry remain unchanged after each.

## Remaining work and next safe step

1. Settle public branch publication approval and verify the resulting remote commit if approved. Local files alone are not durable GitHub handoff.
2. Before extending functionality, reproduce the existing tests in a fresh environment and retain the new logs separately.
3. Add Blender-native complex geometry, nested identity/protection and rollback contracts with bounded tests; current backend supports axis-aligned boxes only.
4. Port production backend selection/prompt/tool lifecycle, source-matched QA, independent Critic and delivery. Existing reconstruction profile exposes only health/inspection for Blender; full discovery plus explicit adaptation is used here.
5. Test actual website tasks and a permitted source reference. Decide on a supported model runtime or deliberately supervised relay; this chat is not an HTTP inference endpoint.

No full production end-to-end run, independent Critic port, source reconstruction, native SketchUp compatibility or structural certification has been completed. Do not label any of these ready based on the current pavilion.

## Software-specific branch index

- SketchUp / SU: existing `main` as observed at the base commit. Its existing code, models and tests belong to the SU line. This experiment does not rename, move or reorganize that active work.
- Blender: `experiment/dot-blender-bridge-20261016`. This independent line owns its Blender adapter, reproducible synthetic model recipe, Blender-specific tests/results/images and project decisions under `experiments/dot_blender_bridge/`.
- Future modeling software: use a separate explicitly named branch and its own code/model/test/decision record. Identify the software in each handoff so searching one branch does not confuse results from another backend.

A branch inherits repository history; inherited SU files are not evidence that they were modified or tested by the Blender round. Native Blender models are generated by this branch's reproducible recipe; no private project model is included.

## Publication transport note

The approved Git push failed because the checkout has no Git credentials. The connected GitHub app has verified write permission and can publish a snapshot via Git object APIs. Local implementation/handoff commit IDs above remain provenance; the connector-created remote commit has a different identity and is based on the same original base. Its commit message records the local checkpoint. The remote branch HEAD, once verified, is the durable recovery reference. No Git credentials are extracted or created.
