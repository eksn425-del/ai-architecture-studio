param([Parameter(Mandatory=$true)][string]$ConfigFile)
$ErrorActionPreference='Stop'
$config=Get-Content -LiteralPath $ConfigFile -Raw -Encoding UTF8 | ConvertFrom-Json
if(-not (Test-Path -LiteralPath (Join-Path $config.runtime_directory 'projects'))){throw 'Existing runtime unavailable.'}
Set-Location -LiteralPath $config.code_directory
$env:PYTHONUTF8='1'
$env:LITELLM_LOCAL_MODEL_COST_MAP='True'
$env:ARCH_STUDIO_RUNTIME_DIR=$config.runtime_directory
$env:ARCH_STUDIO_ECONOMY_PROVIDER='litellm'
$env:ARCH_STUDIO_API_MODEL='openai/deepseek-v4.1-flash'
$env:ARCH_STUDIO_API_BASE='https://api.b.ai/v1'
$env:ARCH_STUDIO_API_KEY_ENV='BAI_API_KEY'
Remove-Item Env:ARCH_STUDIO_ECONOMY_REASONING_EFFORT -ErrorAction SilentlyContinue
$env:ARCH_STUDIO_USE_LAUNCHER_MODEL='0'
$env:ARCH_STUDIO_STANDALONE='1'
$env:ARCH_STUDIO_MCP_CONFIG=$config.api_test_mcp_config
$env:K_STUDIO_LOCAL_API_TEST_BUDGET=$config.api_test_budget
$env:K_STUDIO_DEPLOYMENT_MODE='local'
$env:WEB_CONCURRENCY='1'
& $config.python_executable (Join-Path $config.code_directory 'scripts\dev.py') --port $config.port
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
