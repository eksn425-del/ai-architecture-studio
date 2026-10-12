# K Studio WEBSITE modeling test only; outer Codex controller is unchanged.
$ErrorActionPreference = 'Stop'
$env:ARCH_STUDIO_ECONOMY_PROVIDER = 'codex'
$env:ARCH_STUDIO_ECONOMY_MODEL = 'gpt-6.1-sol'
$env:ARCH_STUDIO_ECONOMY_REASONING_EFFORT = 'medium'
Write-Host 'K Studio website model request: gpt-6.1-sol / medium. Confirm actual app-server thread and turn identity before declaring test PASS.'
python scripts/dev.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
