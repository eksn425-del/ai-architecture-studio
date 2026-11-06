<# Read-only customer diagnostics. No Python/Codex, installation, inference or model scan.
Only the explicitly named output directory is written. Optional HTTP reads target
127.0.0.1 and configuration/status endpoints; no MCP tool or model is invoked.
#>
param(
    [Parameter(Mandatory=$true)][string]$Bundle,
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [string]$Inventory,
    [string]$ExpectedInventorySha256,
    [ValidateRange(0,65535)][int]$RuntimePort=0
)
$ErrorActionPreference='Stop'
$bundlePath=[IO.Path]::GetFullPath($Bundle).TrimEnd('\','/')
$outputPath=[IO.Path]::GetFullPath($OutputDirectory).TrimEnd('\','/')
if(-not(Test-Path -LiteralPath $bundlePath -PathType Container)){throw '请选择已解压的程序目录，不是用户数据或模型目录。'}
if($outputPath -eq $bundlePath -or $outputPath.StartsWith($bundlePath+'\',[StringComparison]::OrdinalIgnoreCase)){throw '报告目录必须在程序包之外，避免更改被检查的包。'}
if(Test-Path -LiteralPath $outputPath){throw '报告目录已经存在；请选择新目录，保留之前的证据。'}
function Safe-BundlePath([string]$Relative){
    if(-not $Relative -or [IO.Path]::IsPathRooted($Relative) -or $Relative.Contains(':') -or $Relative -match '(^|[\\/])\.\.([\\/]|$)'){throw 'Unsafe inventory path'}
    $resolved=[IO.Path]::GetFullPath((Join-Path $bundlePath $Relative))
    if(-not $resolved.StartsWith($bundlePath+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Inventory outside bundle'}
    $current=$resolved
    while($current -and $current.Length -ge $bundlePath.Length){
        if(Test-Path -LiteralPath $current){
            if((Get-Item -LiteralPath $current -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Reparse point is not followed'}
        }
        if($current -eq $bundlePath){break}
        $current=Split-Path -Parent $current
    }
    return $resolved
}
function Bool-OrNull($Object,[string]$Property){
    if($null -eq $Object -or -not $Object.PSObject.Properties[$Property]){return $null}
    if($Object.$Property -is [bool]){return $Object.$Property}
    return $null
}
function Read-FileSha256([string]$Path){
    $stream=[IO.File]::OpenRead($Path);$sha=[Security.Cryptography.SHA256]::Create()
    try{return [BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-','').ToLower()}
    finally{$sha.Dispose();$stream.Dispose()}
}
function Local-Json([string]$Path){
    Add-Type -AssemblyName System.Net.Http
    $handler=New-Object System.Net.Http.HttpClientHandler
    $handler.AllowAutoRedirect=$false;$handler.UseProxy=$false
    $client=New-Object System.Net.Http.HttpClient($handler)
    $client.Timeout=[TimeSpan]::FromSeconds(8)
    try{
        $response=$client.GetAsync('http://127.0.0.1:'+$RuntimePort+$Path).GetAwaiter().GetResult()
        if(-not $response.IsSuccessStatusCode){return $null}
        $content=$response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
        if($content.Length -gt 2000000){return $null}
        return ($content | ConvertFrom-Json)
    }catch{return $null}finally{$client.Dispose();$handler.Dispose()}
}
$report=[ordered]@{
    schema=1;scope='READ_ONLY_CUSTOMER_ENVIRONMENT_CHECK';created_utc=[DateTime]::UtcNow.ToString('o')
    no_install=$true;no_paid_inference=$true;no_native_tool_calls=$true;no_user_models_scanned=$true
    clean_machine_acceptance='NOT_RUN';native_modeling_quality='NOT_RUN';provider_live_acceptance='NOT_RUN'
    privacy='No username, hostname, SID, absolute local paths, credentials, model names or raw API responses included.'
}
$osVersion=[Environment]::OSVersion.Version.ToString()
try{$os=Get-CimInstance Win32_OperatingSystem;$osVersion=$os.Version}catch{}
$report.windows=@{version=$osVersion;is_64bit_os=[Environment]::Is64BitOperatingSystem;is_64bit_process=[Environment]::Is64BitProcess;powershell=$PSVersionTable.PSVersion.ToString();compatibility='DETECTED_ONLY'}
$net=Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full' -ErrorAction SilentlyContinue
$report.dotnet_framework=@{release=$net.Release;version=$net.Version;status=$(if($net.Release){'DETECTED'}else{'NOT_DETECTED'});note='Detection is not a launch compatibility verdict.'}
$webview=@()
foreach($key in @('HKLM:\SOFTWARE\Microsoft\EdgeUpdate\Clients','HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients','HKCU:\SOFTWARE\Microsoft\EdgeUpdate\Clients')){
    foreach($entry in @(Get-ChildItem -LiteralPath $key -ErrorAction SilentlyContinue)){
        $value=Get-ItemProperty -LiteralPath $entry.PSPath -ErrorAction SilentlyContinue
        if($value.name -match 'WebView2' -and $value.pv -match '^\d+(\.\d+){1,4}$'){$webview+=$value.pv}
    }
}
$report.webview2=@{status=$(if($webview.Count){'DETECTED'}else{'NOT_DETECTED'});versions=@($webview|Sort-Object -Unique);note='Evergreen registry detection only; no download or install.'}
$sketchup=@()
foreach($key in @('HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall','HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall','HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall')){
    foreach($entry in @(Get-ChildItem -LiteralPath $key -ErrorAction SilentlyContinue)){
        $value=Get-ItemProperty -LiteralPath $entry.PSPath -ErrorAction SilentlyContinue
        if($value.DisplayName -notmatch '^SketchUp( Pro)? (20\d{2})$'){continue}
        $year=[int]$Matches[2];$exePresent=$false
        if($value.InstallLocation){$exePresent=Test-Path -LiteralPath (Join-Path $value.InstallLocation 'SketchUp.exe') -PathType Leaf}
        $pluginBase=Join-Path $env:APPDATA ('SketchUp\SketchUp '+$year+'\SketchUp\Plugins')
        $plugin=(Test-Path -LiteralPath (Join-Path $pluginBase 'kstudio_connector.rb') -PathType Leaf) -and (Test-Path -LiteralPath (Join-Path $pluginBase 'kstudio_connector\main.rb') -PathType Leaf)
        $version=$null;if($value.DisplayVersion -match '^\d+(\.\d+){0,4}$'){$version=$value.DisplayVersion}
        $sketchup+=@{year=$year;version=$version;executable_present=[bool]$exePresent;public_plugin_files_present=[bool]$plugin;native_compatibility='NOT_RUN'}
    }
}
$report.sketchup=@{registered_installations=$sketchup;running_process_count=@(Get-Process SketchUp -ErrorAction SilentlyContinue).Count;note='No windows, documents or model files inspected; plugin presence is not connection success.'}
$core=@('KStudio.exe','_internal\app\static\index.html','_internal\harness\node.exe','_internal\harness\dsh.cmd','_internal\harness\node_modules\@deepseek-ai\dsh\lib\bin.js','KStudioConnector.exe')
$missing=@();foreach($relative in $core){try{if(-not(Test-Path -LiteralPath (Safe-BundlePath $relative) -PathType Leaf)){$missing+=$relative}}catch{$missing+=$relative}}
$signature='NOT_CHECKED';$exeHash=$null
try{$exe=Safe-BundlePath 'KStudio.exe';if(Test-Path -LiteralPath $exe){$exeHash=Read-FileSha256 $exe;$signature=(Get-AuthenticodeSignature -LiteralPath $exe).Status.ToString()}}catch{$signature='CHECK_UNAVAILABLE'}
$report.bundle=@{core_files_present=($missing.Count -eq 0);missing_core_files=$missing;executable_sha256=$exeHash;authenticode=$signature;publisher_identity_verified=$false;inventory_status='NOT_PROVIDED';trusted_inventory_digest_checked=$false}
if($Inventory){
    try{
        if(-not('KStudioReadOnlyInventory' -as [type])){
            Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Security.Cryptography;
using System.Collections.Concurrent;
using System.Threading.Tasks;
public static class KStudioReadOnlyInventory {
  public static bool[] Verify(string root, string[] paths, string[] hashes, long[] sizes) {
    var result = new bool[paths.Length];
    var directories = new ConcurrentDictionary<string, bool>(StringComparer.OrdinalIgnoreCase);
    Parallel.For(0, paths.Length, new ParallelOptions { MaxDegreeOfParallelism = 8 }, i => {
      try {
        string relative = paths[i].Replace('/', '\\');
        if(Path.IsPathRooted(relative) || relative.Contains(":") || Array.IndexOf(relative.Split('\\'), "..") >= 0) return;
        string full = Path.GetFullPath(Path.Combine(root, relative));
        if(!full.StartsWith(root + "\\", StringComparison.OrdinalIgnoreCase)) return;
        if((File.GetAttributes(full) & FileAttributes.ReparsePoint) != 0) return;
        string parent = Path.GetDirectoryName(full);
        while(parent != null && parent.Length >= root.Length) {
          bool safe = directories.GetOrAdd(parent, p => (File.GetAttributes(p) & FileAttributes.ReparsePoint) == 0);
          if(!safe) return;
          if(parent.Equals(root, StringComparison.OrdinalIgnoreCase)) break;
          parent = Path.GetDirectoryName(parent);
        }
        using(var file = File.OpenRead(full)) {
          if(sizes[i] >= 0 && file.Length != sizes[i]) return;
          using(var sha = SHA256.Create()) result[i] = BitConverter.ToString(sha.ComputeHash(file)).Replace("-", "").Equals(hashes[i], StringComparison.OrdinalIgnoreCase);
        }
      } catch(Exception) { result[i] = false; }
    });
    return result;
  }
}
'@
        }
        $inventoryHash=Read-FileSha256 $Inventory
        if($ExpectedInventorySha256){
            if($ExpectedInventorySha256 -notmatch '^[a-fA-F0-9]{64}$' -or $inventoryHash -ne $ExpectedInventorySha256.ToLower()){throw 'Inventory digest mismatch'}
            $report.bundle.trusted_inventory_digest_checked=$true
        }
        $inventoryData=Get-Content -LiteralPath $Inventory -Raw -Encoding UTF8 | ConvertFrom-Json
        $entries=@($inventoryData.files)
        if(-not $entries.Count -or $entries.Count -gt 100000){throw 'Invalid inventory count'}
        $failed=@();$verified=0;$seen=@{}
        $paths=New-Object 'System.Collections.Generic.List[string]'
        $hashes=New-Object 'System.Collections.Generic.List[string]'
        $sizes=New-Object 'System.Collections.Generic.List[long]'
        $indexes=New-Object 'System.Collections.Generic.List[int]'
        for($i=0;$i -lt $entries.Count;$i++){
            $entry=$entries[$i]
            try{
                if($entry.path -isnot [string] -or $entry.sha256 -notmatch '^[a-fA-F0-9]{64}$' -or $seen.ContainsKey($entry.path.ToLower())){throw 'Invalid inventory row'}
                $seen[$entry.path.ToLower()]=$true
                if($entry.path -match '(?i)^(runtime|profiles|data)([\\/]|$)|(^|[\\/])\.env([\\/]|$)|\.(skp|skb|dpapi|key)$'){throw 'Private data paths are not inspected'}
                $paths.Add($entry.path);$hashes.Add($entry.sha256);$indexes.Add($i+1)
                if($null -eq $entry.bytes){$sizes.Add(-1)}else{$sizes.Add([long]$entry.bytes)}
            }catch{$failed+=($i+1)}
        }
        $hashMatches=[KStudioReadOnlyInventory]::Verify($bundlePath,$paths.ToArray(),$hashes.ToArray(),$sizes.ToArray())
        for($i=0;$i -lt $hashMatches.Length;$i++){if($hashMatches[$i]){$verified++}else{$failed+=$indexes[$i]}}
        $report.bundle.inventory_status=$(if($failed.Count){'MISMATCH'}else{'MATCH'})
        $report.bundle.inventory_sha256=$inventoryHash;$report.bundle.listed_count=$entries.Count;$report.bundle.verified_count=$verified;$report.bundle.failed_row_numbers=$failed
    }catch{$report.bundle.inventory_status='REJECTED';$report.bundle.inventory_error='Manifest unreadable, malformed, unsafe or digest mismatch; raw paths/errors withheld.'}
}
$report.connection=@{status='NOT_REQUESTED';native_reachability='NOT_RUN';project_binding='NOT_RUN'}
if($RuntimePort){
    $status=Local-Json '/api/status';$setup=Local-Json '/api/connectors/sketchup/setup'
    $report.connection=@{status=$(if($status -and $status.app -eq 'ready'){'LOCAL_WORKBENCH_RESPONDED'}else{'UNREACHABLE_OR_NOT_KSTUDIO'});personal_desktop=(Bool-OrNull $status 'personal_desktop');model_route_available=(Bool-OrNull $status 'native_agent_available');connector_configured=(Bool-OrNull $status 'sketchup_configured');public_package_available=(Bool-OrNull $setup 'package_available');native_reachability='NOT_RUN';project_binding='NOT_RUN';note='Only GET configuration/status. Use in-app read-only connection check for actual SU document binding.'}
}
$report.result='REPORT_ONLY_NOT_RELEASE_ACCEPTANCE'
New-Item -ItemType Directory -Path $outputPath | Out-Null
$json=$report | ConvertTo-Json -Depth 10
[IO.File]::WriteAllText((Join-Path $outputPath 'kstudio-environment.json'),$json,[Text.UTF8Encoding]::new($false))
$lines=@('# K Studio read-only Windows environment report','',('Windows: '+$report.windows.version),('WebView2: '+$report.webview2.status),('.NET: '+$report.dotnet_framework.status),('Registered SketchUp entries: '+$sketchup.Count),('Bundle core files present: '+$report.bundle.core_files_present),('Inventory: '+$report.bundle.inventory_status),('Authenticode: '+$signature),('Connection configuration: '+$report.connection.status),'','No install, paid inference, model scan or native tool calls.','MATCH means listed bytes match the supplied inventory, not trusted publisher or full compatibility.','Clean-machine acceptance, real provider modeling and native SU quality remain NOT_RUN.','The JSON is allowlisted/redacted; inspect before sending to support.')
[IO.File]::WriteAllLines((Join-Path $outputPath 'README.txt'),$lines,[Text.UTF8Encoding]::new($false))
Write-Output ('Report written. Inventory='+$report.bundle.inventory_status+'; native/modeling=NOT_RUN. No changes to installed software or user models.')
if($report.bundle.inventory_status -in @('MISMATCH','REJECTED') -or -not $report.bundle.core_files_present){exit 2}
exit 0
