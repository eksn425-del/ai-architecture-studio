# Visual QA

NEEDS_FIX: YES

## Assessment

SOURCE 1–2 establish the ramp-facing short end and adjoining long elevation: a recessed lower frame, projecting glazed buffer galleries and an asymmetric sagging roof. SOURCE 3 shows the ground-level glazing and gallery underside; SOURCE 4 shows both the curved timber hall ceiling and the lower interior structure. SOURCE 5 and 8 provide transverse sections, SOURCE 6 separates the structural layers, and SOURCE 7 supplies three floor plans. CURRENT broadly reproduces the exterior arrangement, but the lower interior ceiling assembly and major interior finishes remain visibly different. Uncut CURRENT views cannot verify the sectional floor arrangement; exact dimensions and concealed joints remain uncertain.

## Highest-impact mismatches

1. [lower] SOURCE 4’s lower panel shows timber ceiling infill between concrete beams, with shallow V-shaped steel members beneath. CURRENT 23 instead exposes extensive open beam grids and views into the storey above, without that ceiling assembly. -> Locally add the source-backed ceiling infill and shallow steel members over the occupied lower bays, retaining only the stair openings and double-height voids supported by SOURCE 5 and 7. Connect member ends to their supporting beams.
2. [source4] SOURCE 4 shows a pale timber ceiling and light floor surfaces. CURRENT 18 and 23 have dark gray floors, while the curved ceiling reads as dark, densely striped boards. These large material zones substantially change the observed interior. -> Lighten the occupied floor finishes and curved timber soffit to match SOURCE 4; reduce the prominence of board seams without changing the curved ceiling geometry.

## KEEP

- Asymmetric concave short-end roof profile, with one edge higher than the other.
- Three descending ramp flights across the short end.
- Setback between the lower frame and projecting upper glazed enclosure.

## Current-revision evidence

- front: outputs/renders/agent-view-front-61d6f19c84.png
- rear: outputs/renders/agent-view-rear-362d680c0d.png
- left: outputs/renders/agent-view-left-b36874f332.png
- right: outputs/renders/agent-view-right-f76ae9c1a4.png
- roof: outputs/renders/agent-view-roof-859f2e5281.png
- oblique: outputs/renders/agent-view-oblique-2fb4ddaa61.png

## Source-matched / interior evidence pairs

- Source1 registered camera; section/plan stays uncut and occluded: inputs/reference/9d05f4a6ae-codex-clipboard-1b4276a9-93d4-4833-95cb-c3b193c9c96d.png -> outputs/renders/agent-view-4415be7328.png
- Source2 registered camera; section/plan stays uncut and occluded: inputs/reference/ade9a9063c-codex-clipboard-273f5c39-ee57-4cd8-a0c0-d1113b742a27.png -> outputs/renders/agent-view-eebffb189d.png
- Source3 registered camera; section/plan stays uncut and occluded: inputs/reference/8e8a3625d5-codex-clipboard-a04d023f-1044-423f-89db-4a0b51e92505.png -> outputs/renders/agent-view-0723ff977b.png
- Source4 registered camera; section/plan stays uncut and occluded: inputs/reference/c55a28860e-codex-clipboard-fdf7fe7c-e5f1-47d4-b800-d4f5eaf99b52.png -> outputs/renders/agent-view-687a87257d.png
- Source5 registered camera; section/plan stays uncut and occluded: inputs/reference/da5324e1c5-codex-clipboard-1ed05c14-1674-4910-bc05-ccb2c03aec93.png -> outputs/renders/agent-view-e9f5623017.png
- Source6 registered camera; section/plan stays uncut and occluded: inputs/reference/4fdbe428b1-codex-clipboard-8856a1fd-12c2-44d9-a5af-868c4c8d4c2a.png -> outputs/renders/agent-view-890375ef14.png
- Source7 registered camera; section/plan stays uncut and occluded: inputs/reference/8328ae9aa4-codex-clipboard-538fb3e3-5783-461e-8458-b231bd90bd57.png -> outputs/renders/agent-view-5aa7cde8b2.png
- Source8 registered camera; section/plan stays uncut and occluded: inputs/reference/92fc9f3b50-codex-clipboard-10ea73cd-a751-4576-b174-295e6446a725.png -> outputs/renders/agent-view-5dbd131667.png
- Lower interior preserved: inputs/reference/c55a28860e-codex-clipboard-fdf7fe7c-e5f1-47d4-b800-d4f5eaf99b52.png -> outputs/renders/agent-view-63016fc669.png
- Long eave general: inputs/reference/da5324e1c5-codex-clipboard-1ed05c14-1674-4910-bc05-ccb2c03aec93.png -> outputs/renders/agent-view-189ace459d.png
- South hinge sash stay and backing aperture: inputs/reference/da5324e1c5-codex-clipboard-1ed05c14-1674-4910-bc05-ccb2c03aec93.png -> outputs/renders/agent-view-1ddff5c0ca.png
- North hinge sash stay and backing aperture: inputs/reference/da5324e1c5-codex-clipboard-1ed05c14-1674-4910-bc05-ccb2c03aec93.png -> outputs/renders/agent-view-bc88f554be.png
- South inside aperture outward: inputs/reference/da5324e1c5-codex-clipboard-1ed05c14-1674-4910-bc05-ccb2c03aec93.png -> outputs/renders/agent-view-a70b5f1301.png
- Preserved west door/ramp bay: inputs/reference/da5324e1c5-codex-clipboard-1ed05c14-1674-4910-bc05-ccb2c03aec93.png -> outputs/renders/agent-view-1a82987680.png

## Writer verification

- model_revisions: {"glass_curved_roof": 17}
- all current writer receipts verified: true
