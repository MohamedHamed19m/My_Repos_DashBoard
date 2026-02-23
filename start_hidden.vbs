' Helper script to run command completely hidden
Set objShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script is located
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
logFile = fso.BuildPath(scriptDir, "dashboard.log")

' Build command: use UV directly (assumes UV is in PATH)
command = "cmd /c cd /d """ & scriptDir & """ && uv run my-repos-dashboard --reload --host 127.0.0.1 --port 8000 > """ & logFile & """ 2>&1"

' Run the command hidden (0 = hide window)
objShell.Run command, 0, False
