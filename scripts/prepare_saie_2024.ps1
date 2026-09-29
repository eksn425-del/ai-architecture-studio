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

& (Join-Path $PSScriptRoot 'apply_saie_2024_patch.ps1') -SourceRoot $saieRoot

Write-Host 'Installing pinned SAIE checkout into the project venv...' -ForegroundColor Cyan
& $python -m pip install $saieRoot 'mcp==1.30.0'
if ($LASTEXITCODE -ne 0) { throw 'Pinned SAIE and MCP 1.30.0 install failed.' }

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
    if ($Symlink) { throw 'The reproducible 2024 compatibility install uses a copied plugin; -Symlink is unsupported.' }
    $pluginsDir = Join-Path $env:APPDATA "SketchUp\SketchUp $Version\SketchUp\Plugins"
    if (-not (Test-Path -LiteralPath $pluginsDir)) { throw "SketchUp plugin directory not found: $pluginsDir" }
    $sourcePlugin = Join-Path $saieRoot 'ruby_plugin\su_mcp_bridge'
    $sourceLoader = Join-Path $saieRoot 'ruby_plugin\su_mcp_bridge.rb'
    if (-not (Test-Path -LiteralPath $sourcePlugin) -or -not (Test-Path -LiteralPath $sourceLoader)) {
        throw 'Pinned SAIE Ruby plugin sources are incomplete.'
    }
    $installedPlugin = Join-Path $pluginsDir 'su_mcp_bridge'
    New-Item -ItemType Directory -Force -Path $installedPlugin | Out-Null
    Copy-Item -Path (Join-Path $sourcePlugin '*') -Destination $installedPlugin -Recurse -Force
    Copy-Item -LiteralPath $sourceLoader -Destination (Join-Path $pluginsDir 'su_mcp_bridge.rb') -Force
    Write-Host "Installed patched SAIE Ruby plugin into SketchUp $Version. Restart SketchUp before ping/smoke." -ForegroundColor Green
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
