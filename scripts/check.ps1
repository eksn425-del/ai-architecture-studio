$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $repoRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $pythonPath)) {
    throw 'Run .\scripts\setup.ps1 first.'
}

Set-Location $repoRoot
& $pythonPath -m compileall -q app
if ($LASTEXITCODE -ne 0) { throw 'Python syntax check failed.' }
& $pythonPath -m pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Demo checks failed.' }
Write-Host 'All Demo v0.1 checks passed.' -ForegroundColor Green
