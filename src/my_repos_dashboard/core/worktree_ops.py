"""Worktree operations and git info retrieval."""

from __future__ import annotations

import os
from typing import Optional

from .git_utils import run_git, get_branch_sha, get_worktree_age


def get_merge_status(branch: str, parent_branch: str, cwd: str) -> tuple[str, str]:
    """
    Returns (status, color):
      FRESH      - branch SHA == parent SHA (no divergence yet)
      MERGED     - branch commits already exist in parent
      NOT MERGED - branch has unique commits not in parent
    Mirrors wtm.py get_merge_status() logic exactly.
    """
    if not branch or not parent_branch or branch == parent_branch:
        return "N/A", "dim"

    branch_sha = get_branch_sha(branch, cwd)
    parent_sha = get_branch_sha(parent_branch, cwd)

    if not branch_sha or not parent_sha:
        return "ERROR", "red"

    if branch_sha == parent_sha:
        return "FRESH", "cyan"

    merged_out = run_git(["branch", "--merged", parent_branch], cwd) or ""
    merged_branches = [b.strip().lstrip("* ") for b in merged_out.splitlines()]
    if branch in merged_branches:
        return "MERGED", "green"

    return "NOT MERGED", "yellow"


def get_worktrees_for_repo(repo_path: str) -> list[dict]:
    """
    Full worktree list with merge status, age, SHA.
    Mirrors wtm.py get_worktrees() logic.
    """
    output = run_git(["worktree", "list"], repo_path)
    if not output:
        return []

    parent_branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo_path) or ""
    parent_sha = get_branch_sha(parent_branch, repo_path, short=True)
    lines = output.splitlines()

    worktrees = []
    for i, line in enumerate(lines):
        parts = line.split()
        if not parts:
            continue
        path = parts[0]
        branch = next(
            (p.strip("[]") for p in parts if p.startswith("[") and p.endswith("]")),
            None,
        )
        age = get_worktree_age(path)
        is_main = (i == 0)

        if branch:
            branch_sha = get_branch_sha(branch, repo_path, short=True)
            status, status_color = get_merge_status(branch, parent_branch, repo_path)
        else:
            branch = None
            branch_sha = ""
            status, status_color = "DETACHED", "red"

        worktrees.append({
            "path": path,
            "branch": branch,
            "branch_sha": branch_sha,
            "status": status,
            "status_color": status_color,
            "age": age,
            "is_main": is_main,
            "parent_branch": parent_branch,
            "parent_sha": parent_sha,
        })

    return worktrees


def get_git_info(path: str) -> Optional[dict]:
    """Get comprehensive git information for a repository."""
    if not os.path.exists(os.path.join(path, ".git")):
        return None

    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], path)
    if not branch:
        return None

    status_output = run_git(["status", "--porcelain"], path) or ""
    is_dirty  = bool(status_output)
    staged    = sum(1 for l in status_output.splitlines() if l and l[0] in "MADRC")
    unstaged  = sum(1 for l in status_output.splitlines() if l and l[1] in "MD")
    untracked = sum(1 for l in status_output.splitlines() if l.startswith("??"))

    ahead, behind = 0, 0
    ab = run_git(["rev-list", "--left-right", "--count", f"{branch}...@{{u}}"], path) or ""
    if ab:
        parts = ab.split()
        if len(parts) == 2:
            try:
                ahead, behind = int(parts[0]), int(parts[1])
            except ValueError:
                pass

    log = run_git(["log", "-1", "--pretty=format:%s|||%ar|||%H"], path) or ""
    last_msg = last_time = last_hash = ""
    if "|||" in log:
        parts = log.split("|||")
        last_msg  = parts[0]
        last_time = parts[1] if len(parts) > 1 else ""
        last_hash = parts[2][:7] if len(parts) > 2 else ""

    ts_str  = run_git(["log", "-1", "--pretty=format:%ct"], path) or ""
    last_ts = int(ts_str) if ts_str.isdigit() else 0

    worktrees   = get_worktrees_for_repo(path)
    stash_out   = run_git(["stash", "list"], path) or ""
    stash_count = len(stash_out.splitlines()) if stash_out else 0

    return {
        "branch": branch,
        "is_dirty": is_dirty,
        "staged": staged,
        "unstaged": unstaged,
        "untracked": untracked,
        "ahead": ahead,
        "behind": behind,
        "last_msg": last_msg,
        "last_time": last_time,
        "last_hash": last_hash,
        "last_ts": last_ts,
        "worktrees": worktrees,
        "stash_count": stash_count,
    }
