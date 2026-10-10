# Reconstruction planning JSON contracts

Paths are relative to the PROJECT root: inputs/reference/file.png, never ../../inputs/... . Keep whole view sheets intact. Evidence sources.kind is exterior_image/interior_image/floorplan_image/cad/document/dimension_note; provenance is pending/observed/user_confirmed/inferred. A six-panel sheet is kind=exterior_image; describe its panels in notes/role. Observed exterior_views.source_refs and scale_anchors.source_ref must be actual PROJECT-relative input FILE PATHS (inputs/reference/file.png), never source IDs such as source_sheet_01. Estimated scale anchors are objects with name, positive value_mm, provenance=inferred. hard_constraints and assumptions are string lists. unseen_exterior is infer_coherent/do_not_infer; unseen_interior is infer_plausible/do_not_infer. Mark absent CAD/floorplan/interior provided=false and provenance=pending.

Facade provenance additionally allows mixed. opening_count and door_count must be nonnegative integers or null; dimensions_mm values are nonnegative numbers or null. features/notes/divisions/global_features/user_confirmed/inferred are string lists. JSON syntax alone does not prove schema validity.

## Evidence template
```json
{
  "schema_version": 1,
  "fidelity_mode": "pending",
  "primary_source": "",
  "sources": [],
  "exterior_views": {
    "front": {
      "provenance": "pending",
      "source_refs": [],
      "notes": []
    },
    "rear": {
      "provenance": "pending",
      "source_refs": [],
      "notes": []
    },
    "left": {
      "provenance": "pending",
      "source_refs": [],
      "notes": []
    },
    "right": {
      "provenance": "pending",
      "source_refs": [],
      "notes": []
    },
    "roof": {
      "provenance": "pending",
      "source_refs": [],
      "notes": []
    },
    "oblique": {
      "provenance": "pending",
      "source_refs": [],
      "notes": []
    }
  },
  "floorplan": {
    "provided": false,
    "provenance": "pending",
    "source_refs": [],
    "levels": [],
    "notes": []
  },
  "cad": {
    "provided": false,
    "provenance": "pending",
    "source_refs": [],
    "notes": []
  },
  "interior": {
    "provided": false,
    "provenance": "pending",
    "source_refs": [],
    "spaces": [],
    "notes": []
  },
  "scale_anchors": [],
  "hard_constraints": [],
  "assumptions": [],
  "inference_policy": {
    "unseen_exterior": "infer_coherent",
    "unseen_interior": "infer_plausible",
    "preserve_circulation": true
  }
}
```

## Facade schedule template
```json
{
  "schema_version": 1,
  "source_mode": "pending",
  "dimensions_mm": {
    "overall_width": null,
    "overall_depth": null,
    "level_height": null,
    "floor_count": null
  },
  "views": {
    "front": {
      "provenance": "pending",
      "opening_count": null,
      "door_count": null,
      "features": [],
      "notes": []
    },
    "rear": {
      "provenance": "pending",
      "opening_count": null,
      "door_count": null,
      "features": [],
      "notes": []
    },
    "left": {
      "provenance": "pending",
      "opening_count": null,
      "door_count": null,
      "features": [],
      "notes": []
    },
    "right": {
      "provenance": "pending",
      "opening_count": null,
      "door_count": null,
      "features": [],
      "notes": []
    }
  },
  "roof": {
    "provenance": "pending",
    "type": "pending",
    "parapet": "pending",
    "divisions": [],
    "notes": []
  },
  "global_features": [],
  "user_confirmed": [],
  "inferred": []
}
```
