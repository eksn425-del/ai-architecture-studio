param([Parameter(Mandatory=$true)][string]$InstallRoot,[Parameter(Mandatory=$true)][string]$DataDir)
$ErrorActionPreference='Stop'
$resolvedRoot=[IO.Path]::GetFullPath($InstallRoot)
$lockDirectory=Join-Path $resolvedRoot 'installer-lock'
[IO.Directory]::CreateDirectory($lockDirectory) | Out-Null
$lease=[IO.File]::Open((Join-Path $lockDirectory '.kstudio-runtime.lock'),[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::ReadWrite)
try {
if ($lease.Length -eq 0) { $lease.WriteByte(0); $lease.Flush() }
try { $lease.Lock(0,1) } catch { throw 'K Studio is updating; please reopen after the update completes.' }
$current=Get-Content -LiteralPath (Join-Path $resolvedRoot 'current.json') -Raw | ConvertFrom-Json
if ($current.version -notmatch '^[A-Za-z0-9][A-Za-z0-9.-]{0,79}$') { throw 'Invalid release pointer' }
$versionPath=[IO.Path]::GetFullPath((Join-Path $resolvedRoot ('versions\'+$current.version)))
if (-not $versionPath.StartsWith($resolvedRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid release destination' }
$exe=Join-Path $versionPath 'KStudio.exe'
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) { throw 'Installed K Studio executable missing' }
$process=Start-Process -FilePath $exe -ArgumentList @('--data-dir',('"'+[IO.Path]::GetFullPath($DataDir)+'"')) -WorkingDirectory $versionPath -WindowStyle Hidden -PassThru
$deadline=[DateTime]::UtcNow.AddSeconds(30)
while ([DateTime]::UtcNow -lt $deadline) {
    if ($process.HasExited) { break }
    $profileLock=Join-Path $DataDir 'desktop-instance\.kstudio-runtime.lock'
    if (Test-Path -LiteralPath $profileLock) {
        $probe=$null
        try { $probe=[IO.File]::Open($profileLock,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::ReadWrite); $probe.Lock(0,1); $probe.Unlock(0,1) }
        catch [IO.IOException] { break }
        finally { if ($probe) { $probe.Dispose() } }
    }
    Start-Sleep -Milliseconds 100
}
} finally { $lease.Dispose() }
