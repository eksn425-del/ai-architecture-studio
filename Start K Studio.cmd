@echo off
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
  py -3 scripts\start.py
) else (
  python scripts\start.py
)
if errorlevel 1 (
  echo.
  echo Startup failed. Install Python 3.11 or newer with PATH enabled, then try again.
  pause
)
