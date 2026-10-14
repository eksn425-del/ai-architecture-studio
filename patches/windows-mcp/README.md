# Local Windows-MCP path input safety patch

Applied to the owner's installed CursorTouch/Windows-MCP 0.8.7 checkout (MIT;
copyright and full license in LICENSE.md). This is a small upstream wrapper fix,
not a replacement desktop-control engine. The original two files were backed up
privately before editing. Apply the relative patch to that matching checkout;
the regression test runs with its existing dependencies.

Absolute file paths directed at Codex/ChatGPT chat now fail before any click,
clear, paste or Enter. Real native file dialogs remain allowed. The target root
window must stay foreground after click and before clear/paste/Enter. Intentional
Codex path input needs explicit allow_codex_path_input=true. This parameter must
only be used for an actual human request to send that content.

64 focused Windows-MCP tests passed, including chat rejection before input and
foreground change refusal. Tests mock native calls; they do not send chat messages.
The running MCP process has already imported the old module: reconnect/restart
that server to load the installed patch. No claim of hot reload or a live
negative test is made. Until then the persistent local Windows Computer Use
skill mandates fresh application/dialog snapshots, press_enter=false for file
paths, and clicking the observed Open button after verifying the populated field.

K Studio's native-development runtime also defaults its project input-token,
turn input-token and turn tool-call caps to 0 (disabled). Existing native usage
history, model identity, geometry ownership and approval guards stay intact.
This does not authorize paid API calls or remove provider/account rate limits.
