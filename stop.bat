@echo off
REM My Repos Dashboard Stop Script
setlocal
set "DIR=%~dp0"
set "DIR=%DIR:~0,-1%"
set "PID_FILE=%DIR%\.dashboard.pid"

echo.
echo   Stopping My Repos Dashboard...
echo.

set "KILLED=0"

REM Kill ALL python processes (aggressive approach)
taskkill /F /IM python.exe >nul 2>&1
if not errorlevel 1 (
    echo   Killed all python processes
    set "KILLED=1"
)

REM Also try to kill uvicorn
taskkill /F /IM uvicorn.exe >nul 2>&1
if not errorlevel 1 (
    echo   Killed uvicorn process
    set "KILLED=1"
)

REM Clean up PID file
if exist "%PID_FILE%" del "%PID_FILE%" 2>nul

if "%KILLED%"=="1" (
    echo.
    echo   Done! Dashboard server has been stopped.
) else (
    echo   No running dashboard server found.
)

echo.
ping 127.0.0.1 -n 2 >nul
exit
