# Current interior completion: revision 16

Same disposable model; script_id glass_curved_roof; root persistent ID 20606.

## Committed

- R15: three spiral flights retain their original container IDs. Added continuous 740mm-diameter central supports, radial tread supports, 50mm-pitch fine white mesh, handrails and top bridges. Stair outer radius reduced from 2100 to 1700mm to avoid the retained west beam. Existing floor holes and slab/frame geometry untouched.
- Tread vertical-ray test: 216 points passed 2100mm clearance. This is a limited sample, not a complete route or compliance certification. Actual west side gap is about 121mm. Do not interpret projected horizontal beam bands as an occupied floor void; actual L2 west void remains about 30x11m.
- 18 tables: four legs, aprons, braces and rails each. Three tables adjacent to the circular opening moved to Y1500..2500mm. R16 aligned their 36 support instances under those tops; tabletop geometry preserved. Four legs of each corrected table bear from its floor level to tabletop underside at +720mm.
- Upper hall: three suspended curved translucent curtain zones, folded panels, tracks, hooks and roof-fit hangers. Partition placement and hidden joints inferred from source4 and plans, not measured.
- Existing L3 horizontal faces assigned pale mineral material RGB225/224/216; timber shell faces assigned pale wood RGB233/216/183. Only material assignments; roof/floor edge and face identities/coordinates retained. Lower floor finishes were protected and not changed.

## Verified preservation

R16 native transaction committed and post-readback verified. Exact scope guard passed. 21 explicit KEEP paths passed, including beams/frame, outer enclosure, external galleries/platforms/mesh/stairs, ramps, all floors, roof, curtains and completed spiral assemblies. R15 similarly passed the 14 required external/structural KEEP paths plus roof/floor shape assertions. No wrapped SAIE/ADAI method events in these local passes.

## Current review and remaining mismatch

All six native-certified revision16 canonical views and 13 current source-matched/detail captures were submitted to the independent critic. Verdict remains NEEDS_FIX. See visual_qa.md and visual_review.json.

1. New central support is visibly bulkier than source4; diameter reduction with rooted short brackets is prepared in scripts/refine_interior_support_finish.rb but NOT COMMITTED.
2. Interior floors and timber soffit still render darker than the luminous source despite lighter material assignments. A second pale-material refinement is in that same unexecuted script. Do not report its proposed RGB248/246/236 and253/240/216 as present.
3. Critic requests removal of intermediate slab/beam bands; this conflicts with the explicit user KEEP and prior geometric proof of the open west atrium. No beams or slabs were cut. Source-matched section/plan captures remain uncut and occluded; exact section fidelity remains unresolved.

Native writer refused the next refinement: turn write budget exhausted (one initial pass plus at most two targeted corrections). No attempted revision17 transaction was started. Current committed revision remains16. Do not change script_id, scope files or rebuild to evade this limit.

No explicit save/reopen confirmation was received in this agent loop.
