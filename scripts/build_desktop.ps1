param()
$ErrorActionPreference = 'Stop'
$repoPath = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $repoPath '.venv/Scripts/python.exe'
Push-Location -LiteralPath $repoPath
try {
    $env:LITELLM_LOCAL_MODEL_COST_MAP = 'True'
    & $pythonPath -m PyInstaller --noconfirm --windowed --name KStudio `
        --distpath runtime/desktop-dist --workpath runtime/desktop-build --specpath runtime/desktop-build `
        --add-data "$repoPath/app/static;app/static" --add-data "$repoPath/app/vendor;app/vendor" --add-data "$repoPath/scripts;scripts" `
        --add-data "$repoPath/THIRD_PARTY_NOTICES.md;." --collect-all webview --collect-all litellm `
        --collect-submodules uvicorn --hidden-import tomli --exclude-module pytest scripts/desktop.py
    if ($LASTEXITCODE -ne 0) { throw 'Desktop packaging failed.' }
    Write-Host 'Local desktop build: runtime/desktop-dist/KStudio/KStudio.exe'
    Write-Host 'This build does not distribute SketchUp, Codex credentials or the locally installed Kongxing plugin.'
} finally { Pop-Location }
