"""Git-specific API endpoints for log, branches, recent files, and details."""

from __future__ import annotations

import os

from fastapi import APIRouter

from ..core.config import BASE_PATH
from ..core.git_utils import run_git

router = APIRouter(tags=["git"])


@router.get("/git/{name}/log")
def git_log(name: str, limit: int = 20):
    """Get git log as structured data."""
    full_path = os.path.join(BASE_PATH, name)
    log_output = run_git(["log", f"-{limit}", "--pretty=format:%H|||%s|||%cr|||%an"], full_path)
    if not log_output:
        return {"commits": []}

    commits = []
    for line in log_output.splitlines():
        parts = line.split("|||")
        if len(parts) == 4:
            commits.append({
                "hash": parts[0][:7],
                "message": parts[1],
                "date": parts[2],
                "author": parts[3],
            })
    return {"commits": commits}


@router.get("/git/{name}/branches")
def git_branches(name: str, limit: int = 5):
    """Get the latest git branches as structured data."""
    full_path = os.path.join(BASE_PATH, name)
    branch_output = run_git(["branch", f"-{limit}"], full_path)
    if not branch_output:
        return {"branches": []}

    branches = []
    for line in branch_output.splitlines():
        line = line.strip()
        if not line:
            continue
        is_current = line.startswith("*")
        branch_name = line.lstrip("*").strip()
        branches.append({
            "name": branch_name,
            "is_current": is_current
        })
    return {"branches": branches}


@router.get("/git/{name}/recent-files")
def git_recent_files(name: str, depth: int = 1):
    """Return files changed in the last N commits, with change type (M/A/D/R)."""
    full_path = os.path.join(BASE_PATH, name)
    if not os.path.isdir(os.path.join(full_path, ".git")):
        return {"files": []}
    out = run_git(["diff", "--name-status", f"HEAD~{depth}..HEAD"], full_path) or ""
    if not out:
        # Fewer than depth commits — diff from first commit
        out = run_git(["diff", "--name-status", "--root", "HEAD"], full_path) or ""
    files = []
    seen = set()
    for line in out.splitlines():
        parts = line.split("\t", 1)
        if len(parts) == 2:
            status, path = parts[0][0], parts[1]  # M/A/D/R first char
            if path not in seen:
                seen.add(path)
                files.append({"status": status, "path": path})
    return {"files": files[:20]}  # cap at 20


@router.get("/git/{name}/details")
def get_git_details(name: str):
    """Get detailed git information including branches and commits."""
    full_path = os.path.join(BASE_PATH, name)
    if not os.path.isdir(os.path.join(full_path, ".git")):
        return {"error": "Not a git repository"}

    # 1. Get branches
    branch_out = run_git(["branch"], full_path) or ""
    branches = [b.strip() for b in branch_out.splitlines()]

    # 2. Get the last 10 commits with a specific format: Hash|Subject|Time|Author
    log_out = run_git(["log", "-n", "10", "--pretty=format:%h|%s|%ar|%an"], full_path) or ""
    commits = []
    if log_out:
        for line in log_out.splitlines():
            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append({
                    "hash": parts[0],
                    "message": parts[1],
                    "time": parts[2],
                    "author": parts[3]
                })

    return {"branches": branches, "commits": commits}
