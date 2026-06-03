@echo off
title Thesis Library Server
echo ----------------------------------------------------
echo         THESIS LIBRARY SYSTEM - START UP
echo ----------------------------------------------------
echo.

:: Ensure the script runs in the directory where it is located
cd /d "%~dp0"

echo Checking for Python...

set PYTHON_CMD=
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
    echo [INFO] Found Python Launcher [py]
) else (
    python --version >nul 2>&1
    if %errorlevel% equ 0 (
        set PYTHON_CMD=python
        echo [INFO] Found Python [python]
    )
)

if not defined PYTHON_CMD (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python from python.org before running this.
    echo.
    echo TIP: If Python is installed, search "App execution aliases" in Windows Settings
    echo and toggle OFF the aliases for "python.exe" and "python3.exe".
    pause
    exit /b 1
)

:: Sync IP to .env file and detect IP robustly
echo Detecting System IP...
for /f "tokens=*" %%i in ('%PYTHON_CMD% update_env_ip.py') do set IP=%%i

if not defined IP (
    set IP=127.0.0.1
)

:: Check if MySQL (MariaDB) is running
echo Checking database connection...
%PYTHON_CMD% db_timeout.py
if %errorlevel% neq 0 (
    echo.
    echo ====================================================
    echo [CRITICAL ERROR] MySQL [XAMPP] is NOT running!
    echo Please open the XAMPP Control Panel and start MySQL.
    echo ====================================================
    echo.
    pause
    exit /b 1
)

echo.
echo ====================================================
echo SYSTEM IS NOW LIVE!
echo.
echo Main IP Address: %IP%
echo Clients can connect at: http://%IP%:8000
echo.
echo [KEEP THIS WINDOW OPEN WHILE SYSTEM IS IN USE]
echo ====================================================
echo.

:: Start the Django server
%PYTHON_CMD% manage.py runserver 0.0.0.0:8000

if %errorlevel% neq 0 (
    echo.
    echo [CRITICAL ERROR] The server failed to start.
    pause
)
