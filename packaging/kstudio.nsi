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
!include "StrFunc.nsh"
${StrStr}
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
Var InstallerMutex
Var RootLease
Var ProfileLease
Var PointerTemp
Var HighestTemp

!macro CheckFixedRoot Prefix
Function ${Prefix}CheckFixedRoot
  ; Ignore /D= overrides: this product owns exactly one fixed per-user root.
  StrCpy $INSTDIR "${INSTALL_ROOT}"
  StrCpy $CheckPath $INSTDIR
  Call ${Prefix}CheckPathAncestors
FunctionEnd
Function ${Prefix}CheckPathAncestors
  check_parent_${Prefix}:
    System::Call 'kernel32::GetFileAttributesW(w "\\?\$CheckPath") i.r0'
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

; Share-zero handles interoperate with the byte leases held by the launcher,
; updater and DesktopInstance: an existing open lease prevents this open and
; this handle prevents a new runtime from acquiring its lease during mutation.
!macro ExclusiveLocks Prefix
Function ${Prefix}AcquireMutex
  System::Call 'kernel32::CreateMutexW(p 0, i 0, w "Local\${PRODUCT_ID}-Installer") p.r0 ?e'
  Pop $1
  StrCpy $InstallerMutex $0
  StrCmp $0 0 busy_${Prefix}
  IntCmp $1 183 busy_${Prefix}
  Return
  busy_${Prefix}:
    IfSilent +2
    MessageBox MB_ICONSTOP "K Studio 正在运行、启动或安装。请正常关闭后重试。"
    SetErrorLevel 5
    Abort
FunctionEnd
Function ${Prefix}AcquireRootLease
  StrCmp $RootLease "" 0 root_done_${Prefix}
  StrCpy $CheckPath "$INSTDIR\installer-lock"
  Call ${Prefix}CheckPathAncestors
  CreateDirectory "$INSTDIR\installer-lock"
  System::Call 'kernel32::CreateFileW(w "$INSTDIR\installer-lock\.kstudio-runtime.lock", i 0xC0000000, i 0, p 0, i 4, i 0x80, p 0) p.r0'
  StrCmp $0 -1 lease_busy_${Prefix}
  StrCpy $RootLease $0
  root_done_${Prefix}:
  Return
  lease_busy_${Prefix}:
    IfSilent +2
    MessageBox MB_ICONSTOP "K Studio 正在运行、启动或更新。请正常关闭后重试。"
    SetErrorLevel 5
    Abort
FunctionEnd
Function ${Prefix}AcquireProfileLease
  ; Profiles may intentionally live on another drive behind a compatibility
  ; junction. We never delete profile data, and the app opens this same path.
  ; Reject a reparse lock file itself, not legitimate directory ancestors.
  System::Call 'kernel32::GetFileAttributesW(w "${PROFILE_ROOT}\desktop-instance\.kstudio-runtime.lock") i.r0'
  IntCmp $0 -1 profile_path_ok_${Prefix}
  IntOp $1 $0 & 0x400
  IntCmp $1 0 profile_path_ok_${Prefix}
  SetErrorLevel 2
  Abort
  profile_path_ok_${Prefix}:
  CreateDirectory "${PROFILE_ROOT}\desktop-instance"
  System::Call 'kernel32::CreateFileW(w "${PROFILE_ROOT}\desktop-instance\.kstudio-runtime.lock", i 0xC0000000, i 0, p 0, i 4, i 0x80, p 0) p.r0'
  StrCmp $0 -1 profile_busy_${Prefix}
  StrCpy $ProfileLease $0
  Return
  profile_busy_${Prefix}:
    IfSilent +2
    MessageBox MB_ICONSTOP "K Studio 正在运行。请正常关闭后重试。"
    SetErrorLevel 5
    Abort
FunctionEnd
!macroend
!insertmacro ExclusiveLocks ""
!insertmacro ExclusiveLocks "un."

Function .onInit
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "K Studio R3 需要 64 位 Windows。未更改系统。" /SD IDOK
    SetErrorLevel 2
    Abort
  ${EndIf}
  SetShellVarContext current
  SetRegView 64
  Call AcquireMutex
  Call CheckFixedRoot
  IfFileExists "$INSTDIR\*.*" 0 init_done
  ReadINIStr $0 "$INSTDIR\.kstudio-owner.ini" "Owner" "Product"
  StrCmp $0 "${PRODUCT_ID}" 0 foreign_root
  Call AcquireRootLease
  ; Current release high-water mark is plain JSON integer, also used by the
  ; frozen signed updater. Refuse installer downgrade and malformed pointers.
  ; An interrupted first extraction has an owner marker but no published pointer.
  IfFileExists "$INSTDIR\highest-sequence.json" read_high
  IfFileExists "$INSTDIR\current.json" check_current init_done
  read_high:
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
    IntCmp $1 ${SEQUENCE} check_current check_current downgrade
  check_current:
    ; current is authoritative if a crash occurred before high-water publication.
    IfFileExists "$INSTDIR\current.json" 0 init_done
    FileOpen $0 "$INSTDIR\current.json" r
    StrCpy $4 ""
  pointer_line:
    ClearErrors
    FileRead $0 $1
    IfErrors pointer_read
    StrCpy $4 "$4$1"
    Goto pointer_line
  pointer_read:
    FileClose $0
    ${StrStr} $4 $4 '$\"sequence$\"'
    StrCmp $4 "" foreign_root
    ${StrStr} $4 $4 ":"
    StrCpy $4 $4 "" 1
  pointer_space:
    StrCpy $3 $4 1
    StrCmp $3 " " 0 pointer_number
    StrCpy $4 $4 "" 1
    Goto pointer_space
  pointer_number:
    ; IntOp reads the integer prefix (followed by comma/brace/newline).
    IntOp $4 $4 + 0
    IntCmp $4 0 foreign_root foreign_root
    IntCmp $4 ${SEQUENCE} init_done init_done downgrade
  downgrade:
    MessageBox MB_ICONSTOP "已安装更新的版本。为保护数据与更新信任，本安装包不能降级覆盖。" /SD IDOK
    SetErrorLevel 3
    Abort
  foreign_root:
    MessageBox MB_ICONSTOP "目标目录不是可识别的 K Studio R3 安装，或版本记录异常。没有覆盖该目录。" /SD IDOK
    SetErrorLevel 2
    Abort
  init_done:
    ; Take the root before profile, matching the launcher/updater lock order.
    IfFileExists "$INSTDIR\*.*" 0 +2
    Call AcquireRootLease
    Call AcquireProfileLease
FunctionEnd

!include "${PAYLOAD_INCLUDE}"
Section "K Studio R3（必选）" Main
  SectionIn RO
  SetShellVarContext current
  SetRegView 64
  Call CheckFixedRoot
  IfFileExists "$INSTDIR\versions\${VERSION}\*.*" 0 slot_ready
  ReadINIStr $0 "$INSTDIR\versions\${VERSION}\.kstudio-slot.ini" "Owner" "Product"
  StrCmp $0 "${PRODUCT_ID}" existing_slot
  MessageBox MB_ICONSTOP "版本目录包含不属于本安装器的文件，未覆盖。" /SD IDOK
  SetErrorLevel 2
  Abort
  existing_slot:
  MessageBox MB_ICONSTOP "此版本目录已存在。为保护原程序，本候选版不覆盖修复；请使用更新构建序号的安装包升级。个人数据与原版本已保留。" /SD IDOK
  SetErrorLevel 6
  Abort
  slot_ready:
  CreateDirectory "$INSTDIR"
  Call AcquireRootLease
  CreateDirectory "$INSTDIR\versions\${VERSION}"
  WriteINIStr "$INSTDIR\.kstudio-owner.ini" "Owner" "Product" "${PRODUCT_ID}"
  WriteINIStr "$INSTDIR\versions\${VERSION}\.kstudio-slot.ini" "Owner" "Product" "${PRODUCT_ID}"
  ClearErrors
  !insertmacro InstallPayload
  IfErrors install_failed
  SetOutPath "$INSTDIR"
  File /oname=launch_installed.ps1 "${LAUNCHER_FILE}"
  File /oname=NSIS-LICENSE.txt "${NSIS_LICENSE}"
  IfErrors install_failed
  WriteINIStr "$INSTDIR\versions\${VERSION}\.kstudio-slot.ini" "Owner" "Product" "${PRODUCT_ID}"
  WriteINIStr "$INSTDIR\.kstudio-owner.ini" "Owner" "Product" "${PRODUCT_ID}"
  System::Call 'kernel32::GetCurrentProcessId() i.r1'
  StrCpy $PointerTemp "$INSTDIR\.current.$1.tmp"
  StrCpy $HighestTemp "$INSTDIR\.highest.$1.tmp"
  ClearErrors
  FileOpen $0 "$PointerTemp" w
  IfErrors install_failed
  FileWrite $0 '{$\"version$\":$\"${VERSION}$\",$\"sequence$\":${SEQUENCE},$\"data_schema$\":1}'
  IfErrors install_failed_close
  System::Call 'kernel32::FlushFileBuffers(p r0) i.r1'
  FileClose $0
  StrCmp $1 0 install_failed
  ; Same-volume atomic replacement: failure leaves the old pointer untouched.
  System::Call 'kernel32::MoveFileExW(w "$PointerTemp", w "$INSTDIR\current.json", i 9) i.r1'
  StrCmp $1 0 install_failed
  ; Publish high-water only after current; startup also checks current.sequence.
  ClearErrors
  FileOpen $0 "$HighestTemp" w
  IfErrors highwater_done
  FileWrite $0 "${SEQUENCE}"
  IfErrors highwater_close
  System::Call 'kernel32::FlushFileBuffers(p r0) i.r1'
  FileClose $0
  StrCmp $1 0 highwater_done
  System::Call 'kernel32::MoveFileExW(w "$HighestTemp", w "$INSTDIR\highest-sequence.json", i 9) i.r1'
  StrCmp $1 0 0 highwater_done
  DetailPrint "High-water publication deferred; current.sequence preserves downgrade protection."
  Goto highwater_done
  highwater_close:
  FileClose $0
  highwater_done:
  Delete "$HighestTemp"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
  CreateShortcut "$SMPROGRAMS\${PRODUCT_NAME}\K Studio.lnk" "$SYSDIR\WindowsPowerShell\v1.0\powershell.exe" '-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "$INSTDIR\launch_installed.ps1" -InstallRoot "$INSTDIR" -DataDir "${PROFILE_ROOT}"' "$INSTDIR\versions\${VERSION}\KStudio.exe" 0 SW_SHOWMINIMIZED
  CreateShortcut "$SMPROGRAMS\${PRODUCT_NAME}\卸载.lnk" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_ID}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_ID}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_ID}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_ID}" "UninstallString" '$\"$INSTDIR\Uninstall.exe$\"'
  ; _?= must be last and unquoted; makes silent invocation wait for the actual
  ; uninstaller and preserve refusal exit codes instead of a detached stub.
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_ID}" "QuietUninstallString" '$\"$INSTDIR\Uninstall.exe$\" /S _?=$INSTDIR'
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_ID}" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_ID}" "NoRepair" 1
  Goto install_done
  install_failed_close:
    FileClose $0
  install_failed:
    Delete "$PointerTemp"
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
  Call un.AcquireMutex
  Call un.CheckFixedRoot
  ReadINIStr $0 "$INSTDIR\.kstudio-owner.ini" "Owner" "Product"
  StrCmp $0 "${PRODUCT_ID}" un_owned
  SetErrorLevel 2
  Abort
  un_owned:
    Call un.AcquireRootLease
    Call un.AcquireProfileLease
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
