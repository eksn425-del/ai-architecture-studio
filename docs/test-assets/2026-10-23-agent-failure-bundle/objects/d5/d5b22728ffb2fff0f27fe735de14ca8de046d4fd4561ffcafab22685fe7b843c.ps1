$ErrorActionPreference='Stop'
$latest='E:\K Studio\latest'
$current=Get-Content -LiteralPath (Join-Path $latest 'version.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$proposed=Join-Path $PSScriptRoot 'proposed-version.json'
$next=Get-Content -LiteralPath $proposed -Raw -Encoding UTF8 | ConvertFrom-Json
& $next.python_executable (Join-Path $latest 'verify-release.py') $next.code_directory $next.commit
if($LASTEXITCODE -ne 0){throw 'Release verification failed.'}
$status=Invoke-RestMethod ('http://127.0.0.1:'+$current.port+'/api/status') -TimeoutSec 5
if($status.active_project_id){throw 'An active modeling task must finish before UI update.'}
$listener=Get-NetTCPConnection -LocalPort $current.port -State Listen | Select-Object -First 1
$backend=Get-CimInstance Win32_Process -Filter ('ProcessId='+$listener.OwningProcess)
if($backend.CommandLine -notlike ('*'+(Join-Path $current.code_directory 'scripts\dev.py')+'*')){throw 'Unexpected port owner.'}
$all=@(Get-CimInstance Win32_Process)
$desktop=Join-Path $current.code_directory 'scripts\desktop.py'
$owned=[System.Collections.Generic.HashSet[int]]::new()
$all | Where-Object {$_.Name -eq 'pythonw.exe' -and $_.CommandLine -like ('*'+$desktop+'*') -and $_.CommandLine -like ('*--attach '+$current.port+'*')} | ForEach-Object {[void]$owned.Add([int]$_.ProcessId)}
do {$added=$false;foreach($proc in $all){if($owned.Contains([int]$proc.ParentProcessId) -and $owned.Add([int]$proc.ProcessId)){$added=$true}}}while($added)
foreach($ownedId in $owned){Stop-Process -Id $ownedId -ErrorAction SilentlyContinue}
Stop-Process -Id $backend.ProcessId
Copy-Item -LiteralPath $proposed -Destination (Join-Path $latest 'version.json') -Force
$env:WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS='--disable-gpu'
& (Join-Path $latest 'Open-KStudio.ps1')
