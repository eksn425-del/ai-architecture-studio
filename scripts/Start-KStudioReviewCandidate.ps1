param(
  [string]$PythonExecutable='',
  [int]$Port=8897
)
$ErrorActionPreference='Stop'
$candidateRoot=Split-Path -Parent $PSScriptRoot
$candidateData=Join-Path $candidateRoot 'outputs\read-only-review'
if(-not $PythonExecutable){$candidateOutputs=Split-Path -Parent (Split-Path -Parent $candidateRoot); $PythonExecutable=Join-Path $candidateOutputs 'video-storage\tools\kstudio-unified-retest-20261024\Scripts\python.exe'}
if(-not (Test-Path -LiteralPath $PythonExecutable)){throw 'The candidate Python runtime is unavailable.'}
if($Port -lt 1024 -or $Port -gt 65535){throw 'Invalid local candidate port.'}
# Child-process environment only. No existing settings, credentials, model files,
# native policy, or old budget ledger is copied or modified.
Get-ChildItem Env: | Where-Object {$_.Name -match '^ARCH_STUDIO_' -or $_.Name -match '_API_KEY$'} | ForEach-Object {Remove-Item -LiteralPath ('Env:\'+$_.Name)}
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
$env:LITELLM_LOCAL_MODEL_COST_MAP='True'
$env:ARCH_STUDIO_RUNTIME_DIR=Join-Path $candidateData 'runtime'
$env:KSTUDIO_CONNECTIONS_DIR=Join-Path $candidateData 'empty-settings'
$env:ARCH_STUDIO_ECONOMY_PROVIDER='litellm'
$env:ARCH_STUDIO_API_MODEL=''
$env:ARCH_STUDIO_API_KEY_ENV='KSTUDIO_NO_INHERITED_API_KEY'
$env:ARCH_STUDIO_STANDALONE='1'
$env:KSTUDIO_PERSONAL_DESKTOP='1'
$env:WEB_CONCURRENCY='1'
$env:K_STUDIO_DEPLOYMENT_MODE='local'
Set-Location -LiteralPath $candidateRoot
Write-Output "K Studio isolated read-only review: http://127.0.0.1:$Port"
& $PythonExecutable -m uvicorn app.review_candidate:create_review_app --factory --host 127.0.0.1 --port $Port
exit $LASTEXITCODE
