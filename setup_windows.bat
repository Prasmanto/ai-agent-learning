@echo off
echo ========================================
echo UnixPunks Hunter - Windows Setup
echo ========================================
echo.

echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo.
echo Installing required packages...
pip install requests

if %errorlevel% neq 0 (
    echo ERROR: Failed to install packages
    pause
    exit /b 1
)

echo.
echo ========================================
echo Setup complete! 
echo ========================================
echo.
echo To run the hunter:
echo   python unixpunks_hunter_windows.py
echo.
echo Optional: Create proxies.txt with your proxy list
echo Format: host:port:username:password (one per line)
echo.
pause