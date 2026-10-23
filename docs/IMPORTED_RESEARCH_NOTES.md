# Imported research notes for Blender planning

Upload a UTF-8 `.md` or `.txt` file with the existing reference upload control (API: `POST /api/projects/{id}/inputs/reference?filename=research.md`). Include source URLs/titles, observations, and explicitly uncertain dimensions. Ask for a plan in the same Blender project. The actual provider prompt now includes the uploaded text, relative source filename, SHA-256 and `external_manual_upload_unverified` provenance.

This is manual/external research import, not live web search. No URLs are fetched, sources independently verified, networking enabled, credentials configured, or provider tools added. Notes are untrusted evidence, never instructions or geometry approval. Image-role and plan approval gates remain in force. Notes do not become target-building images.

Limits: eight notes, 30,000 UTF-8 bytes per note, 120,000 bytes combined. Malformed UTF-8, empty/control-character text, escaped/missing paths and symlinks are rejected before invoking the provider; malformed uploads may be stored by the existing upload route but cannot be used for Blender planning. Replace invalid notes through the existing project workflow. PDF/DOCX extraction is not included in this scoped import.

`tests/test_imported_research.py` exercises the real upload/conversation HTTP routes with a deterministic provider fixture. This is offline product plumbing evidence, not real model inference, live research or architectural visual acceptance.
