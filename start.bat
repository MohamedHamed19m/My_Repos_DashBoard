@echo off
REM Worktree Dashboard Launcher
setlocal
set "DIR=%~dp0"
set "DIR=%DIR:~0,-1%"

echo.
echo   Worktree Dashboard
echo   ==================
echo.

REM Check if uv is available, fall back to plain uvicorn
where uv >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo [1/3] Starting backend with uv...
    start /B uv run --with fastapi --with uvicorn uvicorn main:app --app-dir "%DIR%" --host 127.0.0.1 --port 8000 > "%DIR%\server.log" 2>&1
) else (
    echo [1/3] Starting backend with uvicorn...
    start /B uvicorn main:app --app-dir "%DIR%" --host 127.0.0.1 --port 8000 > "%DIR%\server.log" 2>&1
)

REM Wait for server to be ready (poll instead of fixed sleep)
echo [2/3] Waiting for server...
:WAIT_LOOP
timeout /t 1 /nobreak >nul
curl -s http://127.0.0.1:8000/projects >nul 2>&1
if %ERRORLEVEL% NEQ 0 goto WAIT_LOOP

echo        Server ready on http://127.0.0.1:8000
echo.

REM Open dashboard
echo [3/3] Opening dashboard...
start "" "%DIR%\index.html"
echo        Done!
echo.
echo   Press any key to stop the server and exit.
echo.

pause >nul

REM Kill uvicorn on exit
taskkill /F /IM uvicorn.exe >nul 2>&1
echo   Server stopped.