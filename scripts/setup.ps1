param(
    [switch]$InstallModelProviders,
    [switch]$InstallSaie
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $repoRoot '.venv'
$pythonCommand = Get-Command python -ErrorAction Stop

if (-not (Test-Path (Join-Path $venvPath 'Scripts/python.exe'))) {
    & $pythonCommand.Source -m venv $venvPath
}

$python = Join-Path $venvPath 'Scripts/python.exe'
& $python -m pip install --upgrade pip
& $python -m pip install -r (Join-Path $repoRoot 'requirements.txt')
if ($InstallModelProviders) {
    & $python -m pip install -r (Join-Path $repoRoot 'requirements-model-providers.txt')
    Write-Host 'Optional LiteLLM model provider adapter is installed.' -ForegroundColor Cyan
}
if ($InstallSaie) {
    Write-Host 'Installing upstream SAIE package (MIT). SAIE currently targets SketchUp 2025 upstream; verify the local SketchUp/plugin version before enabling it in AI Architecture Studio.' -ForegroundColor Yellow
    & $python -m pip install saie
    Write-Host 'SAIE Python/MCP package installed. Do not enable ARCH_STUDIO_ENABLE_SAIE until the SAIE SketchUp plugin is installed and `saie ping` succeeds.' -ForegroundColor Cyan
}
Write-Host 'AI Architecture Studio environment is ready.' -ForegroundColor Green
