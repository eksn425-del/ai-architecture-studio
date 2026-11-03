# Discovery and selection only. No software launches, model writes or registry changes.
function Get-KStudioSketchUpInstallations {
    $roots = @(
        'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
        'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
        'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'
    )
    foreach ($root in $roots) {
        Get-ChildItem $root -ErrorAction SilentlyContinue |
            ForEach-Object { Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue } |
            Where-Object { $_.DisplayName -match '^SketchUp( Pro)? (20\d{2})$' -and $_.InstallLocation }
    }
}

function Get-KStudioSketchUpBridgePath {
    param([int]$Year, [string]$RoamingRoot)
    if ($RoamingRoot) {
        return Join-Path $RoamingRoot "SketchUp\SketchUp $Year\SketchUp\Plugins\kongxing_ai_sketchup\main.rb"
    }
    return $null
}

function Select-KStudioSketchUpInstallation {
    param(
        [object[]]$Installations = @(),
        [string[]]$RunningExecutablePaths = @(),
        [int]$RequestedYear = 0,
        [string]$RoamingRoot = ''
    )
    if ($RequestedYear -ne 0 -and ($RequestedYear -lt 2000 -or $RequestedYear -gt 2099)) {
        throw 'SketchUpYear must be a four-digit installed year (20xx), or 0 for automatic detection.'
    }
    $seen = @{}
    $candidates = @(foreach ($item in $Installations) {
        if ($item.DisplayName -notmatch '^SketchUp( Pro)? (20\d{2})$' -or -not $item.InstallLocation) { continue }
        $year = [int]$Matches[2]
        $exe = [IO.Path]::GetFullPath((Join-Path $item.InstallLocation 'SketchUp.exe'))
        if (-not (Test-Path -LiteralPath $exe -PathType Leaf) -or $seen.ContainsKey($exe)) { continue }
        $seen[$exe] = $true
        $plugin = Get-KStudioSketchUpBridgePath -Year $year -RoamingRoot $RoamingRoot
        [pscustomobject]@{
            DisplayName = $item.DisplayName; InstallLocation = $item.InstallLocation
            Year = $year; ExecutablePath = $exe
            BridgePresent = [bool]($plugin -and (Test-Path -LiteralPath $plugin -PathType Leaf))
        }
    })
    if ($RequestedYear -ne 0) {
        $selected = @($candidates | Where-Object Year -eq $RequestedYear)
        if ($selected.Count -ne 1) { throw "Requested SketchUp $RequestedYear installation is missing or ambiguous. No other version was selected." }
        return $selected[0]
    }
    $running = @($RunningExecutablePaths | Where-Object { $_ } | ForEach-Object { [IO.Path]::GetFullPath($_) } | Sort-Object -Unique)
    if ($running.Count -gt 1) { throw 'Several SketchUp versions are running. Keep only the version you intend to connect, or select -SketchUpYear explicitly.' }
    if ($running.Count -eq 1) {
        $selected = @($candidates | Where-Object { $_.ExecutablePath -eq $running[0] })
        if ($selected.Count -ne 1) { throw 'The running SketchUp executable could not be matched to an installed version. No alternative version was selected.' }
        return $selected[0]
    }
    $configured = @($candidates | Where-Object BridgePresent)
    if ($configured.Count -eq 1) { return $configured[0] }
    if ($candidates.Count -eq 1) { return $candidates[0] }
    if ($candidates.Count -eq 0) { throw 'No registered SketchUp installation with a valid executable was found. Install or configure your existing SketchUp; no specific year is required.' }
    throw 'Several SketchUp installations are available. Open your preferred version first, or select -SketchUpYear explicitly. K Studio will not choose a different version silently.'
}
