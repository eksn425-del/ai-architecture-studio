param([int]$Port = 8787, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$trialWorkspace = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $trialWorkspace
if (-not (Get-Command codex -ErrorAction SilentlyContinue)) {
    throw 'The existing local Codex installation was not found. No provider has been substituted.'
}
$trialUrl = "http://127.0.0.1:$Port/"
try { $existingTrial = Invoke-RestMethod ($trialUrl + 'api/status') -TimeoutSec 2 }
catch { $existingTrial = $null }
if ($existingTrial) {
    if ($existingTrial.model_router.economy.provider -ne 'codex-app-server' -or
        $existingTrial.native_agent_model -ne 'gpt-6.1-sol' -or
        $existingTrial.native_agent_reasoning_effort -ne 'medium') {
        throw 'A different model route is already running on this port. Close that server explicitly before starting this candidate.'
    }
    Write-Host "Existing Sol 6.1 Medium workbench: $trialUrl"
    if (-not $NoBrowser) { Start-Process $trialUrl }
    return
}
$env:ARCH_STUDIO_ECONOMY_PROVIDER = 'codex'
$env:ARCH_STUDIO_ECONOMY_MODEL = 'gpt-6.1-sol'
$env:ARCH_STUDIO_ECONOMY_REASONING_EFFORT = 'medium'
$env:ARCH_STUDIO_CODEX_REASONING_EFFORT = 'medium'
$env:ARCH_STUDIO_CODEX_RECONSTRUCTION_THREAD_MODE = 'native'
$env:ARCH_STUDIO_RECONSTRUCTION_PROMPT_PROFILE = 'harness'
# Select the owner's existing Sol route without deleting the encrypted API setting.
$env:ARCH_STUDIO_USE_LAUNCHER_MODEL = '1'
$env:ARCH_STUDIO_CODEX_TIMEOUT_SECONDS = '1800'
$env:CODEX_CLI_PATH = (Get-Command codex).Source
$env:PYTHONIOENCODING = 'utf-8'
Write-Host "Local SU trial: $trialUrl -- gpt-6.1-sol / medium via existing Codex. Keep this terminal open."
if (-not $NoBrowser) { Start-Process $trialUrl }
& python scripts/dev.py --port $Port
if ($LASTEXITCODE -ne 0) { throw 'The trial server did not start. Check dependencies and whether the port is occupied.' }
