from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.oss_backends import SdkStdioMCPBackend  # noqa: E402


REQUIRED_TOOLS = {
    "ping",
    "scene_summary",
    "create_wall",
    "modify_wall",
    "delete_wall",
    "cut_opening",
    "create_slab",
    "create_roof",
    "inspect_entity",
    "verify_model",
    "view_snapshot",
}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Run a deterministic SAIE wall/opening/slab/roof/query/view/edit smoke against an already-running "
            "disposable SketchUp model. This script makes no architecture-model/LLM call."
        )
    )
    default_command = ROOT / ".venv" / "Scripts" / "saie-mcp.exe"
    p.add_argument("--command", default=str(default_command), help="Path to saie-mcp executable")
    p.add_argument(
        "--output-dir",
        type=Path,
        help="Ignored output directory. Defaults to runtime/saie-compat/smoke-<UTC timestamp>.",
    )
    return p


def compact_result(value: dict[str, Any]) -> dict[str, Any]:
    compact: dict[str, Any] = {
        "success": bool(value.get("success")),
        "isError": bool(value.get("isError")),
        "text": [],
        "images": 0,
    }
    for item in value.get("contentItems") or []:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "inputText":
            text = str(item.get("text") or "")
            compact["text"].append(text[:4000])
        elif item.get("type") == "inputImage":
            compact["images"] += 1
    return compact


def upstream_error(value: dict[str, Any]) -> str | None:
    if value.get("success") is False or value.get("isError") is True:
        return "MCP marked the call as an error."
    for item in value.get("contentItems") or []:
        if not isinstance(item, dict) or item.get("type") != "inputText":
            continue
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and payload.get("error"):
            return str(payload["error"])
    return None


def tool_payload(value: dict[str, Any]) -> dict[str, Any]:
    for item in value.get("contentItems") or []:
        if isinstance(item, dict) and item.get("type") == "inputText":
            try:
                parsed = json.loads(str(item.get("text") or ""))
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
    raise RuntimeError("SAIE did not return a JSON object for required verification.")


def persist_inline_images(step: str, value: dict[str, Any], output_dir: Path) -> list[str]:
    paths: list[str] = []
    for index, item in enumerate(value.get("contentItems") or []):
        if not isinstance(item, dict) or item.get("type") != "inputImage":
            continue
        image_url = str(item.get("imageUrl") or "")
        if not image_url.startswith("data:image/") or "," not in image_url:
            continue
        header, encoded = image_url.split(",", 1)
        extension = "jpg" if "jpeg" in header else "png"
        path = output_dir / f"{step}-{index + 1}.{extension}"
        path.write_bytes(base64.b64decode(encoded))
        paths.append(str(path))
    return paths


def main() -> int:
    args = parser().parse_args()
    command = Path(args.command).expanduser().resolve()
    if not command.is_file() and not shutil.which(args.command):
        print(f"ERROR: SAIE MCP executable not found: {args.command}", file=sys.stderr)
        return 2

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = (args.output_dir or ROOT / "runtime" / "saie-compat" / f"smoke-{stamp}").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    backend = SdkStdioMCPBackend("saie", str(command))
    tools = backend.list_tools()
    tool_names = {str(tool.get("name")) for tool in tools}
    (output_dir / "live-tools.json").write_text(json.dumps(tools, indent=2, ensure_ascii=False), encoding="utf-8")

    missing = sorted(REQUIRED_TOOLS - tool_names)
    if missing:
        (output_dir / "result.json").write_text(
            json.dumps({"status": "blocked", "missing_tools": missing, "tool_count": len(tools)}, indent=2),
            encoding="utf-8",
        )
        print("BLOCKED: live SAIE server is missing required tools: " + ", ".join(missing), file=sys.stderr)
        return 3

    steps: list[dict[str, Any]] = []

    def call(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        print(f"[SAIE smoke] {name}")
        value = backend.call_for_agent(name, arguments or {})
        error = upstream_error(value)
        images = persist_inline_images(f"{len(steps) + 1:02d}-{name}", value, output_dir)
        record = {"tool": name, "arguments": arguments or {}, "result": compact_result(value), "images": images}
        steps.append(record)
        if error:
            raise RuntimeError(f"{name} failed: {error}")
        return value

    try:
        call("ping")
        call("scene_summary")

        walls = [
            ("W_SOUTH", [[0, 0], [6000, 0]]),
            ("W_EAST", [[6000, 0], [6000, 6000]]),
            ("W_NORTH", [[6000, 6000], [0, 6000]]),
            ("W_WEST", [[0, 6000], [0, 0]]),
        ]
        for ai_id, centerline in walls:
            call(
                "create_wall",
                {
                    "ai_id": ai_id,
                    "centerline": centerline,
                    "thickness_mm": 200,
                    "height_mm": 3000,
                    "level": "GF",
                },
            )

        call(
            "cut_opening",
            {
                "ai_id": "DOOR_SOUTH_01",
                "wall_id": "W_SOUTH",
                "offset_mm": 2500,
                "width_mm": 1000,
                "height_mm": 2200,
                "sill_mm": 0,
            },
        )
        call(
            "create_slab",
            {
                "ai_id": "SLAB_GF",
                "polygon": [[0, 0], [6000, 0], [6000, 6000], [0, 6000]],
                "thickness_mm": 180,
                "top_or_bottom": "bottom",
                "base_z_mm": 0,
            },
        )
        call(
            "create_roof",
            {
                "ai_id": "ROOF_MAIN",
                "footprint": [[0, 0], [6000, 0], [6000, 6000], [0, 6000]],
                "kind": "gable",
                "pitch_deg": 25,
                "ridge_height_mm": 0,
                "eave_overhang_mm": 300,
                "base_z_mm": 3000,
            },
        )
        initial_verify = tool_payload(call(
            "verify_model",
            {
                "expected_ids": [
                    "W_SOUTH",
                    "W_EAST",
                    "W_NORTH",
                    "W_WEST",
                    "DOOR_SOUTH_01",
                    "SLAB_GF",
                    "ROOF_MAIN",
                ]
            },
        ))
        if initial_verify.get("status") != "clean":
            raise RuntimeError(f"Initial SAIE ID verification diverged: {initial_verify}")
        south = tool_payload(call("inspect_entity", {"ai_id": "W_SOUTH"}))
        openings = south.get("openings_spec") or []
        if south.get("type") != "wall" or not isinstance(south.get("wall_spec"), dict) or not any(
            isinstance(item, dict) and item.get("ai_id") == "DOOR_SOUTH_01" for item in openings
        ):
            raise RuntimeError(f"SAIE wall/opening metadata did not round-trip: {south}")
        call("view_snapshot", {"width": 1000, "height": 750, "quality": 75, "source": "view"})

        # Same-model edit proof.
        call(
            "modify_wall",
            {
                "ai_id": "W_EAST",
                "centerline": [[6000, 0], [6000, 6000]],
                "thickness_mm": 250,
                "height_mm": 3000,
                "level": "GF",
            },
        )
        east = tool_payload(call("inspect_entity", {"ai_id": "W_EAST"}))
        if (east.get("wall_spec") or {}).get("thickness_mm") != 250:
            raise RuntimeError(f"Modified wall spec did not persist: {east}")

        # Delete/repair proof on a wall without the test opening.
        call("delete_wall", {"ai_id": "W_NORTH"})
        call(
            "create_wall",
            {
                "ai_id": "W_NORTH",
                "centerline": [[6000, 6000], [0, 6000]],
                "thickness_mm": 200,
                "height_mm": 3000,
                "level": "GF",
            },
        )
        final_verify = tool_payload(call(
            "verify_model",
            {
                "expected_ids": [
                    "W_SOUTH",
                    "W_EAST",
                    "W_NORTH",
                    "W_WEST",
                    "DOOR_SOUTH_01",
                    "SLAB_GF",
                    "ROOF_MAIN",
                ]
            },
        ))
        if final_verify.get("status") != "clean":
            raise RuntimeError(f"Final SAIE ID verification diverged: {final_verify}")
        call("scene_summary")
        call("view_snapshot", {"width": 1000, "height": 750, "quality": 75, "source": "view"})
    except Exception as error:
        payload = {
            "status": "failed",
            "error": str(error),
            "tool_count": len(tools),
            "steps": steps,
        }
        (output_dir / "result.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"FAIL: {error}\nEvidence: {output_dir}", file=sys.stderr)
        return 4

    payload = {
        "status": "passed",
        "tool_count": len(tools),
        "required_tools": sorted(REQUIRED_TOOLS),
        "steps": steps,
        "note": "Deterministic no-LLM smoke only. This is not an architecture-quality benchmark.",
    }
    (output_dir / "result.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"PASS: SAIE deterministic geometry smoke completed. Evidence: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
