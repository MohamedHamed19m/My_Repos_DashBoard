@echo off
REM My Repos Dashboard Launcher - Starts server in hidden background
setlocal
set "DIR=%~dp0"
set "DIR=%DIR:~0,-1%"
set "PID_FILE=%DIR%\.dashboard.pid"

echo.
echo   My Repos Dashboard
echo   ===================
echo.

REM Check if .venv exists, if not create it
if not exist "%DIR%\.venv" (
    echo No virtual environment found. Creating one...
    cd /d "%DIR%"
    uv venv
    if errorlevel 1 (
        echo.
        echo Failed to create virtual environment!
        ping 127.0.0.1 -n 4 >nul
        exit
    )
)

REM Check if already running
if exist "%PID_FILE%" (
    set /p DASH_PID=<"%PID_FILE%"
    tasklist /FI "PID eq %DASH_PID%" 2>nul | find /I /N "python.exe">nul
    if not errorlevel 1 (
        echo   Dashboard is already running! PID: %DASH_PID%
        echo   Use stop.bat to stop it first.
        ping 127.0.0.1 -n 4 >nul
        exit
    )
    del "%PID_FILE%" 2>nul
)

REM Start the server using VBScript (completely hidden)
echo   Starting dashboard in background...
echo   Server: http://127.0.0.1:8000
echo   Log file: %DIR%\dashboard.log
echo.

start "" wscript.exe "%DIR%\start_hidden.vbs"

REM Wait for server to start and capture PID
ping 127.0.0.1 -n 4 >nul

REM Find the PID and save it
for /f "tokens=2" %%a in ('tasklist ^| findstr /i "python.exe"') do (
    set "DASH_PID=%%a"
    goto :found_pid
)

:found_pid
if defined DASH_PID (
    echo %DASH_PID% > "%PID_FILE%"
    echo   Started! PID: %DASH_PID%
    echo   Use stop.bat to stop the server.
) else (
    echo   Warning: Could not determine PID.
    echo   Check dashboard.log for errors.
)

echo.
echo   Server is running in BACKGROUND.
echo   You can close this window safely.
echo.
ping 127.0.0.1 -n 3 >nul
exit
