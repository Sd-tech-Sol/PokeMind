; PokeMind installer (Inno Setup 6). Built by scripts/Build-PokeMindInstaller.ps1, which passes
; AppVersion, DistDir, IconFile, SmallImage and OutputDir. Per-user install: no administrator rights.
; Uninstalling removes the program only; the data in %LOCALAPPDATA%\PokeMind stays.
#ifndef AppVersion
  #error Build with scripts/Build-PokeMindInstaller.ps1
#endif

[Setup]
AppId={{9B4E3B52-6C1D-4E7A-9F3B-5A2C8D1E7F40}
AppName=PokeMind
AppVersion={#AppVersion}
AppVerName=PokeMind {#AppVersion}
AppPublisher=PokeMind (unofficial fan project)
DefaultDirName={localappdata}\Programs\PokeMind
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir={#OutputDir}
OutputBaseFilename=PokeMind-Setup-{#AppVersion}
SetupIconFile={#IconFile}
LicenseFile=..\LICENSE
WizardSmallImageFile={#SmallImage}
UninstallDisplayIcon={app}\PokeMind.exe
UninstallDisplayName=PokeMind
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ShowLanguageDialog=auto
#ifdef SignToolName
; Defined by the build script only when a signing certificate is given.
SignTool={#SignToolName}
SignedUninstaller=yes
#endif

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"; InfoBeforeFile: "notice-en.txt"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"; InfoBeforeFile: "notice-fr.txt"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[InstallDelete]
; An update replaces the bundled Python runtime as a whole, never mixing two versions.
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\LICENSE"; DestDir: "{app}"; DestName: "LICENSE.txt"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\PokeMind"; Filename: "{app}\PokeMind.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\PokeMind"; Filename: "{app}\PokeMind.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\PokeMind.exe"; Description: "{cm:LaunchProgram,PokeMind}"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent
