param([switch]$IncludeLocalConnectorTrial,
      [Parameter(Mandatory=$true)][string]$PythonExecutable,
      [Parameter(Mandatory=$true)][string]$HarnessNodeRoot,
      [Parameter(Mandatory=$true)][string]$HarnessSdkSite,
      [Parameter(Mandatory=$true)][string]$NodeExecutable,
      [Parameter(Mandatory=$true)][string]$NodeLicense,
      [string]$AdaiSource,
      [Parameter(Mandatory=$true)][string]$OutputRoot)
$ErrorActionPreference = 'Stop'
$repoPath = Split-Path -Parent $PSScriptRoot
$pythonPath = $PythonExecutable
$OutputRoot = [IO.Path]::GetFullPath($OutputRoot)
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
$harnessStage = Join-Path $OutputRoot 'harness-stage'
if (Test-Path -LiteralPath $harnessStage) {throw 'Use a new output directory to preserve previous builds.'}
if (-not (Test-Path -LiteralPath (Join-Path $HarnessNodeRoot 'node_modules/@deepseek-ai/dsh/lib/bin.js'))) {throw 'Pinned official Harness entry is missing.'}
if (-not (Test-Path -LiteralPath (Join-Path $HarnessSdkSite 'deepseek_harness/__init__.py'))) {throw 'Official Python SDK is missing.'}
New-Item -ItemType Directory -Path $harnessStage | Out-Null
Copy-Item -LiteralPath $NodeExecutable -Destination (Join-Path $harnessStage 'node.exe')
Copy-Item -LiteralPath $NodeLicense -Destination (Join-Path $harnessStage 'LICENSE.Node.txt')
# Only dependency code is included, never the owner's runtime, projects or keys.
& robocopy (Join-Path $HarnessNodeRoot 'node_modules') (Join-Path $harnessStage 'node_modules') /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /MT:8 /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) {throw 'Harness dependency copy failed.'}
$sdkStage = Join-Path $OutputRoot 'python-sdk'
New-Item -ItemType Directory -Path $sdkStage | Out-Null
Copy-Item -LiteralPath (Join-Path $HarnessSdkSite 'deepseek_harness') -Destination $sdkStage -Recurse
Get-ChildItem -LiteralPath $HarnessSdkSite -Directory -Filter 'deepseek_harness_sdk-*.dist-info' | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $sdkStage -Recurse
}
& $pythonPath (Join-Path $PSScriptRoot 'prepare_desktop_sdk.py') $sdkStage
if ($LASTEXITCODE -ne 0) {throw 'SDK Windows launch preparation failed.'}
$env:PYTHONPATH = $sdkStage + [IO.Path]::PathSeparator + $repoPath
Set-Content -LiteralPath (Join-Path $harnessStage 'dsh.cmd') -Encoding ascii -Value '@echo off', '"%~dp0node.exe" "%~dp0node_modules\@deepseek-ai\dsh\lib\bin.js" %*'
Push-Location -LiteralPath $repoPath
try {
    $connectorPackage = Join-Path $OutputRoot 'public-connector'
    & $pythonPath (Join-Path $PSScriptRoot 'package_public_connector.py') $connectorPackage
    if ($LASTEXITCODE -ne 0) {throw 'Public connector packaging failed.'}
    $connectorDataArgs = @('--add-data', "$connectorPackage;connector-distribution")
    if ($IncludeLocalConnectorTrial) {
        $connectorPackage = Join-Path $repoPath 'runtime/connector-distribution'
        if (-not (Test-Path -LiteralPath (Join-Path $connectorPackage 'manifest.json'))) {
            throw 'Prepare the reviewed local connector trial package first. No placeholder installer will be bundled.'
        }
        $connectorDataArgs = @('--add-data', "$connectorPackage;connector-distribution")
        Write-Host 'PRIVATE LOCAL CONNECTOR TRIAL: redistribution rights and clean-machine acceptance remain unverified.' -ForegroundColor Yellow
    }
    $env:LITELLM_LOCAL_MODEL_COST_MAP = 'True'
    # tiktoken discovers encodings via a namespace plugin, invisible to static
    # import analysis. Ship its plugin and cached vocabulary for offline startup.
    $env:TIKTOKEN_CACHE_DIR = Join-Path $OutputRoot 'tokenizer-cache'
    & $pythonPath -c "import tiktoken; tiktoken.get_encoding('cl100k_base'); tiktoken.get_encoding('o200k_base')"
    if ($LASTEXITCODE -ne 0) { throw 'Tokenizer vocabulary preparation failed.' }
    $nativeDataArgs = @()
    Get-ChildItem -LiteralPath (Join-Path $repoPath 'app') -Filter '*.rb' | ForEach-Object { $nativeDataArgs += @('--add-data', "$($_.FullName);app") }
    & $pythonPath -m PyInstaller --noconfirm --windowed --name KStudio --icon "$repoPath/app/static/kstudio.ico" `
        --distpath "$OutputRoot/dist" --workpath "$OutputRoot/build" --specpath "$OutputRoot/build" `
        --paths $sdkStage --collect-all deepseek_harness --copy-metadata deepseek-harness-sdk --add-data "$sdkStage/deepseek_harness;deepseek_harness" `
        --add-data "$sdkStage/KSTUDIO-SDK-PATCH.json;." `
        --add-data "$repoPath/app/dsh_host_tools.mjs;app" `
        --add-data "$repoPath/app/dsh_tool_policy.mjs;app" `
        --add-data "$repoPath/app/architecture_skills;app/architecture_skills" `
        --add-data "$repoPath/app/static;app/static" --add-data "$repoPath/app/vendor;app/vendor" --add-data "$repoPath/scripts;scripts" `
        --add-data "$repoPath/THIRD_PARTY_NOTICES.md;." --add-data "$repoPath/app/adopted_sketchup_helpers.rb;app" --collect-all webview --collect-all litellm `
        --add-data "$repoPath/app/native_deep_fingerprint.rb;app" --add-data "$repoPath/app/native_definition_graph.rb;app" `
        --add-data "$repoPath/app/path_scope_guard.rb;app" --add-data "$repoPath/app/path_scope_graph_guard.rb;app" --add-data "$repoPath/app/edit_scope_guard.rb;app" --add-data "$repoPath/app/oss_method_runtime.rb;app" `
        --add-data "$env:TIKTOKEN_CACHE_DIR;tokenizer-cache" --hidden-import tiktoken_ext.openai_public `
        --collect-submodules uvicorn --hidden-import tomli --exclude-module pytest @nativeDataArgs @connectorDataArgs scripts/desktop.py
    if ($LASTEXITCODE -ne 0) { throw 'Desktop packaging failed.' }
    & $pythonPath -m PyInstaller --noconfirm --onefile --console --name KStudioConnector `
        --distpath "$OutputRoot/connector-dist" --workpath "$OutputRoot/connector-build" --specpath "$OutputRoot/connector-build" `
        scripts/connector_stdio.py
    if ($LASTEXITCODE -ne 0) {throw 'Public connector executable packaging failed.'}
    Copy-Item -LiteralPath (Join-Path $OutputRoot 'connector-dist/KStudioConnector.exe') -Destination (Join-Path $OutputRoot 'dist/KStudio/KStudioConnector.exe')
    $internal = Join-Path $OutputRoot 'dist/KStudio/_internal'
    # Node owns its native modules. Avoid PyInstaller reclassifying binaries for
    # every platform in the npm tree as Python DLL dependencies.
    & robocopy $harnessStage (Join-Path $internal 'harness') /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /MT:8 /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) {throw 'Bundled Harness assembly failed.'}
    if ($AdaiSource) {
        $adaiTarget = Join-Path $internal 'third-party/adai'
        New-Item -ItemType Directory -Path $adaiTarget -Force | Out-Null
        foreach($name in @('skill','LICENSE','NOTICE','README.md')) {
            Copy-Item -LiteralPath (Join-Path $AdaiSource $name) -Destination $adaiTarget -Recurse
        }
    }
    Write-Host "Local desktop build: $OutputRoot/dist/KStudio/KStudio.exe"
    Write-Host 'This build excludes SketchUp, user data, pairing tokens and API credentials. Public first-party connector included; a private-trial override is never a public release.'
} finally { Pop-Location }
