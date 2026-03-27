@echo off
setlocal

REM ── Progress Print Service Uninstaller ────────────────────────────────────
REM Run this script as Administrator (right-click > Run as administrator).

REM ── require administrator ──────────────────────────────────────────────────
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This script must be run as Administrator.
    echo Right-click uninstall.bat and select "Run as administrator".
    exit /b 1
)

REM ── stop then uninstall ───────────────────────────────────────────────────
echo Stopping Progress Print Service...
print-service.exe stop
REM Stop may return non-zero if service is already stopped — not fatal

echo Removing Windows Service registration...
print-service.exe uninstall
if %errorlevel% neq 0 (
    echo ERROR: Service removal failed. The service may not be registered.
    exit /b 1
)

echo.
echo SUCCESS: Progress Print Service removed.
endlocal
