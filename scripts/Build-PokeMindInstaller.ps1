param([string]$DistDir = 'dist/PokeMind', [string]$OutputDir = 'dist/installer',
      [string[]]$SignArguments = @(), [string]$TimestampUrl = 'http://timestamp.digicert.com')
# One-file Windows installer from a built distribution (Build-PokeMindDesktop.ps1 first).
# Needs Inno Setup 6: winget install --id JRSoftware.InnoSetup -e --scope user
# Optional code signing (signtool from the Windows SDK) of PokeMind.exe in DistDir, the installer and its uninstaller:
#   certificate in the Windows store: -SignArguments '/sha1','<thumbprint>'
#   Azure Trusted Signing: -SignArguments '/dlib','<dir>\Azure.CodeSigning.Dlib.dll','/dmdf','<dir>\metadata.json'
#                          -TimestampUrl 'http://timestamp.acs.microsoft.com'
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$interpreter = Join-Path $projectRoot '.venv-desktop/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $interpreter)) { throw 'Lancer Install-PokeMindDesktop.ps1 en premier.' }
$compiler = @((Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'),
              (Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'),
              (Join-Path $env:ProgramFiles 'Inno Setup 6\ISCC.exe')) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $compiler) { $compiler = (Get-Command ISCC.exe -ErrorAction SilentlyContinue).Source }
if (-not $compiler) { throw 'Inno Setup 6 introuvable : winget install --id JRSoftware.InnoSetup -e --scope user' }
$dist = [System.IO.Path]::GetFullPath($DistDir)
$output = [System.IO.Path]::GetFullPath($OutputDir)
foreach ($path in @($dist, $output)) {
    if (-not $path.StartsWith($projectRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Chemin hors projet refusé.' }
}
foreach ($required in @('PokeMind.exe', 'THIRD_PARTY_NOTICES.md')) {
    if (-not (Test-Path -LiteralPath (Join-Path $dist $required))) { throw "Distribution incomplète ($required) : lancer Build-PokeMindDesktop.ps1." }
}
# Program files only: the same refusals as a deployment, so no personal file can be packaged.
foreach ($entry in Get-ChildItem -LiteralPath $dist -Recurse -Force) {
    if ($entry.Attributes -band [System.IO.FileAttributes]::ReparsePoint) { throw 'Redirection dans la distribution refusée.' }
    if ($entry.PSIsContainer -and $entry.Name -in @('data','local','chat','backups','conversations','logs')) { throw 'Dossier personnel dans la distribution refusé.' }
    if (-not $entry.PSIsContainer -and ($entry.Extension.ToLowerInvariant() -in @('.sqlite','.sqlite3','.db','.json','.jsonl','.log','.env') -or $entry.Name.StartsWith('.env'))) { throw 'Fichier personnel dans la distribution refusé.' }
}
# Nor any build-machine path (account name, user profile, repository), checked before signing (SECURITY.md).
$scan = & $interpreter scripts/scan_binary_personal_paths.py $dist --require-archive
if ($LASTEXITCODE) { throw "Chemin de la machine de construction dans la distribution : $scan" }
$version = (& $interpreter -c "import sys; sys.path.insert(0, 'src'); import pokemind; print(pokemind.__version__)").Trim()
$work = Join-Path $projectRoot 'build/installer'
New-Item -ItemType Directory -Force -Path $work, $output | Out-Null
$icon = Join-Path $work 'pokemind.ico'
$small = Join-Path $work 'wizard-small.bmp'
& $interpreter scripts/make_icon.py $icon | Out-Null
& $interpreter scripts/make_icon.py $small --size 110 | Out-Null
$signing = @()
if ($SignArguments.Count) {
    $signtool = Get-ChildItem -LiteralPath (Join-Path ${env:ProgramFiles(x86)} 'Windows Kits\10\bin') -Recurse -Filter signtool.exe -ErrorAction SilentlyContinue |
        Where-Object { $_.Directory.Name -eq 'x64' } | Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
    if (-not $signtool) { $signtool = (Get-Command signtool.exe -ErrorAction SilentlyContinue).Source }
    if (-not $signtool) { throw 'signtool introuvable : winget install --id Microsoft.WindowsSDK.10.0.26100 -e' }
    $options = @('sign', '/fd', 'SHA256') + $(if ($TimestampUrl) { @('/tr', $TimestampUrl, '/td', 'SHA256') } else { @() }) + $SignArguments
    & $signtool @options (Join-Path $dist 'PokeMind.exe') | Out-Null
    if ($LASTEXITCODE) { throw "Signature de PokeMind.exe en échec ($LASTEXITCODE)." }
    # Inno Setup signs the installer and the uninstaller with the same command ($q quote, $f file).
    $command = (@('$q' + $signtool + '$q') + ($options | ForEach-Object { if ($_ -match '\s') { '$q' + $_ + '$q' } else { $_ } }) + '$f') -join ' '
    $signing = @("/Spokemindsign=$command", '/DSignToolName=pokemindsign')
}
& $compiler /Q "/DAppVersion=$version" "/DDistDir=$dist" "/DIconFile=$icon" "/DSmallImage=$small" "/DOutputDir=$output" @signing (Join-Path $projectRoot 'packaging/PokeMind.iss')
if ($LASTEXITCODE) { throw "Inno Setup en échec ($LASTEXITCODE)." }
$installer = Join-Path $output "PokeMind-Setup-$version.exe"
if ($SignArguments.Count) {
    foreach ($file in @((Join-Path $dist 'PokeMind.exe'), $installer)) {
        if (-not (Get-AuthenticodeSignature -LiteralPath $file).SignerCertificate) { throw "Signature absente : $file" }
    }
}
$hash = (Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash
# Published next to the installer, in the sha256sum format (computed after signing).
Set-Content -LiteralPath "$installer.sha256" -Value ($hash.ToLowerInvariant() + '  ' + (Split-Path -Leaf $installer)) -Encoding ascii
Write-Output ("installer=" + [System.IO.Path]::GetRelativePath($projectRoot, $installer) + " size_mb=" + [math]::Round((Get-Item -LiteralPath $installer).Length / 1MB, 1) + " sha256=" + $hash + " signed=" + [bool]$SignArguments.Count)
