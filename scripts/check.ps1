$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $repoRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $pythonPath)) {
    throw 'Run .\scripts\setup.ps1 first.'
}

Set-Location $repoRoot
& $pythonPath -m compileall -q app
if ($LASTEXITCODE -ne 0) { throw 'Python syntax check failed.' }
# Runtime folders can contain third-party plugin caches with their own tests.
# Keep this check scoped to the repository-owned suite.
& $pythonPath -m pytest -q tests
if ($LASTEXITCODE -ne 0) { throw 'Demo checks failed.' }
Write-Host 'All workspace and case-study checks passed.' -ForegroundColor Green
