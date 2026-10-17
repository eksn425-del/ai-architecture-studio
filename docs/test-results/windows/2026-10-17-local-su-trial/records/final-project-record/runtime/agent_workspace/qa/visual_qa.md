# Visual QA

NEEDS_FIX: YES

## Assessment

SOURCE shows a front-left view of a two-storey white volume with a thin roof edge, two upper front glazed openings, one broad ground-floor sliding opening, two stacked narrow left windows, a projecting glass-railed balcony, a full-height timber strip at front right, a grey plinth and an extended paved terrace. CURRENT retains these principal facade elements, but the ground-floor opening nearly touches the balcony underside and the terrace is missing. Balcony returns appear connected in the supplied views; concealed joints cannot be verified. Rear, right facade and roof surface are unobserved in SOURCE. The stated 1200 mm railing height cannot be verified from screenshots.

## Highest-impact mismatches

1. [front] CURRENT leaves only a narrow strip above the ground-floor glazing; SOURCE shows a substantially deeper white header below the balcony soffit. -> Locally lower the ground-floor opening head and resize its frame/glazing, retaining its sill and width. Match the source-visible soffit-to-head clearance.
2. [source-matched] SOURCE has a paved terrace projecting beyond the front and visible left wall. CURRENT terminates at a narrow base flush with the building. -> Add the visible low terrace slab around the front and left side, matching its projection and thin exposed edge without inventing hidden extents.

## KEEP

- Two upper front openings with central vertical divisions.
- Broad two-panel ground-floor glazing arrangement.
- Two vertically aligned narrow windows on the left facade.
- Full-height vertical timber strip at the front-right edge.
- Thin visible roof-edge coping.

## Current-revision evidence

- front: outputs/renders/agent-view-front-f759e273e9.png
- rear: outputs/renders/agent-view-rear-56685dafbe.png
- left: outputs/renders/agent-view-left-0431bc1711.png
- right: outputs/renders/agent-view-right-7298e37e25.png
- roof: outputs/renders/agent-view-roof-06a94715b4.png
- oblique: outputs/renders/agent-view-oblique-2f73e1f3bc.png

## Source-matched / interior evidence pairs

- 仅栏杆高度改为1200；其余保持: inputs/reference/2fc62f9b95-villa-single-view.png -> outputs/renders/agent-view-29454d0b07.png

## Writer verification

- model_revisions: {"su1017_villa": 4}
- all current writer receipts verified: true

Local request outcome revision4: native readback verifies FRONT/LEFT/RIGHT guard base3000, top4200, height1200; root19 and target PIDs retained. All16 unrelated assembly deep KEEP/scope checks passed. Critic still flags prior source header/terrace issues, which this user explicitly prohibited changing. Latest request is completed geometrically; overall reconstruction remains not visually accepted. Supplied tools expose no model save/export lifecycle operation, so current revision4 save/download is not confirmed by this agent.
