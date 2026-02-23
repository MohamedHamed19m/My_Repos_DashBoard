@echo off
REM My Repos Dashboard Restart Script
setlocal

echo.
echo   Restarting My Repos Dashboard...
echo.

REM Stop the server
set "DIR=%~dp0"
set "DIR=%DIR:~0,-1%"
set "PID_FILE=%DIR%\.dashboard.pid"

set "KILLED=0"
if exist "%PID_FILE%" (
    set /p DASH_PID=<"%PID_FILE%"
    if defined DASH_PID (
        tasklist /FI "PID eq %DASH_PID%" 2>nul | find /I /N "python.exe">nul
        if not errorlevel 1 (
            taskkill /F /PID %DASH_PID% >nul 2>&1
            echo   Stopped dashboard process %DASH_PID%
            set "KILLED=1"
        )
    )
    del "%PID_FILE%" 2>nul
)

if "%KILLED%"=="0" (
    for /f "tokens=2" %%a in ('tasklist ^| findstr /i "python.exe"') do (
        wmic process where "ProcessId=%%a" get CommandLine 2>nul | findstr /i "my_repos_dashboard" >nul
        if not errorlevel 1 (
            taskkill /F /PID %%a >nul 2>&1
            echo   Stopped dashboard process %%a
            set "KILLED=1"
        )
    )
)

echo.
ping 127.0.0.1 -n 2 >nul

REM Start the server
call "%~dp0start.bat"

