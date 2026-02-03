@echo off
REM WhatsApp Form Auto-Fill System - Quick Start Script
REM Usage: run.bat <form_url>

cd /d "%~dp0"

if "%~1"=="" (
    echo.
    echo Usage: run.bat ^<form_url^>
    echo.
    echo Example:
    echo   run.bat "https://forms.office.com/Pages/..."
    echo.
    pause
    exit /b 1
)

echo ============================================================
echo WhatsApp Form Auto-Fill System
echo ============================================================
echo.

REM Close Chrome if running
taskkill /F /IM chrome.exe 2>nul

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Run the system
.\venv\Scripts\python.exe main.py %1

echo.
echo ============================================================
echo Done!
echo ============================================================
pause
