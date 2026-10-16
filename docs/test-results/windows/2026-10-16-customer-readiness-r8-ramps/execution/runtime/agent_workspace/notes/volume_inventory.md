# Source to model inventory
| Source | Observed system and proportion anchor | Exact named path | Status |
|---|---|---|---|
| 3,4 lower,5,6,8 | Concrete skeleton, plan 2.5:1, 10 bays | STRUCTURE_EXISTING | pending readback |
| 5,7,8 | Four levels; L2 large boundary-connected atrium | FLOORS | pending readback |
| 1,2,4 upper,5,6,8 | Short-span hanging roof, asymmetric edges, long extrusion | ROOF_TIMBER/CURVED_SHELL | pending readback |
| 1,2,3,5,6 | Deep buffer, upper box, lower inset, flat perimeter canopies | ENVELOPE_OUTER | pending readback |
| 1,2,3 upper,7 | Short-end folded ramp, landings to circulation levels | EXTERNAL_ASSEMBLY | pending readback |
| 4,5,7 | Circular void and spiral stairs, east end stair | CIRCULATION_INTERNAL | pending readback |
| 1,3,5 lower | Adjacent ground only | SITE_GROUND | pending readback |

Source camera pairs: short end (-X); end/long-side oblique (-X,-Y); entrance near short-end corner; long-side gallery underside; top floor interior; lower double-height interior; plan/section-informed unseen sides. No dimensioned CAD supplied. Primary silhouette and ramp connectivity outrank furniture.

Roof-only r3 readback: ROOF_TIMBER PID 77872, CURVED_SHELL PID 77873, ROOF_SUPPORTS PID 78849 retained; roof assembly reflected about Y=10000. Ramp-end screen right (-Y) now high. All ramps and other systems protected, no claim that their source mismatches are fixed. Evidence qa/roof_edit_receipt.json.


Upper receiving doors r7: only NORTH_BAY_0 (two) and SOUTH_BAY_00 (one) cut to2200x2400mm clear openings inside existing rail gates. Module extents/mullions and all other assemblies retained. Source dimensions estimated. See upper_glazing_door_edit.md and qa/upper_glazing_door_receipt.json. Independent review pending.


Upper ramp containment authorized: only15 named upper ramp/platform/apron paths, lowest and all unrelated systems protected. SOURCE1/2/7 end screened circulation relations; exact native candidate and QA in upper_ramp_containment_edit.md.
