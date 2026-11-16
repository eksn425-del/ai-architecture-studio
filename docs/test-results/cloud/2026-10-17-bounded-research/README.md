# Bounded public research and reconstruction workflow fixes

Baseline: dba75b176b8dcbf3007c6747ddafbf32de331062.

Adds host-authorized, restricted read-only public search/fetch tools separately from geometry permissions; source-labelled imported reference TXT/MD; fixes legitimate reference/plan false blocks; fits oblique previews to model bounds. Existing brief/site uploads remain supported. Includes SSRF, redirect, DNS, query-scope, permissions, imported-path and workflow regressions.

Final exact full suite: 780 passed, 15 skipped, 1 warning, 131.18 seconds. Independent focused review: 186 passed.

Actual live search and fetch were attempted and returned dns_resolution_failed. Normal cloud browser service route returned ERR_CONNECTION_REFUSED. API/TestClient and actual Blender tool execution are verified, not GUI clicks or successful autonomous retrieval. Research policy currently requires an explicitly authorized host policy; no general end-user research opt-in interface was added. Request budget resets per turn, not cumulative project quota.

The separate private twin-tower case uses explicitly simulated current-assistant responses and externally supplied, provenance-labelled source research. Blender plan/approval, edits, unchanged-object checks, editable save and native reopen ran. Visual fidelity remains partial; inferred dimensions and hidden geometry are not as-built measurements. No original Windows SU rerun or independent provider-quality acceptance is claimed. Private images, models and raw logs are excluded.
