param(
    [Parameter(Mandatory = $false)]
    [ValidatePattern('^[a-z0-9][a-z0-9-]{0,55}$')]
    [string]$ProjectId = 'demo-cultural-center',
    [Parameter(Mandatory = $false)]
    [string]$RuntimeRoot = '',
    [Parameter(Mandatory = $false)]
    [string]$ModelPath = '',
    [Parameter(Mandatory = $false)]
    [ValidateRange(0,2026)]
    [int]$SketchUpYear = 0,
    [switch]$PrepareOnly
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$runtimeRootResolved = if ([string]::IsNullOrWhiteSpace($RuntimeRoot)) { Join-Path $repoRoot 'runtime' } else { [System.IO.Path]::GetFullPath($RuntimeRoot) }
$expectedProjectsRoot = [System.IO.Path]::GetFullPath((Join-Path $runtimeRootResolved 'projects')).TrimEnd('\') + '\'
$modelDirectory = [System.IO.Path]::GetFullPath((Join-Path $runtimeRootResolved "projects\$ProjectId\outputs\model"))
if (-not $modelDirectory.StartsWith($expectedProjectsRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'The disposable SketchUp copy must stay under this project runtime directory.'
}
$uninstallRoots = @(
    'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
    'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'
)
$installations = foreach ($root in $uninstallRoots) {
    Get-ChildItem $root -ErrorAction SilentlyContinue |
        ForEach-Object { Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue } |
        Where-Object { $_.DisplayName -match '^SketchUp( Pro)? (2018|2019|2020|2021|2022|2023|2024|2025|2026)$' -and $_.InstallLocation }
}
if ($SketchUpYear -ne 0 -and ($SketchUpYear -lt 2018 -or $SketchUpYear -gt 2026)) {
    throw 'SketchUpYear must be 2018..2026, or 0 for the existing 2024/2022 default.'
}
if ($SketchUpYear -ne 0) {
    # Explicit selection for per-version compatibility probes. Never substitute.
    $installation = $installations | Where-Object {
        $_.DisplayName -match (" " + $SketchUpYear + "$")
    } | Select-Object -First 1
} else {
    # Preserve the existing default 2024 then 2022.
    $installation = $installations | Where-Object {
        $_.DisplayName -match '2024$|2022$'
    } | Sort-Object @{ Expression = { if ($_.DisplayName -match '2024$') { 0 } else { 1 } } } | Select-Object -First 1
}
if (-not $installation) {
    throw "Requested SketchUp version not found. Default is 2024 then 2022; explicit -SketchUpYear targets 2018..2026 only when installed."
}

$installRoot = $installation.InstallLocation.TrimEnd('\')
$sketchupExe = Join-Path $installRoot 'SketchUp.exe'
if (-not (Test-Path $sketchupExe)) {
    throw "SketchUp executable not found under the registered install location."
}
$templateRoots = @(
    (Join-Path $installRoot 'Resources\zh-cn\Templates'),
    (Join-Path $installRoot 'Resources\en-US\Templates')
)
$template = foreach ($root in $templateRoots) {
    $candidate = Join-Path $root 'Temp01a - Simple.skp'
    if (Test-Path $candidate) { $candidate; break }
}
if (-not $template) {
    # Some older versions or localizations use different template names.
    foreach ($root in $templateRoots) {
        if (-not (Test-Path $root)) { continue }
        $template = Get-ChildItem -Path $root -Filter '*.skp' -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match 'Simple|简易|简单' } |
            Select-Object -First 1 -ExpandProperty FullName
        if ($template) { break }
    }
}
if (-not $template) {
    throw 'No blank Simple template found for this version. Supply a project-owned blank-disposable SKP from the target version.'
}

New-Item -ItemType Directory -Force -Path $modelDirectory | Out-Null
if (-not [string]::IsNullOrWhiteSpace($ModelPath)) {
    $modelPath = [System.IO.Path]::GetFullPath($ModelPath)
    if (-not $modelPath.StartsWith(($modelDirectory.TrimEnd('\') + '\'), [System.StringComparison]::OrdinalIgnoreCase) -or
        [System.IO.Path]::GetExtension($modelPath) -ne '.skp' -or
        -not [System.IO.Path]::GetFileName($modelPath).StartsWith('blank-disposable-', [System.StringComparison]::OrdinalIgnoreCase) -or
        -not (Test-Path -LiteralPath $modelPath -PathType Leaf)) {
        throw 'The requested SketchUp session file is not a valid project disposable copy.'
    }
} else {
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $modelPath = Join-Path $modelDirectory "blank-disposable-$stamp.skp"
    Copy-Item -LiteralPath $template -Destination $modelPath
}
$bridgeStartup = Join-Path $PSScriptRoot 'start_existing_sketchup_bridge.rb'
if (-not (Test-Path $bridgeStartup)) {
    throw 'Bridge startup helper is missing from scripts.'
}
if ($PrepareOnly) { Write-Host "Prepared disposable model: $modelPath"; return }
# This launcher uses the EXISTING Kongxing bridge, not the separate ADAI MCP.
# Opening SketchUp without the per-version extension would look like a
# successful launch although no K Studio modeling tools can connect.
if ($installation.DisplayName -notmatch '(20[12][0-9]) '-RubyStartup "' + $bridgeStartup + '" "' + $modelPath + '"'
Start-Process -FilePath $sketchupExe -ArgumentList $arguments | Out-Null
Write-Host 'Opened a copied SketchUp Simple template in a disposable Demo model.' -ForegroundColor Green
Write-Host 'Started the already-installed Kongxing AI local Bridge through SketchUp RubyStartup.'
Write-Host "Disposable model: $modelPath"
) {
    throw 'Could not resolve the selected SketchUp installation year.'
}
$selectedYear = [int]$Matches[1]
if (-not $env:APPDATA) {
    throw 'APPDATA unavailable; cannot check the SketchUp per-version plugin.'
}
$pluginMain = Join-Path $env:APPDATA "SketchUp\\SketchUp $selectedYear\\SketchUp\\Plugins\\kongxing_ai_sketchup\\main.rb"
if (-not (Test-Path -LiteralPath $pluginMain -PathType Leaf)) {
    throw "SketchUp $selectedYear is installed, but its Kongxing bridge was not found. Install/validate the compatible plugin for that version or test ADAI in a separate profile. Version discovery is not functional compatibility."
}
$arguments = '-RubyStartup "' + $bridgeStartup + '" "' + $modelPath + '"'
Start-Process -FilePath $sketchupExe -ArgumentList $arguments | Out-Null
Write-Host 'Opened a copied SketchUp Simple template in a disposable Demo model.' -ForegroundColor Green
Write-Host 'Started the already-installed Kongxing AI local Bridge through SketchUp RubyStartup.'
Write-Host "Disposable model: $modelPath"
