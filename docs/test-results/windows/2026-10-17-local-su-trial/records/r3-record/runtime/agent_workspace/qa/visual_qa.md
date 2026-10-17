# Visual QA

NEEDS_FIX: YES

## Assessment

SOURCE shows one two-storey white volume from the front-left: two upper glazed openings, one broad ground-floor opening, two stacked narrow left windows, a projecting glass-railed balcony, a full-height right timber strip, thin roof coping and surrounding paving. CURRENT preserves this opening arrangement and material placement, but compresses the clearance beneath the balcony and omits the projecting paved terrace. The supplied source-matched camera still differs in perspective, so apparent building width/depth differences are uncertain. Rear, right elevation and roof surface are unobserved in SOURCE. Screenshots show no obvious floating balcony components, but cannot establish concealed connections.

## Highest-impact mismatches

1. [front] CURRENT places the balcony underside almost against the ground-floor glazing head. SOURCE has a clearly visible white wall band between them, giving the balcony and lower opening distinct separation. -> Locally adjust balcony elevation and ground-floor opening head height to restore the source clearance; retain the opening’s two-panel division and horizontal placement.
2. [front-left] SOURCE has a paved terrace projecting beyond both the front and left walls, including beyond the balcony footprint. CURRENT terminates at a narrow base strip, losing this visible ground-level silhouette. -> Add the shallow projecting paved platform along the observed front and left edges, keeping it distinct from the wall plinth. Infer concealed extents conservatively.

## KEEP

- Two separate paired upper glazed openings.
- Central division of the broad ground-floor glazing.
- Two vertically aligned narrow left-side windows.
- Placement of the full-height timber strip at the front-right edge.

## Current-revision evidence

- front: outputs/renders/agent-view-front-edcf5035c1.png
- rear: outputs/renders/agent-view-rear-b312617ae5.png
- left: outputs/renders/agent-view-left-885b952794.png
- right: outputs/renders/agent-view-right-581fc54ac6.png
- roof: outputs/renders/agent-view-roof-7af21af71a.png
- oblique: outputs/renders/agent-view-oblique-c74b7a0fac.png

## Source-matched / interior evidence pairs

- 当前第三版正面及左侧源图对比: inputs/reference/2fc62f9b95-villa-single-view.png -> outputs/renders/agent-view-c7c738cea5.png

## Writer verification

- model_revisions: {"su1017_villa": 3}
- all current writer receipts verified: true

Builder scope resolution / final status: revision3 committed and verified, no fourth mutation. NEEDS_FIX remains YES: ground glazing head to balcony underside clearance is visually compressed (150mm). Future candidate head2250, not built. Terrace omission is intentional under user no-environment instruction. KEEP: upper door arrangements, stacked side windows, timber strip. No save/reopen verification performed.
