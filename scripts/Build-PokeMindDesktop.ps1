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
# The PokeMind / TCG Coach card (src/pokemind/desktop/branding) is bundled for the window, menu and banner, and
# the .ico derived from it becomes the EXE resource (Explorer, taskbar, Start menu and desktop shortcuts).
$icon = Join-Path $buildRoot 'build/pokemind.ico'
& $interpreter scripts/make_icon.py $icon
if ($LASTEXITCODE -ne 0) { throw 'Icône PokeMind impossible.' }
$branding = Join-Path $projectRoot 'src/pokemind/desktop/branding'
if (-not (Test-Path -LiteralPath (Join-Path $branding 'pokemind-card.png'))) { throw 'Carte PokeMind absente : python scripts/make_icon.py --card' }
$brandingArguments = @('--add-data', ($branding + ';pokemind/desktop/branding'))
# Version shown in the file properties of PokeMind.exe, from pokemind.__version__ (same as the app and the installer).
$versionFile = Join-Path $buildRoot 'build/version-info.txt'
& $interpreter scripts/make_version_info.py $versionFile
if ($LASTEXITCODE -ne 0) { throw 'Version de PokeMind.exe impossible.' }
& $interpreter -m PyInstaller --noconfirm --onedir --windowed --name PokeMind --icon $icon --version-file $versionFile --paths src --distpath (Join-Path $buildRoot 'dist') --workpath (Join-Path $buildRoot 'build/desktop') --specpath (Join-Path $buildRoot 'build') @qaArguments @terminalArguments @brandingArguments --collect-binaries winpty --hidden-import winpty --hidden-import pyte --hidden-import pokemind.demo --exclude-module PySide6.QtWebEngineCore --exclude-module PySide6.QtWebEngineWidgets --exclude-module PySide6.QtPdf --exclude-module PySide6.QtQml src/pokemind/desktop/app.py
if ($LASTEXITCODE -ne 0) { throw 'Compilation Windows impossible.' }
$notices = Join-Path $outputTarget 'THIRD_PARTY_NOTICES.md'
Copy-Item -LiteralPath (Join-Path $projectRoot 'THIRD_PARTY_NOTICES.md') -Destination $notices
& $interpreter scripts/desktop_licenses.py --destination (Join-Path $outputTarget 'licenses')
if ($LASTEXITCODE -ne 0) { throw 'Collecte des avis impossible.' }
Write-Output 'Application compilée dans la destination sélectionnée. Les données locales ne sont pas embarquées.'
