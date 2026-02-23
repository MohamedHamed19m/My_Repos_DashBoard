"""Worktree management API endpoints."""

from __future__ import annotations

import os
from datetime import datetime

from fastapi import APIRouter, HTTPException

from ..core.config import BASE_PATH
from ..core.git_utils import run_git, run_git_out
from ..core.worktree_ops import get_worktrees_for_repo
from ..models.schemas import CreateWT, RemoveWTBody, MergeWTBody

router = APIRouter(tags=["worktrees"])


@router.get("/wt/{name}/list")
def wt_list(name: str):
    """List all worktrees for a repo with full merge status, age, SHA."""
    repo_path = os.path.join(BASE_PATH, name)
    if not os.path.isdir(repo_path):
        raise HTTPException(404, "Repo not found")
    worktrees = get_worktrees_for_repo(repo_path)
    current = run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo_path) or ""
    return {"worktrees": worktrees, "current_branch": current}


@router.get("/wt/{name}/default-suffix")
def wt_default_suffix(name: str):
    """Return the default chronological branch suffix (mirrors wtm.py naming)."""
    repo_path = os.path.join(BASE_PATH, name)
    worktrees = get_worktrees_for_repo(repo_path)
    counter = max(0, len(worktrees) - 1)
    suffix = datetime.now().strftime(f"fix-%b%d-%H%M-{counter}")
    return {"suffix": suffix}


@router.post("/wt/{name}/create")
def wt_create(name: str, body: CreateWT):
    """Create a new worktree at BASE_PATH/suffix with a new branch named suffix."""
    repo_path = os.path.join(BASE_PATH, name)
    if not os.path.isdir(repo_path):
        raise HTTPException(404, "Repo not found")

    suffix = body.suffix.strip()
    if not suffix:
        raise HTTPException(400, "suffix is required")

    new_path = os.path.join(BASE_PATH, suffix)
    ok, out = run_git_out(["worktree", "add", new_path, "-b", suffix], repo_path, timeout=20)
    return {"success": ok, "output": out, "path": new_path, "branch": suffix}


@router.post("/wt/{name}/remove")
def wt_remove(name: str, body: RemoveWTBody):
    """Force-remove a worktree and optionally delete its branch. Prunes after."""
    repo_path = os.path.join(BASE_PATH, name)
    if not os.path.isdir(repo_path):
        raise HTTPException(404, "Repo not found")

    ok, out = run_git_out(
        ["worktree", "remove", "--force", body.worktree_path], repo_path, timeout=15
    )
    if not ok:
        return {"success": False, "output": out}

    run_git(["worktree", "prune"], repo_path)

    branch_out = ""
    if body.delete_branch and body.branch and body.branch not in ("N/A", None):
        _, branch_out = run_git_out(["branch", "-D", body.branch], repo_path)

    return {
        "success": True,
        "output": out,
        "branch_deleted": body.delete_branch,
        "branch_output": branch_out,
    }


@router.post("/wt/{name}/merge")
def wt_merge(name: str, body: MergeWTBody):
    """
    Merge a worktree's branch into the repo's current branch.
    Optionally clean up worktree + branch after successful merge.
    Mirrors wtm.py merge_worktree() logic.
    """
    repo_path = os.path.join(BASE_PATH, name)
    if not os.path.isdir(repo_path):
        raise HTTPException(404, "Repo not found")

    current = run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo_path)
    if not current:
        return {"success": False, "output": "Cannot determine current branch"}

    if body.branch == current:
        return {"success": False, "output": f"Cannot merge '{body.branch}' into itself"}

    ok, out = run_git_out(["merge", body.branch], repo_path, timeout=30)
    if not ok:
        return {"success": False, "output": out, "merged_into": current}

    cleanup_out = ""
    if body.cleanup:
        run_git_out(["worktree", "remove", "--force", body.worktree_path], repo_path)
        run_git(["worktree", "prune"], repo_path)
        if body.delete_branch:
            _, cleanup_out = run_git_out(["branch", "-D", body.branch], repo_path)

    return {
        "success": True,
        "output": out,
        "merged_into": current,
        "cleanup_done": body.cleanup,
        "cleanup_output": cleanup_out,
    }
