param([Parameter(Mandatory=$true)][string]$ConfigFile)
$ErrorActionPreference='Stop'
$config=Get-Content -LiteralPath $ConfigFile -Raw -Encoding UTF8 | ConvertFrom-Json
if($config.desktop_mode -ne 'personal-byok'){throw 'This launcher requires the personal API profile.'}
if($config.api_test_budget -or $env:K_STUDIO_LOCAL_API_TEST_BUDGET -or $env:K_STUDIO_OPERATOR_MAX_USD){throw 'An existing monetary-budget profile is present. Use its guarded launcher; no budget was removed.'}
if(-not (Test-Path -LiteralPath (Join-Path $config.runtime_directory 'projects'))){throw 'Existing project data is unavailable; startup stopped.'}
Set-Location -LiteralPath $config.code_directory
. $config.storage_workspace_script | Out-Null
$env:PYTHONUTF8='1'
$env:LITELLM_LOCAL_MODEL_COST_MAP='True'
# Drop inherited experiment routing and billing configuration only in this child
# process. No user/machine environment, credentials or historical ledger is changed.
Get-ChildItem Env: | Where-Object {$_.Name -match '^ARCH_STUDIO_' -or $_.Name -match '_API_KEY$'} | ForEach-Object {Remove-Item -LiteralPath ('Env:\'+$_.Name)}
$env:ARCH_STUDIO_RUNTIME_DIR=$config.runtime_directory
$env:ARCH_STUDIO_ECONOMY_PROVIDER='litellm'
$env:ARCH_STUDIO_API_MODEL=''
$env:ARCH_STUDIO_API_KEY_ENV='KSTUDIO_NO_INHERITED_API_KEY'
$env:ARCH_STUDIO_STANDALONE='1'
$env:ARCH_STUDIO_MCP_CONFIG=$config.api_test_mcp_config
$env:ARCH_STUDIO_GENERATED_SCRIPT_DIR=$config.generated_script_directory
$env:ARCHFLOW_GENERATED_SCRIPT_DIR=$config.generated_script_directory
$env:ARCH_STUDIO_CODEX_HOME=Join-Path $config.desktop_data_directory 'agent-runtime'
$env:ARCH_STUDIO_CODEX_RECONSTRUCTION_THREAD_MODE='native'
$env:ARCH_STUDIO_RECONSTRUCTION_PROMPT_PROFILE='harness'
$env:ARCH_STUDIO_CODEX_TIMEOUT_SECONDS='3600'
$env:KSTUDIO_PERSONAL_DESKTOP='1'
$env:KSTUDIO_CONNECTIONS_DIR=$config.connections_directory
$env:KSTUDIO_INSTALLED_COMMIT=$config.commit
if($config.agent_engine -eq 'deepseek-harness'){
    $env:KSTUDIO_AGENT_ENGINE='deepseek-harness'
    $env:KSTUDIO_DSH_SDK_SITE=$config.deepseek_sdk_site
    $env:KSTUDIO_DSH_BIN=$config.deepseek_bin
    $env:KSTUDIO_DSH_GUIDANCE=$config.deepseek_guidance
    $env:KSTUDIO_DSH_CAPABILITIES=if($config.deepseek_capabilities){$config.deepseek_capabilities}else{'protected'}
    if($config.deepseek_skill_dirs){$env:KSTUDIO_DSH_SKILL_DIRS=ConvertTo-Json -InputObject @($config.deepseek_skill_dirs) -Compress}
    if($config.deepseek_mcp_config){$env:KSTUDIO_DSH_MCP_CONFIG=$config.deepseek_mcp_config}
    if($config.adai_geometry){$env:ARCH_STUDIO_ENABLE_ADAI_GEOMETRY='1'}
    $env:KSTUDIO_DSH_MAX_OUTPUT_TOKENS='32768'
}
$env:K_STUDIO_DEPLOYMENT_MODE='local'
$env:KSTUDIO_EXECUTION_LIMITS=$config.execution_limits
$env:WEB_CONCURRENCY='1'
# An executable supports explicitly configured Responses transport; its login is
# never used. Ordinary Chat Completions has no Codex process dependency.
if($config.codex_executable -and (Test-Path -LiteralPath $config.codex_executable)){$env:CODEX_CLI_PATH=$config.codex_executable}
if($config.blender_directory){$env:PATH=$config.blender_directory+';'+$env:PATH}
& $config.python_executable (Join-Path $config.code_directory 'scripts\dev.py') --port $config.port
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
