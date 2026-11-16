$ErrorActionPreference='Stop'
$current=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'version.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$rollbackFile=Join-Path $current.upgrade_audit 'rollback-version.json'
if(-not (Test-Path -LiteralPath $rollbackFile)){throw 'Rollback snapshot unavailable.'}
$listener=Get-NetTCPConnection -LocalPort $current.port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if($listener){
    $owner=Get-CimInstance Win32_Process -Filter ('ProcessId='+$listener.OwningProcess)
    if($owner.CommandLine -notlike ('*'+(Join-Path $current.code_directory 'scripts\dev.py')+'*')){throw 'A different service owns this port. Rollback stopped.'}
    $status=Invoke-RestMethod ('http://127.0.0.1:'+$current.port+'/api/status') -TimeoutSec 3
    if($status.active_project_id){throw 'A project task is active. Finish or stop it normally before rollback.'}
    Get-CimInstance Win32_Process | Where-Object {$_.Name -eq 'pythonw.exe' -and $_.CommandLine -like ('*'+(Join-Path $current.code_directory 'scripts\desktop.py')+'*') -and $_.CommandLine -like ('*--attach '+$current.port+'*')} | ForEach-Object {Stop-Process -Id $_.ProcessId}
    Stop-Process -Id $owner.ProcessId
}
Copy-Item -LiteralPath $rollbackFile -Destination (Join-Path $PSScriptRoot 'version.json') -Force
& (Join-Path $PSScriptRoot 'Open-KStudio-v2.ps1')
