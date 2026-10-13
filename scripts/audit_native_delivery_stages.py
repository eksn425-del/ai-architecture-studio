"""Strict, READ-ONLY three-stage native SKP delivery investigation.

Usage:
  python -m scripts.audit_native_delivery_stages before-save.json bound-reopened.json clean-download-reopened.json --json
  python -m scripts.audit_native_delivery_stages before-save.json bound-reopened.json clean-download-reopened.json --receipt native_delivery_checkpoint.json --downloaded-skp clean.skp --json

Capture each fingerprint by the SAME host-side deep native read-only procedure:
per-name world-space transforms, complete nested face/edge/material topology.
Never compare just revision, model GUID, image similarity, file size, root bounds
or direct group count; never patch the user's original SKP from this script.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from scripts.compare_native_replay import compare


def audit_stages(before_save: dict[str, Any], bound_reopened: dict[str, Any],
                 clean_download_reopened: dict[str, Any],
                 *, receipt: dict[str, Any] | None = None,
                 downloaded_bytes: bytes | None = None) -> dict[str, Any]:
    if receipt is not None:
        if receipt.get("status") != "UNVERIFIED_NATIVE_REOPEN":
            raise ValueError("Expected original unverified native checkpoint, not an asserted PASS.")
        expected = (receipt.get("download_candidate") or {}).get("sha256")
        if not isinstance(expected, str) or len(expected) != 64 or downloaded_bytes is None:
            raise ValueError("Receipt comparison needs real downloaded candidate bytes.")
        if hashlib.sha256(downloaded_bytes).hexdigest() != expected:
            return {"status": "FAIL", "reason": "download_candidate_sha_mismatch",
                    "native_delivery_proven": False, "transitions": []}
    stages = [
        ("before_save_to_bound_reopen", before_save, bound_reopened),
        ("bound_reopen_to_clean_download_reopen", bound_reopened, clean_download_reopened),
        ("before_save_to_clean_download_reopen", before_save, clean_download_reopened),
    ]
    findings = [{"transition": label, "comparison": compare(left, right)}
                for label, left, right in stages]
    failed = [item["transition"] for item in findings if item["comparison"]["status"] != "PASS"]
    return {
        "schema_version": 1,
        "status": "PASS" if not failed else "FAIL",
        "native_delivery_proven": not failed,
        "first_failing_transition": failed[0] if failed else None,
        "failed_transitions": failed,
        "transitions": findings,
        "limitations": [
            "PASS applies only to the three actual read-only native fingerprints supplied.",
            "No claim about new images, user edit/save/reopen, strict blank replay, or visual source fidelity.",
        ],
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("before_save", type=Path)
    p.add_argument("bound_reopened", type=Path)
    p.add_argument("clean_download_reopened", type=Path)
    p.add_argument("--receipt", type=Path)
    p.add_argument("--downloaded-skp", type=Path)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    if bool(args.receipt) != bool(args.downloaded_skp):
        p.error("--receipt and --downloaded-skp must be provided together")
    load = lambda path: json.loads(path.read_text(encoding="utf-8"))
    report = audit_stages(load(args.before_save), load(args.bound_reopened),
                          load(args.clean_download_reopened),
                          receipt=load(args.receipt) if args.receipt else None,
                          downloaded_bytes=args.downloaded_skp.read_bytes() if args.downloaded_skp else None)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(report["status"], report.get("first_failing_transition") or "")
        for finding in report["transitions"]:
            print(finding["transition"], finding["comparison"]["status"])
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
