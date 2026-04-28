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
echo  Copying server files to dist\...
echo  ==========================================

:: Copy required files alongside the .exe
copy /Y "server.js" "dist\" >nul
copy /Y "package.json" "dist\" >nul
if exist "package-lock.json" copy /Y "package-lock.json" "dist\" >nul
copy /Y "blb-stock-dashboard.html" "dist\" >nul
copy /Y "blb-request-dashboard.html" "dist\" >nul
if exist ".env" copy /Y ".env" "dist\" >nul
if exist ".env.example" copy /Y ".env.example" "dist\" >nul

:: Copy node_modules (if exists - to skip npm install on target)
if exist "node_modules\" (
    echo  Copying node_modules...
    xcopy /E /I /Q /Y "node_modules" "dist\node_modules" >nul
)

echo.
echo  ==========================================
echo    Build successful!
echo  ==========================================
echo.
echo  Output folder: dist\
echo  Run: dist\BMS-BLB-Stock.exe
echo.
echo  Files in dist\:
dir /B dist
echo.
echo  Distribute the entire 'dist' folder.
echo  Target machine needs Node.js installed.
echo  ==========================================
echo.

pause
