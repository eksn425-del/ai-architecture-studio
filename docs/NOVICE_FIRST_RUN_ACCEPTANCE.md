# New-user workflow acceptance — 2026-10-01

## Scope and execution ownership

Started from clean, up-to-date `main` at `0f06f485a1a7f000508fd737fb4ed899016839b9`. Latest user explicitly asked for natural text/image/document/site conversation, paste upload, connection teaching, visible progress, editable SKP download, local software vs website advice and optional own API. This overrides the older image-only scope only for explicitly supplied evidence and this usability turn; no old DesignIR geometry restrictions, no new CAD/MCP engine, no payments/auth/cloud launch.

Browser clicks, file chooser, actual Ctrl+V image paste and ordinary Chinese text drove the real product. Website GPT-6.1 Sol Low authored all building geometry in its persistent workspace. Outer integration agent repaired product code and inspected results; it did not supply building Ruby. No Astra or hidden rescue route was used.

## What was really tested

| Step | Evidence | Result |
|---|---|---|
| New conversation | Created `architecture-project-d478d` through UI | Fresh project |
| Paste image | Clipboard PNG → Ctrl+V in composer → visible thumbnail | Actual paste upload works |
| Unified documents | Uploaded synthetic TXT task and DXF 30×30m site using file chooser | Both supplied to Agent; response cited scope/site |
| Simple first prompt | “请根据我给的图片、任务说明和场地，帮我做一个 SU 模型。先看看还缺什么信息。” | 145.344s; clarification, no geometry tools |
| Ordinary answer | Four total levels including garage; orbit/edit; small site | 164.875s; continued discussion, no premature plan/execution |
| Plan button | Generic UI action, no professional user prompt | 206.875s; actual parameter card, no SU edits |
| Approval/connection | Click approve → tutorial; check MCP → open independent model | Existing Kongxing bridge opened separate blank file in about 13s |
| Actual build | Explicit approve after connection | 476.735s, 19 dynamic calls, 1 failure; revisions 1–3 |
| Same-model follow-up | “请检查正面、背面、左右侧和屋顶…保留现在这栋房子和所有已完成细节。” | 299.969s, 22 calls, 0 failures; revision 4, root remains 37843 |
| Download | Clicked SKP download through actual browser | Download and saved artifact identical |
| Desktop | Built and launched actual PyInstaller EXE, fresh per-user runtime and API dialog | Native Windows UI and own localhost server work after first-run seed fix |

The plan intentionally reconciled apparent extra floors in the source with the explicit four-total-storey task. Estimates: 10×12m building, about 13.5m tall, site 30×30m, balcony depth1.4m. The model is therefore an adaptation to confirmed inputs, not exact source fidelity or a parity benchmark.

## User-visible geometry inspection

Inspected final front, rear, left, right and roof captures. The developed model includes garage/entrance, external stair and handrail, upper glazing with frame/recess depth, balcony slabs/glass rails, timber-colored repeated slats, window trim/sills, complete rooftop rail perimeter, site wall/drive and limited planting. Side/rear geometry is inferred. Same owned root 37843 survived r3→r4.

There is still a clear material/render/detail difference from the source. Surface finishes are simplified; side/rear window rhythm is generic, environment sparse, and inferred interiors are not a designed or validated floor plan. Exterior screenshots do not prove watertight solids, internal circulation, code compliance or absence of all collisions. This is a usable editable reconstruction flow, not photorealistic output or automatic professional design approval.

Download SHA-256: `2c239348d52c01b300f15fb735855559e8684cb4ba74a48d2f41f1759f850952`. Private reference image, generated Ruby, transcripts, screenshots, SKP and desktop binary remain in ignored local runtime / local Downloads; none are committed.

## Defects fixed during usage

- Automatic second-message planning replaced with continuing clarification; explicit plan button.
- Unified image/document/site upload, real paste and drag/drop handlers, normalized images and clear unsupported-format responses.
- Explicit document/site/URL evidence included without silently substituting historic output; unreadable DWG/scanned PDF is disclosed.
- Licensed Markdown rendering for tables/lists/parameter card; no arbitrary HTML or remote image loading.
- Approval opens a connection lesson if no generated SU session; connection never implicitly approves execution.
- Connection originally opened an overlay that blocked approval at narrow width. It now closes the result panel; medium-width layout no longer overlays chat. The failed clicks and successful keyboard approval were part of the real test, not concealed as first-click success.
- A blank template initially appeared as downloadable final output. Download now requires committed geometry, and list filters to current saved model.
- Live progress comes from actual sanitized events and Ruby commits, including pending call stage/failed calls. No fake percentage or raw private transcript.
- Local API settings use LiteLLM, clear password field, keep key only in server memory, redact provider errors, reset incompatible provider/model thread while retaining project card/scripts/model.
- Desktop build used relative data paths incorrectly; fixed absolute build inputs. Fresh packaged startup previously expected legacy examples; now creates a blank starter project when examples are not shipped.
- Loopback client/Host and same-origin mutation checks added; standalone existing MCP configuration optional, no connector rewrite.

## Acceptance / release gates

The actual configured-machine user path reaches modeled SU, same-root revision and matching downloadable SKP. `scripts/check.ps1`: 114 passed; final JS syntax and git whitespace check recorded in HANDOFF.

Not accepted as a commercial clean-machine release:

1. Licensed redistributable Kongxing/SketchUp plugin installation and connector setup are still separate; no compatible license was established for bundling the installed machine-specific bridge. Do not copy it or the competitor’s source.
2. Preset native model still depends on available local Codex login. BYOK configuration/contracts are real, but no spare user API credential was provided for live BYOK inference; no API quality success is invented.
3. Long chat/plan/build latency needs a separate measured product target. Progress visibility reduces uncertainty, not actual inference time.
4. Packaged shell was tested on this machine with installed WebView2 and SketchUp. Clean Windows installation, fully automatic plugin onboarding, comprehensive dependency license audit and unattended recovery remain unverified.
5. Generic multi-document architectural design, DXF ambiguity resolution and every upload variant were not all exercised against live models. Tests cover safe extraction and explicit unsupported input behavior.

Recommendation: local Windows workbench first, same web workspace/runtime reused. A later cloud website can use a separately installed local connector; desktop alone does not produce stronger reconstruction reasoning.
