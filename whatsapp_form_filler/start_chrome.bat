@echo off
REM ============================================================
REM Start Chrome in Debug Mode
REM This allows Playwright to connect without closing Chrome
REM ============================================================

echo ============================================================
echo Starting Chrome with Remote Debugging
echo ============================================================
echo.

REM Close existing Chrome instances
echo Closing existing Chrome instances...
taskkill /F /IM chrome.exe /T 2>nul
timeout /t 1 /nobreak >nul
taskkill /F /IM chrome.exe /T 2>nul

echo Starting Chrome in debug mode...
echo.

REM Find Chrome
set "CHROME_PATH="

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe"
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
) else if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
)

if "%CHROME_PATH%"=="" (
    echo.
    echo ERROR: Chrome not found automatically!
    echo.
    echo Please manually edit this file and set the path to chrome.exe
    pause
    exit /b 1
)

echo Found Chrome at: "%CHROME_PATH%"
echo.
echo Chrome will open with:
echo   - Remote debugging enabled (port 9222)
echo   - Your normal profile
echo.

REM Start Chrome
start "" "%CHROME_PATH%" --remote-debugging-port=9222 --user-data-dir="%LOCALAPPDATA%\Google\Chrome\User Data"

echo.
echo ============================================================
echo Chrome launched! 
echo Please check if you see the "Controlled by automated software" bar.
echo Port: 9222
echo ============================================================
echo.
echo Press any key to stop Chrome (this will close everything)
pause >nul

REM When user presses key, close Chrome
taskkill /F /IM chrome.exe /T
