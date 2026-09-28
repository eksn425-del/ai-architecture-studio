param(
    [switch]$Update
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot '.venv\Scripts\python.exe'
$targetRoot = Join-Path $repoRoot '.local\oss'
$target = Join-Path $targetRoot 'archflow-studio'
$upstream = 'https://github.com/bingxijun/archflow-studio.git'

if (-not (Test-Path $python)) {
    throw 'Project virtual environment is missing. Run scripts\setup.ps1 first.'
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'git is required to adopt ArchFlow source.'
}

New-Item -ItemType Directory -Force -Path $targetRoot | Out-Null

if (-not (Test-Path (Join-Path $target '.git'))) {
    Write-Host 'Cloning upstream ArchFlow Studio into ignored .local/oss/ ...' -ForegroundColor Cyan
    & git clone --depth 1 $upstream $target
} elseif ($Update) {
    Write-Host 'Updating existing ArchFlow checkout with fast-forward only ...' -ForegroundColor Cyan
    & git -C $target pull --ff-only
} else {
    Write-Host 'Using existing ignored ArchFlow checkout. Pass -Update to fast-forward it.' -ForegroundColor Yellow
}

& $python -m pip install -e $target

$coreSkill = Join-Path $target 'plugins\archflow-studio\skills\archflow-studio'
Write-Host "ArchFlow source checkout: $target" -ForegroundColor Green
Write-Host "ArchFlow core skill: $coreSkill" -ForegroundColor Green
Write-Host 'The checkout is under .local/ and is ignored by this repository.' -ForegroundColor Green
Write-Host 'Run the following in the current shell before ArchFlow CLI work:' -ForegroundColor Cyan
Write-Host "  `$env:ARCHFLOW_CORE_SKILL = '$coreSkill'"
Write-Host 'Then verify without modifying CAD/SketchUp:' -ForegroundColor Cyan
Write-Host '  archflow doctor --json'
