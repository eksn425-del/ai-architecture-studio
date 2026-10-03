param()
$ErrorActionPreference = 'Stop'
$repoPath = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $repoPath '.venv/Scripts/python.exe'
Push-Location -LiteralPath $repoPath
try {
    $env:LITELLM_LOCAL_MODEL_COST_MAP = 'True'
    # tiktoken discovers encodings via a namespace plugin, invisible to static
    # import analysis. Ship its plugin and cached vocabulary for offline startup.
    $env:TIKTOKEN_CACHE_DIR = Join-Path $repoPath 'runtime/tokenizer-cache'
    & $pythonPath -c "import tiktoken; tiktoken.get_encoding('cl100k_base'); tiktoken.get_encoding('o200k_base')"
    if ($LASTEXITCODE -ne 0) { throw 'Tokenizer vocabulary preparation failed.' }
    & $pythonPath -m PyInstaller --noconfirm --windowed --name KStudio `
        --distpath runtime/desktop-dist --workpath runtime/desktop-build --specpath runtime/desktop-build `
        --add-data "$repoPath/app/static;app/static" --add-data "$repoPath/app/vendor;app/vendor" --add-data "$repoPath/scripts;scripts" `
        --add-data "$repoPath/THIRD_PARTY_NOTICES.md;." --collect-all webview --collect-all litellm `
        --add-data "$env:TIKTOKEN_CACHE_DIR;tokenizer-cache" --hidden-import tiktoken_ext.openai_public `
        --collect-submodules uvicorn --hidden-import tomli --exclude-module pytest scripts/desktop.py
    if ($LASTEXITCODE -ne 0) { throw 'Desktop packaging failed.' }
    Write-Host 'Local desktop build: runtime/desktop-dist/KStudio/KStudio.exe'
    Write-Host 'This build does not distribute SketchUp, Codex credentials or the locally installed Kongxing plugin.'
} finally { Pop-Location }
