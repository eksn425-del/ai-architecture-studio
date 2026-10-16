# Roof clearance correction — scope conflict, no geometry write

2026-10-14 latest request: increase central clearance using original sections; preserve concave roof and correct right-high direction; do not change ramps, floors, glass or other geometry.

All eight original attached sheets directly re-inspected, including exterior/model pairs (1/2), entry/gallery (3), upper and double-height interiors (4), section/ground plan (5), four exploded systems (6), three floor plans (7), climate/structure sections (8). Sources 5/8 show a visibly taller upper-hall central clearance; sources 1/2 corroborate the band between the roof trough and outer flat canopy. Source 4 preserves concave timber soffit. Dimensions are inferred, not measured.

Current verified model blank-disposable-p0-repaired-r2; root 20606 revision 3. ROOF_TIMBER 77872 contains CURVED_SHELL 77873 and ROOF_SUPPORTS 78849. Shell minimum is approximately 13800 mm; top floor 10800 mm, central clearance approximately 3000 mm. Outer canopy is 13500 mm. A preliminary source-proportioned target is approximately 4000 mm central clearance, subject to joint solution; no exact dimension is supplied.

ROOF_SUPPORTS also owns END_GLASS_0/1_* and END_MULLION_0/1_*: their upper edges follow the CURRENT roof curve (central glass max 13802.9 mm etc.). After r3 reflection their relationship is unchanged. Raising the short-end roof trough about 1000 mm with these glass edges fixed would create an approximately 1000 mm separation. Raising the interior alone while pinning both short ends would introduce an unsupported longitudinal hump absent from sources 2/6. Adding a deep opaque fascia would likewise invent a new material band. None is silently assumed.

Pending user selection: keep glass exactly unchanged and accept roof/glass separation, or permit only upper glass/frame edges to follow the corrected curve. No geometry writes or saves this turn so far. All ramps, floors, other glass and assemblies remain unchanged.

Method candidate kstudio.custom_owned_ruby for in-place native roof vertex correction and, only if authorized, connected upper glass/frame vertices. SAIE straight walls are not suitable; ADAI re-extrusion would replace existing native mesh unnecessarily. No helper invoked. Prior roof-handedness script must never be rerun for this new request. Keep right-high edge positions and continuous concavity.


Owner approved connected end-glass upper edges and frames; gap is forbidden. Selected 1000mm smooth middle lift, zero at roof side endpoints. Actual shell underside vertices supply the reference profile, with interpolation evaluated for every end-glass joint; protected side posts and edge rails unchanged. All other geometry KEEP.
