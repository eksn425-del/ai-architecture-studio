param([Parameter(Mandatory=$true)][string]$Bundle,
      [Parameter(Mandatory=$true)][string]$BinaryMap,
      [Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath $Output) {throw 'Preserve prior vendor evidence; choose a new output.'}
$bundleRoot = [IO.Path]::GetFullPath($Bundle).TrimEnd('\')
$map = Get-Content -LiteralPath $BinaryMap -Raw | ConvertFrom-Json
$rows = @()
foreach ($item in $map.binaries) {
    if ($item.category -ne 'MICROSOFT_RUNTIME_OR_WEBVIEW_REDISTRIBUTION_TERMS_REVIEW' -and $item.path -notmatch '/conpty/|OpenConsole|conpty\.dll') {continue}
    $target = [IO.Path]::GetFullPath((Join-Path $bundleRoot $item.path))
    if (-not $target.StartsWith($bundleRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {throw 'Vendor target escaped bundle.'}
    $file = Get-Item -LiteralPath $target
    $signature = Get-AuthenticodeSignature -LiteralPath $target
    $rows += [ordered]@{
        path=$item.path; bytes=$file.Length; sha256=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLower();
        product_name=$file.VersionInfo.ProductName; product_version=$file.VersionInfo.ProductVersion;
        file_version=$file.VersionInfo.FileVersion; original_filename=$file.VersionInfo.OriginalFilename;
        company=$file.VersionInfo.CompanyName; copyright=$file.VersionInfo.LegalCopyright;
        signature_status=[string]$signature.Status;
        signer_subject=$(if ($signature.SignerCertificate) {$signature.SignerCertificate.Subject} else {$null});
        signer_thumbprint=$(if ($signature.SignerCertificate) {$signature.SignerCertificate.Thumbprint} else {$null});
        timestamp_subject=$(if ($signature.TimeStamperCertificate) {$signature.TimeStamperCertificate.Subject} else {$null});
        component=$item.component;
        distribution_grant='NOT_INFERRED_FROM_SIGNATURE';
    }
}
$result = [ordered]@{schema=1; scope='Actual bundled PE metadata and current Windows Authenticode verification; neither alone establishes redistribution rights'; binaries=$rows}
$result | ConvertTo-Json -Depth 9 | Set-Content -LiteralPath $Output -Encoding utf8
Write-Output ('Collected actual vendor metadata for ' + $rows.Count + ' binaries.')
