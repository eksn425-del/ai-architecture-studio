param([Parameter(Mandatory=$true)][string]$InstallationReceipt)
$ErrorActionPreference='Stop'
$receipt=Get-Content -LiteralPath $InstallationReceipt -Raw -Encoding utf8 | ConvertFrom-Json
$expectedShortcut=Join-Path ([Environment]::GetFolderPath('Desktop')) 'K Studio（本机候选版）.lnk'
if($receipt.schema -ne 1 -or $receipt.shortcut -ne $expectedShortcut){throw '不是当前用户的候选版安装记录。'}
$shell=New-Object -ComObject WScript.Shell
if(-not(Test-Path -LiteralPath $expectedShortcut)){throw '候选入口已不存在；原正式版未改动。'}
$current=$shell.CreateShortcut($expectedShortcut)
if($current.TargetPath -ne (Join-Path $receipt.destination 'KStudio.exe')){throw '候选入口已被其他版本修改，停止回退以保留当前设置。'}
if($receipt.previous_shortcut){
    $previous=$receipt.previous_shortcut
    if(-not(Test-Path -LiteralPath $previous.target)){throw '上一版程序不存在，保留当前入口。'}
    $current.TargetPath=$previous.target
    $current.Arguments=$previous.arguments
    $current.WorkingDirectory=$previous.working_directory
    $current.IconLocation=$previous.icon
    $current.Save()
}else{
    Remove-Item -LiteralPath $expectedShortcut
}
Write-Output '候选入口已回退；所有程序版本、项目、API配置与原正式入口保留。正在运行的程序未被强制关闭。'
