# Modeling quality source provenance

This folder preserves license text for two upstream projects whose implementation patterns are adapted by app/modeling_quality.py.

1. gaoypeng/3dcodebench
   Revision: 42c7780ed3fcbd466f17f058f62e7996233777f7
   Source studied: core/visual_critique.py
   License: Apache-2.0
   Local change: retain the bounded NEEDS_FIX parser idea, remove code-writing from the critic, cap output to three architectural mismatches, and add a KEEP list.

2. dcc-mcp/dcc-mcp-sketchup
   Revision: b7981838eca24996e7e9c2959af1463162022f66
   Source studied: src/dcc_mcp_sketchup/write_contract.py
   License: MIT
   Local change: enforce expected/actual evidence against K Studio's owned project root after commit while keeping the existing Kongxing bridge and recoverable checkpoint semantics.
