; K Studio per-user candidate installer. Payload commands are generated from an
; audited exact inventory; uninstall never recursively deletes a chosen folder.
Unicode true
ManifestDPIAware true
RequestExecutionLevel user
SetCompressor /SOLID zlib
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"
!include "x64.nsh"
Name "${PRODUCT_NAME}"
OutFile "${OUTPUT_EXE}"
InstallDir "${INSTALL_ROOT}"
BrandingText "K Studio · AI Architecture"
ShowInstDetails show
ShowUninstDetails show
VIProductVersion "3.0.0.${SEQUENCE}"
VIAddVersionKey /LANG=1033 "ProductName" "K Studio R3"
VIAddVersionKey /LANG=1033 "FileDescription" "K Studio R3 internal candidate installer"
VIAddVersionKey /LANG=1033 "FileVersion" "${VERSION}"
VIAddVersionKey /LANG=1033 "LegalCopyright" "K Studio contributors"
!define MUI_ABORTWARNING
!define MUI_ICON "${APP_ICON}"
!define MUI_UNICON "${APP_ICON}"
!define MUI_WELCOMEPAGE_TEXT "安装 K Studio R3 内部候选版。需要 Windows x64、WebView2 和您自己的合法 SketchUp 2024。安装不会包含 SketchUp、作者 API 或旧项目。现有 R2 安装与数据不会改变。当前未获得公开发行验收。"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_TEXT "候选版已安装。可从开始菜单打开 K Studio R3。个人数据保存在独立账户资料目录，卸载默认保留。没有为您开通真实短信、微信支付或公网服务。"
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "English"
Var CheckPath

!macro CheckFixedRoot Prefix
Function ${Prefix}CheckFixedRoot
  ; Ignore /D= overrides: this product owns exactly one fixed per-user root.
  StrCpy $INSTDIR "${INSTALL_ROOT}"
  StrCpy $CheckPath $INSTDIR
  Call ${Prefix}CheckPathAncestors
FunctionEnd
Function ${Prefix}CheckPathAncestors
  check_parent_${Prefix}:
    System::Call 'kernel32::GetFileAttributesW(w "$CheckPath") i.r0'
    IntCmp $0 -1 check_next_${Prefix}
    IntOp $1 $0 & 0x400
    IntCmp $1 0 check_next_${Prefix}
    MessageBox MB_ICONSTOP "安装位置包含目录链接，已停止以保护现有文件。" /SD IDOK
    SetErrorLevel 2
    Abort
  check_next_${Prefix}:
    ${GetParent} "$CheckPath" $1
    StrCmp $1 "" check_done_${Prefix}
    StrCmp $1 $CheckPath check_done_${Prefix}
    StrCpy $CheckPath $1
    Goto check_parent_${Prefix}
  check_done_${Prefix}:
FunctionEnd
!macroend
!insertmacro CheckFixedRoot ""
!insertmacro CheckFixedRoot "un."

Function .onInit
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "K Studio R3 需要 64 位 Windows。未更改系统。" /SD IDOK
    SetErrorLevel 2
    Abort
  ${EndIf}
  SetShellVarContext current
  SetRegView 64
  Call CheckFixedRoot
  IfFileExists "$INSTDIR\*.*" 0 init_done
  ReadINIStr $0 "$INSTDIR\.kstudio-owner.ini" "Owner" "Product"
  StrCmp $0 "${PRODUCT_ID}" 0 foreign_root
  ; Current release high-water mark is plain JSON integer, also used by the
  ; frozen signed updater. Refuse installer downgrade and malformed pointers.
  IfFileExists "$INSTDIR\highest-sequence.json" 0 foreign_root
  FileOpen $0 "$INSTDIR\highest-sequence.json" r
  FileRead $0 $1
  FileClose $0
  StrCpy $2 0
  digit_loop:
    StrCpy $3 $1 1 $2
    StrCmp $3 "" digits_done
    StrCmp $3 "$\r" digits_done
    StrCmp $3 "$\n" digits_done
    StrCmp $3 "0" digit_ok
    StrCmp $3 "1" digit_ok
    StrCmp $3 "2" digit_ok
    StrCmp $3 "3" digit_ok
    StrCmp $3 "4" digit_ok
    StrCmp $3 "5" digit_ok
    StrCmp $3 "6" digit_ok
    StrCmp $3 "7" digit_ok
    StrCmp $3 "8" digit_ok
    StrCmp $3 "9" digit_ok
    Goto foreign_root
  digit_ok:
    IntOp $2 $2 + 1
    IntCmp $2 9 foreign_root 0 foreign_root
    Goto digit_loop
  digits_done:
    IntCmp $2 0 foreign_root
    IntCmp $1 ${SEQUENCE} init_done init_done downgrade
  downgrade:
    MessageBox MB_ICONSTOP "已安装更新的版本。为保护数据与更新信任，本安装包不能降级覆盖。" /SD IDOK
    SetErrorLevel 3
    Abort
  foreign_root:
    MessageBox MB_ICONSTOP "目标目录不是可识别的 K Studio R3 安装，或版本记录异常。没有覆盖该目录。" /SD IDOK
    SetErrorLevel 2
    Abort
  init_done:
FunctionEnd

!include "${PAYLOAD_INCLUDE}"
Section "K Studio R3（必选）" Main
  SectionIn RO
  SetShellVarContext current
  SetRegView 64
  Call CheckFixedRoot
  IfFileExists "$INSTDIR\versions\${VERSION}\*.*" 0 slot_ready
  ReadINIStr $0 "$INSTDIR\versions\${VERSION}\.kstudio-slot.ini" "Owner" "Product"
  StrCmp $0 "${PRODUCT_ID}" slot_ready
  MessageBox MB_ICONSTOP "版本目录包含不属于本安装器的文件，未覆盖。" /SD IDOK
  SetErrorLevel 2
  Abort
  slot_ready:
  CreateDirectory "$INSTDIR"
  CreateDirectory "$INSTDIR\versions\${VERSION}"
  WriteINIStr "$INSTDIR\.kstudio-owner.ini" "Owner" "Product" "${PRODUCT_ID}"
  WriteINIStr "$INSTDIR\versions\${VERSION}\.kstudio-slot.ini" "Owner" "Product" "${PRODUCT_ID}"
  FileOpen $0 "$INSTDIR\highest-sequence.json" w
  FileWrite $0 "${SEQUENCE}"
  FileClose $0
  ClearErrors
  !insertmacro InstallPayload
  IfErrors install_failed
  SetOutPath "$INSTDIR"
  File /oname=launch_installed.ps1 "${LAUNCHER_FILE}"
  File /oname=NSIS-LICENSE.txt "${NSIS_LICENSE}"
  IfErrors install_failed
  WriteINIStr "$INSTDIR\versions\${VERSION}\.kstudio-slot.ini" "Owner" "Product" "${PRODUCT_ID}"
  WriteINIStr "$INSTDIR\.kstudio-owner.ini" "Owner" "Product" "${PRODUCT_ID}"
  FileOpen $0 "$INSTDIR\current.json" w
  FileWrite $0 '{$\"version$\":$\"${VERSION}$\",$\"sequence$\":${SEQUENCE},$\"data_schema$\":1}'
  FileClose $0
  FileOpen $0 "$INSTDIR\highest-sequence.json" w
  FileWrite $0 "${SEQUENCE}"
  FileClose $0
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
  CreateShortcut "$SMPROGRAMS\${PRODUCT_NAME}\K Studio.lnk" "$SYSDIR\WindowsPowerShell\v1.0\powershell.exe" '-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "$INSTDIR\launch_installed.ps1" -InstallRoot "$INSTDIR" -DataDir "${PROFILE_ROOT}"' "$INSTDIR\versions\${VERSION}\KStudio.exe" 0 SW_SHOWMINIMIZED
  CreateShortcut "$SMPROGRAMS\${PRODUCT_NAME}\卸载.lnk" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_ID}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_ID}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_ID}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_ID}" "UninstallString" '$\"$INSTDIR\Uninstall.exe$\"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_ID}" "QuietUninstallString" '$\"$INSTDIR\Uninstall.exe$\" /S'
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_ID}" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_ID}" "NoRepair" 1
  Goto install_done
  install_failed:
    MessageBox MB_ICONSTOP "安装未完成。请正常关闭 K Studio 后重新运行安装包修复；个人模型与旧版本未删除。" /SD IDOK
    SetErrorLevel 4
    Abort
  install_done:
SectionEnd

Section /o "创建桌面快捷方式" DesktopShortcut
  CreateShortcut "$DESKTOP\${PRODUCT_NAME}.lnk" "$SYSDIR\WindowsPowerShell\v1.0\powershell.exe" '-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "$INSTDIR\launch_installed.ps1" -InstallRoot "$INSTDIR" -DataDir "${PROFILE_ROOT}"' "$INSTDIR\versions\${VERSION}\KStudio.exe" 0 SW_SHOWMINIMIZED
SectionEnd

Function un.onInit
  SetShellVarContext current
  SetRegView 64
  Call un.CheckFixedRoot
  ReadINIStr $0 "$INSTDIR\.kstudio-owner.ini" "Owner" "Product"
  StrCmp $0 "${PRODUCT_ID}" un_owned
  SetErrorLevel 2
  Abort
  un_owned:
FunctionEnd

Section "Uninstall"
  Call un.CheckFixedRoot
  ; Exact generated file names only. Unknown files, prior version slots and the
  ; entire separate profile are deliberately retained. No RMDir /r anywhere.
  !insertmacro UninstallPayload
  Delete "$INSTDIR\versions\${VERSION}\.kstudio-slot.ini"
  RMDir "$INSTDIR\versions\${VERSION}"
  RMDir "$INSTDIR\versions"
  Delete "$INSTDIR\launch_installed.ps1"
  Delete "$INSTDIR\NSIS-LICENSE.txt"
  Delete "$INSTDIR\current.json"
  ; Preserve the tiny ownership/high-water records so a future reinstall can
  ; recognize retained old version slots without accepting arbitrary folders.
  Delete "$INSTDIR\Uninstall.exe"
  Delete "$SMPROGRAMS\${PRODUCT_NAME}\K Studio.lnk"
  Delete "$SMPROGRAMS\${PRODUCT_NAME}\卸载.lnk"
  RMDir "$SMPROGRAMS\${PRODUCT_NAME}"
  Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_ID}"
  RMDir "$INSTDIR"
SectionEnd
