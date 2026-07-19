; Inno Setup script for tikpull.
;
; Compile with ISCC.exe (Inno Setup Compiler), AFTER running build.ps1,
; which must produce dist\tikpull\tikpull.exe first:
;
;   powershell -ExecutionPolicy Bypass -File packaging\windows\build.ps1
;   iscc packaging\windows\installer.iss
;
; Produces dist_installer\tikpull-setup.exe.
;
; Pass /DAppVersion=x.y.z to stamp a specific version (CI does this from
; the git tag). Defaults to 0.0.0-dev for local manual compiles.

#ifndef AppVersion
  #define AppVersion "0.0.0-dev"
#endif

[Setup]
AppId={{658ACCA3-3765-4134-BA72-F74C28711FEA}
AppName=tikpull
AppVersion={#AppVersion}
AppPublisher=Ronan
DefaultDirName={autopf}\tikpull
DefaultGroupName=tikpull
UninstallDisplayIcon={app}\tikpull.exe
OutputDir=..\..\dist_installer
OutputBaseFilename=tikpull-setup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
SetupIconFile=icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\..\dist\tikpull\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\tikpull"; Filename: "{app}\tikpull.exe"
Name: "{autodesktop}\tikpull"; Filename: "{app}\tikpull.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\tikpull.exe"; Description: "Launch tikpull"; Flags: nowait postinstall skipifsilent
