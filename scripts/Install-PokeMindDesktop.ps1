$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if (-not (Test-Path -LiteralPath '.venv-desktop/Scripts/python.exe')) {
    python -m venv .venv-desktop
    if ($LASTEXITCODE -ne 0) { throw 'Création de la venv impossible.' }
}
& .venv-desktop/Scripts/python.exe -m pip install --index-url https://pypi.org/simple --no-build-isolation -e '.[desktop-build]' pytest==9.1.1
if ($LASTEXITCODE -ne 0) { throw 'Installation isolée impossible.' }
Write-Output 'PokeMind Desktop installé dans la venv du projet. Lancer scripts/Start-PokeMindDesktop.ps1.'
