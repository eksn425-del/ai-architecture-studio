param([string]$ConfigFile=(Join-Path $PSScriptRoot 'version.json'))
$ErrorActionPreference='Stop'
$mutex=[Threading.Mutex]::new($false,'Local\KStudioLatestDesktopLauncher')
$locked=$false
try {
    $locked=$mutex.WaitOne(0)
    if(-not $locked){exit}
    $config=Get-Content -LiteralPath $ConfigFile -Raw -Encoding UTF8 | ConvertFrom-Json
    & $config.python_executable (Join-Path $PSScriptRoot 'verify-release.py') $config.code_directory $config.commit
    if($LASTEXITCODE -ne 0){throw 'K Studio source verification failed.'}
    if(-not (Test-Path -LiteralPath (Join-Path $config.runtime_directory 'projects'))){throw 'Existing project data is unavailable; startup stopped.'}
    $listener=Get-NetTCPConnection -LocalPort $config.port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if($listener){
        $owner=Get-CimInstance Win32_Process -Filter ('ProcessId='+$listener.OwningProcess)
        if($owner.CommandLine -notlike ('*'+(Join-Path $config.code_directory 'scripts\dev.py')+'*')){throw 'The port is owned by another release or service. No process was stopped.'}
    }else{
        $backend=if($config.api_test_mode){$config.backend_script}else{Join-Path $PSScriptRoot 'Start-KStudioBackend.ps1'}
        $argsLine='-NoProfile -ExecutionPolicy Bypass -File "'+$backend+'" -ConfigFile "'+$ConfigFile+'"'
        Start-Process powershell.exe -ArgumentList $argsLine -WorkingDirectory $config.code_directory -WindowStyle Hidden -RedirectStandardOutput (Join-Path $PSScriptRoot 'backend.stdout.log') -RedirectStandardError (Join-Path $PSScriptRoot 'backend.stderr.log') | Out-Null
    }
    $ready=$false
    for($attempt=0;$attempt -lt 60;$attempt++){
        try{
            $status=Invoke-RestMethod ('http://127.0.0.1:'+$config.port+'/api/status') -TimeoutSec 2
            if($status.app -eq 'ready'){$ready=$true;break}
        }catch{Start-Sleep -Milliseconds 500}
    }
    if(-not $ready){throw 'K Studio did not become ready. Read backend.stderr.log; existing models were not changed.'}
    if($config.api_test_mode){if($status.model_router.economy.provider -ne 'litellm' -or $status.model_router.providers.'codex-app-server'.available){throw 'API test profile must have no Codex inference fallback.'}}else{$expectedEffort=if($config.local_reasoning_effort){$config.local_reasoning_effort}else{'medium'};if($status.native_agent_model -ne 'gpt-6.1-sol' -or $status.native_agent_reasoning_effort -ne $expectedEffort){throw 'The local model profile differs from the explicitly configured Sol effort.'}}
    $desktop=Join-Path $config.code_directory 'scripts\desktop.py'
    $instances=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -eq 'pythonw.exe' -and $_.CommandLine -like ('*'+$desktop+'*') -and $_.CommandLine -like ('*--attach '+$config.port+'*')})
    $existing=$instances | Where-Object {(Get-Process -Id $_.ProcessId -ErrorAction SilentlyContinue).MainWindowHandle -ne [IntPtr]::Zero} | Select-Object -First 1
    if(-not $existing){$existing=$instances | Select-Object -First 1}
    if($existing){
        $desktopId=$existing.ProcessId
        $shell=New-Object -ComObject WScript.Shell
        [void]$shell.AppActivate([int]$desktopId)
    }else{
        $window=Start-Process -FilePath $config.desktop_python -ArgumentList ('"'+$desktop+'" --attach '+$config.port) -WorkingDirectory $config.code_directory -WindowStyle Hidden -RedirectStandardOutput (Join-Path $PSScriptRoot 'desktop.stdout.log') -RedirectStandardError (Join-Path $PSScriptRoot 'desktop.stderr.log') -PassThru
        $desktopId=$window.Id
    }
    @{status='ready';commit=$config.commit;port=$config.port;desktop_pid=$desktopId;code_directory=$config.code_directory;runtime_directory=$config.runtime_directory;opened_at=(Get-Date -Format o)} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'last-launch.json') -Encoding UTF8
    '' | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'launch-error.txt') -Encoding UTF8
}catch{
    $_.Exception.Message | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'launch-error.txt') -Encoding UTF8
    throw
}finally{
    if($locked){$mutex.ReleaseMutex()}
    $mutex.Dispose()
}
