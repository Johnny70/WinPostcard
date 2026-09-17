; Inno Setup script for the standalone WinPostcard build (`just package`
; produces the source tree this compiles; `just installer` runs both).
; AppId is fixed so re-running the installer upgrades in place instead of
; creating a second Start Menu entry -- never change it.

#define MyAppName "WinPostcard"
#define MyAppVersion "0.0.0-dev"
#define MyAppPublisher "WinPostcard"
#define MyAppExeName "WinPostcard.exe"
#define MySourceDir "..\build\pkg-dist\WinPostcard"

[Setup]
AppId={{866E7BE0-009C-4D98-844D-10AF46FAA702}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
; No admin rights required: installs under the user's own AppData, not
; Program Files -- matches installing e.g. VS Code or Discord per-user.
; {autopf} (Program Files) needs elevation, which PrivilegesRequired=lowest
; then can't grant -- {localappdata}\Programs is the correct pair for this.
PrivilegesRequired=lowest
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=..\build\pkg-installer
OutputBaseFilename=WinPostcard-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=WinPostcard.ico
; Verified the failure mode this guards against: with the default (yes),
; RestartManager tries to close a running WinPostcard.exe gracefully, and if
; it doesn't (observed: it didn't, twice, with the app just sitting idle),
; Setup aborts the whole update rather than proceeding -- force terminates
; it instead so an update never silently just fails to apply. Mail data
; (SQLite db, GSettings, Credential Manager) all live outside {app}, so this
; only affects the running window, never account data -- verified separately
; by editing the live db under a running install and confirming it survived
; an aborted update attempt untouched.
CloseApplications=force
RestartApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "{#MySourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
