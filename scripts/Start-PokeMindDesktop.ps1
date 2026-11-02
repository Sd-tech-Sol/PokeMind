$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$interpreter = Join-Path $projectRoot '.venv-desktop/Scripts/pythonw.exe'
if (-not (Test-Path -LiteralPath $interpreter)) { throw 'Lancer Install-PokeMindDesktop.ps1 en premier.' }
Start-Process -FilePath $interpreter -ArgumentList @('-m', 'pokemind', 'desktop') -WorkingDirectory $projectRoot -WindowStyle Normal
