# K Studio WEBSITE modeling test only; outer Codex controller is unchanged.
$ErrorActionPreference = 'Stop'
$env:ARCH_STUDIO_ECONOMY_PROVIDER = 'codex'
$env:ARCH_STUDIO_ECONOMY_MODEL = 'gpt-6.1-sol'
$env:ARCH_STUDIO_ECONOMY_REASONING_EFFORT = 'medium'
# Owner-authorized local iteration: retain usage telemetry, disable cost/call caps.
# This is the native proxy only; paid Responses budgets remain independent.
$env:ARCH_STUDIO_CODEX_MAX_PROJECT_INPUT_TOKENS = '0'
$env:ARCH_STUDIO_CODEX_PROJECT_DELIVERY_RESERVE = '0'
$env:ARCH_STUDIO_CODEX_MAX_TURN_INPUT_TOKENS = '0'
$env:ARCH_STUDIO_CODEX_MAX_TURN_TOOL_CALLS = '0'
Write-Host 'K Studio website model request: gpt-6.1-sol / medium. Confirm actual app-server thread and turn identity before declaring test PASS.'
python scripts/dev.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
