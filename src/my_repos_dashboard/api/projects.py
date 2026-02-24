"""Projects and statistics API endpoints."""

from __future__ import annotations

import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

import fastapi
from fastapi import APIRouter

from ..core.config import BASE_PATH
from ..core.git_utils import run_git
from ..core.worktree_ops import get_git_info
from .pinned import load_pinned

router = APIRouter(tags=["projects"])

# Scratchpad storage directory
SCRATCHPAD_DIR = os.path.join(BASE_PATH, ".my_dashboard", "repos")


@router.get("/projects")
def get_projects():
    """Get all projects with git information."""
    folders = [
        f for f in os.listdir(BASE_PATH)
        if os.path.isdir(os.path.join(BASE_PATH, f)) and f != "my-dashboard"
    ]

    # Load pinned repos for filtering and sorting
    pinned = load_pinned()

    def process(name):
        full_path = os.path.join(BASE_PATH, name)
        result = {"name": name, "path": full_path, "git": get_git_info(full_path)}

        # Check if scratchpad has content
        scratchpad_file = os.path.join(SCRATCHPAD_DIR, name, "scratch.md")
        result["hasScratchpad"] = False
        if os.path.exists(scratchpad_file):
            try:
                with open(scratchpad_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    result["hasScratchpad"] = bool(content)
            except Exception:
                result["hasScratchpad"] = False

        # Check if repo is pinned
        result["isPinned"] = name in pinned

        return result

    with ThreadPoolExecutor(max_workers=min(len(folders), 12)) as executor:
        projects = list(executor.map(process, folders))

    # Sort: pinned repos first, then by last_ts (most recent first)
    projects.sort(key=lambda p: (
        not p.get("isPinned", False),  # Pinned repos first (False sorts after True)
        p["git"]["last_ts"] if p["git"] else 0  # Then by timestamp (reverse)
    ), reverse=True)

    return {"projects": projects}


@router.get("/stats")
def get_stats(days: int = 7):
    """Get advanced statistics including streaks, heatmap, and week-over-week comparison."""
    now = datetime.now()
    today = now.date()
    since_main = (now - timedelta(days=days)).strftime("%Y-%m-%d")
    week_start = today - timedelta(days=6)   # rolling 7 days ending today
    prev_start = today - timedelta(days=13)  # the 7 days before that

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
        cur_ts = [int(t) for t in cur_out.splitlines() if t.strip().isdigit()]

        # 1-year history for streaks + hour heatmap + week comparison
        all_out = run_git(["log", "--since=1 year ago", "--pretty=format:%ct"], repo_path) or ""
        all_ts = [int(t) for t in all_out.splitlines() if t.strip().isdigit()]

        # Uncommitted work snapshot
        status_out = run_git(["status", "--porcelain"], repo_path) or ""
        lines = status_out.splitlines()
        staged = sum(1 for l in lines if l and l[0] in "MADRC")
        modified = sum(1 for l in lines if l and l[1] in "MD")
        untracked = sum(1 for l in lines if l.startswith("??"))

        return {
            "name": folder,
            "cur_ts": cur_ts,
            "all_ts": all_ts,
            "is_dirty": bool(status_out),
            "staged": staged,
            "modified": modified,
            "untracked": untracked,
        }

    with ThreadPoolExecutor(max_workers=min(len(folders), 12)) as ex:
        results = [r for r in ex.map(collect_repo, folders) if r]

    # ── aggregate ──────────────────────────────────────────────────────────────
    all_commits = []   # (ts, name) — current period only
    all_commits_all = []   # (ts, name) — full 1-year
    repo_activity = []
    dirty_repos = total_staged = total_modified = total_untracked = 0

    for r in results:
        if r["cur_ts"]:
            all_commits.extend((ts, r["name"]) for ts in r["cur_ts"])
            repo_activity.append({"name": r["name"], "commits": len(r["cur_ts"]), "cur_ts": r["cur_ts"]})
        all_commits_all.extend((ts, r["name"]) for ts in r["all_ts"])
        if r["is_dirty"]:
            dirty_repos += 1
            total_staged += r["staged"]
            total_modified += r["modified"]
            total_untracked += r["untracked"]

    repo_activity.sort(key=lambda x: x["commits"], reverse=True)
    total_commits = len(all_commits)

    # ── day-of-week distribution (current period) ──────────────────────────────
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_counts = defaultdict(int)
    for ts, _ in all_commits:
        day_counts[datetime.fromtimestamp(ts).weekday()] += 1

    day_distribution = []
    most_active_day = "No commits"
    most_active_pct = 0
    if total_commits:
        best = max(day_counts, key=lambda k: day_counts[k])
        most_active_day = day_names[best]
        most_active_pct = round(day_counts[best] / total_commits * 100)
        for i in range(7):
            day_distribution.append({
                "day": day_names[i],
                "count": day_counts[i],
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
    week_labels = [(week_start + timedelta(days=i)).strftime("%a") for i in range(7)]

    # ── latest commit ──────────────────────────────────────────────────────────
    latest_commit = latest_repo = None
    if all_commits:
        latest_ts, latest_repo = max(all_commits, key=lambda x: x[0])
        secs = int((now - datetime.fromtimestamp(latest_ts)).total_seconds())
        if secs < 60:
            latest_commit = f"{secs}s ago"
        elif secs < 3600:
            latest_commit = f"{secs // 60}m ago"
        elif secs < 86400:
            latest_commit = f"{secs // 3600}h ago"
        else:
            latest_commit = f"{secs // 86400}d ago"

    # ── streaks (longest + current) — computed from 1-year history ────────────
    longest_streak = current_streak_val = 0
    streak_start_date = streak_end_date = None

    if all_commits_all:
        unique_dates = sorted(
            {datetime.fromtimestamp(ts).date() for ts, _ in all_commits_all},
            reverse=True
        )

        # Current streak — walk back from today
        cur = 0
        check = today
        for d in unique_dates:
            if d == check or d == check - timedelta(days=1):
                cur += 1
                check = d
            elif d < check - timedelta(days=1):
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
        longest_streak = best_run
        streak_end_date = best_end
        streak_start_date = best_end - timedelta(days=best_run - 1)

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
        "top_repos": top_repos,
        "day_distribution": day_distribution,
        "hour_distribution": hour_distribution,
        "most_active_day": most_active_day,
        "most_active_percentage": most_active_pct,
        "latest_commit": latest_commit,
        "latest_commit_repo": latest_repo,
        "longest_streak": longest_streak,
        "current_streak": current_streak_val,
        "streak_start": streak_start_date.isoformat() if streak_start_date else None,
        "streak_end": streak_end_date.isoformat() if streak_end_date else None,
        "this_week": this_week,
        "last_week": last_week,
        "week_labels": week_labels,
        "dirty_repos": dirty_repos,
        "total_staged": total_staged,
        "total_modified": total_modified,
        "total_untracked": total_untracked,
        "total_commits": total_commits,
        "days_period": days,
    }
