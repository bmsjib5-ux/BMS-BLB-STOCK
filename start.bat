@echo off
chcp 65001 >nul 2>&1
title BMS Blood Stock - API Server

echo.
echo  ==========================================
echo    BMS Blood Stock - API Server
echo  ==========================================
echo.

cd /d "%~dp0"

:: Check Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Node.js not found!
    echo  Please install Node.js from https://nodejs.org
    echo.
    pause
    exit /b 1
)

:: Show Node version
for /f "tokens=*" %%v in ('node -v') do echo  Node.js : %%v

:: Install dependencies if needed
if not exist "node_modules\" (
    echo.
    echo  Installing dependencies...
    npm install
    echo.
)

echo.
echo  Starting server...
echo  Dashboard : http://localhost:3000
echo  Press Ctrl+C to stop
echo  ==========================================
echo.

node server.js

pause
