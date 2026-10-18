# K Studio visual refresh — 2026-10-18

Base: `821433ecfce5d222ac2603d4a3c057aa71aeec0b`. Owner requested a more distinctive UI and a designed central K. Isolated UI branch; no main merge or deployment.

The shared interface now uses a deep green sidebar, warm drawing-paper canvas, a locally authored folded K SVG, clearer input styling and three numbered suggestion cards. The same monogram is used in the sidebar. No remote font, image generation, new dependency or model call is required. Workflow handlers, approval bindings and modeling tools are unchanged; the original suggestion prompts remain intact.

Validation: JavaScript syntax and SVG XML parsing passed. The three existing frontend suites passed **95/95**, with no skips. Actual local browser checks verified the existing empty session, the K image, suggestion-to-draft behavior without submission, and opening/closing the files panel. A 390×844 preview had no horizontal document overflow; the temporary viewport was reset. Private screenshots and test output remain in ignored local runtime storage.

The native desktop shell was reopened against the existing service to load the changed resources. Desktop launcher metadata is updated to this local UI commit; the service and the existing project runtime are retained. No source image upload, conversation submission, plan approval, inference, geometry modification or native delivery test was performed. These checks establish UI behavior only, not architectural model quality.

## Connection dialog follow-up

Owner identified the missing close control and unclear automatic/manual connection distinction. Added a labeled top-right close button using the existing dismissal path (which clears pending automatic execution), explicit local SketchUp access disclosure, collapsible manual Kongxing bridge steps, and truthful button labels separating read-only MCP checks from opening/binding a project model. An already-approved execution flow has an explicit execution label. The manual guide states that arbitrary MCP endpoint configuration is not implemented in this dialog.

The existing 95 frontend checks pass after this change. Actual browser interaction confirmed close/reopen and manual-guide expansion, without pressing either native connection/check button. One initial exact-text locator for the guide did not match its decorative arrow; the visible summary selector then worked. No product recovery or backend change was needed. Screenshots remain local. Actual MCP connectivity and native project binding were not retested for this UI-only change.

## Installed software/version correction

Owner clarified that SketchUp and future modeling software must use the user's installed version instead of requiring a developer-tested year. Removed the 2024 prerequisite from connection instructions and replaced the launcher's hardcoded 2024-then-2022 preference with deterministic installation selection: explicit year without fallback, identified running executable, otherwise the sole configured bridge/installation; ambiguity is rejected with instructions to choose. Discovery now includes per-user registrations and registered 20xx years rather than a fixed historical list. The existing project-copy boundary, matching-plugin requirement and explicit-version selection remain. No software or plugin was installed, upgraded or switched.

Fifteen offline selection checks passed (including running 2022 ahead of configured 2024, missing explicit year, ambiguous installations, missing executable and duplicate registry entries); fake files were never executed. Ten existing launcher/component checks and 95 frontend checks passed. Read-only discovery on this machine selected its currently running 2024 executable and detected the bridge file; no native model calls/writes were issued. Native compatibility of other versions is **NOT_RUN**, and a discovered executable/plugin is not compatibility certification. The general rule is recorded in `docs/SOFTWARE_VERSION_POLICY.md` and AGENTS; prior version-specific evidence is retained.
