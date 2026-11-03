param(
    [Parameter(Mandatory=$true)][string]$Bundle,
    [Parameter(Mandatory=$true)][string]$Destination,
    [Parameter(Mandatory=$true)][string]$DataDirectory,
    [string]$RuntimeDirectory,
    [string]$ConnectionsDirectory,
    [string]$BridgeConfig,
    [string]$GeneratedDirectory
)
$ErrorActionPreference='Stop'
$source=[IO.Path]::GetFullPath($Bundle)
$target=[IO.Path]::GetFullPath($Destination)
if(Test-Path -LiteralPath $target){throw '目标版本已存在；请使用新版本目录，旧版本不会覆盖。'}
if(-not(Test-Path -LiteralPath (Join-Path $source 'KStudio.exe'))){throw '候选程序缺失。'}
if($target.StartsWith($source+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw '安装目录不能位于源程序包内。'}
foreach($path in @($DataDirectory,$RuntimeDirectory,$ConnectionsDirectory,$BridgeConfig,$GeneratedDirectory)){
    if($path -and $path.Contains('"')){throw '配置路径不能包含双引号。'}
}
if($RuntimeDirectory -and -not(Test-Path -LiteralPath (Join-Path $RuntimeDirectory 'projects'))){throw '原项目目录不可用；停止安装。'}
if($BridgeConfig -and -not(Test-Path -LiteralPath $BridgeConfig)){throw '原连接配置不可用；停止安装。'}
New-Item -ItemType Directory -Path $target | Out-Null
& robocopy $source $target /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /MT:8 /NFL /NDL /NJH /NJS /NP | Out-Null
if($LASTEXITCODE -ge 8){throw '复制失败；未创建或更新桌面入口，原版本保留。'}
# Verify every file before exposing the new entry. No profile is copied.
$count=& (Join-Path $PSScriptRoot 'Verify-KStudioBundle.ps1') -Source $source -Target $target
$arguments=@('--data-dir',('"'+[IO.Path]::GetFullPath($DataDirectory)+'"'))
foreach($pair in @(@('--runtime-dir',$RuntimeDirectory),@('--connections-dir',$ConnectionsDirectory),@('--bridge-config',$BridgeConfig),@('--generated-dir',$GeneratedDirectory))){
    if($pair[1]){$arguments+=@($pair[0],('"'+[IO.Path]::GetFullPath($pair[1])+'"'))}
}
$shortcutPath=Join-Path ([Environment]::GetFolderPath('Desktop')) 'K Studio（本机候选版）.lnk'
$shell=New-Object -ComObject WScript.Shell
$previous=$null
if(Test-Path -LiteralPath $shortcutPath){
    $old=$shell.CreateShortcut($shortcutPath)
    $previous=@{target=$old.TargetPath;arguments=$old.Arguments;working_directory=$old.WorkingDirectory;icon=$old.IconLocation}
}
$entry=$shell.CreateShortcut($shortcutPath)
$entry.TargetPath=Join-Path $target 'KStudio.exe'
$entry.Arguments=$arguments -join ' '
$entry.WorkingDirectory=$target
$entry.Description='K Studio 本机候选版；原正式入口和资料保留'
$entry.Save()
@{schema=1;installed_at=(Get-Date).ToString('o');files_verified=$count;destination=$target;shortcut=$shortcutPath;arguments=$entry.Arguments;previous_shortcut=$previous;public_release_ready=$false} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $target 'installation-receipt.json') -Encoding utf8
Write-Output "候选版安装完成；已校验 $count 个文件。原正式版入口未改动。"
