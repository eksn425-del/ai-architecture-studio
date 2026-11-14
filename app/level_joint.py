"""Measure an axis-aligned horizontal join using native face sections in world millimetres."""
from __future__ import annotations

TOOL = "sketchup_measure_level_joint"
TOLERANCE_MM = 0.05
PATH = {"type": "array", "items": {"type": "string", "minLength": 1, "maxLength": 200},
        "minItems": 1, "maxItems": 8}
PROPERTIES = {
    "negative_path": PATH, "positive_path": PATH,
    "axis": {"type": "string", "enum": ["x", "y"]},
    "position_mm": {"type": "number"}, "elevation_mm": {"type": "number"},
    "span_mm": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2},
}
SPEC = {
    "name": TOOL,
    "description": "Read-only full-width check for the horizontal edge between two owned parts "
                   "(e.g. stair top tread and landing). In world mm specify exact named paths on "
                   "the negative and positive sides of the x or y plane, its position, the shared "
                   "top elevation, and a [min,max] span on the other horizontal axis. "
                   "Returns covered and missing intervals for this revision; no headroom, "
                   "walkability, visual or code-compliance certification.",
    "inputSchema": {"type": "object", "properties": PROPERTIES,
                    "required": list(PROPERTIES), "additionalProperties": False},
}


def validate_joint(args: dict) -> None:
    if not isinstance(args, dict) or args.keys() != PROPERTIES.keys():
        raise ValueError("Provide exactly the level joint fields shown in the tool schema.")
    for key in ("negative_path", "positive_path"):
        path = args[key]
        if (not isinstance(path, list) or not 1 <= len(path) <= 8
                or any(not isinstance(name, str) or not name.strip() or len(name) > 200 for name in path)):
            raise ValueError("Level joints require two exact owned paths of one to eight names.")
    a, b = args["negative_path"], args["positive_path"]
    if a[:len(b)] == b or b[:len(a)] == a:
        raise ValueError("The two level joint paths must be disjoint.")
    span = args["span_mm"]
    if args["axis"] not in ("x", "y") or not isinstance(span, list) or len(span) != 2:
        raise ValueError("Use axis x or y and a two-number span on the other horizontal axis.")
    numbers = [*span, args["position_mm"], args["elevation_mm"]]
    if any(type(value) not in (int, float) or not -1e7 <= value <= 1e7 for value in numbers):
        raise ValueError("World coordinates must be finite millimetre numbers within +/-10,000,000.")
    if span[1] - span[0] <= TOLERANCE_MM:
        raise ValueError("The joint span must be ascending and wider than the tolerance.")


def _merge(intervals):
    merged = []
    for lo, hi in sorted(intervals):
        if hi - lo <= TOLERANCE_MM:
            continue
        if merged and lo <= merged[-1][1] + TOLERANCE_MM:
            merged[-1][1] = max(hi, merged[-1][1])
        else:
            merged.append([lo, hi])
    return merged


def _subtract(intervals, excluded):
    result = intervals
    for lo, hi in excluded:
        pieces = []
        for start, end in result:
            if hi <= start or lo >= end:
                pieces.append([start, end])
            else:
                pieces.extend([[start, min(end, lo)], [max(start, hi), end]])
        result = pieces
    return _merge(result)


def measure_joint(negative_faces, positive_faces, *, position_mm, elevation_mm, axis, span_mm):
    along = 0 if axis == "x" else 1
    across = 1 - along

    def edge(triangles, side):
        supported, crossing = [], []
        z_levels = set()
        for triangle in triangles:
            if len(triangle) != 3:
                continue
            z = triangle[0][2]
            if any(abs(point[2] - z) > TOLERANCE_MM for point in triangle):
                continue
            offsets = [p[along] - position_mm for p in triangle]
            offsets = [0 if abs(value) <= TOLERANCE_MM else value for value in offsets]
            if min(offsets) > 0 or max(offsets) < 0:
                continue
            section = [p[across] for p, distance in zip(triangle, offsets) if distance == 0]
            for index in range(3):
                next_index = (index + 1) % 3
                d1, d2 = offsets[index], offsets[next_index]
                if d1 * d2 < 0:
                    a, b = triangle[index][across], triangle[next_index][across]
                    section.append(a + (b - a) * d1 / (d1 - d2))
            if len(section) < 2:
                continue
            lo, hi = max(min(section), span_mm[0]), min(max(section), span_mm[1])
            if hi - lo <= TOLERANCE_MM:
                continue
            z_levels.add(round(z, 2))
            if abs(z - elevation_mm) > TOLERANCE_MM:
                continue
            if any(side * offset > 0 for offset in offsets):
                supported.append([lo, hi])
            if any(side * offset < 0 for offset in offsets):
                crossing.append([lo, hi])
        return _subtract(_merge(supported), _merge(crossing)), sorted(z_levels)

    negative, negative_levels = edge(negative_faces, -1)
    positive, positive_levels = edge(positive_faces, 1)
    shared = _merge([max(a, c), min(b, d)] for a, b in negative for c, d in positive)
    missing = _subtract([span_mm], shared)
    clean = lambda intervals: [[round(a, 3), round(b, 3)] for a, b in intervals]
    return {"status": "FULL_WIDTH" if not missing else "PARTIAL_WIDTH" if shared else "NO_SEAM",
            "negative_levels_at_plane_mm": negative_levels, "positive_levels_at_plane_mm": positive_levels,
            "shared_intervals_mm": clean(shared), "missing_intervals_mm": clean(missing),
            "covered_width_mm": round(sum(b - a for a, b in shared), 3),
            "tolerance_mm": TOLERANCE_MM}
