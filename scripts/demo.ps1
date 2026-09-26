$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot

if (-not (Test-Path (Join-Path $repoRoot '.venv\Scripts\python.exe'))) {
    & (Join-Path $PSScriptRoot 'setup.ps1')
}

Set-Location $repoRoot
& (Join-Path $repoRoot '.venv\Scripts\python.exe') -m uvicorn app.main:app --host 127.0.0.1 --port 8787
