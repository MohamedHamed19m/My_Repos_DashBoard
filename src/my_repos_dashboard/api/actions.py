"""Action endpoints for opening files, directories, and running basic git actions."""

from __future__ import annotations

import os
import subprocess

from fastapi import APIRouter

from ..core.config import BASE_PATH
from ..core.git_utils import run_git_out

router = APIRouter(tags=["actions"])


@router.get("/open/{name}")
def open_vscode(name: str):
    """Open a repository in VS Code."""
    full_path = os.path.join(BASE_PATH, name)
    subprocess.Popen(["code", full_path], shell=True)
    return {"message": f"Opening {name}"}


@router.get("/open-terminal/{name}")
def open_terminal(name: str):
    """Open a PowerShell terminal in the repository directory."""
    full_path = os.path.join(BASE_PATH, name)
    subprocess.Popen(["start", "powershell", "-NoExit", "-Command", f"Set-Location '{full_path}'"], shell=True)
    return {"message": f"Opening terminal in {name}"}


@router.get("/open-worktree")
def open_worktree_path(path: str):
    """Open a worktree path in VS Code."""
    subprocess.Popen(["code", path], shell=True)
    return {"message": f"Opening {path}"}


@router.get("/readme/{name}")
def get_readme(name: str):
    """Fetch the README.md content for a repository."""
    full_path = os.path.join(BASE_PATH, name)
    for file in os.listdir(full_path):
        if file.lower() == "readme.md":
            with open(os.path.join(full_path, file), "r", encoding="utf-8") as f:
                return {"content": f.read()}
    return {"content": "No README.md found in this repo."}


@router.post("/git/{name}/{action}")
def git_action(name: str, action: str):
    """Run a basic git action (pull, fetch, stash, stash-pop, reset, clean, log)."""
    full_path = os.path.join(BASE_PATH, name)
    commands = {
        "pull": ["pull"],
        "fetch": ["fetch", "--all"],
        "stash": ["stash"],
        "stash-pop": ["stash", "pop"],
        "reset": ["reset", "--hard", "HEAD"],
        "clean": ["clean", "-fd"],
        "log": ["log", "--oneline", "-10"],
    }
    if action not in commands:
        return {"success": False, "output": "Unknown action"}
    ok, out = run_git_out(commands[action], full_path, timeout=30)
    return {"success": ok, "output": out}
