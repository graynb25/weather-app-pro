; Inno Setup script for Weather App Pro (release-plan item 2.1).
;
; Compiled by build.ps1, which passes the version from the VERSION
; file:
;
;   ISCC installer\weatherapp.iss /DAppVersion=0.13.0

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

#define MyAppName "Weather App Pro"
#define MyAppExe "WeatherAppPro.exe"

[Setup]
AppId={{7E2A5C64-93B8-4B5D-9A0F-2C1D64F8E9B1}
AppName={#MyAppName}
AppVersion={#AppVersion}
AppVerName={#MyAppName} v{#AppVersion}
DefaultDirName={autopf}\{#MyAppName}
PrivilegesRequiredOverridesAllowed=dialog commandline
OutputDir=..\release
OutputBaseFilename=WeatherAppPro-setup-{#AppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\resources\icons\app.ico
LicenseFile=..\LICENSE
InfoBeforeFile=..\installer\install-info.txt
UninstallDisplayIcon={app}\{#MyAppExe}

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; \
    GroupDescription: "Shortcuts:"

[Files]
Source: "..\dist\WeatherAppPro\*"; DestDir: "{app}"; \
    Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\THIRD-PARTY-NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\PRIVACY.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; \
    Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExe}"; Description: "Launch {#MyAppName}"; \
    Flags: nowait postinstall skipifsilent

[Code]
// User data (key file, settings, favorites, cache) lives outside the
// install directory, so the uninstaller never touches it by default.
// The owner chooses; keeping it is the default action.
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
    DataDir: string;
begin
    if CurUninstallStep = usDone then begin
        DataDir := ExpandConstant('{localappdata}\WeatherAppPro');

        if DirExists(DataDir) then begin
            if MsgBox('Keep your saved API key, settings, favorites, and cache?' #13#10 '(Choosing No deletes the WeatherAppPro data folder.)', mbConfirmation, MB_YESNO) = IDNO then
                DelTree(DataDir, True, True, True);
        end;
    end;
end;
