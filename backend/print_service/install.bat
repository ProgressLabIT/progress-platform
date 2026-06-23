@echo off
setlocal EnableDelayedExpansion

REM ── Progress Print Service Installer ──────────────────────────────────────
REM Run this script as Administrator (right-click > Run as administrator).

REM ── require administrator ──────────────────────────────────────────────────
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This script must be run as Administrator.
    echo Right-click install.bat and select "Run as administrator".
    exit /b 1
)

REM ── check Python ──────────────────────────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: python not found in PATH. Install Python 3.11+ from python.org and re-run install.bat
    echo Make sure to check "Add Python to PATH" and use "Install for all users" during Python setup.
    exit /b 1
)

REM ── install dependencies ──────────────────────────────────────────────────
echo Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: pip install failed. Check your Python/pip installation.
    exit /b 1
)

REM ── pre-flight: parse API URL from .env ───────────────────────────────────
set "API_URL="
if not exist ".env" (
    echo ERROR: .env file not found.
    echo Copy .env.example to .env and fill in your API URL.
    exit /b 1
)
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if /i "%%A"=="PROGRESS_PRINT_SERVICE_API_URL" set "API_URL=%%B"
)
if "!API_URL!"=="" (
    echo ERROR: PROGRESS_PRINT_SERVICE_API_URL not found in .env
    echo Copy .env.example to .env and fill in your API URL.
    exit /b 1
)

REM ── pre-flight: connectivity check ────────────────────────────────────────
echo Checking API connectivity at !API_URL!/health ...
curl.exe --silent --fail --max-time 10 "!API_URL!/health" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: API unreachable at !API_URL!/health -- check PROGRESS_PRINT_SERVICE_API_URL in .env
    exit /b 1
)
echo API connectivity OK.

REM ── register Windows Service ──────────────────────────────────────────────
echo Registering Windows Service...
print-service.exe install
if %errorlevel% neq 0 (
    echo ERROR: Service registration failed.
    exit /b 1
)

echo.
echo SUCCESS: Progress Print Service installed and will start automatically on boot.
echo To start it now: print-service.exe start
endlocal
