"""Small typed SU surface shared by official Harnesses; no model-authored code.

The host compiles validated geometry data and uses the existing ProjectRuby
transaction, atomic document/root checks, path KEEP guard and disk checkpoint.
This module does not implement an agent loop or contain a building recipe.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import math
import re
import uuid
from pathlib import Path

from .agent_tools import AgentToolContext, canonical_camera_from_bounds_mm
from .level_joint import SPEC as LEVEL_JOINT_SPEC, TOOL as LEVEL_JOINT_TOOL
from .project_ruby import ProjectRubyExecutor

NAMES = frozenset({"sketchup_model_state", "sketchup_apply_parts", "sketchup_inspect_part", "sketchup_view", "sketchup_save_plan", LEVEL_JOINT_TOOL})
SCRIPT_ID = "harness_building"
STAGES = ("structure", "enclosure", "sample", "repetition", "circulation", "finish", "correction")


def number(value, label, limit=100000):
    if type(value) not in (int, float) or not -limit <= value <= limit:
        raise ValueError(f"{label} must be a finite millimetre number within +/-{limit}.")
    return value


def vector(value, label):
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError(f"{label} requires three coordinates.")
    return [number(x, label) for x in value]


def validate_color(color, label):
    if not isinstance(color, list) or len(color) != 3 or any(type(c) is not int or not 0 <= c <= 255 for c in color):
        raise ValueError(f"{label} is RGB 0..255.")


def validate_window_bay(piece, repeat, step, rotation):
    width, thickness, height = vector(piece["size"], "size")
    vector(piece["origin"], "origin")
    opening = piece["opening"]
    if not isinstance(opening, list) or len(opening) != 4:
        raise ValueError("Opening needs [offset, sill, width, height] in mm.")
    offset, sill, opening_width, opening_height = [number(value, "opening") for value in opening]
    frame = number(piece["frame_width_mm"], "frame_width_mm")
    depth = number(piece["frame_depth_mm"], "frame_depth_mm")
    glass = number(piece.get("glass_thickness_mm", 6), "glass_thickness_mm")
    recess = number(piece["recess_mm"], "recess_mm")
    if min(offset, sill, width - offset - opening_width, height - sill - opening_height) < 1:
        raise ValueError("Window opening must be enclosed by at least 1 mm of wall on all four sides.")
    if frame < 1 or min(opening_width, opening_height) - 2 * frame < 1:
        raise ValueError("Frame must be at least 1 mm wide and leave a clear pane in both directions.")
    if not 1 <= glass <= depth or recess < 0 or recess + depth > thickness:
        raise ValueError("Frame must fit inside wall thickness after the recess, with glass at least 1 mm thick fitting inside the frame.")
    for key in ("frame_color", "glass_color"):
        if key in piece:
            validate_color(piece[key], key)
    if not 0 <= number(piece.get("glass_alpha", 0.45), "glass_alpha", 1) <= 1:
        raise ValueError("glass_alpha must be between 0 and 1.")
    if repeat > 1:
        angle = math.radians(rotation)
        dx, dy, dz = step
        along = dx * math.cos(angle) + dy * math.sin(angle)
        across = -dx * math.sin(angle) + dy * math.cos(angle)
        dimensions = (width, thickness, height)
        if all(abs(delta) + 1e-6 < size for delta, size in zip((along, across, dz), dimensions)):
            raise ValueError("Repeated bays overlap; step is in part axes after rotation and needs at least one full bay dimension.")


def profile_vertices(piece):
    """Sample a closed planar cubic Bezier perimeter; no code or topology escapes."""
    segments=piece['segments']; samples=piece.get('samples',8)
    if not isinstance(segments,list) or not 2<=len(segments)<=32 or type(samples) is not int or not 4<=samples<=16 or len(segments)*samples>256:
        raise ValueError('Profile requires 2..32 cubic segments, 4..16 samples each, at most 256 vertices.')
    for segment in segments:
        if not isinstance(segment,list) or len(segment)!=4:raise ValueError('Each cubic segment needs four XYZ control points.')
        for point in segment:vector(point,'control point')
    for i,segment in enumerate(segments):
        if any(abs(a-b)>0.001 for a,b in zip(segment[-1],segments[(i+1)%len(segments)][0])):
            raise ValueError('Profile segments must join and close.')
    controls=[p for segment in segments for p in segment]
    origin=controls[0]; normal=None
    for i in range(1,len(controls)-1):
        a=[controls[i][k]-origin[k] for k in range(3)]; b=[controls[i+1][k]-origin[k] for k in range(3)]
        n=[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
        length=math.sqrt(sum(x*x for x in n))
        if length>0.000001:normal=[x/length for x in n];break
    if normal is None or any(abs(sum((p[k]-origin[k])*normal[k] for k in range(3)))>0.001 for p in controls):
        raise ValueError('Profile controls must form a nondegenerate plane.')
    points=[]
    for segment in segments:
        for i in range(samples):
            t=i/samples; weights=((1-t)**3,3*(1-t)**2*t,3*(1-t)*t*t,t**3)
            points.append([sum(weights[j]*segment[j][k] for j in range(4)) for k in range(3)])
    return points


def validate_parts(arguments):
    if set(arguments) != {"parts"}:
        raise ValueError("Only parts is accepted; no code, paths or lifecycle options.")
    parts = copy.deepcopy(arguments["parts"])
    if not isinstance(parts, list) or not 1 <= len(parts) <= 32:
        raise ValueError("Supply 1..32 named parts per call.")
    seen, count, bay_count = set(), 0, 0
    for part in parts:
        if not isinstance(part, dict) or set(part) != {"name", "pieces"}:
            raise ValueError("Each part requires exactly name and pieces.")
        name = part["name"]
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", name) or name in seen:
            raise ValueError("Part names must be distinct ASCII identifiers, max 64 characters.")
        seen.add(name)
        pieces = part["pieces"]
        if not isinstance(pieces, list) or not 1 <= len(pieces) <= 300:
            raise ValueError("Each part requires 1..300 pieces.")
        for piece in pieces:
            if not isinstance(piece, dict):
                raise ValueError("Invalid piece.")
            kind = piece.get("kind")
            if not isinstance(kind, str):
                raise ValueError("Piece requires a documented kind.")
            required = {"box": {"origin", "size"}, "polygon": {"vertices", "extrude"},
                        "cylinder": {"origin", "radius", "height"}, "profile":{"segments","extrude"},
                        "window_bay": {"origin", "size", "opening", "frame_width_mm", "frame_depth_mm", "recess_mm"}}.get(kind)
            optional={"kind", "color", "alpha", "repeat", "step", "rotation_deg", "smooth"}
            if kind=='profile':optional.add('samples')
            if kind == "window_bay":
                optional = (optional - {"alpha", "smooth"}) | {"frame_color", "glass_color", "glass_alpha", "glass_thickness_mm"}
            if required is None or not required.issubset(piece) or set(piece) - (required | optional):
                raise ValueError("Piece must use a documented box, polygon, cylinder, profile or window_bay schema.")
            if type(piece.get('smooth',False)) is not bool:raise ValueError('smooth must be boolean.')
            if kind=='profile':
                piece['vertices']=profile_vertices(piece)
                piece.pop('segments');piece.pop('samples',None);piece['kind']='polygon'
            if kind in {"box", "cylinder"}:
                vector(piece["origin"], "origin")
            if kind == "box" and any(x <= 0 for x in vector(piece["size"], "size")):
                raise ValueError("Box dimensions must be positive.")
            if kind == "cylinder" and any(number(piece[k], k) <= 0 for k in ("radius", "height")):
                raise ValueError("Cylinder dimensions must be positive.")
            if kind in {"polygon","profile"}:
                vertices = piece["vertices"]
                if not isinstance(vertices, list) or not 3 <= len(vertices) <= (256 if kind=='profile' else 48):
                    raise ValueError("Polygon needs bounded coplanar perimeter vertices.")
                for v in vertices:
                    vector(v, "vertex")
                number(piece["extrude"], "extrude")
            validate_color(piece.get("color", [190, 180, 160]), "color")
            alpha = number(piece.get("alpha", 1), "alpha", 1)
            if alpha < 0:
                raise ValueError("alpha is 0..1.")
            repeat = piece.get("repeat", 1)
            if type(repeat) is not int or not 1 <= repeat <= 100:
                raise ValueError("repeat is 1..100.")
            step = vector(piece.get("step", [0, 0, 0]), "step")
            if any(abs(c * (repeat-1)) > 100000 for c in step):
                raise ValueError("Repeated translation exceeds limit.")
            rotation = number(piece.get("rotation_deg", 0), "rotation_deg", 360)
            if kind == "window_bay":
                validate_window_bay(piece, repeat, step, rotation)
                bay_count += 1
            count += repeat
    if count > 3000:
        raise ValueError("At most 3000 pieces per operation.")
    if bay_count > 128:
        raise ValueError("At most 128 window bay definitions fit the native method ledger per operation.")
    return parts


def compile_parts(arguments):
    parts = validate_parts(arguments)
    literal = ProjectRubyExecutor._ruby_string(json.dumps(parts, ensure_ascii=True, allow_nan=False))
    return "parts = JSON.parse(" + literal + ")\n" + r'''
parts.each do |part|
  matches = root.entities.select do |entity|
    (entity.is_a?(Sketchup::Group) || entity.is_a?(Sketchup::ComponentInstance)) && entity.name == part['name']
  end
  raise 'Part name must resolve to one existing group' if matches.size > 1 || (matches.first && !matches.first.is_a?(Sketchup::Group))
  group = matches.first
  if group
    if part['pieces'].any? { |piece| piece['kind'] == 'window_bay' }
      axes = group.transformation
      x, y, z = [axes.xaxis, axes.yaxis, axes.zaxis]
      unless [x, y, z].all? { |axis| (axis.length - 1.0).abs < 1e-6 } && x.cross(y).dot(z) > 1.0 - 1e-6
        raise 'Existing part axes are scaled, skewed or mirrored; use the scoped existing-model workflow'
      end
    end
    clear_owned_contents.call([part['name']])
  else
    group = root.entities.add_group
    group.name = part['name']
  end
  part['pieces'].each_with_index do |piece, index|
    window_bay = piece['kind'] == 'window_bay'
    name = "piece_#{index}"
    if window_bay
      child = build_window_bay.call(group, piece, name)
    else
      child = group.entities.add_group
      child.name = name
      ent = child.entities
    end
    origin = piece.fetch('origin', [0,0,0])
    case piece['kind']
    when 'box'
      x,y,z = origin.map { |n| n.mm }
      w,d,h = piece['size'].map { |n| n.mm }
      face = ent.add_face([x,y,z], [x+w,y,z], [x+w,y+d,z], [x,y+d,z])
      raise 'Degenerate box base' unless face
      face.reverse! if face.normal.z < 0
      face.pushpull(h)
    when 'polygon'
      face = ent.add_face(piece['vertices'].map { |v| v.map { |n| n.mm } })
      raise 'Nonplanar or degenerate polygon' unless face
      face.pushpull(piece['extrude'].mm) unless piece['extrude'] == 0
    when 'cylinder'
      edges = ent.add_circle(origin.map { |n| n.mm }, [0,0,1], piece['radius'].mm, 24)
      face = ent.add_face(edges)
      face.reverse! if face.normal.z < 0
      face.pushpull(piece['height'].mm)
    end
    unless window_bay
      rgb = piece.fetch('color', [190,180,160])
      alpha = piece.fetch('alpha', 1)
      material_name = 'KStudioAB_' + rgb.join('_') + '_' + alpha.to_s
      material = model.materials[material_name]
      unless material
        material = model.materials.add(material_name)
        material.color = Sketchup::Color.new(*rgb)
        material.alpha = alpha
      end
      ent.grep(Sketchup::Face).each { |f| f.material = material; f.back_material = material }
      if piece.fetch('smooth',false)
        ent.grep(Sketchup::Edge).each do |edge|
          faces = edge.faces
          if faces.length == 2 && faces[0].normal.dot(faces[1].normal) > 0.94
            edge.soft = true
            edge.smooth = true
          end
        end
      end
    end
    rotation = Geom::Transformation.rotation(origin.map { |n| n.mm }, [0,0,1], piece.fetch('rotation_deg',0).degrees)
    if window_bay
      rotation *= Geom::Transformation.translation(origin.map { |n| n.mm })
    end
    child.transform!(rotation)
    step = piece.fetch('step', [0,0,0])
    (1...piece.fetch('repeat',1)).each do |i|
      instance = group.entities.add_instance(child.definition, Geom::Transformation.translation(step.map { |n| (n*i).mm }) * child.transformation)
      instance.name = "piece_#{index}_#{i}"
      if window_bay && instance.definition.persistent_id != child.definition.persistent_id
        raise 'Repeated window bay did not retain its original component definition'
      end
    end
  end
end
'''


def tool_specs(writing=True, planning=False):
    specs = [
        {"name":"sketchup_save_plan","description":"Save the plain-language modeling plan in this project's fixed plan card, for the user's visible approval. Describe observations, estimates, coordinates, semantic parts and KEEP constraints. Does not approve or build anything. No filename or code accepted.","inputSchema":{"type":"object","properties":{"text":{"type":"string","minLength":40,"maxLength":16000}},"required":["text"],"additionalProperties":False}},
        {"name":"sketchup_model_state","description":"Read actual bound SU document identity and current owned root/revision. Always inspect before construction.","inputSchema":{"type":"object","properties":{},"additionalProperties":False}},
        {"name":"sketchup_inspect_part","description":"Read actual named owned part dimensions and hierarchy. Empty path reads the whole owned root. For a window bay, use its exact nested path (for example ['FrontEast','piece_0']) and window_bay:true to read native hole loops, frame/glass depth planes and definition instance count.","inputSchema":{"type":"object","properties":{"path":{"type":"array","items":{"type":"string"},"maxItems":8},"window_bay":{"type":"boolean"}},"required":["path"],"additionalProperties":False}},
        {"name":"sketchup_view","description":"Capture a real native viewport and return its image pixels for visual review; preserves display style. Views front/oblique/roof.","inputSchema":{"type":"object","properties":{"view":{"type":"string","enum":["front","oblique","roof"]}},"required":["view"],"additionalProperties":False}},
    ]
    if writing:
        specs.append(LEVEL_JOINT_SPEC)
        specs.append({"name": "sketchup_apply_parts", "description": (
            "Create/update only named direct architectural parts, retaining all others. Units are mm in the part's local axes. "
            "Each part has name (stable ASCII ID) and pieces. Piece kinds: box(origin[3],size[3]>0); "
            "polygon(vertices[3..48][3],extrude signed along normal); cylinder(origin[3],radius,height); "
            "profile(segments: 2..32 closed coplanar cubic Bezier segments of four XYZ points, extrude, samples default 8, max 256 sampled vertices). "
            "window_bay (SketchUp 2022+ API): origin at the outer lower left, size[width,thickness,height] along +X,+Y,+Z, "
            "opening[offset_from_left,sill,width,height], frame_width_mm, frame_depth_mm, recess_mm. "
            "Use for a straight opaque wall with one fully enclosed rectangular window; it creates separate solid Wall, Frame and Glass. "
            "Optional frame_color, glass_color (RGB), glass_alpha and glass_thickness_mm (default 6); only ordinary pieces support alpha and smooth. "
            "All pieces optionally color[RGB], rotation_deg about origin Z, repeat[1..100], step[3] along part axes. "
            "Check one bay before repeating. Window bay repeats share native component definitions and must not overlap. "
            "Keep terraces, roof, slabs and entrance separate. Max three successful writes per part per task. "
            "Returns actual commit, KEEP and checkpoint evidence. No code accepted."
        ), "inputSchema": {"type": "object", "properties": {"parts": {"type": "array", "minItems": 1,
            "maxItems": 32, "items": {"type": "object", "properties": {"name": {"type": "string"},
                "pieces": {"type": "array", "items": {"type": "object"}}}, "required": ["name", "pieces"],
                "additionalProperties": False}}, "construction_stage": {"type": "string", "enum": list(STAGES),
                    "description": "Optional label for the current bounded construction stage."}},
                "required": ["parts"], "additionalProperties": False}})
    return specs if planning else [s for s in specs if s['name']!='sketchup_save_plan']


class SUHarnessTools:
    def __init__(self, runtime_root, mcp):
        self.runtime_root, self.mcp = Path(runtime_root), mcp

    def prepare(self, *, project_dir, mcp_enabled, model_path=None, model_guid="", ruby_state=None, allow_plan=False, allowed_parts=None, stage_scoped=False, **_):
        project_dir = Path(project_dir).resolve()
        if mcp_enabled and (not model_path or not model_guid):
            raise ValueError("Verified test model path and GUID required.")
        executor = (ProjectRubyExecutor(self.runtime_root, project_dir.name,
            expected_model_path=Path(model_path), expected_model_guid=model_guid, mcp=self.mcp, ruby_state=ruby_state) if mcp_enabled else None)
        writes={}
        views={}
        quality={"backend":"sketchup", "views":{}, "writes":[]}
        def dispatch(name, arguments):
            if name not in NAMES:
                raise ValueError("Unknown controlled SU tool.")
            if name == "sketchup_save_plan":
                if not allow_plan or mcp_enabled:raise ValueError("Saving a plan is allowed only in the host's planning stage.")
                if set(arguments)!={"text"} or not isinstance(arguments['text'],str) or not 40<=len(arguments['text'])<=16000:
                    raise ValueError("Provide a bounded plain-language plan.")
                card=project_dir/'runtime/agent_workspace/notes/reconstruction_card.md'
                if any(p.is_symlink() for p in (project_dir,card.parent,card,project_dir/'runtime',project_dir/'runtime/agent_workspace')):
                    raise ValueError("Plan path must not be a link.")
                card.parent.mkdir(parents=True,exist_ok=True)
                card.write_text(arguments['text'],encoding='utf-8')
                return {'success':True,'saved_plan':True,'approval_granted':False,'sha256':hashlib.sha256(arguments['text'].encode()).hexdigest()}
            if executor is None:raise ValueError("This is discussion/planning; native model tools require host-confirmed execution.")
            if name == LEVEL_JOINT_TOOL:
                result = executor.measure_level_joint(SCRIPT_ID, arguments)
                quality.setdefault("level_joints", []).append(result)
                return result
            identity = executor.verify_active_model()
            state = executor.ruby_state.get(SCRIPT_ID, {})
            if name == "sketchup_model_state":
                if arguments: raise ValueError("No arguments accepted.")
                return {"success":True, "identity":identity, "script_id":SCRIPT_ID, "revision":state.get("revision",0), "root_pid":state.get("root_pid")}
            if name == "sketchup_inspect_part":
                if "path" not in arguments or set(arguments) - {"path", "window_bay"}:
                    raise ValueError("Provide path and optional window_bay.")
                return executor.inspect_owned({**arguments, "script_id": SCRIPT_ID, "limit": 100})
            if name == "sketchup_apply_parts":
                stage = arguments.get('construction_stage')
                if 'construction_stage' in arguments and stage not in STAGES:
                    raise ValueError('Unknown construction stage.')
                parts = arguments.get('parts', [])
                if allowed_parts is not None and isinstance(parts, list) and any(
                    isinstance(p, dict) and isinstance(p.get('name'), str) and p['name'] not in allowed_parts
                    for p in parts
                ):
                    raise ValueError("Part is outside the approved scope; use only these direct part names: " + ", ".join(sorted(allowed_parts)) + ". Preserve all other parts; group subordinate elements inside the appropriate approved part.")
                source = compile_parts({key: value for key, value in arguments.items() if key != 'construction_stage'})
                if any(writes.get(p['name'],0)>=3 for p in arguments['parts']):
                    raise ValueError('Correction limit reached for this part. Preserve the current model, inspect once and report remaining mismatches; no further cosmetic rewriting this task.')
                params = {"script_id":SCRIPT_ID,"ruby_source":source,"update_mode":"edit" if state.get("root_pid") else "replace"}
                if state.get("root_pid"):
                    params["allowed_mutation_paths"] = [[p["name"]] for p in arguments["parts"]]
                result = executor.run(params)
                if result.get('success') is not False:
                    for part in arguments['parts']:writes[part['name']]=writes.get(part['name'],0)+1
                    quality['writes'].append({'parts':[p['name'] for p in arguments['parts']],
                        'revision':executor.ruby_state.get(SCRIPT_ID,{}).get('revision',0)})
                record = project_dir / "runtime" / f"parts-{uuid.uuid4().hex}.json"
                record.write_text(json.dumps(arguments,ensure_ascii=False,indent=2),encoding="utf-8")
                return result
            if set(arguments) != {"view"} or arguments["view"] not in {"front","oblique","roof"}:
                raise ValueError("Unknown view.")
            view_key=(state.get('revision',0),arguments['view'])
            if view_key in views:return views[view_key]
            if state.get("root_pid"):
                observed = executor.inspect_owned({"script_id":SCRIPT_ID,"path":[],"limit":1})
                observed = json.loads(observed["contentItems"][0]["text"])
                bounds = observed.get("bounds_mm") or observed.get("snapshot",{}).get("bounds_mm")
                if not bounds: raise ValueError("Actual owned bounds unavailable.")
                camera = canonical_camera_from_bounds_mm(bounds, arguments["view"])
                executor.adapter.set_camera(camera["eye_m"],camera["target_m"],camera["up_m"])
                executor.refresh_active_model_snapshot()
            dest = project_dir / "outputs" / "renders" / f"harness-{arguments['view']}-{uuid.uuid4().hex}.png"
            dest.parent.mkdir(parents=True,exist_ok=True)
            executor.adapter.capture_view(dest,width=1200,height=1000,zoom_extents=False)
            executor.refresh_active_model_snapshot()
            pixels = dest.read_bytes()
            info = {"success":True,"revision":state.get("revision",0),"view":arguments["view"],"path":str(dest),"sha256":hashlib.sha256(pixels).hexdigest()}
            quality['views'][arguments['view']]=info
            result={**info,"contentItems":[{"type":"inputText","text":json.dumps(info)}, {"type":"inputImage","imageUrl":"data:image/png;base64,"+base64.b64encode(pixels).decode()}]}
            views[view_key]=result
            return result
        available=tool_specs(planning=True)
        if stage_scoped:
            available=(tool_specs(writing=True,planning=False) if mcp_enabled else
                       [s for s in tool_specs(writing=False,planning=True) if s['name']=='sketchup_save_plan'] if allow_plan else [])
        return AgentToolContext(dynamic_tools=available,dispatch=dispatch,quality_state=quality)
