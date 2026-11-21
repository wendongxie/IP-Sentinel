#ifndef TestBuild
  #define ProductId "IPSentinel.Desktop"
  #define LinkName "IP Sentinel"
  #define SetupName "IPSentinel_Setup_v1.2.0"
#else
  #define ProductId "IPSentinel.V11.Test"
  #define LinkName "IP Sentinel V11 Test"
  #define SetupName "IPSentinel_Test"
#endif

[Setup]
AppId={#ProductId}
AppName=IP Sentinel
AppVersion=1.2.0
AppVerName=IP Sentinel V1.2.0
AppPublisher=文东工作室
VersionInfoVersion=1.2.0.0
VersionInfoCompany=文东工作室
VersionInfoDescription=IP Sentinel V1.2.0 安装程序
DefaultDirName={localappdata}\Programs\IP Sentinel
DefaultGroupName=IP Sentinel
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
OutputDir=..\release
OutputBaseFilename={#SetupName}
SetupIconFile=..\assets\icons\ip-sentinel.ico
UninstallDisplayIcon={app}\IP Sentinel.exe
DisableWelcomePage=no
WizardStyle=modern
Compression=lzma2/fast
SolidCompression=yes
CloseApplications=yes

[Languages]
Name: "zhcn"; MessagesFile: "ChineseSimplified.isl"

[Messages]
WelcomeLabel1=欢迎安装 IP Sentinel
WelcomeLabel2=IP Sentinel V1.2.0 是一款公网出口 IP 纯净度检测与监控工具。%n%n文东工作室出品。支持公网 IP 检测、自动监控、历史查询及机器人告警。

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"

[Files]
Source: "..\dist\IP Sentinel\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\docs\IP_Sentinel_V1.2.0_用户使用手册.docx"; DestDir: "{app}"; Flags: ignoreversion

Source: "..\docs\风险名单许可.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\docs\X4BNet-MIT.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{userprograms}\{#LinkName}"; Filename: "{app}\IP Sentinel.exe"; WorkingDir: "{app}"
Name: "{userprograms}\{#LinkName} 用户使用手册"; Filename: "{app}\IP_Sentinel_V1.2.0_用户使用手册.docx"
Name: "{userdesktop}\{#LinkName}"; Filename: "{app}\IP Sentinel.exe"; WorkingDir: "{app}"; Tasks: desktopicon; Check: DesktopLinkAvailable

[Code]
function DesktopLinkAvailable: Boolean;
begin
  Result := not FileExists(ExpandConstant('{userdesktop}\{#LinkName}.lnk'));
end;



