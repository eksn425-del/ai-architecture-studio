"""Host-only READ-ONLY native evidence for a pre-opened SketchUp COPY.

Do not run against the original private owner SKP; make a safe disposable copy.
This does NOT open/save/modify SketchUp, call any language model or change the
K Studio geometry transaction. Requires the user's normal configured Kongxing
MCP, target SKP already open in SU2024, and explicit live GUID + root PID.
Usage (from repository root):
  python -m scripts.capture_native_deep_fingerprint --model "C:\\private\\bound-copy.skp" \
      --guid "REAL_LIVE_GUID" --root-pid 20606 \
      --output "C:\\private\\audit\\bound-reopened.json"
Then use python -m scripts.audit_native_delivery_stages on stage files. If an
historic before-save capture was not made, it is NOT_RUN; do not fabricate one.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from app.sketchup_mcp import SketchUpAdapter


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--guid", required=True)
    parser.add_argument("--root-pid", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = SketchUpAdapter().capture_native_deep_fingerprint(
        expected_model_path=args.model, expected_guid=args.guid,
        root_pid=args.root_pid, output_path=args.output,
    )
    print("READ_ONLY_CAPTURED:", args.output.resolve())
    print("MODEL_ROOT:", payload["root_name"], "GROUPS:", len(payload["groups"]),
          "ENTITIES:", payload["visited_entities"])
    print("GEOMETRY_SHA:", payload["root_geometry_material_sha256"])
    print("DELIVERY_STATUS: NOT_VERIFIED_BY_SINGLE_CAPTURE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
