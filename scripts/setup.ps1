param(
    [switch]$InstallModelProviders
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $repoRoot '.venv'
$pythonCommand = Get-Command python -ErrorAction Stop

if (-not (Test-Path (Join-Path $venvPath 'Scripts/python.exe'))) {
    & $pythonCommand.Source -m venv $venvPath
}

& (Join-Path $venvPath 'Scripts/python.exe') -m pip install --upgrade pip
& (Join-Path $venvPath 'Scripts/python.exe') -m pip install -r (Join-Path $repoRoot 'requirements.txt')
if ($InstallModelProviders) {
    & (Join-Path $venvPath 'Scripts/python.exe') -m pip install -r (Join-Path $repoRoot 'requirements-model-providers.txt')
    Write-Host 'Optional LiteLLM model provider adapter is installed.' -ForegroundColor Cyan
}
Write-Host 'AI Architecture Studio environment is ready.' -ForegroundColor Green
