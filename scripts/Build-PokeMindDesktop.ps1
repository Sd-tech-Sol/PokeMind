param([string]$SyntheticQaRoot, [string]$StagingRoot)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$interpreter = Join-Path $projectRoot '.venv-desktop/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $interpreter)) { throw 'Lancer Install-PokeMindDesktop.ps1 en premier.' }
$buildRoot = $projectRoot
if ($SyntheticQaRoot -and $StagingRoot) { throw 'Choisir une seule destination de build.' }
if ($StagingRoot) {
    $buildRoot = [System.IO.Path]::GetFullPath($StagingRoot)
    $expectedParent = Join-Path $projectRoot 'build'
    if ((Split-Path -Parent $buildRoot) -ne $expectedParent -or (Split-Path -Leaf $buildRoot) -notmatch '^exe-upgrade-[0-9a-f]{32}$') { throw 'Staging hors destination dédiée.' }
    foreach ($component in @($projectRoot, $expectedParent, $buildRoot)) {
        if ((Test-Path -LiteralPath $component) -and ((Get-Item -LiteralPath $component).Attributes -band [System.IO.FileAttributes]::ReparsePoint)) { throw 'Redirection staging refusée.' }
    }
    if (Test-Path -LiteralPath $buildRoot) { throw 'Staging déjà occupé : aucun remplacement.' }
}
if ($SyntheticQaRoot) {
    $buildRoot = [System.IO.Path]::GetFullPath($SyntheticQaRoot)
    $expectedParent = Join-Path $projectRoot 'build'
    if ((Split-Path -Parent $buildRoot) -ne $expectedParent -or (Split-Path -Leaf $buildRoot) -notmatch '^synthetic-release-[0-9a-f]{32}$') { throw 'QA synthétique hors destination dédiée.' }
    $marker = Join-Path $buildRoot '.orchestrator/SYNTHETIC_QA_ONLY'
    # Check every ancestor before reading the marker or creating build outputs.
    $component = $buildRoot
    while ($component -and $component -ne $projectRoot) {
        if ((Test-Path -LiteralPath $component) -and ((Get-Item -LiteralPath $component).Attributes -band [System.IO.FileAttributes]::ReparsePoint)) { throw 'Redirection QA refusée.' }
        $component = Split-Path -Parent $component
    }
    foreach ($component in @((Join-Path $buildRoot '.orchestrator'), $marker)) {
        if ((Get-Item -LiteralPath $component).Attributes -band [System.IO.FileAttributes]::ReparsePoint) { throw 'Redirection marqueur QA refusée.' }
    }
    if ((Get-Content -LiteralPath $marker -Raw).Trim() -ne 'POKEMIND_SYNTHETIC_RELEASE_QA_V1') { throw 'Marqueur QA fictive absent.' }
    if (Test-Path -LiteralPath (Join-Path $buildRoot 'dist')) { throw 'Sortie QA déjà occupée : aucun remplacement.' }
}
$outputTarget = [System.IO.Path]::GetFullPath((Join-Path $buildRoot 'dist/PokeMind'))
if (-not $outputTarget.StartsWith($projectRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Sortie build hors projet.' }
if (Test-Path -LiteralPath $outputTarget) { throw 'Distribution existante : choisir un staging neuf, aucun remplacement par le build.' }
foreach ($target in @((Join-Path $buildRoot 'dist'), $outputTarget, (Join-Path $buildRoot 'build'))) {
    if ((Test-Path -LiteralPath $target) -and ((Get-Item -LiteralPath $target).Attributes -band [System.IO.FileAttributes]::ReparsePoint)) { throw 'Redirection build refusée.' }
}
$qaArguments = @()
if ($SyntheticQaRoot) { $qaArguments = @('--paths', 'scripts', '--hidden-import', 'qa_unified_desktop') }
# ConPTY of the Terminal page: conpty.dll starts OpenConsole.exe from its own folder (not a DLL, so named here).
$winpty = & $interpreter -c "import os, winpty; print(os.path.dirname(winpty.__file__))"
if ($LASTEXITCODE -ne 0) { throw 'pywinpty absent de la venv de build.' }
$terminalArguments = @('--add-binary', ((Join-Path $winpty 'OpenConsole.exe') + ';winpty'), '--add-binary', ((Join-Path $winpty 'winpty-agent.exe') + ';winpty'))
# The logo is drawn in code; the .ico is generated for the EXE (Explorer, taskbar, shortcuts).
$icon = Join-Path $buildRoot 'build/pokemind.ico'
& $interpreter scripts/make_icon.py $icon
if ($LASTEXITCODE -ne 0) { throw 'Icône PokeMind impossible.' }
& $interpreter -m PyInstaller --noconfirm --onedir --windowed --name PokeMind --icon $icon --paths src --distpath (Join-Path $buildRoot 'dist') --workpath (Join-Path $buildRoot 'build/desktop') --specpath (Join-Path $buildRoot 'build') @qaArguments @terminalArguments --collect-binaries winpty --hidden-import winpty --hidden-import pyte --exclude-module PySide6.QtWebEngineCore --exclude-module PySide6.QtWebEngineWidgets --exclude-module PySide6.QtPdf --exclude-module PySide6.QtQml src/pokemind/desktop/app.py
if ($LASTEXITCODE -ne 0) { throw 'Compilation Windows impossible.' }
$notices = Join-Path $outputTarget 'THIRD_PARTY_NOTICES.md'
Copy-Item -LiteralPath (Join-Path $projectRoot 'THIRD_PARTY_NOTICES.md') -Destination $notices
& $interpreter scripts/desktop_licenses.py --destination (Join-Path $outputTarget 'licenses')
if ($LASTEXITCODE -ne 0) { throw 'Collecte des avis impossible.' }
Write-Output 'Application compilée dans la destination sélectionnée. Les données locales ne sont pas embarquées.'
