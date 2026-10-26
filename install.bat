@echo off
setlocal

echo === Antigravity Discord RPC Setup (Windows) ===

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    pause
    exit /b 1
)

set SCRIPT_DIR=%~dp0
echo Project directory: %SCRIPT_DIR%

echo.
echo Configuring Antigravity hooks...
python "%SCRIPT_DIR%setup_hooks.py" --global

echo.
echo Checking Discord connection...
python "%SCRIPT_DIR%main.py" --test

echo.
echo Setup complete!
echo To run the daemon in the background on Windows:
echo   pythonw "%SCRIPT_DIR%main.py"
echo (You can add a shortcut to pythonw main.py in your shell:startup folder)

pause
