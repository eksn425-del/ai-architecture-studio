param([Parameter(Mandatory=$true)][string]$PythonExecutable,[Parameter(Mandatory=$true)][string]$OutputRoot)
$ErrorActionPreference='Stop'
$repoRoot=Split-Path -Parent $PSScriptRoot
$OutputRoot=[IO.Path]::GetFullPath($OutputRoot)
if (Test-Path -LiteralPath $OutputRoot) { throw 'Use a new updater output folder to retain old builds.' }
New-Item -ItemType Directory -Path $OutputRoot | Out-Null
$env:PYINSTALLER_CONFIG_DIR=Join-Path $OutputRoot 'cache'
Push-Location -LiteralPath $repoRoot
try {
    & $PythonExecutable -m PyInstaller --noconfirm --onedir --console --name KStudioUpdate `
        --distpath (Join-Path $OutputRoot 'dist') --workpath (Join-Path $OutputRoot 'work') --specpath $OutputRoot `
        --paths $repoRoot --add-data ((Join-Path $PSScriptRoot 'verify_authenticode.ps1')+';.') `
        --add-data ((Join-Path $PSScriptRoot 'launch_installed.ps1')+';.') `
        --add-data ((Join-Path $PSScriptRoot 'install_shortcut.ps1')+';.') `
        (Join-Path $PSScriptRoot 'release_cli.py')
    if ($LASTEXITCODE -ne 0) { throw 'Updater packaging failed.' }
    & $PythonExecutable (Join-Path $PSScriptRoot 'collect_updater_licenses.py') (Join-Path $OutputRoot 'dist\KStudioUpdate')
    if ($LASTEXITCODE -ne 0) { throw 'Updater dependency license collection failed.' }
    Write-Output (Join-Path $OutputRoot 'dist\KStudioUpdate\KStudioUpdate.exe')
} finally { Pop-Location }
