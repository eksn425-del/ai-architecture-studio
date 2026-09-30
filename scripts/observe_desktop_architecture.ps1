param(
    [Parameter(Mandatory=$false)]
    [string]$InstallPath = "",

    [Parameter(Mandatory=$false)]
    [string]$RbzPath = "",

    [Parameter(Mandatory=$false)]
    [string]$OutputDir = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $OutputDir) {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $OutputDir = Join-Path $RepoRoot "runtime/reviews/competitor-desktop-$stamp"
}
$OutputDir = [System.IO.Path]::GetFullPath($OutputDir)
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

function Get-RelativeSafePath([string]$Base, [string]$Path) {
    try {
        $baseUri = New-Object System.Uri(($Base.TrimEnd('\') + '\'))
        $pathUri = New-Object System.Uri($Path)
        return [System.Uri]::UnescapeDataString($baseUri.MakeRelativeUri($pathUri).ToString()).Replace('/', '\')
    } catch {
        return [System.IO.Path]::GetFileName($Path)
    }
}

function Get-FileInventory([string]$Root) {
    if (-not $Root -or -not (Test-Path -LiteralPath $Root)) { return @() }
    $resolved = (Resolve-Path -LiteralPath $Root).Path
    $items = Get-ChildItem -LiteralPath $resolved -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 4000
    $result = @()
    foreach ($item in $items) {
        $hash = $null
        if ($item.Length -le 50MB) {
            try { $hash = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash } catch {}
        }
        $result += [pscustomobject]@{
            relative_path = Get-RelativeSafePath $resolved $item.FullName
            extension = $item.Extension.ToLowerInvariant()
            bytes = $item.Length
            sha256 = $hash
        }
    }
    return $result
}

function Get-ReadableArchitectureHints([string]$Root) {
    if (-not $Root -or -not (Test-Path -LiteralPath $Root)) { return @() }
    $resolved = (Resolve-Path -LiteralPath $Root).Path
    $extensions = @('.rb', '.json', '.toml', '.yaml', '.yml', '.md', '.txt', '.js', '.ts')
    $patterns = @(
        'mcp', 'server', 'tool', 'ruby', 'sketchup', 'localhost', '127.0.0.1',
        'websocket', 'socket', 'http://', 'https://', 'execute', 'eval', 'screenshot',
        'camera', 'undo', 'selection', 'model', 'save_copy', 'startserver', 'stopserver'
    )
    $hints = @()
    $files = Get-ChildItem -LiteralPath $resolved -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $extensions -contains $_.Extension.ToLowerInvariant() -and $_.Length -le 2MB } |
        Select-Object -First 800
    foreach ($file in $files) {
        try {
            $lines = Get-Content -LiteralPath $file.FullName -ErrorAction Stop
            $matches = @()
            for ($i = 0; $i -lt $lines.Count; $i++) {
                $line = [string]$lines[$i]
                $lower = $line.ToLowerInvariant()
                if ($patterns | Where-Object { $lower.Contains($_) }) {
                    $sanitized = $line.Trim()
                    if ($sanitized.Length -gt 280) { $sanitized = $sanitized.Substring(0, 280) }
                    $matches += [pscustomobject]@{ line = $i + 1; text = $sanitized }
                    if ($matches.Count -ge 30) { break }
                }
            }
            if ($matches.Count -gt 0) {
                $hints += [pscustomobject]@{
                    relative_path = Get-RelativeSafePath $resolved $file.FullName
                    matches = $matches
                }
            }
        } catch {}
    }
    return $hints
}

$report = [ordered]@{
    generated_at = (Get-Date).ToString('o')
    purpose = 'Read-only architecture observation. Do not copy proprietary implementation into the repository.'
    install_path_provided = [bool]$InstallPath
    rbz_path_provided = [bool]$RbzPath
    install_inventory = @()
    rbz_inventory = @()
    readable_architecture_hints = @()
    processes = @()
    listening_ports = @()
}

if ($InstallPath) {
    if (-not (Test-Path -LiteralPath $InstallPath)) { throw "InstallPath not found: $InstallPath" }
    $report.install_inventory = @(Get-FileInventory $InstallPath)
    $report.readable_architecture_hints += @(Get-ReadableArchitectureHints $InstallPath)
}

if ($RbzPath) {
    if (-not (Test-Path -LiteralPath $RbzPath)) { throw "RbzPath not found: $RbzPath" }
    $rbzResolved = (Resolve-Path -LiteralPath $RbzPath).Path
    $extractRoot = Join-Path $OutputDir 'rbz-expanded'
    New-Item -ItemType Directory -Force -Path $extractRoot | Out-Null
    $zipCopy = Join-Path $OutputDir 'plugin.zip'
    Copy-Item -LiteralPath $rbzResolved -Destination $zipCopy -Force
    try {
        Expand-Archive -LiteralPath $zipCopy -DestinationPath $extractRoot -Force
        $report.rbz_inventory = @(Get-FileInventory $extractRoot)
        $report.readable_architecture_hints += @(Get-ReadableArchitectureHints $extractRoot)
    } finally {
        Remove-Item -LiteralPath $zipCopy -Force -ErrorAction SilentlyContinue
    }
}

$processes = Get-Process -ErrorAction SilentlyContinue |
    Where-Object {
        $_.ProcessName -match 'sketchup|electron|python|node|sutu|xuezhang|jianzh'
    } |
    Select-Object Id, ProcessName, Path
$report.processes = @($processes)

try {
    $ports = Get-NetTCPConnection -State Listen -ErrorAction Stop | ForEach-Object {
        $processName = $null
        try { $processName = (Get-Process -Id $_.OwningProcess -ErrorAction Stop).ProcessName } catch {}
        [pscustomobject]@{
            local_address = $_.LocalAddress
            local_port = $_.LocalPort
            owning_process = $_.OwningProcess
            process_name = $processName
        }
    }
    $report.listening_ports = @($ports)
} catch {
    $report.listening_ports = @()
}

$jsonPath = Join-Path $OutputDir 'observation.json'
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $jsonPath -Encoding UTF8

$summary = @"
# Competitor desktop architecture observation

Generated: $($report.generated_at)

This report is local evidence only. Separate observed facts from inference. Do not commit proprietary source, installer contents, private paths or protected binaries.

- Install files inventoried: $($report.install_inventory.Count)
- RBZ files inventoried: $($report.rbz_inventory.Count)
- Text files with architecture hints: $($report.readable_architecture_hints.Count)
- Matching running processes: $($report.processes.Count)
- Listening TCP sockets recorded: $($report.listening_ports.Count)

Raw local JSON: observation.json
"@
$summary | Set-Content -LiteralPath (Join-Path $OutputDir 'README.md') -Encoding UTF8

Write-Host "Read-only observation saved to: $OutputDir"
Write-Host "JSON: $jsonPath"
