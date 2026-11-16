# Offline launcher-selection tests. Fake EXEs and bridge files are never executed.
$ErrorActionPreference = 'Stop'
. (Join-Path (Split-Path -Parent $PSScriptRoot) 'scripts\sketchup_installation_selection.ps1')
$fixtureRoot = Join-Path (Split-Path -Parent $PSScriptRoot) ('runtime\version-selection-tests\' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $fixtureRoot -Force | Out-Null
$roaming = Join-Path $fixtureRoot 'roaming'
function New-FixtureInstallation([int]$Year, [bool]$Bridge = $false) {
    $directory = Join-Path $fixtureRoot "SU$Year"
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
    New-Item -ItemType File -Path (Join-Path $directory 'SketchUp.exe') -Force | Out-Null
    if ($Bridge) {
        $plugin = Get-KStudioSketchUpBridgePath -Year $Year -RoamingRoot $roaming
        New-Item -ItemType Directory -Path (Split-Path -Parent $plugin) -Force | Out-Null
        New-Item -ItemType File -Path $plugin -Force | Out-Null
    }
    return [pscustomobject]@{DisplayName="SketchUp Pro $Year";InstallLocation=$directory}
}
function Assert-Year($Selection, [int]$Year, [string]$Name) {
    if ($Selection.Year -ne $Year) { throw "$Name expected $Year, got $($Selection.Year)" }
    Write-Output "PASS: $Name"
}
function Assert-Rejected([scriptblock]$Action, [string]$Message, [string]$Name) {
    $caught = $false
    try { & $Action | Out-Null } catch { if ($_.Exception.Message -notmatch $Message) { throw }; $caught=$true }
    if (-not $caught) { throw "$Name was not rejected" }
    Write-Output "PASS: $Name"
}
$su22 = New-FixtureInstallation 2022
$su24 = New-FixtureInstallation 2024 $true
$su25 = New-FixtureInstallation 2025
$su30 = New-FixtureInstallation 2030
$all = @($su22,$su24,$su25)
Assert-Year (Select-KStudioSketchUpInstallation -Installations $all -RunningExecutablePaths (Join-Path $su22.InstallLocation 'SketchUp.exe') -RoamingRoot $roaming) 2022 'running user version takes precedence over configured 2024'
Assert-Year (Select-KStudioSketchUpInstallation -Installations $all -RequestedYear 2025 -RoamingRoot $roaming) 2025 'explicit installed selection is respected'
Assert-Year (Select-KStudioSketchUpInstallation -Installations $all -RoamingRoot $roaming) 2024 'only configured bridge is unambiguous'
Assert-Year (Select-KStudioSketchUpInstallation -Installations @($su25)) 2025 'single installed version without historical preference'
Assert-Year (Select-KStudioSketchUpInstallation -Installations @($su30)) 2030 'discovery is not capped at historical test years'
Assert-Year (Select-KStudioSketchUpInstallation -Installations @($su22,$su22)) 2022 'duplicate registry entries are deduplicated'
Assert-Rejected { Select-KStudioSketchUpInstallation -Installations $all -RequestedYear 2023 } 'missing or ambiguous' 'missing explicit version never falls back'
Assert-Rejected { Select-KStudioSketchUpInstallation -Installations @($su22,$su25) } 'Several SketchUp installations' 'ambiguous closed installations are not guessed'
Assert-Rejected { Select-KStudioSketchUpInstallation -Installations $all -RunningExecutablePaths @((Join-Path $su22.InstallLocation 'SketchUp.exe'),(Join-Path $su24.InstallLocation 'SketchUp.exe')) } 'Several SketchUp versions are running' 'multiple running versions are not guessed'
Assert-Rejected { Select-KStudioSketchUpInstallation -Installations $all -RunningExecutablePaths (Join-Path $fixtureRoot 'unknown\SketchUp.exe') } 'could not be matched' 'unknown running installation does not fall back'
Assert-Rejected { Select-KStudioSketchUpInstallation -Installations @() } 'No registered SketchUp' 'missing executable fails clearly'
$missing = [pscustomobject]@{DisplayName='SketchUp 2023';InstallLocation=(Join-Path $fixtureRoot 'absent')}
Assert-Rejected { Select-KStudioSketchUpInstallation -Installations @($missing) } 'No registered SketchUp' 'invalid registry executable is rejected'
$su25 = New-FixtureInstallation 2025 $true
Assert-Rejected { Select-KStudioSketchUpInstallation -Installations @($su24,$su25) -RoamingRoot $roaming } 'Several SketchUp installations' 'multiple configured bridges still require a choice'
Assert-Year (Select-KStudioSketchUpInstallation -Installations $all -RunningExecutablePaths @((Join-Path $su22.InstallLocation 'SketchUp.exe'),(Join-Path $su22.InstallLocation 'SketchUp.exe'))) 2022 'multiple documents in same executable do not imply multiple versions'
Assert-Rejected { Select-KStudioSketchUpInstallation -Installations $all -RequestedYear 1234 } 'four-digit' 'invalid year rejected'
Write-Output '15 offline selection checks passed. Native software compatibility was not tested.'
