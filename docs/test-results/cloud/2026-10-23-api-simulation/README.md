# Cloud simulated API / Agent usage experiment — 2026-10-23

## Authorization and non-claims

Owner requested tests on the assistant's cloud computer, using a simulated API for the Agent, with special attention to usage and the difference from the Codex open-source route. No owner-PC access, live paid model call, main merge or deployment. Publication is still a separate pending question. This work extends private repair commit c0cefe3 on `test/cloud-api-simulation-20261023`.

Three separate evidence classes are kept distinct:
1. Fixed scripted HTTP/SSE responses for controlled transport/context measurement.
2. Those HTTP responses driving the actual K Studio router, LiteLLM loop, tool surface and real Blender 4.3.2.
3. A four-response assistant-mediated relay: the supervising assistant read each request, chose an inspection/edit/render, inspected the actual PNG received on the simulated API, then supplied the final answer. This is NOT an automatically callable chat-model API or a comparable autonomous-model billing run.

## Measured findings

### Checkpoint gate (unchanged by the preceding repair)

The same 24 workspace-tool sequence uses 25 HTTP requests. With valid structured checkpoint: 1,516,300 cumulative wire bytes. Without checkpoint: 4,241,080 bytes and zero compactions. This is 64.25% less transport in that controlled fixture, not 64.25% cheaper inference. Base a85c62c and prior repair c0cefe3 have identical metrics on all five benchmark cases: no prior cost reduction is invented. Explicit 503 yields one request/no retry; invalid-tool recovery and new-user/source dedup are separately tested.

### Blender visual feedback was missing

The old API adapter returned native `image_path` as text but no image payload. Actual generated Blender PNG reached no model request. The new adapter checks current host receipt, native revision, confined owned path, no symlinks, PNG format/dimensions/size, and forwards actual pixels. Successful Blender writes invalidate stale images. Failed adapter conversion retains tool IDs/native result and is not mistaken for a failed native mutation. Full Blender JSON is preserved in the journal rather than cut at 60,000 characters.

The new neutral readback label also required a compaction fix: internal render feedback must not be treated as a new human request. Regression proves the latest two complete tool batches survive, the real owner instruction remains, and unresolved tool effects are never compacted away.

### Structured active-wire projection (final frozen r6)

Full native vertices/faces duplicated across scene receipts are replaced only on the active wire by per-object counts/digest and one shared explanation. Exact authored specs, native transforms/dimensions/materials, all status/errors/other fields remain. Raw journals keep the complete data. `blender_inspect_scene` offers explicit selected-ID full-geometry retrieval (1..8 IDs), which bypasses projection. Default host inspection `{}` remains unchanged.

Same scripted 13 responses, same 11 image attachments and 1,703,509 decoded image bytes:
- Correct image/full-receipt r4: 2,307,262 text-JSON bytes; 4,579,352 total wire bytes.
- Final projected r6: 1,512,939 text-JSON bytes; 3,785,029 total wire bytes.
- Reduction: **34.427% text**, **17.346% wire**. No request-count reduction.

The earlier broken path was smaller because it omitted necessary images and truncated JSON; it is NOT the savings baseline. Intermediate r3 and r5 remain recorded separately. A separate two-response detail probe retrieves exact native mesh arrays and performs no geometry mutation; its requests are not hidden inside the primary 13-response comparison.

Mock `usage` fields are a ceil(UTF-8 text JSON bytes/4) proxy to exercise accounting contracts. They are NOT a named model tokenizer, Chinese-token estimate, vision/reasoning charge, cache/bill receipt or CNY/building proof. Repeated bytes are not necessarily uncached billed tokens. Images remain required evidence, not removable overhead.

## Codex comparison limitation

Installed upstream Codex 0.163.0 was actually started. Its config/read confirmed a localhost fixture before thread creation. Thread/start then failed in the sandbox helper (socket directory owner/mode-0700 requirement), even with isolated user-owned 0700 paths. No sandbox bypass/fallback; model HTTP requests = 0, tool dispatches = 0. Zero means NOT_RUN, not cheaper or better.

Independently characterized product limitation: current `_prepare_home` requires an auth.json and rewrites configuration without custom `model_provider/model_providers`. Therefore the normal K Studio native entry does not directly route custom APIs through the same upstream harness. The loopback upstream experiment used the verified transport layer, not a false claim that public `respond()` already supports it. This integration limitation is distinct from the cloud sandbox blocker and from underlying model capabilities.

## Actual native results

13-response test: synthetic 74-object scene, 6 target changes, 68 preserved objects, actual save/fresh-process reopen and immutable old .blend checks pass. Premature, KEEP, stale-instruction and unknown-tool writes rejected. The received native PNG SHA matches its file. Raw journals retain complete 74-object geometry; projected omissions have verified counts/digests; targeted full details retrieve correctly.

Assistant-mediated task is a different two-rail edit, not compared as a faster version of the 13-response workload. It used 4 responses and 3 tools, preserved untargeted geometry and verified the actual returned picture. Its usage is not the cost of this assistant's reasoning/context.

## Remaining boundaries

Blender full tool profile still does not invoke the dedicated SketchUp visual Critic; the image fix restores Builder perception, not independent visual acceptance. Source-photo fidelity, arbitrary building competence, natural-language approval, real-provider quality/cache/reasoning/cost and native SketchUp acceptance remain NOT_RUN. Simulation cannot prove a cheap LLM chooses the right tools or architecture. Large authored mesh specs are intentionally retained, so this projection is not a universal context-size ceiling.

Use isolated writable HOME and `LITELLM_LOCAL_MODEL_COST_MAP=True` for reproducible offline tests. Source/test scripts and final aggregate results are attached separately; all paid-service credentials remain absent.

## Final aggregate verification

Frozen final application source: **1315 passed, 9 skipped, 0 failed**, 238.00 seconds. See `test-summary.json`, `pytest-final.log` and `pytest-final.xml`. Nine skips are not passes. This is regression evidence, not real-provider quality or commercial acceptance.
