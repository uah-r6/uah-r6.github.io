@echo off
setlocal
set "NECC_LAUNCHER_ENTRY=%~f0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1"
if errorlevel 1 pause
