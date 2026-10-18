# Use the owner's installed modeling software

Owner decision, 2026-10-18: K Studio must respect the modeling software and version the user already has. This applies to SketchUp and future software integrations. A historically tested version is evidence, not a mandatory product-wide installation requirement.

- Prefer the user's explicitly selected version or the unambiguously identified running installation. Never install, upgrade, downgrade or silently substitute software versions.
- Keep executable discovery, bridge availability, tool capability checks and actual end-to-end validation distinct. An executable or plugin file alone does not certify compatibility.
- When multiple installations are ambiguous, ask the user to open the intended version or use an explicit local selection. Do not guess the newest version or impose a developer's preferred version.
- Require a matching bridge/plugin and preserve document ownership, project copies and original models. Missing capabilities must fail clearly; do not disable guards for an older/newer version.
- Record the actual application/bridge version and available capabilities when evidenced. Retain historical version-specific failures and test limits. This policy does not claim untested versions or future software integrations are already supported.

The Windows SketchUp launcher now discovers registered 20xx installations (including per-user registrations), respects an explicit `-SketchUpYear` without fallback, and otherwise prioritizes a uniquely identified running installation. With no running instance it uses the only installation with the known bridge location, or the sole installed candidate; ambiguous cases require user selection. The existing per-version plugin check remains in force. Registry/template/plugin layout differences and actual tool/model-format compatibility still require native validation.
