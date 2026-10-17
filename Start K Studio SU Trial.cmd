@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -File "%~dp0scripts\start_su_trial.ps1"
if errorlevel 1 pause
