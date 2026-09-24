# SketchUp Agent Technical Spike v0.1

## Purpose

This spike answers one product question:

**Can an AI agent continuously operate a real SketchUp project, preserve state, create/edit real geometry, inspect the result, and safely iterate on the same model?**

It is not a full-product build.

## Target loop

Project Context  
→ Agent  
→ SketchUp Connector  
→ Editable Model  
→ Screenshot / Model State  
→ AI Review  
→ Natural-Language Modification  
→ Updated Same Model

## Success dimensions

The spike should eventually validate:

1. **Connection** — stable communication with SketchUp.
2. **Query** — read model/document state.
3. **Editability** — create real editable geometry.
4. **Continuous modification** — modify existing objects rather than rebuild the whole project.
5. **State consistency** — project state reflects SketchUp state.
6. **Inspection** — obtain model data and viewport captures.
7. **Recovery** — save/version/undo or otherwise recover from failed operations.
8. **Traceability** — logs explain what changed and why.

## Suggested minimal tool families

These are hypotheses, not requirements for Phase A+B.

### Connection
- ping
- get_model_info
- save_model

### Query
- list_entities
- get_entity
- get_selection
- get_model_bounds
- get_layers_or_tags
- get_component_summary

### Geometry
- create_group
- create_face
- extrude_face
- create_box
- create_polyline

### Transform
- move_entity
- rotate_entity
- scale_entity
- delete_entity

### Organization
- set_name
- set_tag_or_layer
- set_material

### Validation
- calculate_area
- calculate_volume
- get_dimensions
- check_duplicate_entities

### View
- set_camera
- zoom_extents
- capture_viewport

Do not expose a huge tool surface before evidence shows it is needed.

## Benchmark principle

Use the user's graduation project as a **local/private benchmark**, not as public repository content.

Prefer to first inspect and modify an existing accepted model if available. A from-scratch generation test may be added later.

## Continuous-edit benchmark concept

Later phases should test a sequence similar to:

1. Lower the sports hall by one floor.
2. Widen the public street by roughly 20%.
3. Move the library toward the main entrance while preserving its connection to the public street.
4. Adjust roof language toward a precedent without directly copying it.
5. Save the current scheme as a new version without changing the overall design.

Each operation must build on the prior state.

## Planned phases

### Phase A — Environment Audit
Determine the real local development environment and constraints.

### Phase B — Existing Connector Evaluation
Evaluate open-source SketchUp MCP / connector options and choose a minimal architecture.

### Phase C — Minimal Project State
Define only the state required by the spike.

### Phase D — Minimal SketchUp Tool Set
Implement the smallest stable tool surface.

### Phase E — Existing Model Read
Read and identify major objects in a local benchmark model.

### Phase F — Continuous Editing Benchmark
Run sequential modifications against the same model.

### Phase G — Screenshot + Review Loop
Combine structured state with viewport inspection.

### Phase H — Evaluation
Produce a written result and decide whether the spike is accepted.

## Final acceptance criteria

The spike is accepted only if:

- SketchUp connection is stable enough for repeated operations.
- Basic model state can be queried.
- Real editable geometry can be created and modified.
- At least 4 of 5 predefined continuous modifications succeed.
- Successful modifications do not rely on full-model regeneration.
- Model state and SketchUp state remain materially consistent.
- Important steps can produce screenshots or equivalent viewport evidence.
- A failed operation does not permanently destroy the benchmark model.
- A prior stable version can be restored.
- Execution logs are sufficient to diagnose failures.

Final status must be one of:

**SPIKE_ACCEPTED**

or

**SPIKE_NOT_ACCEPTED**

Do not hide core-loop failure behind web UI, rendering, CAD, or other peripheral features.
