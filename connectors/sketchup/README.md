# K Studio local SketchUp connector (candidate)

This first-party thin transport uses SketchUp's official `SketchupExtension` and
`UI.start_timer` APIs. It contains no Kongxing code or private plugin assets.
It does not replace ProjectRuby, its document/root/revision checks, KEEP guards
or the existing native save checkpoint. It exposes only health/context and the
generated-script channel; legacy primitive shortcuts are deliberately absent.

Pairing is stored under the current Windows user's LOCALAPPDATA/KStudio folder.
The installer protects that directory with the user/SYSTEM ACL. No TCP/HTTP port
is opened. Requests and receipts are HMAC authenticated, expire before execution,
and have a durable operation journal. A STARTED journal without a receipt is
unresolved, never automatically replayed. Ruby runs on SketchUp's main thread.
This is protection against cross-user/network callers, not a sandbox against a
compromised same-user process. Arbitrary generated Ruby retains native powers;
product ownership guards and authorization must remain enabled.

After installation through SketchUp Extension Manager, restart SketchUp once.
The enabled extension starts when SketchUp starts; K Studio does not claim that
opening a SKP installs or starts an absent plugin. Stop/start controls are under
Extensions > K Studio Connector. Disable pairing to revoke access.

Compatibility: uses Ruby 2.5+ APIs (SketchUp 2019+ candidate). Only tested versions
may be marked verified in the release matrix; candidate is not verified. No macOS
support is claimed for this Windows pairing path. See docs/execution/R2_CONNECTOR.md.
