param([Parameter(Mandatory=$true)][string]$InstallRoot,[Parameter(Mandatory=$true)][string]$DataDir)
$ErrorActionPreference='Stop'
$InstallRoot=[IO.Path]::GetFullPath($InstallRoot)
$DataDir=[IO.Path]::GetFullPath($DataDir)
$launcher=Join-Path $InstallRoot 'launch_installed.ps1'
if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) { throw 'Installed launcher missing' }
$current=Get-Content -LiteralPath (Join-Path $InstallRoot 'current.json') -Raw | ConvertFrom-Json
if ($current.version -notmatch '^[A-Za-z0-9][A-Za-z0-9.-]{0,79}$') { throw 'Invalid installed version' }
$desktop=[Environment]::GetFolderPath('Desktop')
$destination=Join-Path $desktop 'K Studio.lnk'
if (Test-Path -LiteralPath $destination) {
    $backup=Join-Path $desktop ('K Studio - before update '+[DateTime]::Now.ToString('yyyyMMdd-HHmmss-ffff')+'.lnk')
    Copy-Item -LiteralPath $destination -Destination $backup -ErrorAction Stop
}
$shell=New-Object -ComObject WScript.Shell
$link=$shell.CreateShortcut($destination)
$link.TargetPath=Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$link.Arguments='-NoProfile -WindowStyle Hidden -File "'+$launcher+'" -InstallRoot "'+$InstallRoot+'" -DataDir "'+$DataDir+'"'
$link.WorkingDirectory=$InstallRoot
$link.IconLocation=(Join-Path $InstallRoot ('versions\'+$current.version+'\KStudio.exe'))+',0'
$link.Description='K Studio · AI Architecture'
$link.Save()
Write-Output 'Desktop shortcut installed; prior shortcut preserved if present.'
