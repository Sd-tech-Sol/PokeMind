[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Daily', 'Deep', 'Auto')]
    [string]$Mode,
    [ValidatePattern('^(?:[01]\d|2[0-3]):[0-5]\d$')]
    [string]$DeepTime,
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Database
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $projectRoot

$arguments = @(
    '-m', 'pokemind', 'knowledge', 'update',
    '--mode', $Mode.ToLowerInvariant(),
    '--apply', '--confirm-owner', '--public-only', '--json', '--db', $Database
)
if ($Mode -in @('Deep', 'Auto')) {
    if (-not $DeepTime) {
        throw 'DeepTime est requis pour les modes Deep et Auto.'
    }
    $arguments += @('--deep-time', $DeepTime)
}
& python @arguments
exit $LASTEXITCODE
