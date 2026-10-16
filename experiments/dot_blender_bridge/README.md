# Supervised K Studio tool pipeline → MCP → Blender experiment

Base commit: `59fa229b5ae8873d05d42aafadfbc61c7af7ec41`. Date: 2026-10-16.
Isolated branch: `experiment/dot-blender-bridge-20261016`.
No production `app/` files, existing SU project, main branch or original reference assets changed.

## What actually works

The original K Studio `AgentToolSurface.prepare/dynamic_tools/dispatch`, `ConfiguredSketchUpMCP`, provider tool-schema converter and tool-call parser drive a new, bounded Blender backend on Linux, Blender 4.3.2.

A supervised chat-driven test completed **plan → create → inspect → render → local edit → KEEP → save/reopen → six-view render**. The assistant chose a synthetic 6×4 m open pavilion, examined its actual image, then chose to enlarge only the roof to 6.8×4.8 m. Four columns and slab were identical after editing, with stable identities. The roof has 0.4 m overhang beyond the slab on each side. Real native world bounds agree within 0.000001 m; float32 deviations are retained.

- 14 transport/integration checks pass.
- 16 native final checks pass, including five unchanged protected objects, IDs, revision, bounds, six PNGs and render→reopen consistency.
- Three negative controls pass: stale digest, disallowed column edit, and partially executed failed creation all leave saved file bytes and native geometry unchanged.
- Parent assistant inspected actual before/after oblique images. Larger roof overhang is visibly present. Low-sample render noise remains; no rendering-quality or structural certification claim.

See [supervised results](evidence/supervised_results.json), [guard tests](evidence/guard_checks.json), [before image](evidence/views/before-oblique.png), [after image](evidence/views/oblique.png). Six views are under `evidence/views/`.

## Exact boundary

This is an **explicit adapted Blender tool pipeline with supervised assistant decisions**, not the unchanged production SU Agent, not a live model API, and not a website end-to-end run. A file relay carries the assistant-selected tool calls through the actual product parser and dispatcher. No external model call or credentials are used.

The backend currently creates/edits named axis-aligned box assemblies only. It has host-owned edit scope, optimistic geometry digest checks, stable IDs, protection of every non-target mesh and atomic candidate-file commit. These bounded checks do not reproduce the entire production Ruby writer, hierarchical KEEP semantics or independent Critic. Complex mesh topology, source-image reconstruction, product UI integration, arbitrary script execution, `.skp` delivery and automatic model service remain unsupported/unverified.

The original product prompts are exported unchanged for comparison, while the **explicitly adapted** instructions in `backend_contract.py` control this Blender experiment. No silent Ruby→Python substitution or fake provider response is used.

## Reproduce

Prerequisites: pinned repository base, Python with Pillow, Blender4.3.2 on PATH. No external MCP library is needed. From repository root:

    python experiments/dot_blender_bridge/run_checks.py /tmp/fresh-transport
    python experiments/dot_blender_bridge/replay_supervised.py /tmp/fresh-pavilion
    python experiments/dot_blender_bridge/verify_pavilion.py /tmp/fresh-pavilion
    python experiments/dot_blender_bridge/check_guards.py /tmp/fresh-pavilion

Use fresh directories. Replay reproduces **saved assistant decisions**, not new inference. It produces real `.blend` files, screenshots, native evidence and logs. Generated runtime state stays outside the source checkout. The native model is reproducible locally rather than embedding environment-specific binary metadata in this public experiment.

For a new supervised decision, `interactive_seam.py export <directory> <prompt>` writes the actual tool schema and adapted instructions; `consume <directory> <response.json>` parses and executes the reply via product code. Host-approved edit names are in the isolated connector's environment; they are not granted by model arguments.

No global configuration, public listener or persistent credentials are created. The MCP stdio framing matches this repository's existing Content-Length transport. Every Blender operation starts in factory startup and opens only its disposable scene. Failed Blender Python exceptions are detected even when process exit status is0. A file lock prevents concurrent writes. The read-only inspector does not save.

## Failures retained

Initial rendering failed because the installed Blender build lacks OpenImageDenoise. We explicitly disabled denoising and reran. The failed log remains in `evidence/initial-failed-run.log`; passing logs are separate. Negative-control errors in the supervised log are intentional evidence, not concealed failures.

## What remains before replacing local SU testing

1. Port complex owned geometry, nested protection/rollback and full project lifecycle to a Blender backend with tests.
2. Make production tool selection, prompts, native identities, cameras, source-matched QA and file delivery backend-aware. Existing reconstruction profile only admits Blender health/inspection, as recorded in `compatibility.json`; the isolated experiment uses full discovery and its own explicit backend instructions.
3. Connect a legitimately available model runtime or productize an explicitly supervised bridge. This chat cannot simply be exposed as an HTTP inference API. No paid inference was requested or run.
4. Test the actual website with natural-language tasks, a source reference, local edits and independent review. Success in Blender cannot certify native SketchUp behavior.

Current result: **bounded supervised Blender modeling works here; full production Agent/API replacement remains unfinished.** No local computer is necessary for this completed experiment.
