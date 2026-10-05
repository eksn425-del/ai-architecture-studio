# Cloud follow-up to failed Windows reconstruction

Baseline: ac8f597. Reviewed the public Windows report/reference and screenshots: single model partial; six-view walls disconnected; roof capped; architectural quality still FAIL. No cloud SketchUp installation, geometry repair or new SKP acceptance.

Changes:
- Reject the reported mixed-unit pattern before execution: a metric script with a nonzero raw-literal Geom::Point3d origin must use explicit .m/.mm/.cm or intentional .inch. Zero origins and inch-only scripts remain valid. This is a narrow static check, not a Ruby parser, full units analysis or a guarantee about variable-based transforms.
- Existing-root replace requires allow_full_rebuild=true; otherwise fail before model access. Local fixes use edit and scoped remove_owned_group. An explicit full rebuild still changes object IDs; this guard does not itself prove an Agent chose the right edit.
- Shorten old tool-result text above 8,000 characters to its first/last 2,000, retaining six recent tool results, exchange IDs, original user/source evidence, reasoning and full on-disk audit. Historical detail must be reread before use. This reduces repeated dumps, not a complete token-budget solution: tool-call arguments and other history can still grow. No real-provider performance/quality claim.
- Visible building-stage hint and checklist separate execution/artifacts from unverified reconstruction quality. No automatic PASS is assigned; Agent prose may still be wrong and must be checked.

Validation: 202 passed, 2 Windows-specific skips, 3 existing dependency warnings. Python compile, JS syntax and diff check pass. Chromium DOM fixture confirms quality remains pending with simulated committed geometry; no real geometry or provider inference in that fixture. Scope-preserving Skill remains below its 10,000-character budget.

Local Codex next: pull main; reuse the six-view project or a dedicated blank, read its current card/source/model before editing. Repair metric origins and inspect x/y/z bounds and all four wall corners against the approved scale. Correct window counts and open roof/parapet; capture front/rear/both sides/roof/close oblique. For local corrections use edit, verify unrelated child persistent IDs before/after. Only request explicit full rebuild if genuinely necessary and report its ID changes. Download/reopen six-view SKP and perform a real post-reopen local edit. Record failures, any guards triggered, total time/usage and remaining visual mismatches. Publish sanitized evidence and push main; do not repeat the previous false completion.
