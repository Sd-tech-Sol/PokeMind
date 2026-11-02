param(
    [string]$Workspace,
    [ValidateSet('first', 'resume')][string]$Exercise
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$interpreter = Join-Path $projectRoot '.venv-desktop/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $interpreter)) {
    throw 'Environnement Qt existant requis; aucune installation automatique.'
}
$qaArguments = @('-B', (Join-Path $PSScriptRoot 'qa_offline_gui.py'))
if ($Workspace) {
    if ($Workspace -notmatch '^build/qr-[0-9a-f]{8}$') { throw 'Workspace QA relatif invalide.' }
    $qaArguments += @('--workspace', $Workspace)
}
if ($Exercise) { $qaArguments += @('--exercise', $Exercise) }
Push-Location -LiteralPath $projectRoot
try {
    & $interpreter @qaArguments
    if ($LASTEXITCODE -ne 0) { throw "QA interrompue (code $LASTEXITCODE)." }
}
finally { Pop-Location }
