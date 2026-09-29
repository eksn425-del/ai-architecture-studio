param([string]$SourceRoot = '')

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$source = if ($SourceRoot) { [System.IO.Path]::GetFullPath($SourceRoot) } else { Join-Path $repoRoot '.local\oss\saie' }
$patch = Join-Path $repoRoot 'patches\saie\saie-2024-compat.patch'
$expected = 'eff6f41ff866bef6b4f2b90be2faa6fe2cc4347f'

if (-not (Test-Path -LiteralPath (Join-Path $source '.git'))) { throw "SAIE source checkout missing: $source" }
if (-not (Test-Path -LiteralPath $patch)) { throw "SAIE compatibility patch missing: $patch" }
$actual = (git -C $source rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $actual -ne $expected) { throw "SAIE checkout must be pinned to $expected (found $actual)." }

git -C $source apply --check --reverse $patch 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host 'SAIE 2024 compatibility patch is already applied.' -ForegroundColor Green
    return
}
$dirty = @(git -C $source status --porcelain)
if ($LASTEXITCODE -ne 0 -or $dirty.Count -gt 0) { throw 'SAIE source has other changes; refusing to apply the patch.' }
git -C $source apply --check $patch
if ($LASTEXITCODE -ne 0) { throw 'SAIE patch does not apply cleanly to pinned upstream.' }
git -C $source apply $patch
if ($LASTEXITCODE -ne 0) { throw 'SAIE patch application failed.' }
Write-Host 'Applied pinned SAIE 2024 compatibility patch.' -ForegroundColor Green
