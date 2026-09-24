# Demo Schemas v0.1

These are intentionally small. Codex may refine fields when implementation requires it, but should not replace them with a large generic ontology.

## ProjectContext

```json
{
  "project_id": "demo-cultural-center",
  "project_name": "Demo Cultural Center",
  "brief": {
    "source_files": [],
    "summary": "",
    "requirements": []
  },
  "site": {
    "source_files": [],
    "boundary": [],
    "north": null,
    "access_points": []
  },
  "references": [
    {
      "type": "url|image|note",
      "source": "",
      "observed_principles": []
    }
  ],
  "user_intent": "",
  "decisions": [],
  "unresolved": []
}
```

## DesignIR

```json
{
  "version": "0.1",
  "project_id": "demo-cultural-center",
  "concept": {
    "summary": "",
    "reference_principles_used": [],
    "reference_principles_rejected": []
  },
  "site": {
    "boundary": []
  },
  "program": [
    {
      "id": "PROGRAM_01",
      "name": "Library",
      "target_area": 1200
    }
  ],
  "objects": [
    {
      "id": "MASS_01",
      "type": "building_mass",
      "name": "Library",
      "footprint": [[0,0],[20,0],[20,30],[0,30]],
      "floors": 3,
      "floor_height": 4.0,
      "height": 12.0,
      "metadata": {}
    },
    {
      "id": "PUBLIC_STREET_01",
      "type": "circulation",
      "name": "Public Street",
      "polyline": [[0,0],[40,0]],
      "width": 8.0,
      "metadata": {}
    }
  ],
  "relationships": [],
  "metrics": {},
  "assumptions": [],
  "unresolved": []
}
```

Coordinate/units convention for Demo v0.1:
- meters in DesignIR
- connector converts to SketchUp native units as required
- XY = ground plane
- Z = height

## BuildPlan

```json
{
  "version": "0.1",
  "project_id": "demo-cultural-center",
  "operations": [
    {
      "op_id": "OP_001",
      "action": "create_mass",
      "target_id": "MASS_01",
      "args": {}
    }
  ],
  "validation": {
    "required_ids": ["MASS_01"],
    "expected_object_count_min": 1
  }
}
```

Allowed demo actions should remain small:

- `create_mass`
- `create_circulation`
- `modify_object`
- `capture_view`
- `save_model`

Do not invent dozens of actions for Demo v0.1.

## ModelState

```json
{
  "project_id": "demo-cultural-center",
  "model_path": null,
  "objects": [
    {
      "stable_id": "MASS_01",
      "connector_ref": "",
      "name": "Library",
      "bounds": null,
      "height": 12.0
    }
  ],
  "last_capture": null,
  "last_operation": null,
  "status": "ready"
}
```

## OutputManifest

```json
{
  "project_id": "demo-cultural-center",
  "drawing": [],
  "render": [],
  "presentation": [],
  "model_captures": []
}
```
