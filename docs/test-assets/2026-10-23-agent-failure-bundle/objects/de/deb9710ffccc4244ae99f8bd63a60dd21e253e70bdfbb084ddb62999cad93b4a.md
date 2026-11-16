# Construction strategy JSON contract

Read before writing notes/construction_strategy.json. JSON syntax alone is insufficient. Use current_stage=pending before execution; plan_only is invalid.

Stages: pending (current_stage only), primary_form, representative_module, replication, variants, finish.
Methods: continuous_wall_with_openings, custom_owned_ruby, loft_or_mesh, profile_extrusion, prototype_instance, typed_semantic_helper.
Roles: balcony, facade_detail, interior_detail, opening_system, repetition, roof, shell, site.
Status: built, needs_fix, pending, verified.
Parameter provenance: estimated, inferred, observed, pending, user_confirmed.
Parameter units: count, degrees, mm, ratio, text.

Numeric units require one numeric value, not an array. Split level/bay arrays into named scalar parameters; put explanations in source/notes, not provenance. Text units require a string. depends_on must reference shared parameter keys. target_paths is a list of exact owned-name segment lists. verification_views only front/rear/left/right/roof/oblique. notes must be concise string lists.
For every new geometry system, include method_id (a concrete OSS provider+method) and selection_reason. For custom Ruby, explain why compatible verified SAIE/ADAI helpers are unsuitable. An upstream method that is listed but not actually called is NOT product-used. ADAI may be chosen only if its pinned helper is installed and explicitly enabled; runtime validates calls.

```json
{
  "schema_version": 1,
  "current_stage": "pending",
  "stage_order": [
    "primary_form",
    "representative_module",
    "replication",
    "variants",
    "finish"
  ],
  "shared_parameters": {
    "storey_height": {
      "value": 3100,
      "units": "mm",
      "provenance": "estimated",
      "source": "image proportion"
    }
  },
  "systems": [
    {
      "id": "walls",
      "stage": "primary_form",
      "role": "shell",
      "method": "continuous_wall_with_openings",
      "status": "pending",
      "method_id": "saie.wall_with_openings",
      "selection_reason": "Standard rectangular observed openings; installed SAIE helper is more suitable than general profile loft.",
      "depends_on": [
        "storey_height"
      ],
      "target_paths": [
        [
          "WALL_FRONT"
        ]
      ],
      "verification_views": [
        "front",
        "oblique"
      ],
      "notes": [
        "Verify actual openings before replication."
      ]
    }
  ],
  "notes": []
}
```
