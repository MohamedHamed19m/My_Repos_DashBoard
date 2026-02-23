"""Custom commands API endpoints for managing and running repo-specific commands."""

from __future__ import annotations

import json
import os
import subprocess

from fastapi import APIRouter, HTTPException

from ..core.config import COMMANDS_FILE, BASE_PATH
from ..models.schemas import CommandsBody, RunCommandBody

router = APIRouter(tags=["commands"])


def load_commands() -> dict:
    """Load commands from the commands.json file."""
    try:
        if os.path.exists(COMMANDS_FILE):
            with open(COMMANDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_commands(data: dict):
    """Save commands to the commands.json file."""
    with open(COMMANDS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


@router.get("/commands/{name}")
def get_commands(name: str):
    """Get saved commands for a repo."""
    all_cmds = load_commands()
    return {"commands": all_cmds.get(name, [])}


@router.post("/commands/{name}")
def set_commands(name: str, body: CommandsBody):
    """Save commands for a repo."""
    all_cmds = load_commands()
    all_cmds[name] = body.commands
    save_commands(all_cmds)
    return {"success": True}


@router.post("/commands/{name}/run")
def run_command(name: str, body: RunCommandBody):
    """Run a shell command inside a repo directory."""
    repo_path = os.path.join(BASE_PATH, name)
    if not os.path.isdir(repo_path):
        raise HTTPException(404, "Repo not found")
    try:
        result = subprocess.run(
            body.cmd,
            cwd=repo_path,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        out = result.stdout or result.stderr or "(no output)"
        return {"success": result.returncode == 0, "output": out, "returncode": result.returncode}
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "Command timed out after 60s"}
    except Exception as e:
        return {"success": False, "output": str(e)}
