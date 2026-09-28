param(
    [string]$Version = '2024',
    [switch]$InstallPlugin,
    [switch]$Symlink
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot '.venv\Scripts\python.exe'
$saieRoot = Join-Path $repoRoot '.local\oss\saie'
$metadataDir = Join-Path $repoRoot 'runtime\saie-compat'
$metadataPath = Join-Path $metadataDir 'source.json'
$saieRepo = 'https://github.com/iamahsanmehmood/saie.git'
# Latest upstream main commit reviewed by ChatGPT on 2026-09-28.
# Pin the compatibility smoke so Codex and later reviewers test the same code.
$saieRevision = 'eff6f41ff866bef6b4f2b90be2faa6fe2cc4347f'

if (-not (Test-Path $python)) {
    throw 'Project venv is missing. Run .\scripts\setup.ps1 first.'
}

New-Item -ItemType Directory -Path (Split-Path -Parent $saieRoot) -Force | Out-Null
New-Item -ItemType Directory -Path $metadataDir -Force | Out-Null

if (-not (Test-Path (Join-Path $saieRoot '.git'))) {
    Write-Host 'Cloning upstream SAIE into ignored .local/oss/saie...' -ForegroundColor Cyan
    git clone $saieRepo $saieRoot
    if ($LASTEXITCODE -ne 0) { throw 'git clone SAIE failed.' }
} else {
    Write-Host 'Refreshing existing ignored SAIE checkout...' -ForegroundColor Cyan
    git -C $saieRoot fetch origin
    if ($LASTEXITCODE -ne 0) { throw 'git fetch SAIE failed.' }
}

git -C $saieRoot checkout --detach $saieRevision
if ($LASTEXITCODE -ne 0) { throw "Could not checkout pinned SAIE revision $saieRevision." }

Write-Host 'Installing pinned SAIE checkout into the project venv...' -ForegroundColor Cyan
& $python -m pip install -e $saieRoot
if ($LASTEXITCODE -ne 0) { throw 'SAIE editable install failed.' }

$actualRevision = (git -C $saieRoot rev-parse HEAD).Trim()
$metadata = [ordered]@{
    upstream = 'iamahsanmehmood/saie'
    revision = $actualRevision
    expected_revision = $saieRevision
    saie_version = '1.0.0'
    requested_sketchup_version = $Version
    plugin_install_requested = [bool]$InstallPlugin
    install_mode = $(if ($Symlink) { 'symlink' } else { 'copy' })
    prepared_at = (Get-Date).ToUniversalTime().ToString('o')
}
$metadata | ConvertTo-Json -Depth 4 | Set-Content -Path $metadataPath -Encoding UTF8

if ($InstallPlugin) {
    $installer = Join-Path $saieRoot 'scripts\install_plugin.ps1'
    if (-not (Test-Path $installer)) {
        throw "Upstream installer missing: $installer"
    }
    Write-Host "Installing the unmodified upstream SAIE plugin into SketchUp $Version..." -ForegroundColor Yellow
    if ($Symlink) {
        & $installer -Version $Version -Symlink -Force
    } else {
        & $installer -Version $Version -Force
    }
    if ($LASTEXITCODE -ne 0) { throw 'Upstream SAIE plugin installer failed.' }
}

$saieMcp = Join-Path $repoRoot '.venv\Scripts\saie-mcp.exe'
$saieCli = Join-Path $repoRoot '.venv\Scripts\saie.exe'
Write-Host ''
Write-Host 'SAIE compatibility source is prepared.' -ForegroundColor Green
Write-Host "  revision: $actualRevision"
Write-Host "  metadata: $metadataPath"
Write-Host "  CLI:      $saieCli"
Write-Host "  MCP:      $saieMcp"
Write-Host ''
if (-not $InstallPlugin) {
    Write-Host "Plugin was NOT installed. Re-run with -InstallPlugin only when ready for the reversible SketchUp $Version smoke." -ForegroundColor Yellow
} else {
    Write-Host "Next: launch SketchUp $Version, inspect Ruby Console/Extensions, then run '$saieCli ping'." -ForegroundColor Cyan
}
Write-Host "For website discovery in the same PowerShell session:" -ForegroundColor Cyan
Write-Host "  `$env:ARCH_STUDIO_ENABLE_SAIE = '1'"
Write-Host "  `$env:ARCH_STUDIO_SAIE_COMMAND = '$saieMcp'"
