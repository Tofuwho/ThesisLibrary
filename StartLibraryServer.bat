@echo off
title Thesis Library Server
echo ----------------------------------------------------
echo         THESIS LIBRARY SYSTEM - START UP
echo ----------------------------------------------------
echo.
echo Checking for Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python from python.org before running this.
    pause
    exit
)

:: Auto-detect the local IPv4 address
echo Detecting System IP...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| find "IPv4 Address"') do (
    set IP=%%a
)

:: Trim leading space
if defined IP (
    set IP=%IP:~1%
) else (
    set IP=127.0.0.1
    echo [WARNING] Could not detect LAN IP. Using Localhost.
)

echo.
echo ====================================================
echo SYSTEM IS NOW LIVE!
echo.
echo Main IP Address: %IP%
echo Clients can connect at: http://%IP%:8000
echo.
echo (KEEP THIS WINDOW OPEN WHILE SYSTEM IS IN USE)
echo ====================================================
echo.

:: Start the Django server
python manage.py runserver 0.0.0.0:8000

if %errorlevel% neq 0 (
    echo.
    echo [CRITICAL ERROR] The server failed to start.
    echo Check if MySQL (XAMPP) is running!
    pause
)
