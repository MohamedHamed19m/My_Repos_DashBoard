from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import subprocess
import time
import json
from datetime import datetime
from typing import Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi import Request
from fastapi.responses import JSONResponse

app = FastAPI()


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"success": False, "output": f"Server error: {str(exc)}"},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_PATH = r"C:\Users\user\Desktop\test\0_my_repo"


# ── GIT HELPERS ───────────────────────────────────────────────────────────────

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
    args = ["rev-parse"]
    if short:
        args.append("--short")
    args.append(branch)
    return run_git(args, cwd) or ""


def get_worktree_age(path: str) -> str:
    try:
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


def get_merge_status(branch: str, parent_branch: str, cwd: str) -> Tuple[str, str]:
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


# ── DASHBOARD GIT INFO ────────────────────────────────────────────────────────

def get_git_info(path: str) -> Optional[dict]:
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


# ── DASHBOARD ENDPOINTS ───────────────────────────────────────────────────────

@app.get("/projects")
def get_projects():
    folders = [
        f for f in os.listdir(BASE_PATH)
        if os.path.isdir(os.path.join(BASE_PATH, f)) and f != "my-dashboard"
    ]

    def process(name):
        full_path = os.path.join(BASE_PATH, name)
        return {"name": name, "path": full_path, "git": get_git_info(full_path)}

    with ThreadPoolExecutor(max_workers=min(len(folders), 12)) as executor:
        projects = list(executor.map(process, folders))

    projects.sort(key=lambda p: p["git"]["last_ts"] if p["git"] else 0, reverse=True)
    return {"projects": projects}


@app.get("/open/{name}")
def open_vscode(name: str):
    full_path = os.path.join(BASE_PATH, name)
    subprocess.Popen(["code", full_path], shell=True)
    return {"message": f"Opening {name}"}


@app.get("/open-worktree")
def open_worktree_path(path: str):
    subprocess.Popen(["code", path], shell=True)
    return {"message": f"Opening {path}"}


@app.get("/readme/{name}")
def get_readme(name: str):
    full_path = os.path.join(BASE_PATH, name)
    for file in os.listdir(full_path):
        if file.lower() == "readme.md":
            with open(os.path.join(full_path, file), "r", encoding="utf-8") as f:
                return {"content": f.read()}
    return {"content": "No README.md found in this repo."}


@app.post("/git/{name}/{action}")
def git_action(name: str, action: str):
    full_path = os.path.join(BASE_PATH, name)
    commands = {
        "pull":      ["pull"],
        "fetch":     ["fetch", "--all"],
        "stash":     ["stash"],
        "stash-pop": ["stash", "pop"],
        "reset":     ["reset", "--hard", "HEAD"],
        "clean":     ["clean", "-fd"],
        "log":       ["log", "--oneline", "-10"],
    }
    if action not in commands:
        return {"success": False, "output": "Unknown action"}
    ok, out = run_git_out(commands[action], full_path, timeout=30)
    return {"success": ok, "output": out}


@app.get("/git/{name}/log")
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


@app.get("/git/{name}/branches")
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


@app.get("/stats")
def get_stats(days: int = 7):
    from collections import defaultdict
    import datetime as dt_mod

    now        = datetime.now()
    today      = now.date()
    since_main = (now - dt_mod.timedelta(days=days)).strftime("%Y-%m-%d")
    week_start = today - dt_mod.timedelta(days=6)   # rolling 7 days ending today
    prev_start = today - dt_mod.timedelta(days=13)  # the 7 days before that

    folders = [
        f for f in os.listdir(BASE_PATH)
        if os.path.isdir(os.path.join(BASE_PATH, f)) and f != "my-dashboard"
    ]

    # ── collect per-repo data in parallel ─────────────────────────────────────
    def collect_repo(folder):
        repo_path = os.path.join(BASE_PATH, folder)
        if not os.path.exists(os.path.join(repo_path, ".git")):
            return None

        # Current period (for ranking / day-of-week chart)
        cur_out = run_git(["log", f"--since={since_main}", "--pretty=format:%ct"], repo_path) or ""
        cur_ts  = [int(t) for t in cur_out.splitlines() if t.strip().isdigit()]

        # 1-year history for streaks + hour heatmap + week comparison
        all_out = run_git(["log", "--since=1 year ago", "--pretty=format:%ct"], repo_path) or ""
        all_ts  = [int(t) for t in all_out.splitlines() if t.strip().isdigit()]

        # Uncommitted work snapshot
        status_out = run_git(["status", "--porcelain"], repo_path) or ""
        lines      = status_out.splitlines()
        staged     = sum(1 for l in lines if l and l[0] in "MADRC")
        modified   = sum(1 for l in lines if l and l[1] in "MD")
        untracked  = sum(1 for l in lines if l.startswith("??"))

        return {
            "name":      folder,
            "cur_ts":    cur_ts,
            "all_ts":    all_ts,
            "is_dirty":  bool(status_out),
            "staged":    staged,
            "modified":  modified,
            "untracked": untracked,
        }

    with ThreadPoolExecutor(max_workers=min(len(folders), 12)) as ex:
        results = [r for r in ex.map(collect_repo, folders) if r]

    # ── aggregate ──────────────────────────────────────────────────────────────
    all_commits     = []   # (ts, name) — current period only
    all_commits_all = []   # (ts, name) — full 1-year
    repo_activity   = []
    dirty_repos = total_staged = total_modified = total_untracked = 0

    for r in results:
        if r["cur_ts"]:
            all_commits.extend((ts, r["name"]) for ts in r["cur_ts"])
            repo_activity.append({"name": r["name"], "commits": len(r["cur_ts"]), "cur_ts": r["cur_ts"]})
        all_commits_all.extend((ts, r["name"]) for ts in r["all_ts"])
        if r["is_dirty"]:
            dirty_repos     += 1
            total_staged    += r["staged"]
            total_modified  += r["modified"]
            total_untracked += r["untracked"]

    repo_activity.sort(key=lambda x: x["commits"], reverse=True)
    total_commits = len(all_commits)

    # ── day-of-week distribution (current period) ──────────────────────────────
    day_names  = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    day_counts = defaultdict(int)
    for ts, _ in all_commits:
        day_counts[datetime.fromtimestamp(ts).weekday()] += 1

    day_distribution  = []
    most_active_day   = "No commits"
    most_active_pct   = 0
    if total_commits:
        best            = max(day_counts, key=lambda k: day_counts[k])
        most_active_day = day_names[best]
        most_active_pct = round(day_counts[best] / total_commits * 100)
        for i in range(7):
            day_distribution.append({
                "day":        day_names[i],
                "count":      day_counts[i],
                "percentage": round(day_counts[i] / total_commits * 100),
            })

    # ── hour-of-day heatmap (full 1-year history) ──────────────────────────────
    hour_counts = defaultdict(int)
    for ts, _ in all_commits_all:
        hour_counts[datetime.fromtimestamp(ts).hour] += 1
    hour_distribution = [{"hour": h, "count": hour_counts[h]} for h in range(24)]

    # ── this week vs last week ─────────────────────────────────────────────────
    this_week = [0] * 7
    last_week = [0] * 7
    for ts, _ in all_commits_all:
        d = datetime.fromtimestamp(ts).date()
        if week_start <= d <= today:
            this_week[(d - week_start).days] += 1
        elif prev_start <= d < week_start:
            last_week[(d - prev_start).days] += 1
    week_labels = [(week_start + dt_mod.timedelta(days=i)).strftime("%a") for i in range(7)]

    # ── latest commit ──────────────────────────────────────────────────────────
    latest_commit = latest_repo = None
    if all_commits:
        latest_ts, latest_repo = max(all_commits, key=lambda x: x[0])
        secs = int((now - datetime.fromtimestamp(latest_ts)).total_seconds())
        if secs < 60:       latest_commit = f"{secs}s ago"
        elif secs < 3600:   latest_commit = f"{secs // 60}m ago"
        elif secs < 86400:  latest_commit = f"{secs // 3600}h ago"
        else:               latest_commit = f"{secs // 86400}d ago"

    # ── streaks (longest + current) — computed from 1-year history ────────────
    longest_streak = current_streak_val = 0
    streak_start_date = streak_end_date = None

    if all_commits_all:
        unique_dates = sorted(
            {datetime.fromtimestamp(ts).date() for ts, _ in all_commits_all},
            reverse=True
        )

        # Current streak — walk back from today
        cur   = 0
        check = today
        for d in unique_dates:
            if d == check or d == check - dt_mod.timedelta(days=1):
                cur  += 1
                check = d
            elif d < check - dt_mod.timedelta(days=1):
                break
        current_streak_val = cur

        # Longest streak ever
        run = best_run = 1
        best_end = unique_dates[0]
        for i in range(1, len(unique_dates)):
            if (unique_dates[i-1] - unique_dates[i]).days == 1:
                run += 1
                if run > best_run:
                    best_run = run
                    best_end = unique_dates[i-1]
            else:
                run = 1
        longest_streak    = best_run
        streak_end_date   = best_end
        streak_start_date = best_end - dt_mod.timedelta(days=best_run - 1)

    # ── top repos enriched with daily sparkline ───────────────────────────────
    top_repos = []
    for r in repo_activity[:5]:
        spark = [0] * 7
        for ts in r["cur_ts"]:
            d = datetime.fromtimestamp(ts).date()
            if week_start <= d <= today:
                spark[(d - week_start).days] += 1
        top_repos.append({"name": r["name"], "commits": r["commits"], "spark": spark})

    return {
        "top_repos":              top_repos,
        "day_distribution":       day_distribution,
        "hour_distribution":      hour_distribution,
        "most_active_day":        most_active_day,
        "most_active_percentage": most_active_pct,
        "latest_commit":          latest_commit,
        "latest_commit_repo":     latest_repo,
        "longest_streak":         longest_streak,
        "current_streak":         current_streak_val,
        "streak_start":           streak_start_date.isoformat() if streak_start_date else None,
        "streak_end":             streak_end_date.isoformat() if streak_end_date else None,
        "this_week":              this_week,
        "last_week":              last_week,
        "week_labels":            week_labels,
        "dirty_repos":            dirty_repos,
        "total_staged":           total_staged,
        "total_modified":         total_modified,
        "total_untracked":        total_untracked,
        "total_commits":          total_commits,
        "days_period":            days,
    }


# ── WORKTREE MANAGER ENDPOINTS ────────────────────────────────────────────────

@app.get("/wt/{name}/list")
def wt_list(name: str):
    """List all worktrees for a repo with full merge status, age, SHA."""
    repo_path = os.path.join(BASE_PATH, name)
    if not os.path.isdir(repo_path):
        raise HTTPException(404, "Repo not found")
    worktrees = get_worktrees_for_repo(repo_path)
    current = run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo_path) or ""
    return {"worktrees": worktrees, "current_branch": current}


@app.get("/wt/{name}/default-suffix")
def wt_default_suffix(name: str):
    """Return the default chronological branch suffix (mirrors wtm.py naming)."""
    repo_path  = os.path.join(BASE_PATH, name)
    worktrees  = get_worktrees_for_repo(repo_path)
    counter    = max(0, len(worktrees) - 1)
    suffix     = datetime.now().strftime(f"fix-%b%d-%H%M-{counter}")
    return {"suffix": suffix}

@app.get("/git/{name}/recent-files")
def git_recent_files(name: str, depth: int = 5):
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


# ── COMMANDS ─────────────────────────────────────────────────────────────────
COMMANDS_FILE = os.path.join(BASE_PATH, "commands.json")

def load_commands() -> dict:
    try:
        if os.path.exists(COMMANDS_FILE):
            with open(COMMANDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_commands(data: dict):
    with open(COMMANDS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


@app.get("/commands/{name}")
def get_commands(name: str):
    """Get saved commands for a repo."""
    all_cmds = load_commands()
    return {"commands": all_cmds.get(name, [])}


class CommandsBody(BaseModel):
    commands: list  # [{"label": str, "cmd": str}]

@app.post("/commands/{name}")
def set_commands(name: str, body: CommandsBody):
    """Save commands for a repo."""
    all_cmds = load_commands()
    all_cmds[name] = body.commands
    save_commands(all_cmds)
    return {"success": True}


class RunCommandBody(BaseModel):
    cmd: str

@app.post("/commands/{name}/run")
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


@app.get("/git/{name}/details")
def get_git_details(name: str):
    repo_path = os.path.join(BASE_PATH, name)
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        return {"error": "Not a git repository"}

    # 1. Get branches
    branch_out = run_git(["branch"], repo_path) or ""
    branches = [b.strip() for b in branch_out.splitlines()]

    # 2. Get the last 10 commits with a specific format: Hash|Subject|Time|Author
    log_out = run_git(["log", "-n", "10", "--pretty=format:%h|%s|%ar|%an"], repo_path) or ""
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

class CreateWT(BaseModel):
    suffix: str


@app.post("/wt/{name}/create")
def wt_create(name: str, body: CreateWT):
    """Create a new worktree at BASE_PATH/suffix with a new branch named suffix."""
    repo_path = os.path.join(BASE_PATH, name)
    if not os.path.isdir(repo_path):
        raise HTTPException(404, "Repo not found")

    suffix = body.suffix.strip()
    if not suffix:
        raise HTTPException(400, "suffix is required")

    new_path = os.path.join(BASE_PATH, suffix)
    ok, out  = run_git_out(["worktree", "add", new_path, "-b", suffix], repo_path, timeout=20)
    return {"success": ok, "output": out, "path": new_path, "branch": suffix}


class RemoveWTBody(BaseModel):
    worktree_path: str
    branch: Optional[str] = None
    delete_branch: bool = False


@app.post("/wt/{name}/remove")
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


class MergeWTBody(BaseModel):
    branch: str
    worktree_path: str
    cleanup: bool = False
    delete_branch: bool = False


@app.post("/wt/{name}/merge")
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