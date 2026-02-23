"""Git utility functions for running git commands."""

from __future__ import annotations

import os
import subprocess
from typing import Optional, Tuple


def run_git(args: list, cwd: str, timeout: int = 10) -> Optional[str]:
    """Run a git command. Returns stdout string or None on failure."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception:
        return None


def run_git_out(args: list, cwd: str, timeout: int = 10) -> Tuple[bool, str]:
    """Run a git command. Returns (success, output) always."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = result.stdout.strip() or result.stderr.strip()
        return result.returncode == 0, out
    except Exception as e:
        return False, str(e)


def get_branch_sha(branch: str, cwd: str, short: bool = False) -> str:
    """Get the SHA of a branch."""
    args = ["rev-parse"]
    if short:
        args.append("--short")
    args.append(branch)
    return run_git(args, cwd) or ""


def get_worktree_age(path: str) -> str:
    """Get the age of a worktree path as a human-readable string."""
    try:
        import time
        age_seconds = time.time() - os.path.getmtime(path)
        if age_seconds < 3600:
            return f"{int(age_seconds / 60)}m"
        elif age_seconds < 86400:
            return f"{int(age_seconds / 3600)}h"
        elif age_seconds < 604800:
            return f"{int(age_seconds / 86400)}d"
        else:
            return f"{int(age_seconds / 604800)}w"
    except OSError:
        return "?"
