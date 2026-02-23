' Helper script to run command completely hidden
Set objShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script is located
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Build the command
command = "cmd /c cd /d """ & scriptDir & """ && call .venv\Scripts\activate.bat && uv run --no-sync uvicorn my_repos_dashboard.main:app --reload --host 0.0.0.0 --port 8000 > """ & scriptDir & "\dashboard.log"" 2>&1"

' Run the command hidden (0 = hide window)
objShell.Run command, 0, False
