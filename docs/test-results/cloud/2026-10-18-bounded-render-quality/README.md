# Bounded render quality and three-round large-case verification

Baseline: trial/contextual-repair-20261018 f6859a1171df17c0c8c2eefceec9309039440b9f.

The production change adds an optional strictly validated 800–1600 square resolution and boolean denoise to the existing Blender render tool. Defaults remain compatible. Quality variants have distinct render paths and truthful per-process settings receipts. Render errors cannot reuse a stale receipt; rendering never saves or changes model geometry. Installed Blender 4.3.2 lacks OpenImageDenoise, so explicit denoise requests fail honestly. Successful delivered case images use denoise=false.

Final suite: 977 passed, 19 skipped, one existing warning, 97.17 seconds. Independent code review cleared the exact four-file patch; 28 focused tests passed, including native PNG size and unchanged model SHA checks. Independent publication staging reran the full suite: 977 passed, 19 skipped, one warning in 58.94 seconds. Native isolated checks produced actual 800px and1600px PNGs and preserved model SHA/revision.

A private Hangzhou Raffles three-round case exercised actual HTTP discussion/plan/approval routing and the real AgentToolSurface/Blender bridge. The current assistant supplied controlled intent and geometry responses; no external inference or independent vision was evaluated. R1 rebuilt a recovered specification (352 objects), R2 refined a source-visible facade channel/crown and preserved14 non-tower objects, and R3 added inferred context and an internal roof-mesh refinement (497objects,491unchanged in the refinement). Every commit saved and reopened in a fresh native process. Each round and the original were preserved. Source fidelity is partial, surrounding city geometry inferred, and GUI unavailable in the current environment. Public sources establish only basic programme/scale: https://www.unstudio.com/projects/raffles/ .

A deliberate wrong intent classification on the large case still respected explicit no-write/plan-only requests; wrong pending-plan identity was rejected before changes. This is controlled semantic/protocol evidence, not a guarantee against arbitrary natural-language errors.

Private source photographs, models, renders, execution scripts and raw logs are excluded from publication. Main/deployment/user desktop untouched; no credentials or paid model calls.

Publication covers renderer code and tests only. Further private case refinements may continue separately; this record is not final architectural visual acceptance.
