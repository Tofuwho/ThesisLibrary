@echo off
:: ==============================================================================
# ThesisLibrary Backup Runner
# ==============================================================================
# This batch script runs the PowerShell backup script with ExecutionPolicy bypass.
# Run this file as Administrator, or schedule it in Windows Task Scheduler.
# ==============================================================================

cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File .\backup.ps1
pause
