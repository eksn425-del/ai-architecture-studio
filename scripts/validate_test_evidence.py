"""Validate a public K AI Studio test evidence folder and SHA-256 manifest.

No external dependencies. Does not generate evidence or infer test success.
Exit nonzero for absent/invalid current revision screenshots and mandatory data.
Usage:
  python scripts/validate_test_evidence.py docs/test-results/windows/DATE-run --write-manifest
  python scripts/validate_test_evidence.py docs/test-results/windows/DATE-run
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePath
import sys

VIEWS = ("front", "rear", "left", "right", "roof", "oblique")
MANDATORY = ("README.md", "run.json", "metrics.json", "errors.json", "review/review.md")
WHEN_COMMITTED = (
    "source-perspective.png",
    "model/write-verifications.json",
    "model/geometry-readback.json",
    "model/native-reopen.json",
    "review/critique.json",
)
STATES = {"PASS", "PARTIAL", "FAIL", "NOT_RUN", "BLOCKED"}
MANIFEST_FILE = "artifacts.json"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def _is_file_under(path: Path, base: Path) -> bool:
    return path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(base.resolve())


def _check(condition: bool, errors: list[str], msg: str) -> None:
    if not condition:
        errors.append(msg)


def _inventory(directory: Path) -> list[dict]:
    records = []
    # Windows Path ordering is case-insensitive; Linux Path ordering is not.
    # A GitHub Actions checkout must compare the SAME canonical file order as
    # Codex generated on Windows, otherwise unchanged manifests falsely fail.
    for path in sorted(
        directory.rglob("*"),
        key=lambda item: (
            item.relative_to(directory).as_posix().casefold(),
            item.relative_to(directory).as_posix(),
        ),
    ):
        if path.is_symlink():
            raise ValueError(f"Symlink not allowed in public evidence: {path}")
        if not path.is_file() or path.name == MANIFEST_FILE:
            continue
        relative = path.relative_to(directory).as_posix()
        records.append({"path": relative, "bytes": path.stat().st_size, "sha256": _hash(path)})
    return records


def _legacy_windows_newline_equivalent(directory: Path, previous: dict, inventory: list[dict]) -> bool:
    """Accept only exact CRLF<->LF checkout conversion in pre-2026-10-10 reports.

    Old Codex manifests were hashed on Windows before Git's text conversion.
    Future packages remain byte-exact. Binary evidence can NEVER differ.
    """
    if directory.name[:10] >= "2026-10-10":
        return False
    if not isinstance(previous, dict) or previous.get("schema_version") != 1:
        return False
    recorded = previous.get("files")
    if not isinstance(recorded, list) or len(recorded) != len(inventory):
        return False
    actual_by_name = {item["path"]: item for item in inventory}
    if len(actual_by_name) != len(recorded):
        return False
    for expected in recorded:
        if not isinstance(expected, dict) or expected.get("path") not in actual_by_name:
            return False
        name = expected["path"]
        actual = actual_by_name[name]
        if expected == actual:
            continue
        if not name.lower().endswith((".json", ".md", ".txt", ".rb", ".csv")):
            return False
        value = (directory / name).read_bytes()
        alternate = (
            value.replace(b"\\r\\n", b"\\n")
            if b"\\r\\n" in value else value.replace(b"\\n", b"\\r\\n")
        )
        if alternate == value or len(alternate) != expected.get("bytes"):
            return False
        if hashlib.sha256(alternate).hexdigest() != expected.get("sha256"):
            return False
    return True


def _manifest_mismatches(expected: dict, observed: list[dict], limit: int = 15) -> list[str]:
    """Report real changed paths, never suppress a failed integrity check."""
    recorded = expected.get("files", [])
    if not isinstance(recorded, list):
        return ["Manifest files is not a list"]
    old = {r.get("path"): r for r in recorded if isinstance(r, dict)}
    actual = {r["path"]: r for r in observed}
    differences = []
    for name in sorted(set(old) | set(actual)):
        before, after = old.get(name), actual.get(name)
        if before == after:
            continue
        if before is None:
            cause = "new file not recorded"
        elif after is None:
            cause = "recorded file absent"
        else:
            cause = (f"hash/size differs: expected {before.get('bytes')} bytes "
                     f"{str(before.get('sha256'))[:16]}, found {after['bytes']} bytes "
                     f"{after['sha256'][:16]}")
        differences.append(f"{name}: {cause}")
        if len(differences) >= limit:
            break
    return differences


def validate(directory: Path, *, write_manifest: bool = False) -> list[str]:
    errors: list[str] = []
    if not directory.is_dir() or directory.is_symlink():
        return [f"Missing regular report directory: {directory}"]
    directory = directory.resolve()
    for relative in MANDATORY:
        _check(_is_file_under(directory / relative, directory), errors, f"Missing required: {relative}")
    if errors:
        return errors
    try:
        run = _load(directory / "run.json")
        metrics = _load(directory / "metrics.json")
        error_entries = _load(directory / "errors.json")
    except (ValueError, OSError) as exc:
        return [f"Cannot parse report JSON: {exc}"]

    _check(isinstance(run, dict) and run.get("schema_version") == 1,
           errors, "run.json requires schema_version=1")
    if not isinstance(run, dict):
        return errors
    _check(run.get("test_id") == directory.name, errors, "test_id must match folder name")
    _check(run.get("status") in STATES, errors, "status requires PASS/PARTIAL/FAIL/NOT_RUN/BLOCKED")
    _check(isinstance(run.get("geometry_committed"), bool),
           errors, "geometry_committed must be true or false")
    _check(isinstance(run.get("source_case"), str) and bool(run.get("source_case")),
           errors, "source_case must identify the exact reference asset")
    _check(isinstance(run.get("base_commit"), str) and len(run["base_commit"]) == 40,
           errors, "base_commit must be a 40-character git commit SHA")
    model = run.get("model")
    _check(isinstance(model, dict) and bool(model.get("actual")) and bool(model.get("runtime")),
           errors, "model.actual and model.runtime must be real runtime observations")
    _check(isinstance(run.get("environment"), dict), errors, "environment missing")
    _check(isinstance(run.get("qa"), dict), errors, "qa object missing")
    _check(isinstance(metrics, dict) and metrics.get("schema_version") == 1,
           errors, "metrics.json requires schema_version=1")
    _check(isinstance(error_entries, list), errors, "errors.json must be a list")
    if isinstance(metrics, dict):
        for key in ("elapsed_ms", "tool_call_count", "failed_tool_calls",
                    "committed_writes", "full_root_rebuilds", "targeted_corrections",
                    "input_tokens", "output_tokens"):
            val = metrics.get(key, "__missing__")
            _check(val is None or (type(val) is int and val >= 0),
                   errors, f"metrics.{key} must be a nonnegative integer or null, not missing")
        _check(isinstance(metrics.get("token_source"), str),
               errors, "metrics.token_source must identify where usage came from or why unavailable")

    if run.get("geometry_committed") is True:
        # Reports from the new 2026-10-10 protocol must include real provider
        # usage evidence, including an honest zero-call report when no OSS
        # geometry method participated. Historical reports are grandfathered.
        is_new_adoption_run = directory.name[:10] >= "2026-10-10"
        if is_new_adoption_run:
            for relative in ("model/oss-method-ledger.json", "model/oss-method-adoption.json"):
                if not _is_file_under(directory / relative, directory):
                    errors.append(f"New model test missing OSS method evidence: {relative}")
            if not errors:
                try:
                    ledger = _load(directory / "model/oss-method-ledger.json")
                    adoption = _load(directory / "model/oss-method-adoption.json")
                    if (not isinstance(ledger, dict)
                            or ledger.get("status") not in {"committed_readback", "missing_or_unverified"}
                            or not isinstance(ledger.get("events"), list)):
                        errors.append("Invalid committed OSS method ledger")
                    if (not isinstance(adoption, dict) or adoption.get("schema_version") != 1
                            or type(adoption.get("any_oss_product_use")) is not bool
                            or not isinstance(adoption.get("actual_wrapped_calls"), dict)):
                        errors.append("Invalid OSS adoption assessment")
                    if not errors:
                        counts = adoption["actual_wrapped_calls"]
                        calls_present = any(type(n) is int and n > 0 for n in counts.values())
                        if calls_present != adoption["any_oss_product_use"]:
                            errors.append("OSS use status contradicts actual wrapped method call counts")
                        if (adoption["any_oss_product_use"]
                                and ledger.get("status") != "committed_readback"):
                            errors.append("OSS product use cannot be claimed without committed SKP readback")
                except (ValueError, OSError) as exc:
                    errors.append(f"Cannot read OSS method adoption evidence: {exc}")
        required = WHEN_COMMITTED + tuple(f"views/{v}.png" for v in VIEWS) + tuple(
            f"views/{v}.evidence.json" for v in VIEWS
        )
        sidecars: dict[str, dict] = {}
        for relative in required:
            path = directory / relative
            if not _is_file_under(path, directory):
                errors.append(f"Committed model missing evidence: {relative}")
                continue
            if relative.endswith(".png"):
                with path.open("rb") as image:
                    _check(image.read(8) == PNG_SIGNATURE, errors, f"Invalid PNG: {relative}")
            if relative.endswith(".evidence.json"):
                try:
                    item = _load(path)
                except (ValueError, OSError) as exc:
                    errors.append(f"Invalid canonical sidecar: {relative}: {exc}")
                    continue
                if not isinstance(item, dict):
                    errors.append(f"Sidecar must be object: {relative}")
                    continue
                sidecars[relative] = item
                expected_view = Path(relative).name.removesuffix(".evidence.json")
                _check(item.get("canonical_view") == expected_view,
                       errors, f"Canonical view label mismatch: {relative}")
                _check(isinstance(item.get("model_revisions"), dict)
                       and bool(item.get("model_revisions")),
                       errors, f"Missing model revision in {relative}")
                _check(isinstance(item.get("camera"), dict),
                       errors, f"Missing certified camera in {relative}")
        if len(sidecars) == 6:
            revisions = [json.dumps(x.get("model_revisions"), sort_keys=True) for x in sidecars.values()]
            _check(len(set(revisions)) == 1, errors,
                   "Six canonical screenshots use mismatched model revisions: recapture current views")

    if errors:
        return errors
    try:
        inventory = _inventory(directory)
    except (OSError, ValueError) as exc:
        return [str(exc)]
    if write_manifest:
        (directory / MANIFEST_FILE).write_text(
            json.dumps({"schema_version": 1, "files": inventory}, indent=2, ensure_ascii=False)
            + "\n", encoding="utf-8"
        )
    else:
        path = directory / MANIFEST_FILE
        if not path.is_file() or path.is_symlink():
            errors.append(f"Missing SHA256 manifest: {MANIFEST_FILE}; run --write-manifest")
        else:
            try:
                previous = _load(path)
                strict_match = previous.get("schema_version") == 1 and previous.get("files") == inventory
                legacy_newlines_only = (
                    not strict_match
                    and _legacy_windows_newline_equivalent(directory, previous, inventory)
                )
                if not (strict_match or legacy_newlines_only):
                    errors.append("Manifest mismatch: report file contents changed or files are missing")
                    for item in _manifest_mismatches(previous, inventory):
                        errors.append("Manifest detail: " + item)
                if legacy_newlines_only:
                    print("LEGACY_NOTE: Windows text EOL normalization only:", directory)
            except (ValueError, OSError, AttributeError) as exc:
                errors.append(f"Invalid SHA256 manifest: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    problems = validate(args.directory, write_manifest=args.write_manifest)
    if problems:
        for problem in problems:
            print("EVIDENCE_ERROR:", problem, file=sys.stderr)
        return 1
    print("K AI Studio evidence validated:", args.directory)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
