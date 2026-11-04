param([Parameter(Mandatory=$true)][string]$Path,[Parameter(Mandatory=$true)][string]$Thumbprint)
$ErrorActionPreference='Stop'
if ($Thumbprint -notmatch '^[A-Fa-f0-9]{40}$') { throw 'A pinned publisher certificate is required.' }
$signature=Get-AuthenticodeSignature -LiteralPath $Path
if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Thumbprint -ne $Thumbprint) {
    throw 'Authenticode status or pinned publisher certificate mismatch.'
}
Write-Output 'authenticode_verified'
