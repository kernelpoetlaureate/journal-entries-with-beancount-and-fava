@echo off
REM Beancount Setup - Windows Batch File
REM Run this once to set up Beancount

echo 🚀 Setting up Beancount environment...
echo This is a one-time setup that may take several minutes.
echo.

REM Check if WSL is available
wsl --list >nul 2>&1
if errorlevel 1 (
    echo ❌ WSL is not available or not running
    echo Please install WSL first: https://docs.microsoft.com/en-us/windows/wsl/install
    pause
    exit /b 1
)

echo 🐧 Starting WSL setup...
echo Please wait while we install Beancount...
echo.

REM Copy the setup script to WSL and run it
wsl -d Ubuntu bash -c "cd ~ && cp /mnt/c/Users/giorgi/Downloads/beancount/setup.sh . && chmod +x setup.sh && ./setup.sh"

if errorlevel 1 (
    echo.
    echo ❌ Setup failed! Please check the error messages above.
    echo You may need to run the setup manually in WSL.
    pause
    exit /b 1
)

echo.
echo ✅ Setup completed successfully!
echo.
echo 📋 Next steps:
echo 1. Double-click 'start-beancount.bat' to start using Beancount
echo 2. Edit your ledger file in VS Code or any text editor
echo 3. Access the web interface at http://localhost:5000
echo.
pause