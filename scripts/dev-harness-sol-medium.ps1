# K Studio NEW-owner-photo development experiment; native Codex Harness continuity.
# This starts the WEBSITE model route only; do not change the outer Codex controller.
$ErrorActionPreference = 'Stop'
$env:ARCH_STUDIO_ECONOMY_PROVIDER = 'codex'
$env:ARCH_STUDIO_ECONOMY_MODEL = 'gpt-6.1-sol'
$env:ARCH_STUDIO_ECONOMY_REASONING_EFFORT = 'medium'
$env:ARCH_STUDIO_CODEX_RECONSTRUCTION_THREAD_MODE = 'native'
$env:ARCH_STUDIO_RECONSTRUCTION_PROMPT_PROFILE = 'harness'
$env:ARCH_STUDIO_USE_LAUNCHER_MODEL = '1'
# Historical user authorization disabled local DEVELOPMENT proxy caps; usage still
# logged. This is NOT permission to spend on managed/paid Responses inference.
$env:ARCH_STUDIO_CODEX_MAX_PROJECT_INPUT_TOKENS = '0'
$env:ARCH_STUDIO_CODEX_PROJECT_DELIVERY_RESERVE = '0'
$env:ARCH_STUDIO_CODEX_MAX_TURN_INPUT_TOKENS = '0'
$env:ARCH_STUDIO_CODEX_MAX_TURN_TOOL_CALLS = '0'
# Real eight-image local edits exceeded the old 900s deadline after committing.
# Leave usage uncapped and allow source review + native delivery to finish.
$env:ARCH_STUDIO_CODEX_TIMEOUT_SECONDS = '3600'
Write-Host 'NEW PHOTO only: real SITE gpt-6.1-sol / medium, experimental native Codex thread continuity and concise skill. Verify actual thread/turn identity and real thread/resume receipt; NEVER reuse the old stopped r6 project.'
python scripts/dev.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
