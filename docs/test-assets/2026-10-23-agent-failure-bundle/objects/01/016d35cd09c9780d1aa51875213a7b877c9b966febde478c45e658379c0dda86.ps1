param([Parameter(Mandatory=$true)][string]$ConfigFile)
$ErrorActionPreference='Stop'
$config=Get-Content -LiteralPath $ConfigFile -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not (Test-Path -LiteralPath (Join-Path $config.runtime_directory 'projects'))) { throw 'Existing project data is unavailable; no empty profile will be created.' }
$cli=$config.codex_executable
if (-not (Test-Path -LiteralPath $cli)) {
    $cli=Get-ChildItem -Path (Join-Path $env:LOCALAPPDATA 'OpenAI\Codex\bin\*\codex.exe') -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
}
if (-not $cli -or -not (Test-Path -LiteralPath $cli)) { throw 'The installed Codex CLI is unavailable; no model/provider substitution was attempted.' }
Set-Location -LiteralPath $config.code_directory
$env:PYTHONUTF8='1'
$env:LITELLM_LOCAL_MODEL_COST_MAP='True'
$env:ARCH_STUDIO_RUNTIME_DIR=$config.runtime_directory
$env:ARCH_STUDIO_ECONOMY_PROVIDER='codex'
$env:ARCH_STUDIO_ECONOMY_MODEL='gpt-6.1-sol'
$env:ARCH_STUDIO_ECONOMY_REASONING_EFFORT=$config.local_reasoning_effort
if(-not $env:ARCH_STUDIO_ECONOMY_REASONING_EFFORT){$env:ARCH_STUDIO_ECONOMY_REASONING_EFFORT='medium'}
$env:ARCH_STUDIO_CODEX_REASONING_EFFORT=$env:ARCH_STUDIO_ECONOMY_REASONING_EFFORT
$env:ARCH_STUDIO_CODEX_RECONSTRUCTION_THREAD_MODE='native'
$env:ARCH_STUDIO_RECONSTRUCTION_PROMPT_PROFILE='harness'
$env:ARCH_STUDIO_USE_LAUNCHER_MODEL='1'
$env:ARCH_STUDIO_CODEX_TIMEOUT_SECONDS='3600'
$env:ARCH_STUDIO_STANDALONE='0'
$env:K_STUDIO_DEPLOYMENT_MODE='local'
$env:WEB_CONCURRENCY='1'
$env:KSTUDIO_EXECUTION_LIMITS='off'
$env:ARCH_STUDIO_CODEX_MAX_PROJECT_INPUT_TOKENS='0'
$env:ARCH_STUDIO_CODEX_PROJECT_DELIVERY_RESERVE='0'
$env:ARCH_STUDIO_CODEX_MAX_TURN_INPUT_TOKENS='0'
$env:ARCH_STUDIO_CODEX_MAX_TURN_TOOL_CALLS='0'
if($config.api_test_mcp_config){$env:ARCH_STUDIO_MCP_CONFIG=$config.api_test_mcp_config}
$env:CODEX_CLI_PATH=$cli
& $config.python_executable (Join-Path $config.code_directory 'scripts\dev.py') --port $config.port
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
