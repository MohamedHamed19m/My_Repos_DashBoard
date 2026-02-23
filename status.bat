@echo off
REM My Repos Dashboard Status Check
setlocal
set "DIR=%~dp0"
set "DIR=%DIR:~0,-1%"
set "PID_FILE=%DIR%\.dashboard.pid"

echo.
echo   My Repos Dashboard Status
echo   ==========================
echo.

set "RUNNING=0"
set "DASH_PID="

REM Check PID file first
if exist "%PID_FILE%" (
    set /p DASH_PID=<"%PID_FILE%"
    if defined DASH_PID (
        tasklist /FI "PID eq %DASH_PID%" 2>nul | find /I /N "python.exe">nul
        if not errorlevel 1 (
            set "RUNNING=1"
        )
    )
)

REM If not found via PID, search for it
if "%RUNNING%"=="0" (
    for /f "tokens=2" %%a in ('tasklist ^| findstr /i "python.exe"') do (
        wmic process where "ProcessId=%%a" get CommandLine 2>nul | findstr /i "my_repos_dashboard" >nul
        if not errorlevel 1 (
            set "DASH_PID=%%a"
            set "RUNNING=1"
            goto :found
        )
    )
)

:found
if "%RUNNING%"=="1" (
    echo   [RUNNING] Dashboard is active
    echo   PID: %DASH_PID%
    echo   URL: http://127.0.0.1:8000
    echo   Log: %DIR%\dashboard.log
) else (
    echo   [STOPPED] Dashboard is not running
    echo.
    echo   To start: double-click start.bat
)

echo.
echo Press any key to close...
pause >nul
exit
