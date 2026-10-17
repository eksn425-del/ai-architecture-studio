$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot | Split-Path -Parent
Set-Location -LiteralPath $taskRoot
$env:ARCH_STUDIO_ECONOMY_PROVIDER = 'codex'
$env:ARCH_STUDIO_ECONOMY_MODEL = 'gpt-6.1-sol'
$env:ARCH_STUDIO_ECONOMY_REASONING_EFFORT = 'medium'
$env:ARCH_STUDIO_CODEX_REASONING_EFFORT = 'medium'
$env:ARCH_STUDIO_CODEX_RECONSTRUCTION_THREAD_MODE = 'native'
$env:ARCH_STUDIO_RECONSTRUCTION_PROMPT_PROFILE = 'harness'
$env:ARCH_STUDIO_USE_LAUNCHER_MODEL = '1'
$env:ARCH_STUDIO_CODEX_TIMEOUT_SECONDS = '1800'
$env:CODEX_CLI_PATH = (Get-Command codex).Source
$env:PYTHONIOENCODING = 'utf-8'
& 'D:\python3.10.4\python.exe' scripts/dev.py --port 8787
