@echo off
REM Beancount Daily Startup - Windows Batch File
REM Double-click this file to start Beancount quickly

echo 💰 Starting Beancount in WSL...
echo.

REM Check if WSL is available
wsl --list >nul 2>&1
if errorlevel 1 (
    echo ❌ WSL is not available or not running
    echo Please install WSL or check your installation
    pause
    exit /b 1
)

REM Start WSL and run the startup script
echo 🐧 Opening WSL and starting Beancount...
echo 📊 Your browser should automatically open to http://localhost:5000
echo 🛑 Close this window when you're done using Beancount
echo.

wsl -d Ubuntu cd ~ ^&^& ./start-beancount.sh

echo.
echo Beancount session ended.
pause