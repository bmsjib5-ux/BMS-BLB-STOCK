@echo off
chcp 65001 >nul 2>&1
title Build BMS Blood Stock Launcher

echo.
echo  ==========================================
echo    Build BMS Blood Stock Launcher to .exe
echo  ==========================================
echo.

cd /d "%~dp0"

:: Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python not found!
    echo  Please install Python from https://python.org
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version') do echo  Python: %%v

:: Install pyinstaller if needed
echo.
echo  Checking PyInstaller...
python -m pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo  Installing PyInstaller...
    python -m pip install --upgrade pip
    python -m pip install pyinstaller
)

:: Clean previous builds
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "launcher.spec" del /q "launcher.spec"

echo.
echo  Building launcher.exe...
echo  ==========================================

python -m PyInstaller ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name "BMS-BLB-Stock" ^
    --collect-all tkinter ^
    launcher.py

if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo  ==========================================
echo    Build successful!
echo  ==========================================
echo.
echo  Output: dist\BMS-BLB-Stock.exe
echo.
echo  Note: The .exe is a launcher only.
echo  You still need:
echo    - Node.js installed on the target machine
echo    - server.js, package.json, *.html in the same folder as .exe
echo.
echo  Files needed alongside the .exe:
echo    - server.js
echo    - package.json
echo    - blb-stock-dashboard.html
echo    - blb-request-dashboard.html
echo    - .env (optional, for default DB config)
echo  ==========================================
echo.

pause
