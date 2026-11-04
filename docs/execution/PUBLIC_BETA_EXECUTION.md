# R2 execution — 2026-11-04

Status: IN_PROGRESS. User adopts complete R2 execution book, superseding previous visual proposal and closed-case scope only as explicitly described therein. No main merge, production launch or real customer charging authorized. New paid inference budget currently 0 under R2 section3.6; prior experiments do not establish remaining authorized funds for this batch.

Baseline PR24 ef52a76f7bda15d59939369da200b3e55778f0a6 confirmed remote unchanged. Branch codex/kstudio-r2-public-beta-20261104. Managed isolated checkout created; original dirty workspaces preserved. R2 standalone MD equals ZIP version; 30 SHA256 entries verified. Private design input and outputs remain in owning E-drive job kstudio-r2-20261104. Managed checkout created by desktop app; cross-volume git worktree move failed without changing source. New runtime/cache/build output must use E.

Work ownership: runtime agent owns effective provider configuration, image pipeline, approved spatial handoff and related tests; cloud agent owns cloud/, deploy/, tests/cloud; web agent owns website/ and minimal app/static polish; controller owns connector, release/update, local security, remaining regression, integration, native checks and final evidence. Single native writer is controller.

Current actions: reproduce full baseline with UTF-8 and E-drive test temporary files; implement independent tracks. No new paid request has been issued. Final acceptance is not established by creating this tracker.

Next: integrate runtime fixes and all independent engineering, verify real interfaces, build candidate and deployable server bundle; record external-only blockers precisely. Do not stop at this checkpoint.
