from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.codex_parity import prepare_codex_parity_workspace  # noqa: E402
from app.project_ruby import ProjectRubyExecutor  # noqa: E402
from app.sketchup_mcp import ConfiguredSketchUpMCP, SketchUpAdapter  # noqa: E402
from app.workspace_ruby import run_workspace_ruby  # noqa: E402


V1_SOURCE = """# Codex parity deterministic smoke v1
ents = root.entities

make_box = lambda do |parent, name, x0, y0, z0, x1, y1, z1|
  group = parent.add_group
  group.name = name
  face = group.entities.add_face(
    Geom::Point3d.new(x0, y0, z0),
    Geom::Point3d.new(x1, y0, z0),
    Geom::Point3d.new(x1, y1, z0),
    Geom::Point3d.new(x0, y1, z0)
  )
  raise "Could not create face for #{name}" unless face
  face.reverse! if face.normal.z < 0
  face.pushpull(z1 - z0)
  group
end

make_box.call(ents, 'Base_Plinth', 0, 0, 0, 12.m, 8.m, 0.35.m)
make_box.call(ents, 'West_Wing', 0.6.m, 0.8.m, 0.35.m, 5.4.m, 7.2.m, 4.2.m)
make_box.call(ents, 'East_Wing', 6.4.m, 1.2.m, 0.35.m, 11.4.m, 6.8.m, 6.0.m)
make_box.call(ents, 'Upper_Bridge', 4.7.m, 2.8.m, 3.4.m, 7.2.m, 5.0.m, 4.0.m)
model.active_view.zoom_extents
"""


V2_SOURCE = """# Codex parity deterministic smoke v2
ents = root.entities

make_box = lambda do |parent, name, x0, y0, z0, x1, y1, z1|
  group = parent.add_group
  group.name = name
  face = group.entities.add_face(
    Geom::Point3d.new(x0, y0, z0),
    Geom::Point3d.new(x1, y0, z0),
    Geom::Point3d.new(x1, y1, z0),
    Geom::Point3d.new(x0, y1, z0)
  )
  raise "Could not create face for #{name}" unless face
  face.reverse! if face.normal.z < 0
  face.pushpull(z1 - z0)
  group
end

make_box.call(ents, 'Base_Plinth', 0, 0, 0, 12.m, 8.m, 0.35.m)
make_box.call(ents, 'West_Wing', 0.6.m, 0.8.m, 0.35.m, 5.4.m, 7.2.m, 4.2.m)
make_box.call(ents, 'East_Wing', 6.4.m, 1.2.m, 0.35.m, 11.4.m, 6.8.m, 6.0.m)
make_box.call(ents, 'Upper_Bridge', 4.7.m, 2.8.m, 3.4.m, 7.2.m, 5.0.m, 4.0.m)
make_box.call(ents, 'North_Terrace', 2.2.m, 6.6.m, 2.7.m, 9.8.m, 7.8.m, 3.05.m)

roof = ents.add_group
roof.name = 'Sloped_Roof_Profile'
profile = roof.entities.add_face(
  Geom::Point3d.new(0.6.m, 0.8.m, 4.2.m),
  Geom::Point3d.new(3.0.m, 0.8.m, 5.8.m),
  Geom::Point3d.new(5.4.m, 0.8.m, 4.2.m)
)
raise 'Could not create sloped roof profile' unless profile
profile.pushpull(6.4.m)

marker = ents.add_group
marker.name = 'Entry_Canopy'
canopy = marker.entities.add_face(
  Geom::Point3d.new(4.5.m, -0.6.m, 2.7.m),
  Geom::Point3d.new(7.5.m, -0.6.m, 2.7.m),
  Geom::Point3d.new(7.0.m, 1.2.m, 3.2.m),
  Geom::Point3d.new(5.0.m, 1.2.m, 3.2.m)
)
raise 'Could not create canopy face' unless canopy
canopy.pushpull(0.18.m)
model.active_view.zoom_extents
"""


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Validate the persistent Codex-parity Ruby workflow against an already-open verified disposable SketchUp model. "
            "This script does not invoke an architecture LLM."
        )
    )
    p.add_argument("--project-id", default="codex-parity-smoke")
    return p


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def main() -> int:
    args = parser().parse_args()
    runtime_root = (ROOT / "runtime").resolve()
    project_dir = runtime_root / "projects" / args.project_id
    workspace = prepare_codex_parity_workspace(project_dir / "runtime" / "agent_workspace")
    model_root = (project_dir / "outputs" / "model").resolve()

    mcp = ConfiguredSketchUpMCP(timeout_seconds=180)
    adapter = SketchUpAdapter(mcp)
    identity = adapter.get_active_model_identity()
    active_path = Path(str(identity.get("model_path") or "")).resolve()
    guid = str(identity.get("model_guid") or "")

    if not active_path.is_relative_to(model_root):
        print(f"BLOCKED: active model is outside {model_root}: {active_path}", file=sys.stderr)
        return 2
    if active_path.suffix.lower() != ".skp" or not active_path.name.lower().startswith("blank-disposable-"):
        print("BLOCKED: active model must be a blank-disposable project .skp copy.", file=sys.stderr)
        return 2
    if not guid:
        print("BLOCKED: SketchUp did not return a model GUID.", file=sys.stderr)
        return 2

    state: dict[str, dict[str, Any]] = {}
    executor = ProjectRubyExecutor(
        runtime_root,
        args.project_id,
        expected_model_path=active_path,
        expected_model_guid=guid,
        mcp=mcp,
        ruby_state=state,
        adapter=adapter,
    )

    script_path = workspace / "scripts" / "parity_geometry.rb"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_dir = project_dir / "runtime" / "codex-parity-smoke" / stamp
    evidence_dir.mkdir(parents=True, exist_ok=True)

    try:
        script_path.write_text(V1_SOURCE, encoding="utf-8", newline="\n")
        first = run_workspace_ruby(
            executor,
            agent_workspace=workspace,
            arguments={"script_id": "parity_geometry", "relative_path": "scripts/parity_geometry.rb"},
        )
        first_state = dict(state.get("parity_geometry") or {})

        script_path.write_text(V2_SOURCE, encoding="utf-8", newline="\n")
        second = run_workspace_ruby(
            executor,
            agent_workspace=workspace,
            arguments={"script_id": "parity_geometry", "relative_path": "scripts/parity_geometry.rb"},
        )
        second_state = dict(state.get("parity_geometry") or {})

        views = {
            "iso": ([20, -16, 15], [6, 4, 2.5], [0, 0, 1]),
            "top": ([6, 4, 28], [6, 4, 0], [0, 1, 0]),
            "south": ([6, -24, 5], [6, 4, 3], [0, 0, 1]),
            "east": ([26, 4, 5], [6, 4, 3], [0, 0, 1]),
        }
        captures: dict[str, str] = {}
        for name, (eye, target, up) in views.items():
            adapter.set_camera(eye, target, up_m=up)
            image = evidence_dir / f"{name}.png"
            adapter.capture_view(image, width=1200, height=800, zoom_extents=False)
            if not image.is_file() or image.stat().st_size <= 0:
                raise RuntimeError(f"SketchUp did not write {name} review image.")
            captures[name] = str(image.relative_to(project_dir))

        payload = {
            "status": "passed",
            "project_id": args.project_id,
            "active_model": active_path.name,
            "workspace": str(workspace.relative_to(project_dir)),
            "script": str(script_path.relative_to(project_dir)),
            "first_revision": first_state,
            "second_revision": second_state,
            "same_root": first_state.get("root_pid") == second_state.get("root_pid"),
            "revision_progression": [first_state.get("revision"), second_state.get("revision")],
            "captures": captures,
            "first_success": bool(first.get("success")),
            "second_success": bool(second.get("success")),
            "note": "Deterministic persistent-script harness smoke only; no architecture model was called.",
        }
        if payload["revision_progression"] != [1, 2] or not payload["same_root"]:
            raise RuntimeError(f"Persistent revision/root continuity failed: {payload}")
        _write_json(evidence_dir / "result.json", payload)
        print(f"PASS: Codex parity persistent-script smoke completed. Evidence: {evidence_dir}")
        return 0
    except Exception as error:
        _write_json(
            evidence_dir / "result.json",
            {
                "status": "failed",
                "error": str(error),
                "state": state,
                "active_model": active_path.name,
            },
        )
        print(f"FAIL: {error}\nEvidence: {evidence_dir}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
