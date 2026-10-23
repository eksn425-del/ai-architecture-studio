# Owner onboarding repair — 2026-10-21

## Actual diagnosis

Owner's apartment request failed twice in the read-only conversation-intent preflight, before Builder/native modeling. Local phase telemetry: awaiting_headers, 242141/241687 ms, zero chunks, ReadTimeout. This establishes absence of response headers at the client, not whether B.AI, an upstream model or network/proxy was responsible. Four other preflight attempts report ValueError; do not count them as native failures or infer their billing. Historical failures remain.

## Changes

- No extra intent inference when there is no current plan/model: host caps the initial turn to clarification/read-only; selected Builder still receives original user text/images. Existing plan approval, stale-plan guards, MCP/identity/KEEP and execution checks remain.
- API setup uses provider/Base URL/model ID/Key, hiding effort tiers and retaining existing connection effort (owner High). New connections use provider default. DPAPI storage and cross-host Key separation remain. Chat Completions compatibility is not universal vision/tool compatibility.
- Desktop explicitly enables text selection. Compact microphone button invokes Windows dictation only in this app's foreground window. Browser fallback requires consent; transcription never submits. Late results cannot overwrite changed drafts/projects.
- Connector download no longer depends on existing configuration/plugin. Manual 2019–2026 candidates are offered with detection/verification labels. Explicit manual choice only configures bridge; never installs SketchUp or overwrites its plugin. 2010–2018 unsupported; no all-version certification.
- Private local connector package rebuilt with manifest/hash and Node license; stdio initialize/tools-list self-check PASS. Source redistribution rights and clean-PC native acceptance remain pending, so package is LOCAL ONLY, excluded from GitHub.

## Verification

200 focused Python checks PASS; two existing symlink tests cannot create Windows symlinks (WinError1314), explicitly deselected after recording failure. 104 UI Node checks PASS. No paid inference, native model writes or cloud deployment. Original models, credential containers and USD2 ledger are preserved. Real paid provider source-to-model quality and actual spoken transcription remain unverified; removing a duplicate request does not repair an unavailable provider.

## Public methods reviewed

[Cline compatible API setup](https://docs.cline.bot/provider-config/openai-compatible): Base URL, Key, model ID; adopted simple fields, not model capability promises.
[pywebview API](https://pywebview.flowrl.com/api/): text_select defaults false, explicitly enabled.
[SketchUp extension installation](https://help.sketchup.com/en/extension-warehouse/installing-trial-extension): RBZ is manually installed through Extension Manager; app configures the local bridge separately.

## Installed verification

Local release installed with private payload; real browser confirms no visible effort selector, saved Key remains masked, candidate 2019–2026 selection works. Download endpoint returned RBZ byte-identical to its manifest payload. Real desktop normal text was selected by double-click and Ctrl+C returned exactly the selected character. Voice UI and mock callbacks verified; no ambient microphone recording was initiated. No new model request or SU write.
