[Setup]
AppName=통합관리시스템
AppVersion=1.0.0
AppPublisher=Your Company
AppPublisherURL=https://yourwebsite.com
DefaultDirName={autopf}\통합관리시스템
DefaultGroupName=통합관리시스템
AllowNoIcons=yes
OutputDir=installer
OutputBaseFilename=통합관리시스템_설치파일_v1.0.0
SetupIconFile=app.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\통합관리시스템.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "config\*"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\통합관리시스템"; Filename: "{app}\통합관리시스템.exe"
Name: "{group}\{cm:UninstallProgram,통합관리시스템}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\통합관리시스템"; Filename: "{app}\통합관리시스템.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\통합관리시스템.exe"; Description: "{cm:LaunchProgram,통합관리시스템}"; Flags: nowait postinstall skipifsilent

[Code]
// 자동 업데이트 지원을 위한 레지스트리 등록
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    RegWriteStringValue(HKEY_CURRENT_USER, 'Software\통합관리시스템', 'InstallPath', ExpandConstant('{app}'));
    RegWriteStringValue(HKEY_CURRENT_USER, 'Software\통합관리시스템', 'Version', '1.0.0');
  end;
end;