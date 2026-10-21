Unicode true
RequestExecutionLevel user
SetCompressor /SOLID zlib
Name "NumberTyper"
OutFile "NumberTyper-Setup.exe"
InstallDir "$LOCALAPPDATA\Programs\NumberTyper"
ShowInstDetails show
ShowUnInstDetails show

!include "MUI2.nsh"

!define APP_NAME "NumberTyper"
!define APP_EXE "NumberTyper.exe"
!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\NumberTyper"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\..\docs\THIRD_PARTY_NOTICES.md"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "Mở NumberTyper"
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "Vietnamese"

Function .onInit
  SetShellVarContext current
FunctionEnd

Section "NumberTyper" SecMain
  SectionIn RO
  SetOutPath "$INSTDIR"
  File /r "..\..\dist\NumberTyper\*.*"
  File "..\..\docs\INSTALL_VI.md"
  File "..\..\docs\THIRD_PARTY_NOTICES.md"

  CreateDirectory "$SMPROGRAMS\NumberTyper"
  CreateShortcut "$SMPROGRAMS\NumberTyper\NumberTyper.lnk" "$INSTDIR\${APP_EXE}"
  CreateShortcut "$SMPROGRAMS\NumberTyper\Hướng dẫn thiết lập.lnk" "$INSTDIR\INSTALL_VI.md"
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayName" "NumberTyper"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayVersion" "0.1.0-preview"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "Publisher" "NumberTyper Preview"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoModify" 1
  WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoRepair" 1
SectionEnd

Section /o "Tạo lối tắt trên Màn hình nền" SecDesktop
  CreateShortcut "$DESKTOP\NumberTyper.lnk" "$INSTDIR\${APP_EXE}"
SectionEnd

Function un.onInit
  SetShellVarContext current
FunctionEnd

Section "Uninstall"
  Delete "$DESKTOP\NumberTyper.lnk"
  Delete "$SMPROGRAMS\NumberTyper\NumberTyper.lnk"
  Delete "$SMPROGRAMS\NumberTyper\Hướng dẫn thiết lập.lnk"
  RMDir "$SMPROGRAMS\NumberTyper"
  DeleteRegKey HKCU "${UNINSTALL_KEY}"
  RMDir /r "$INSTDIR"
  ; User settings and local logs in %LOCALAPPDATA%\NumberTyper are intentionally preserved.
SectionEnd
