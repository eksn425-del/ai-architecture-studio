$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $repoRoot '.venv'
$pythonCommand = Get-Command python -ErrorAction Stop

if (-not (Test-Path (Join-Path $venvPath 'Scripts/python.exe'))) {
    & $pythonCommand.Source -m venv $venvPath
}

& (Join-Path $venvPath 'Scripts/python.exe') -m pip install --upgrade pip
& (Join-Path $venvPath 'Scripts/python.exe') -m pip install -r (Join-Path $repoRoot 'requirements.txt')
Write-Host 'AI Architecture Studio Demo environment is ready.' -ForegroundColor Green
