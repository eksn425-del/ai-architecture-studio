from __future__ import annotations

import base64
import html
import math
from pathlib import Path

import ezdxf

from .models import DesignIR, ProjectContext


def _bounds(design: DesignIR) -> tuple[float, float, float, float]:
    points = [point for point in design.site.boundary]
    for obj in design.objects:
        points.extend(obj.footprint)
        points.extend(obj.polyline)
    if not points:
        points = [(0, 0), (40, 30)]
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    pad = max(max(xs) - min(xs), max(ys) - min(ys), 1) * 0.08
    return min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad


def _rect_circulation(polyline: list[tuple[float, float]], width: float) -> list[tuple[float, float]]:
    if len(polyline) < 2 or width <= 0:
        return polyline
    start, end = polyline[0], polyline[-1]
    length = math.hypot(end[0] - start[0], end[1] - start[1])
    if not length:
        return polyline
    ox = -(end[1] - start[1]) / length * width / 2
    oy = (end[0] - start[0]) / length * width / 2
    return [
        (start[0] + ox, start[1] + oy),
        (end[0] + ox, end[1] + oy),
        (end[0] - ox, end[1] - oy),
        (start[0] - ox, start[1] - oy),
    ]


def generate_drawing(project_dir: Path, design: DesignIR) -> tuple[Path, Path]:
    output_dir = project_dir / "outputs" / "drawings"
    output_dir.mkdir(parents=True, exist_ok=True)
    dxf_path = output_dir / "site-plan.dxf"
    svg_path = output_dir / "site-plan.svg"

    document = ezdxf.new("R2010")
    document.units = ezdxf.units.M
    for name, color in (("SITE", 8), ("MASS", 7), ("CIRCULATION", 4), ("LABELS", 2)):
        if name not in document.layers:
            document.layers.new(name=name, dxfattribs={"color": color})
    modelspace = document.modelspace()
    boundary = design.site.boundary
    if not boundary:
        site = next((obj for obj in design.objects if obj.type == "site_base"), None)
        boundary = site.footprint if site else []
    if boundary:
        modelspace.add_lwpolyline(boundary, close=True, dxfattribs={"layer": "SITE"})
    for obj in design.objects:
        if obj.type in {"site_base", "building_mass"} and obj.footprint:
            modelspace.add_lwpolyline(obj.footprint, close=True, dxfattribs={"layer": "MASS"})
            center = (sum(p[0] for p in obj.footprint) / len(obj.footprint), sum(p[1] for p in obj.footprint) / len(obj.footprint))
            modelspace.add_text(f"{obj.id} | {obj.name}", height=0.65, dxfattribs={"layer": "LABELS", "insert": center})
        elif obj.type == "circulation" and obj.polyline:
            polygon = _rect_circulation(obj.polyline, obj.width)
            if len(polygon) >= 3:
                modelspace.add_lwpolyline(polygon, close=True, dxfattribs={"layer": "CIRCULATION"})
            modelspace.add_lwpolyline(obj.polyline, dxfattribs={"layer": "CIRCULATION"})
    document.saveas(dxf_path)

    min_x, min_y, max_x, max_y = _bounds(design)
    width_px, height_px = 1100, 720
    margin = 76
    span_x, span_y = max_x - min_x, max_y - min_y
    scale = min((width_px - 2 * margin) / span_x, (height_px - 2 * margin) / span_y)

    def xy(point: tuple[float, float]) -> tuple[float, float]:
        return margin + (point[0] - min_x) * scale, height_px - margin - (point[1] - min_y) * scale

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width_px} {height_px}" role="img" aria-label="Site plan drawing">',
        '<rect width="100%" height="100%" fill="#f5f2e9"/>',
        '<path d="M0 624 H1100" stroke="#d4d0c4" stroke-width="1"/>',
    ]
    if boundary:
        coords = " ".join(f"{x:.1f},{y:.1f}" for x, y in (xy(p) for p in boundary))
        svg_parts.append(f'<polygon points="{coords}" fill="#e8e3d7" stroke="#53636b" stroke-width="2"/>')
    for obj in design.objects:
        if obj.type in {"site_base", "building_mass"} and obj.footprint:
            coords = " ".join(f"{x:.1f},{y:.1f}" for x, y in (xy(p) for p in obj.footprint))
            fill = "#e2d9c8" if obj.type == "site_base" else "#bd5d40"
            svg_parts.append(f'<polygon points="{coords}" fill="{fill}" stroke="#182930" stroke-width="2"/>')
            cx, cy = xy((sum(p[0] for p in obj.footprint) / len(obj.footprint), sum(p[1] for p in obj.footprint) / len(obj.footprint)))
            safe_label = html.escape(f"{obj.id} · {obj.name}")
            svg_parts.append(f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" dominant-baseline="middle" fill="#17282f" font-family="sans-serif" font-size="12">{safe_label}</text>')
        elif obj.type == "circulation" and len(obj.polyline) >= 2:
            coords = " ".join(f"{x:.1f},{y:.1f}" for x, y in (xy(p) for p in obj.polyline))
            stroke = max(3.0, obj.width * scale)
            svg_parts.append(f'<polyline points="{coords}" fill="none" stroke="#647e7e" stroke-width="{stroke:.1f}" stroke-linecap="square"/>')
            cx, cy = xy(obj.polyline[len(obj.polyline) // 2])
            svg_parts.append(f'<text x="{cx:.1f}" y="{cy - 12:.1f}" text-anchor="middle" fill="#19343a" font-family="sans-serif" font-size="11">{html.escape(obj.name)}</text>')
    svg_parts.extend([
        '<g transform="translate(1035 76)"><path d="M0 42 L0 0 M0 0 L-7 12 M0 0 L7 12" fill="none" stroke="#182930" stroke-width="2"/><text x="0" y="58" text-anchor="middle" fill="#182930" font-family="sans-serif" font-size="12">N</text></g>',
        f'<text x="44" y="678" fill="#53636b" font-family="sans-serif" font-size="12">{html.escape(design.concept.summary[:110])}</text>',
        "</svg>",
    ])
    svg_path.write_text("".join(svg_parts), encoding="utf-8")
    return dxf_path, svg_path


def generate_presentation(project_dir: Path, context: ProjectContext, design: DesignIR,
                          drawing_svg_path: Path, model_capture_path: Path | None) -> Path:
    output_dir = project_dir / "outputs" / "presentation"
    output_dir.mkdir(parents=True, exist_ok=True)
    presentation_path = output_dir / "presentation.html"
    drawing_svg = drawing_svg_path.read_text(encoding="utf-8") if drawing_svg_path.exists() else ""
    if model_capture_path and model_capture_path.exists():
        mime = "image/png"
        encoded = base64.b64encode(model_capture_path.read_bytes()).decode("ascii")
        model_src = f"data:{mime};base64,{encoded}"
    else:
        model_src = ""
    title = html.escape(context.project_name)
    concept = html.escape(design.concept.summary)
    intent = html.escape(context.user_intent)
    objects = [obj for obj in design.objects if obj.type == "building_mass"]
    mass_rows = "".join(
        f'<li><span>{html.escape(obj.id)}</span><strong>{html.escape(obj.name)}</strong><em>{obj.floors}F · {obj.height:g} m</em></li>'
        for obj in objects
    )
    model_preview = f'<img src="{model_src}" alt="SketchUp viewport capture">' if model_src else '<div class="empty">SketchUp viewport capture will appear here after model build.</div>'
    svg_data = f'<div class="drawing">{drawing_svg}</div>' if drawing_svg else '<div class="empty">Site drawing will appear here after design preparation.</div>'
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} — A3 Preview</title>
<style>
@page {{ size: A3 landscape; margin: 0; }}
* {{ box-sizing:border-box }} body {{ margin:0;background:#c8c9c4;color:#182930;font-family:Georgia,'Times New Roman',serif }}
.board {{ width:1120px; min-height:792px; margin:24px auto; padding:38px 44px 34px; background:#f5f2e9; display:grid; grid-template-rows:auto 1fr auto; gap:23px; box-shadow:0 18px 58px #1321262b }}
header {{ display:flex; justify-content:space-between; align-items:flex-start; border-bottom:1px solid #263b40; padding-bottom:17px }}
.eyebrow,.kicker {{ font:11px/1.4 Arial,sans-serif; letter-spacing:.16em; text-transform:uppercase; color:#7d4c3c }}
h1 {{ margin:8px 0 0; font-size:35px; line-height:1.05; font-weight:500; letter-spacing:-.035em }}
.issue {{ text-align:right; font:11px/1.65 Arial,sans-serif; letter-spacing:.08em; text-transform:uppercase }}
.grid {{ display:grid; grid-template-columns:1.08fr 1fr .72fr; gap:20px; min-height:0 }}
.panel {{ min-width:0; border-top:3px solid #182930; padding-top:11px }}
.panel h2 {{ margin:0 0 11px; font:11px Arial,sans-serif; letter-spacing:.15em; text-transform:uppercase }}
.drawing svg {{ width:100%; height:auto; display:block; border:1px solid #d7d2c7 }}
.model {{ aspect-ratio:4/3; overflow:hidden; background:#e2e6e2; display:grid; place-items:center }}
.model img {{ width:100%; height:100%; object-fit:cover }}
.empty {{ min-height:100%; display:grid; place-items:center; padding:25px; color:#657474; text-align:center; font:13px/1.5 Arial,sans-serif; background:#e9e7de }}
.concept {{ margin:0 0 18px; font-size:18px; line-height:1.4 }}
.intent {{ margin:0 0 22px; font:12px/1.55 Arial,sans-serif; color:#5a686a }}
ul {{ list-style:none; padding:0; margin:0 }} li {{ display:grid; grid-template-columns:55px 1fr; gap:3px 6px; padding:10px 0; border-top:1px solid #cbc9bd }} li span {{ grid-row:span 2; font:11px Arial,sans-serif; color:#9c563d }} li strong {{ font:14px Georgia,serif; font-weight:500 }} li em {{ font:10px Arial,sans-serif; color:#677776; font-style:normal }}
footer {{ display:flex; justify-content:space-between; align-items:end; border-top:1px solid #263b40; padding-top:12px; font:10px/1.45 Arial,sans-serif; letter-spacing:.06em; text-transform:uppercase; color:#58686a }}
@media (max-width:900px) {{ .board {{ width:100%; margin:0; padding:24px; min-height:100vh }} .grid {{ grid-template-columns:1fr }} h1 {{ font-size:29px }} }}
</style></head><body><main class="board">
<header><div><div class="eyebrow">AI Architecture Studio · Demo 0.1</div><h1>{title}</h1></div><div class="issue">Design study<br>Codex brain / SketchUp model<br>01 — 01</div></header>
<section class="grid"><article class="panel"><h2>01 / Site plan</h2>{svg_data}</article><article class="panel"><h2>02 / Model view</h2><div class="model">{model_preview}</div></article><article class="panel"><h2>03 / Design note</h2><p class="concept">{concept}</p><p class="intent">{intent}</p><div class="kicker">Program massing</div><ul>{mass_rows}</ul></article></section>
<footer><span>AI Architecture Studio · Local demo preview</span><span>Working dimensions in meters · Schematic only</span><span>v0.1</span></footer></main></body></html>"""
    presentation_path.write_text(document, encoding="utf-8")
    return presentation_path
