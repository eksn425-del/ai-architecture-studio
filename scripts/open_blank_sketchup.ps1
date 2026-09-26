$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$uninstallRoots = @(
    'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
    'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'
)
$installations = foreach ($root in $uninstallRoots) {
    Get-ChildItem $root -ErrorAction SilentlyContinue |
        ForEach-Object { Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue } |
        Where-Object { $_.DisplayName -match '^SketchUp (2024|Pro 2022)$' -and $_.InstallLocation }
}
$installation = $installations | Sort-Object @{ Expression = { if ($_.DisplayName -match '2024') { 0 } else { 1 } } } | Select-Object -First 1
if (-not $installation) {
    throw 'SketchUp 2024 or SketchUp Pro 2022 was not found in the Windows uninstall registry.'
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
    throw 'The SketchUp Simple template was not found; create a new blank model from SketchUp instead.'
}

$modelDirectory = Join-Path $repoRoot 'runtime\projects\demo-cultural-center\outputs\model'
New-Item -ItemType Directory -Force -Path $modelDirectory | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$modelPath = Join-Path $modelDirectory "blank-disposable-$stamp.skp"
Copy-Item -LiteralPath $template -Destination $modelPath
$bridgeStartup = Join-Path $PSScriptRoot 'start_existing_sketchup_bridge.rb'
if (-not (Test-Path $bridgeStartup)) {
    throw 'Bridge startup helper is missing from scripts.'
}
$arguments = '-RubyStartup "' + $bridgeStartup + '" "' + $modelPath + '"'
Start-Process -FilePath $sketchupExe -ArgumentList $arguments | Out-Null
Write-Host 'Opened a copied SketchUp Simple template in a disposable Demo model.' -ForegroundColor Green
Write-Host 'Started the already-installed Kongxing AI local Bridge through SketchUp RubyStartup.'
Write-Host "Disposable model: $modelPath"
