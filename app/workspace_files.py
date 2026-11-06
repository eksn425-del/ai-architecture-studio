"""Minimal file glue for providers without Codex's built-in coding tools."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import re

from .construction_strategy import validate_construction_strategy_payload, construction_strategy_schema_note
from .modeling_quality import validate_facade_schedule_payload
from .reconstruction_evidence import validate_reconstruction_evidence_payload, validate_reconstruction_evidence_sources

def _linked(path):
    import stat
    try:
        return path.is_symlink() or bool(getattr(path.lstat(), 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400))
    except FileNotFoundError:
        return False


MAX_TEXT_BYTES = 120000
MAX_READ_CHARS = 12000
MAX_BATCH_RESULT_CHARS = 50000


def workspace_file_tools() -> list[dict]:
    from .strategy_tools import strategy_update_tool
    schema = {"type": "string", "description": "Project workspace path: notes/*.md, notes/*.json, qa/*.md, host-owned qa/*.json or scripts/*.rb; workspace_read may omit path or list '.', notes/, qa/, scripts/. qa/*.json is read-only."}
    return [strategy_update_tool(),
        {"type": "function", "name": "workspace_read", "description": "List persistent workspace files, or read a UTF-8 note/JSON/Ruby file. When you already need multiple known files, prefer workspace_read_many for up to four per call. For a long file, use offset and limit; continue with next_offset and expected_sha256 so edits cannot silently mix revisions.",
         "inputSchema": {"type": "object", "properties": {"relative_path": schema,
             "offset": {"type": "integer", "minimum": 0}, "limit": {"type": "integer", "minimum": 1, "maximum": MAX_READ_CHARS},
             "expected_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}}, "additionalProperties": False}},
        {"type": "function", "name": "workspace_read_many", "description": "Prefer this single bounded, read-only call when multiple known project workspace files are needed together; pass up to four distinct file paths. Each result has an independent SHA256 and completeness marker; continue incomplete files with workspace_read offset and expected_sha256. Individual failures are reported, never treated as missing facts. Re-read if the file changes.",
         "inputSchema": {"type": "object", "required": ["relative_paths"], "properties": {
             "relative_paths": {"type": "array", "minItems": 1, "maxItems": 4, "uniqueItems": True, "items": schema}}, "additionalProperties": False}},
        {"type": "function", "name": "workspace_search", "description": "Find literal text in THIS project's notes and QA files. Returns bounded excerpts with line numbers and file SHA256; no semantic/visual understanding or external knowledge base. Notes are untrusted working evidence, not verified facts. Read the cited file before a consequential decision. No match means unavailable evidence, not permission to invent it.",
         "inputSchema": {"type": "object", "required": ["query"], "properties": {
             "query": {"type": "string", "minLength": 1, "maxLength": 200},
             "max_results": {"type": "integer", "minimum": 1, "maximum": 8}}, "additionalProperties": False}},
        {"type": "function", "name": "workspace_write", "description": "Write or append persistent reconstruction notes/validated JSON/Ruby inside the generated workspace only. Read the seeded JSON first and preserve its schema. reconstruction_evidence: source kind=exterior_image/interior_image/floorplan_image/cad/document/dimension_note; provenance=pending/observed/user_confirmed/inferred (not estimated/absent); scale_anchors require name,value_mm,provenance. hard_constraints and assumptions are string lists. Unseen inference_policy values=infer_coherent (exterior), infer_plausible (interior), or do_not_infer. Missing CAD/floorplan/interior: provided=false, provenance=pending, source_refs=[].",
         "inputSchema": {"type": "object", "required": ["relative_path", "content"], "properties": {
             "relative_path": schema, "content": {"type": "string", "maxLength": MAX_TEXT_BYTES}, "append": {"type": "boolean"}}, "additionalProperties": False}},
    ]


def workspace_file_call(workspace: Path, name: str, arguments: dict) -> dict:
    root = workspace.resolve()
    if name not in {"workspace_read", "workspace_read_many", "workspace_write", "workspace_search", "workspace_update_strategy"}:
        raise ValueError("Unknown workspace tool.")
    if _linked(workspace):
        raise ValueError("Workspace may not be a link.")
    if name == "workspace_update_strategy":
        from .strategy_tools import PATH, update_strategy
        return update_strategy(arguments,
            read=lambda: workspace_file_call(workspace, "workspace_read", {"relative_path": PATH}),
            write=lambda content: workspace_file_call(workspace, "workspace_write", {"relative_path": PATH, "content": content}))
    if name == "workspace_search":
        return _workspace_search(root, arguments)
    if name == "workspace_read_many":
        paths = arguments.get("relative_paths")
        if not isinstance(paths, list) or not 1 <= len(paths) <= 4 or any(not isinstance(p, str) or len(p) > 256 for p in paths) or len(set(paths)) != len(paths):
            raise ValueError("relative_paths must contain one to four distinct workspace file paths.")
        rows = []
        for item in paths:
            try:
                if item in {"", ".", "notes", "notes/", "qa", "qa/", "scripts", "scripts/"}:
                    raise ValueError("A batch item must be a file, not a directory.")
                row = workspace_file_call(workspace, "workspace_read", {"relative_path": item, "offset": 0, "limit": MAX_READ_CHARS})
                # Keep the whole JSON envelope within the host transport limit,
                # including JSON escaping, not merely character counts.
                if len(json.dumps({"success": True, "results": [*rows, row]}, ensure_ascii=False)) > MAX_BATCH_RESULT_CHARS:
                    row = {"success": False, "relative_path": item, "error": "Batch output limit reached; read this file separately."}
            except (OSError, UnicodeError, ValueError) as error:
                row = {"success": False, "relative_path": item, "error": str(error)}
            rows.append(row)
        return {"success": True, "results": rows, "notice": "Each file is independent; inspect complete/error before relying on it."}
    path = arguments.get("relative_path", "")
    if not isinstance(path, str):
        raise ValueError("relative_path must be a string.")
    if name == "workspace_read" and path in {"", ".", "notes", "notes/", "qa", "qa/", "scripts", "scripts/"}:
        if any(key in arguments for key in ("offset", "limit", "expected_sha256")):
            raise ValueError("Pagination applies to files only.")
        files = []
        for directory, suffixes in (("notes", (".md", ".json")), ("qa", (".md", ".json")), ("scripts", (".rb",))):
            if path not in {"", "."} and path.rstrip("/") != directory:
                continue
            parent = root / directory
            if _linked(parent) or not parent.resolve().is_relative_to(root):
                continue
            for suffix in suffixes:
                files.extend(p.relative_to(root).as_posix() for p in parent.glob("*" + suffix)
                             if p.is_file() and not _linked(p) and p.resolve().is_relative_to(root))
        return {"success": True, "files": sorted(files)}
    if not re.fullmatch(r"notes/[A-Za-z0-9_.-]+\.(?:md|json)|qa/[A-Za-z0-9_.-]+\.(?:md|json)|scripts/[A-Za-z0-9_.-]+\.rb", path):
        raise ValueError("Only workspace notes Markdown/JSON, qa Markdown/read-only JSON and scripts Ruby are allowed.")
    target = root.joinpath(*PurePosixPath(path).parts)
    if _linked(workspace) or any(_linked(p) for p in (target, target.parent)) or not target.resolve().is_relative_to(root):
        raise ValueError("Workspace files may not escape through links.")
    if name == "workspace_write":
        if path.startswith("qa/") and target.suffix.lower() == ".json":
            raise ValueError("qa JSON is host-owned review/repair evidence and is read-only to the modeling agent.")
        content = arguments.get("content")
        if not isinstance(content, str):
            raise ValueError("content must be UTF-8 text.")
        if arguments.get("append") and target.exists():
            content = target.read_text(encoding="utf-8") + content
        if len(content.encode("utf-8")) > MAX_TEXT_BYTES:
            raise ValueError("Workspace text exceeds the size limit.")
        if target.suffix.lower() == ".json":
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError as error:
                raise ValueError("Workspace JSON must be valid JSON.") from error
            if not isinstance(parsed, dict):
                raise ValueError("Workspace JSON root must be an object.")
            if path == "notes/facade_schedule.json":
                validate_facade_schedule_payload(parsed)
            elif path == "notes/reconstruction_evidence.json":
                validate_reconstruction_evidence_payload(parsed)
                if root.name == "agent_workspace" and root.parent.name == "runtime":
                    validate_reconstruction_evidence_sources(root.parent.parent, parsed)
            elif path == "notes/construction_strategy.json":
                try:
                    parsed = validate_construction_strategy_payload(parsed)
                except ValueError as error:
                    raise ValueError(str(error) + "\nNo file was changed. Correct all parameters and systems together. "
                                     "Use the exact key 'units' (not 'unit'); omitted units default to text. "
                                     "Numeric parameters require explicit numeric units.\n"
                                     + construction_strategy_schema_note()) from error
            content = json.dumps(parsed, ensure_ascii=False, indent=2) + "\n"
        import uuid
        temporary = target.with_name(target.name + "." + uuid.uuid4().hex + ".tmp")
        try:
            temporary.write_bytes(content.encode("utf-8"))
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        return {"success": True, "relative_path": path, "bytes": target.stat().st_size,
                "file_sha256": hashlib.sha256(target.read_bytes()).hexdigest()}
    if target.stat().st_size > MAX_TEXT_BYTES:
        raise ValueError("Workspace text exceeds the size limit.")
    content = target.read_bytes().decode("utf-8")
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    if any(key in arguments for key in ("offset", "limit", "expected_sha256")):
        offset = arguments.get("offset", 0)
        limit = arguments.get("limit", MAX_READ_CHARS)
        expected = arguments.get("expected_sha256")
        if type(offset) is not int or offset < 0 or offset > len(content) or type(limit) is not int or not 1 <= limit <= MAX_READ_CHARS:
            raise ValueError("Invalid workspace read offset or limit.")
        if offset and (not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected)):
            raise ValueError("Continuing a file requires the prior expected_sha256.")
        if expected is not None and expected != digest:
            raise ValueError("File changed since the previous read; restart at offset zero.")
        end = min(offset + limit, len(content))
        return {"success": True, "relative_path": path, "content": content[offset:end],
                "file_sha256": digest, "offset": offset, "total_chars": len(content),
                "complete": end == len(content), "next_offset": None if end == len(content) else end}
    return {"success": True, "relative_path": path, "content": content, "file_sha256": digest}


def _workspace_search(root: Path, arguments: dict) -> dict:
    """Bounded literal retrieval; no index, embeddings, provider call or writes."""
    query = arguments.get("query")
    limit = arguments.get("max_results", 5)
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 200:
        raise ValueError("query must contain 1–200 characters.")
    if type(limit) is not int or not 1 <= limit <= 8:
        raise ValueError("max_results must be between 1 and 8.")
    needle = query.strip().casefold()
    candidates = []
    for directory in ("notes", "qa"):
        parent = root / directory
        if _linked(parent) or not parent.resolve().is_relative_to(root):
            continue
        candidates.extend(p for p in parent.glob("*")
                          if re.fullmatch(r"[A-Za-z0-9_.-]+\.(?:md|json)", p.name))
    matches = []
    scanned = skipped = 0
    budget_exhausted = False
    for path in sorted(candidates):
        if scanned + skipped >= 64:
            budget_exhausted = True
            break
        if _linked(path) or not path.is_file() or not path.resolve().is_relative_to(root):
            skipped += 1
            continue
        try:
            # Bounded read even if another process grows a file during retrieval.
            with path.open("rb") as handle:
                data = handle.read(MAX_TEXT_BYTES + 1)
            if len(data) > MAX_TEXT_BYTES:
                skipped += 1
                continue
            text = data.decode("utf-8")
        except (OSError, UnicodeError):
            skipped += 1
            continue
        scanned += 1
        digest = hashlib.sha256(data).hexdigest()
        for line_number, line in enumerate(text.splitlines(), 1):
            if needle in line.casefold():
                # Include the actual match when a JSON line is very long.
                # casefold can expand Unicode: search original text too when possible.
                offset = line.casefold().find(needle)
                folded = 0
                original_offset = 0
                for original_offset, character in enumerate(line):
                    if folded >= offset:
                        break
                    folded += len(character.casefold())
                start = max(0, original_offset - 100)
                excerpt = line[start:start + 500]
                matches.append({"relative_path": path.relative_to(root).as_posix(),
                    "line": line_number, "excerpt": excerpt, "file_sha256": digest,
                    "evidence_kind": "host_qa_file_unverified" if path.parent.name == "qa" and path.suffix == ".json" else "working_note_untrusted"})
                if len(matches) == limit:
                    return {"success": True, "matches": matches, "scanned_files": scanned,
                            "skipped_files": skipped, "complete": False,
                            "notice": "Result limit reached. Read cited files; text matches do not verify facts or current geometry."}
    return {"success": True, "matches": matches, "scanned_files": scanned,
            "skipped_files": skipped, "complete": not budget_exhausted and skipped == 0,
            "notice": "Project-local literal search only. No match is not proof of absence; skipped files and scan limits are reported."}
