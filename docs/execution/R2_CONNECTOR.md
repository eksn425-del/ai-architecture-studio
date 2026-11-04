# Public local connector — R2

The candidate now includes first-party `connectors/sketchup/` and the console MCP
adapter `app/public_connector.py`, packaged as RBZ + KStudioConnector.exe. No
Kongxing plugin/server/node wrapper is included by the normal build. The private
trial build switch remains explicitly non-public, not a license grant.

Upstream evaluated: `zinin/sketchup-mcp2`, revision
`b8cdda790315fa6304c10b2e415c0aab8ea331b4`, MIT, inspected 2026-11-04. Its poll-on-
SketchUp-main-thread and nonblocking transport are useful reference patterns,
but its unrestricted eval/TCP listener without authentication is unsuitable as
the public protected writer. No source was copied. This small local-file IPC
adapter uses official SketchupExtension/UI.start_timer interfaces and leaves all
geometry implementation in the existing ProjectRuby/native helpers.

Pairing uses user/SYSTEM ACL, random HMAC secret, signed expiring requests and
signed receipts. It opens no network listener. Invalid queue entries are
quarantined, a process lock serializes native dispatch, and operation IDs retain
the initial request digest and document identity. RETURNED means transport
returned, not commit/save success. ProjectRuby's durable unresolved-write gate
blocks a different script ID too. Camera/export requests carry document path
and GUID; the wrong instance does not consume them.

This is not an OS Ruby sandbox. SketchUp Ruby runs as the user's SketchUp
process. A compromised same-user application can access its own pairing data;
filesystem ACL/HMAC do not prevent that. Agent write permission, source guards,
owned root/revision/KEEP and post-commit checkpoint remain mandatory.

Native health: actual SketchUp 24.0.484 / Ruby 3.2.2 / main thread / unique saved
test document verified. First failure was Windows backslashes in ROOT making
Dir.glob see no request files. Fixed by normalizing separators. A Chinese account
also exposed UTF-8 decoding of whoami output; the installer now decodes Windows
ANSI explicitly. Original failures remain in local evidence.

Six real native fixture cases passed after a fixture-only invalid project-ID
correction: before dispatch, transaction abort, lost reply after actual commit,
capture failure, disconnect after scheduled save, normal edit and disk reopen.
Each used a distinct disposable model, real ProjectRuby, two named groups,
deep geometry/material KEEP checks and durable host state. Unknown outcomes
blocked a different operation; no geometry was replayed. These are transport/
recovery tests, not image modeling quality or real end-user UX acceptance.
Private evidence: R2 job `native-faults-01` (fixture ID failures),
`native-faults-02/receipt.json`, per-case native fingerprints and model artifacts.

Candidate API range 2019–2027 is an evaluation range, not supported-version PASS.
Only SU2024 has the above native evidence. Installation on a clean different
computer and other SketchUp versions remains NOT_RUN. Initial plugin installation
requires SketchUp Extension Manager/restart; opening a model alone does not
install a missing extension. Existing plugins/settings are preserved.
