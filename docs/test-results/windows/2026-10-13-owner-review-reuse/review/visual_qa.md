# Visual QA

NEEDS_FIX: YES

## Assessment

SOURCE1 is a near-frontal ground view; SOURCE2 looks along the right flank. Shared landmarks identify the same building: stepped white perforated enclosures, a narrow central strip of small windows, two stacked left glazing bays, a deep right recess with corner glazing and tall red columns, red folded rooftop surfaces, elevated glazed rooms, and external stairs and a pale ramp. CURRENT retains these broad landmarks, but its upper enclosure silhouette and circulation assemblies differ substantially. The source-matched views are elevated relative to the photographs, so perspective alone cannot establish exact dimensions. Rear geometry, concealed roof extents and structural joints remain uncertain; screenshots cannot verify actual geometric attachment.

## Highest-impact mismatches

1. [right] SOURCE2 shows a substantial screened right-hand enclosure continuing below the corner glazing and framing the deep recess. CURRENT10 instead exposes a hanging glazed box with a plain white lower face beneath a comparatively shallow upper screen band. This changes the principal volume and recess boundaries. -> Locally extend and reshape the visible right-side enclosure and its lower return to match SOURCE2, retaining the recessed glazing where its placement agrees. Align screen, soffit and glazing edges at their intended junctions; preserve the open recess.
2. [roof] Both sources show pronounced peaked and sloping white screen outlines around the red folded rooftop geometry. CURRENT9–10 largely flatten these into horizontal rims, with only a small central peak. CURRENT also presents the red assembly mainly as an upright fin and narrow rising strip rather than the broad folded surface visible in SOURCE1. -> Adjust the affected screen crest profiles and visible red fold widths, slopes and connections using both source angles. Limit changes to source-visible portions; do not invent concealed roof geometry.
3. [front] The sources show substantial red stair flights and landings, plus a broad pale ramp with a turning or curved boundary at ground level. CURRENT9–10 reduce these to narrow exposed flights and a straight channel-like ramp, altering the lower silhouette and circulation connections. -> Patch the visible stair widths, solid side/underside profiles and landing connections, then reshape the ramp’s visible boundary and approach to match the sources. Verify continuous connections and clearances at the elevated deck rather than relying on overlapping faces.

## KEEP

- Two stacked glazed bays at the left opening, separated by a red horizontal floor edge.
- The vertical arrangement of three small rectangular openings on the narrow central front strip.

## Current-revision evidence

- front: outputs/renders/agent-view-front-b9f3bc2a62.png
- rear: outputs/renders/agent-view-rear-25b712d708.png
- left: outputs/renders/agent-view-left-21f4417d25.png
- right: outputs/renders/agent-view-right-687c4d72fe.png
- roof: outputs/renders/agent-view-roof-d089a3001c.png
- oblique: outputs/renders/agent-view-oblique-9aadb0f336.png

## Source-matched / interior evidence pairs

- Source1 near front: enclosure and broad connected roof: inputs/reference/f15eca3833-image.png -> outputs/renders/agent-view-8bc68d0b61.png
- Source2 front right: same protected recess, stair sides and roof: inputs/reference/2cc8f551ee-image.png -> outputs/renders/agent-view-43887a3568.png

## Writer verification

- model_revisions: {"reconstruction_357fb": 6}
- all current writer receipts verified: true
