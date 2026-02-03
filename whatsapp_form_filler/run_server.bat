@echo off
title WhatsApp Form Filler Server
color 0A

cd /d "%~dp0"

:loop
cls
echo ============================================================
echo   WhatsApp Form Filler Server - ALWAYS ON
echo   Started at: %time%
echo ============================================================
echo.
echo Running monitor...
echo.

.\venv\Scripts\python.exe watch_whatsapp.py

echo.
echo ============================================================
echo   WARNING: Script crashed or stopped!
echo   Restarting in 10 seconds...
echo ============================================================
timeout /t 10
goto loop
