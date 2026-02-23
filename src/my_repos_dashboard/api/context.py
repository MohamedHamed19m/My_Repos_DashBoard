"""Context capture API endpoints for storing and retrieving developer context."""

from __future__ import annotations

import json
import os
import shutil
import subprocess

from fastapi import APIRouter, HTTPException

from ..core.config import BASE_PATH
from ..models.schemas import ScratchpadBody

router = APIRouter(tags=["context"])

# Storage directory outside of repos
CONTEXT_DIR = os.path.join(BASE_PATH, ".my_dashboard", "repos")

# Prompt for Claude to analyze repo state
CAPTURE_PROMPT = """You are capturing context for a developer returning to this codebase.

Analyze the current state and provide a concise summary in JSON format:
{
  "focusedFile": "path/to/file",
  "summary": "2-3 sentence summary of what's happening",
  "nextStep": "Specific next action to continue"
}

Look at:
- Recent git log (last 3-5 commits)
- Current branch and status
- Recently modified files
- Any TODO comments or incomplete work

Be specific and brief. Focus on what a developer needs to know to continue."""


def get_context_path(name: str) -> str:
    """Get the context directory path for a repo."""
    return os.path.join(CONTEXT_DIR, name)


def get_context_file(name: str) -> str:
    """Get the context.json file path for a repo."""
    return os.path.join(get_context_path(name), "context.json")


def get_scratchpad_file(name: str) -> str:
    """Get the scratch.md file path for a repo."""
    return os.path.join(get_context_path(name), "scratch.md")


@router.get("/repo/{name}/last-session")
def get_last_session(name: str):
    """Get the last captured context for a repo."""
    context_file = get_context_file(name)
    if not os.path.exists(context_file):
        return {"context": None}

    try:
        with open(context_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {"context": data}
    except Exception:
        return {"context": None}


@router.post("/repo/{name}/capture-context")
def capture_context(name: str):
    """Capture context using Claude to analyze repo state."""
    repo_path = os.path.join(BASE_PATH, name)
    if not os.path.isdir(repo_path):
        raise HTTPException(404, "Repo not found")

    # Ensure context directory exists
    context_path = get_context_path(name)
    os.makedirs(context_path, exist_ok=True)

    # Check if git repo
    if not os.path.exists(os.path.join(repo_path, ".git")):
        raise HTTPException(400, "Not a git repository")

    # Find claude executable with fallback
    claude_exe = shutil.which("claude")
    if not claude_exe:
        # Fallback to npm global install path on Windows
        user_home = os.path.expanduser("~")
        npm_claude = os.path.join(user_home, "AppData", "Roaming", "npm", "claude.cmd")
        if os.path.exists(npm_claude):
            claude_exe = npm_claude
        else:
            raise HTTPException(
                400,
                "Claude CLI not found. Please install from https://claude.ai/code "
                "and ensure it's in your PATH, or install via npm: npm install -g @anthropic-ai/claude-cli"
            )

    try:
        # Run claude command with timeout
        import sys
        is_windows = sys.platform == "win32"

        if is_windows:
            # On Windows with shell=True, must pass a string not a list.
            # Use subprocess.list2cmdline to safely quote arguments.
            cmd = subprocess.list2cmdline([claude_exe, "-p", CAPTURE_PROMPT])
        else:
            cmd = [claude_exe, "-p", CAPTURE_PROMPT]

        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60,
            shell=is_windows,
        )

        if result.returncode != 0:
            error_msg = result.stderr or "Claude command failed"
            raise HTTPException(500, f"Claude error: {error_msg}")

        # Parse the JSON response
        output = result.stdout.strip()
        try:
            context_data = json.loads(output)
        except json.JSONDecodeError:
            # Try to extract JSON from the output
            import re
            json_match = re.search(r'\{[^{}]*"focusedFile"[^{}]*\}', output, re.DOTALL)
            if json_match:
                context_data = json.loads(json_match.group(0))
            else:
                raise HTTPException(500, "Failed to parse Claude response as JSON")

        # Add timestamp
        from datetime import datetime
        context_data["capturedAt"] = datetime.now().isoformat()

        # Save to context.json
        context_file = get_context_file(name)
        with open(context_file, "w", encoding="utf-8") as f:
            json.dump(context_data, f, indent=2)

        return {"success": True, "context": context_data}

    except subprocess.TimeoutExpired:
        raise HTTPException(500, "Claude command timed out after 60s")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Capture failed: {str(e)}")


@router.get("/repo/{name}/scratchpad")
def get_scratchpad(name: str):
    """Get the scratchpad content for a repo."""
    scratchpad_file = get_scratchpad_file(name)
    if not os.path.exists(scratchpad_file):
        return {"content": ""}

    try:
        with open(scratchpad_file, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content}
    except Exception:
        return {"content": ""}


@router.post("/repo/{name}/scratchpad")
def save_scratchpad(name: str, body: ScratchpadBody):
    """Save the scratchpad content for a repo."""
    context_path = get_context_path(name)
    os.makedirs(context_path, exist_ok=True)

    scratchpad_file = get_scratchpad_file(name)
    with open(scratchpad_file, "w", encoding="utf-8") as f:
        f.write(body.content)

    return {"success": True}


__all__ = ["router"]