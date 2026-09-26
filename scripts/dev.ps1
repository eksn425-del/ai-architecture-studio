$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $repoRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $pythonPath)) {
    throw 'Run .\scripts\setup.ps1 first.'
}

Set-Location $repoRoot
& $pythonPath -m uvicorn app.main:app --host 127.0.0.1 --port 8787 --reload
