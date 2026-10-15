# Visual QA

NEEDS_FIX: YES

## Assessment

SOURCE panels show one elongated building: a recessed lower frame, a projecting two-storey glazed buffer enclosure, perimeter decks, three alternating end-ramp flights, and a curved timber roof with unequal raised edges. Exterior photographs, the aerial drawing and physical-model views share these landmarks. Interior panels show the curved timber soffit, exposed frame and spiral circulation; plans and sections show floor openings and differing internal floor extents. CURRENT retains the recognizable exterior arrangement, but the roof trough sits too close to the enclosure’s top edge, and ramp terminations need correction or closer verification. No user-confirmed dimensions are supplied. These uncut exterior views cannot establish internal fidelity or prove physical connections; dark outlines alone do not establish incorrect materials.

## Highest-impact mismatches

1. [roof] SOURCE end views show a substantial glazed zone between the roof trough and the horizontal buffer-enclosure roofline. In CURRENT image 15, the trough nearly touches that roofline, compressing the defining upper-storey silhouette. -> Raise the central portion of the curved roof and adjust its adjoining glazing/support heights locally to restore the source-visible clearance. Preserve the right-higher edge relationship; do not protect the entire existing roof profile.
2. [ramp] CURRENT image 15 shows the upper ramp/rail extending beyond the right enclosure edge and broad projecting pieces at the flight ends. SOURCE physical-model views show flights resolving into perimeter decks and defined landings. The current overlaps do not demonstrate continuous walking surfaces or correctly terminated rails. -> Locally align flight endpoints with their receiving decks, trim unsupported overruns, and resolve landing surfaces and rail returns. Verify the joints in close views before accepting them; preserve correctly positioned flight portions.

## KEEP

- Right roof edge higher than the left in the matched ramp-end orientation.
- Alternating slopes of the three exterior ramp flights.

## Current-revision evidence

- front: outputs/renders/agent-view-front-05441c2c8f.png
- rear: outputs/renders/agent-view-rear-5e50a0a7a3.png
- left: outputs/renders/agent-view-left-90c0cb8cc4.png
- right: outputs/renders/agent-view-right-e19cdc7585.png
- roof: outputs/renders/agent-view-roof-eb8de15a48.png
- oblique: outputs/renders/agent-view-oblique-f42ee13533.png

## Source-matched / interior evidence pairs

- Ramp end: right-high now correct, trough too low: inputs/reference/9d05f4a6ae-codex-clipboard-1b4276a9-93d4-4833-95cb-c3b193c9c96d.png -> outputs/renders/agent-view-fff697f6af.png
- Uncut exterior; not a cutaway or interior proof: inputs/reference/ade9a9063c-codex-clipboard-273f5c39-ee57-4cd8-a0c0-d1113b742a27.png -> outputs/renders/agent-view-oblique-f42ee13533.png
- Uncut exterior; not a cutaway or interior proof: inputs/reference/8e8a3625d5-codex-clipboard-a04d023f-1044-423f-89db-4a0b51e92505.png -> outputs/renders/agent-view-oblique-f42ee13533.png
- Uncut exterior; not a cutaway or interior proof: inputs/reference/c55a28860e-codex-clipboard-fdf7fe7c-e5f1-47d4-b800-d4f5eaf99b52.png -> outputs/renders/agent-view-oblique-f42ee13533.png
- Uncut exterior; not a cutaway or interior proof: inputs/reference/da5324e1c5-codex-clipboard-1ed05c14-1674-4910-bc05-ccb2c03aec93.png -> outputs/renders/agent-view-fff697f6af.png
- Uncut exterior; not a cutaway or interior proof: inputs/reference/4fdbe428b1-codex-clipboard-8856a1fd-12c2-44d9-a5af-868c4c8d4c2a.png -> outputs/renders/agent-view-oblique-f42ee13533.png
- Uncut exterior; not a cutaway or interior proof: inputs/reference/8328ae9aa4-codex-clipboard-538fb3e3-5783-461e-8458-b231bd90bd57.png -> outputs/renders/agent-view-roof-eb8de15a48.png
- Uncut exterior; not a cutaway or interior proof: inputs/reference/92fc9f3b50-codex-clipboard-10ea73cd-a751-4576-b174-295e6446a725.png -> outputs/renders/agent-view-fff697f6af.png

## Writer verification

- model_revisions: {"glass_curved_roof": 3}
- all current writer receipts verified: true
