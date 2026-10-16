# Visual QA

NEEDS_FIX: YES

## Assessment

SOURCE 1–2 show the ramp-facing short end and adjoining long elevation, linked by the curved raised roof, projecting two-storey glazed enclosure and stacked ramps. SOURCE 3 shows the lower glazed frontage and projecting grating underside. Both SOURCE 4 interiors show the curved timber ceiling above and concrete framing with timber ceiling panels and shallow V braces below. SOURCE 5 and 8 sections show asymmetric floor levels and voids; SOURCE 7 supplies three plans; SOURCE 6 separates the structural layers. CURRENT captures the principal exterior arrangement, but visible interior ceiling assemblies and major surface finishes still differ. Uncut CURRENT section/plan views cannot verify the internal void arrangement. Screenshots do not establish concealed fasteners or exact joint engagement; the stated 60 mm jamb dimension is not independently confirmed by SOURCE.

## Highest-impact mismatches

1. [lower] SOURCE 4 lower panel shows timber ceiling infill and repeated shallow V braces between concrete beams. CURRENT 23 shows plain grey ceiling surfaces and rectangular framing without those visible braces. -> Locally add the source-visible V braces and timber infill within the corresponding ceiling bays, retaining correctly positioned concrete columns and beams.
2. [source4] SOURCE interiors have pale floors and a light natural timber roof soffit; CURRENT 18 and 23 have charcoal floors, and the curved soffit reads dark grey-brown. These large surfaces substantially change the source’s material balance. -> Correct the floor and curved soffit materials to the source’s pale mineral flooring and light timber, preserving existing openings, curtain geometry and roof curvature.

## KEEP

- Concave short-end roof-edge profile with unequal raised ends.
- Three descending ramp runs at the ramp-facing short end.
- Projecting glazed enclosure around the upper two levels.
- Circular mesh guards and translucent curtain partitions in the upper interior.

## Current-revision evidence

- front: outputs/renders/agent-view-front-705f6f72d3.png
- rear: outputs/renders/agent-view-rear-0776cb5d7e.png
- left: outputs/renders/agent-view-left-a8fe192209.png
- right: outputs/renders/agent-view-right-b16aef0d80.png
- roof: outputs/renders/agent-view-roof-47b9be6569.png
- oblique: outputs/renders/agent-view-oblique-92c393d586.png

## Source-matched / interior evidence pairs

- Source1 registered camera; section/plan stays uncut and occluded: inputs/reference/9d05f4a6ae-codex-clipboard-1b4276a9-93d4-4833-95cb-c3b193c9c96d.png -> outputs/renders/agent-view-3be3f41597.png
- Source2 registered camera; section/plan stays uncut and occluded: inputs/reference/ade9a9063c-codex-clipboard-273f5c39-ee57-4cd8-a0c0-d1113b742a27.png -> outputs/renders/agent-view-7ae0cf844f.png
- Source3 registered camera; section/plan stays uncut and occluded: inputs/reference/8e8a3625d5-codex-clipboard-a04d023f-1044-423f-89db-4a0b51e92505.png -> outputs/renders/agent-view-5b5e3751a7.png
- Source4 registered camera; section/plan stays uncut and occluded: inputs/reference/c55a28860e-codex-clipboard-fdf7fe7c-e5f1-47d4-b800-d4f5eaf99b52.png -> outputs/renders/agent-view-2056a335d2.png
- Source5 registered camera; section/plan stays uncut and occluded: inputs/reference/da5324e1c5-codex-clipboard-1ed05c14-1674-4910-bc05-ccb2c03aec93.png -> outputs/renders/agent-view-0bc2b4bf3a.png
- Source6 registered camera; section/plan stays uncut and occluded: inputs/reference/4fdbe428b1-codex-clipboard-8856a1fd-12c2-44d9-a5af-868c4c8d4c2a.png -> outputs/renders/agent-view-9bc873e548.png
- Source7 registered camera; section/plan stays uncut and occluded: inputs/reference/8328ae9aa4-codex-clipboard-538fb3e3-5783-461e-8458-b231bd90bd57.png -> outputs/renders/agent-view-d02975e366.png
- Source8 registered camera; section/plan stays uncut and occluded: inputs/reference/92fc9f3b50-codex-clipboard-10ea73cd-a751-4576-b174-295e6446a725.png -> outputs/renders/agent-view-964cf8e96b.png
- Lower interior preserved: inputs/reference/c55a28860e-codex-clipboard-fdf7fe7c-e5f1-47d4-b800-d4f5eaf99b52.png -> outputs/renders/agent-view-5f6c3a7fc3.png
- Long eave general: inputs/reference/da5324e1c5-codex-clipboard-1ed05c14-1674-4910-bc05-ccb2c03aec93.png -> outputs/renders/agent-view-5f8c16bd60.png
- South hinge sash stay and backing aperture: inputs/reference/da5324e1c5-codex-clipboard-1ed05c14-1674-4910-bc05-ccb2c03aec93.png -> outputs/renders/agent-view-23f0892cd2.png
- North hinge sash stay and backing aperture: inputs/reference/da5324e1c5-codex-clipboard-1ed05c14-1674-4910-bc05-ccb2c03aec93.png -> outputs/renders/agent-view-840565ce54.png
- South inside aperture outward: inputs/reference/da5324e1c5-codex-clipboard-1ed05c14-1674-4910-bc05-ccb2c03aec93.png -> outputs/renders/agent-view-b98e52a178.png
- Preserved west door/ramp bay: inputs/reference/da5324e1c5-codex-clipboard-1ed05c14-1674-4910-bc05-ccb2c03aec93.png -> outputs/renders/agent-view-29c7bd765a.png
- North east last bay right stay: added missing60mm corner jamb, existing sash/glass/stay retained; compare r17 before capture agent-view-d941574e71 separately. Hidden fasteners inferred.: inputs/reference/da5324e1c5-codex-clipboard-1ed05c14-1674-4910-bc05-ccb2c03aec93.png -> outputs/renders/agent-view-3faf2aa39f.png

## Writer verification

- model_revisions: {"glass_curved_roof": 18}
- all current writer receipts verified: true
