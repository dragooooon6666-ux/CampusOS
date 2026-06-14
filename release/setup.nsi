; CampusOS 安装程序
; NSIS 3.x

Unicode true
Name "CampusOS"
OutFile "CampusOS-Setup-v0.1.2.exe"
InstallDir "$PROGRAMFILES\CampusOS"
InstallDirRegKey HKLM "Software\CampusOS" "InstallDir"
RequestExecutionLevel admin

!include "MUI2.nsh"

; ── 界面 ──
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "SimpChinese"

; ── 安装段 ──
Section "CampusOS" SecMain
  SetOutPath "$INSTDIR"

  ; 主程序
  File /r "CampusOS\*"

  ; 创建必要目录
  CreateDirectory "$INSTDIR\input"
  CreateDirectory "$INSTDIR\output"
  CreateDirectory "$INSTDIR\data"
  CreateDirectory "$INSTDIR\config"

  ; 注册表
  WriteRegStr HKLM "Software\CampusOS" "InstallDir" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CampusOS" "DisplayName" "CampusOS 校园事务智能操作系统"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CampusOS" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CampusOS" "DisplayVersion" "0.1.2"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CampusOS" "Publisher" "CampusOS"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CampusOS" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CampusOS" "NoRepair" 1

  ; 创建卸载程序
  WriteUninstaller "$INSTDIR\uninstall.exe"

  ; 桌面快捷方式
  CreateShortCut "$DESKTOP\CampusOS.lnk" "$INSTDIR\CampusOS.exe" "" "$INSTDIR\CampusOS.exe" 0

  ; 开始菜单
  CreateDirectory "$SMPROGRAMS\CampusOS"
  CreateShortCut "$SMPROGRAMS\CampusOS\CampusOS.lnk" "$INSTDIR\CampusOS.exe" "" "$INSTDIR\CampusOS.exe" 0
  CreateShortCut "$SMPROGRAMS\CampusOS\使用指南.lnk" "$INSTDIR\使用指南.txt"
  CreateShortCut "$SMPROGRAMS\CampusOS\卸载 CampusOS.lnk" "$INSTDIR\uninstall.exe"
SectionEnd

; ── 卸载段 ──
Section "Uninstall"
  Delete "$INSTDIR\uninstall.exe"
  RMDir /r "$INSTDIR"

  Delete "$DESKTOP\CampusOS.lnk"
  RMDir /r "$SMPROGRAMS\CampusOS"

  DeleteRegKey HKLM "Software\CampusOS"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CampusOS"
SectionEnd
