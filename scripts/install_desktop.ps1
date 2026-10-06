param(
    [Parameter(Mandatory = $true)]
    [string]$InstallRoot,
    [ValidateSet('deepseek', 'glm', 'glm-international')]
    [string]$ApiProvider = 'deepseek'
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$source = Join-Path $repoRoot 'runtime\desktop-dist\KStudio'
if (-not (Test-Path -LiteralPath (Join-Path $source 'KStudio.exe'))) {
    throw 'Build the current desktop package with scripts/build_desktop.ps1 first.'
}
# Inspect the frozen package, not just repository source: an old executable may
# otherwise silently omit credential persistence even after git pull.
# Windows PowerShell 5.1 can strip quotes inside a native `python -c` argument.
# Use an ignored script file so package paths and Python string literals stay intact.
$verificationScript = Join-Path $repoRoot 'runtime\desktop-build\verify_desktop_package.py'
New-Item -ItemType Directory -Path (Split-Path -Parent $verificationScript) -Force | Out-Null
@'
import sys
from PyInstaller.archive.readers import CArchiveReader
package = CArchiveReader(sys.argv[1]).open_embedded_archive("PYZ.pyz")
assert "app.local_credentials" in package.toc, "Desktop package lacks credential persistence"
'@ | Set-Content -LiteralPath $verificationScript -Encoding UTF8
& (Join-Path $repoRoot '.venv\Scripts\python.exe') $verificationScript (Join-Path $source 'KStudio.exe')
if ($LASTEXITCODE -ne 0) { throw 'Desktop package verification failed.' }
if (-not (Test-Path -LiteralPath (Join-Path $source '_internal\app\adopted_sketchup_helpers.rb'))) {
    throw 'Desktop package lacks the owned-model Ruby helper. Rebuild the current package.'
}
$install = [System.IO.Path]::GetFullPath($InstallRoot)
$versionName = Get-Date -Format 'yyyyMMdd-HHmmss'
$version = Join-Path $install "versions\$versionName"
$data = Join-Path $install 'data'
New-Item -ItemType Directory -Path $version -Force | Out-Null
New-Item -ItemType Directory -Path $data -Force | Out-Null
# Keep previous packages and the entire data directory for rollback. Never
# replace/remove the runtime junction, project models or encrypted credentials.
Copy-Item -Path (Join-Path $source '*') -Destination $version -Recurse
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'K Studio AI 建模.lnk'))
$shortcut.TargetPath = Join-Path $version 'KStudio.exe'
$shortcut.Arguments = '--data-dir "' + $data + '" --standalone --api-provider ' + $ApiProvider
$shortcut.WorkingDirectory = $version
$shortcut.IconLocation = $shortcut.TargetPath
$shortcut.Save()
Write-Host 'Installed verified desktop package and updated desktop shortcut. Existing data preserved.'
