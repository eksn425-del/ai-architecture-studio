# SketchUp instance selection — 2026-11-05

Implementation evidence, not native geometry acceptance. The runtime agent did
not operate SketchUp, change the installed extension, perform inference, or
write a native model for this change. Root controller owns native acceptance.

## Behavior

- Each running extension boot advertises a signed PID + random boot nonce,
  model path/GUID, title, version and heartbeat. Stop is explicit; missing
  heartbeats expire after eight seconds. Restart never inherits an old pin.
- A project selection is signed and keyed by its full runtime project path,
  so separate profiles with identical project IDs cannot share selections.
- Modern requests use `instance-requests/<instance_id>/`, not the legacy shared
  queue. Older extensions cannot steal them. The selected extension also checks
  the target before expiry/journal/response handling and rechecks document identity
  immediately before dispatch. The shared writer lock and ProjectRuby guards remain.
- With no saved selection, one live modern instance supports the existing
  explicit single-window preparation workflow. Two live instances require a
  choice. A saved stale selection never falls back to another window. Legacy
  transport is retained only when a modern roster has never been created.
- Selection permits only the current project's `blank-disposable-*.skp` copies.
  It rejects active edit contexts, stale observations and unconfirmed writes.
  Existing owned projects cannot switch to another copy through this selector;
  they must use the established recovery flow. No ownership, KEEP, pending-write
  or approval records are cleared by selection.

## Process pin versus document pin

Fixed read-only health/context can read a selected process after its document
changes. This does **not** change the document pin or authorize writes. General
evaluation, camera and export require the selected document path/GUID.

After a confirmed native commit or save, the host can advance the GUID by CAS:
old instance/path/GUID must still match; a signed successful operation must span
that exact before/after identity and postdate selection. Asynchronous commit
checkpoint saves produce this receipt only after both save operations and a
post-save owned project/root/revision check. The caller also matches the exact
checkpoint operation, instance, project, root and revision. Unknown, failed,
wrong-instance and stale receipts cannot advance a pin. Ordinary health never
rebinds. External autosave/manual document changes require explicit reconnection.
Initial connection and explicit checkpoint recovery now snapshot the old selection,
verify successful native identity readback, and CAS the same instance's selection.
An unselected first connection can pin only one uniquely live signed instance;
neither flow can silently pick a different process. Initial reconnect also refuses
unconfirmed writes. Legacy adapters without a process identity are preserved.

These are same-user transport and lifecycle guards, not an OS sandbox.

## Integration

Register `connector_instances.register_routes(app, store, app.state.agent_lock)`
after SketchUp adapter and lock initialization (beside connector setup routes).
It installs project-scoped middleware; the official harness dispatch wrapper
explicitly re-enters that scope in its HTTP worker threads. No selection is global.

- `GET /api/connectors/sketchup/instances?project_id=...`: `instances`,
  `selected_instance_id`, `selection_status`, `detail`. Rows include instance ID,
  PID, title/model name, path/GUID, SketchUp version, last_seen, status,
  selectable/reason. Status is live/stale/stopped; selection status is
  none/selected/stale/document_changed/unknown.
- `POST /api/projects/{id}/connector/instance`: body `instance_id`,
  `expected_model_path`, `expected_model_guid`. Under the existing agent lock,
  it binds and performs a fixed native identity readback before updating session
  ready/path/GUID. Returns session/project and selection status. Frontend still
  checks the normal connector endpoint for actual project_bound.
- The normal connector endpoint must compare the live GUID against session GUID,
  not just test that a GUID is present. Host recovery changing the document must
  refresh selection only after the existing explicit lifecycle verification.

## Validation

163 focused Python/transport/quality/recovery regression tests passed, zero skipped.
New cases cover concurrent per-project routing, legacy queue isolation, ambiguity,
stale/stopped/restarted instances, signed tampering, document changes, GUID CAS,
exact checkpoint metadata, unknown-write preservation, route native-readback
ordering, hidden host binding and the real threaded host HTTP dispatch context.
Native calls are fixtures here. No claim of real dual-window native PASS or
additional supported SketchUp versions is made. Source Ruby syntax and real
dual-window behavior remain for the controller's native gate; no standalone Ruby
interpreter was found on PATH during this work.

Private XML evidence: owning E-drive job `kstudio-r2-live-20261105`,
`instance-pytest-final3.xml`. Historical failures and installed build04 were left intact.

## Immutable-slot connector upgrade follow-up

The desktop bootstrap now backs up the exact previous `bridge.json` bytes under
the profile's `bridge-backups/` before atomically relocating a known first-party
connector to the current version slot. Eligibility requires the old and current
executables to be immediate children of version directories under the same
installation's `versions/`, empty arguments and matching public-pairing/generated
script environment. Only command and a cwd matching the previous slot or its
`_internal` directory change. Custom connectors, other installations, arguments,
working directories, pairing roots and settings are preserved. The frozen runtime
resolver uses the same strict eligibility rule, replacing its older filename-only
fallback. Invalid JSON/schema/duplicate fields fail clearly without replacement.

Program, extension, health and RBZ manifest now agree on `2026.11.05-r2`.
66 focused upgrade/bootstrap/connector tests passed; private evidence is
`connector-upgrade-tests.xml` in the same E-drive job. These use isolated fixture
installations and generated RBZ files, not the owner's live installation. Actual
installed-slot upgrade acceptance remains with the root controller.
