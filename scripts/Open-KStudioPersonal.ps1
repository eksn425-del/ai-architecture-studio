param([Parameter(Mandatory=$true)][string]$ConfigFile)
$ErrorActionPreference='Stop'
$launchRoot=Split-Path -Parent $ConfigFile
$mutex=[Threading.Mutex]::new($false,'Local\KStudioLatestDesktopLauncher')
$locked=$false
try {
    $locked=$mutex.WaitOne(0)
    if(-not $locked){exit}
    $config=Get-Content -LiteralPath $ConfigFile -Raw -Encoding UTF8 | ConvertFrom-Json
    if($config.desktop_mode -ne 'personal-byok'){throw 'Personal API desktop configuration is missing.'}
    & $config.python_executable (Join-Path $launchRoot 'verify-release.py') $config.code_directory $config.commit
    if($LASTEXITCODE -ne 0){throw 'Installed release verification failed.'}
    if(-not (Test-Path -LiteralPath (Join-Path $config.runtime_directory 'projects'))){throw 'Existing project data is unavailable; startup stopped.'}
    $backendPath=Join-Path $config.code_directory 'scripts\dev.py'
    $listener=Get-NetTCPConnection -LocalPort $config.port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if($listener){
        $owner=Get-CimInstance Win32_Process -Filter ('ProcessId='+$listener.OwningProcess)
        if($owner.CommandLine -notlike ('*'+$backendPath+'*')){throw 'This port belongs to another service. No process was stopped.'}
    }else{
        $backend=Join-Path $config.code_directory 'scripts\Start-KStudioPersonalBackend.ps1'
        $arguments='-NoProfile -ExecutionPolicy Bypass -File "'+$backend+'" -ConfigFile "'+$ConfigFile+'"'
        Start-Process powershell.exe -ArgumentList $arguments -WorkingDirectory $config.code_directory -WindowStyle Hidden -RedirectStandardOutput (Join-Path $launchRoot 'backend.stdout.log') -RedirectStandardError (Join-Path $launchRoot 'backend.stderr.log') | Out-Null
    }
    $ready=$false
    for($attempt=0;$attempt -lt 60;$attempt++){
        try{
            # Windows PowerShell 5.1 can decode JSON without a charset using the
            # legacy console code page when launched hidden from a shortcut.
            # Decode the actual UTF-8 bytes before comparing Chinese paths.
            $response=Invoke-WebRequest ('http://127.0.0.1:'+$config.port+'/api/status') -UseBasicParsing -TimeoutSec 2
            $status=[Text.Encoding]::UTF8.GetString($response.RawContentStream.ToArray()) | ConvertFrom-Json
            if($status.app -eq 'ready'){$ready=$true;break}
        }catch{Start-Sleep -Milliseconds 500}
    }
    if(-not $ready){throw 'The local service did not become ready. See backend.stderr.log.'}
    if(-not $status.personal_desktop -or $status.installed_commit -ne $config.commit -or $status.runtime_directory -ne $config.runtime_directory){throw 'The running service does not match this installed personal profile.'}
    if($status.codex_available -or $status.model_router.providers.'codex-app-server'.available){throw 'Personal API profile must not use Codex account inference.'}
    $desktop=Join-Path $config.code_directory 'scripts\desktop.py'
    $instances=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -eq 'pythonw.exe' -and $_.CommandLine -like ('*'+$desktop+'*') -and $_.CommandLine -like ('*--attach '+$config.port+'*')})
    $existing=$instances | Where-Object {(Get-Process -Id $_.ProcessId -ErrorAction SilentlyContinue).MainWindowHandle -ne [IntPtr]::Zero} | Select-Object -First 1
    if($existing){
        $desktopId=$existing.ProcessId
        Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class KStudioWindow {
    [DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr window, int command);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr window);
}
'@
        $windowHandle=(Get-Process -Id $desktopId).MainWindowHandle
        [void][KStudioWindow]::ShowWindowAsync($windowHandle,9)
        [void][KStudioWindow]::SetForegroundWindow($windowHandle)
        $shell=New-Object -ComObject WScript.Shell
        [void]$shell.AppActivate([int]$desktopId)
    }else{
        $arguments='"'+$desktop+'" --attach '+$config.port+' --data-dir "'+$config.desktop_data_directory+'"'
        $window=Start-Process -FilePath $config.desktop_python -ArgumentList $arguments -WorkingDirectory $config.code_directory -WindowStyle Normal -RedirectStandardOutput (Join-Path $launchRoot 'desktop.stdout.log') -RedirectStandardError (Join-Path $launchRoot 'desktop.stderr.log') -PassThru
        $desktopId=$window.Id
    }
    @{status='ready';commit=$config.commit;port=$config.port;desktop_pid=$desktopId;desktop_mode='personal-byok';runtime_directory=$config.runtime_directory;opened_at=(Get-Date -Format o)} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $launchRoot 'last-launch.json') -Encoding UTF8
    '' | Set-Content -LiteralPath (Join-Path $launchRoot 'launch-error.txt') -Encoding UTF8
}catch{
    $_.Exception.Message | Set-Content -LiteralPath (Join-Path $launchRoot 'launch-error.txt') -Encoding UTF8
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show(('K Studio could not start. '+$_.Exception.Message),'K Studio') | Out-Null
    throw
}finally{
    if($locked){$mutex.ReleaseMutex()}
    $mutex.Dispose()
}
