# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Local Worktree Dashboard** - a web application for managing local Git repositories and Git worktrees. It consists of a FastAPI backend structured as a UV package, and a vanilla HTML/CSS/JS frontend (`static/index.html`) with a dark glassmorphism UI.

## Package Structure

```
my-repos-dashboard/
├── pyproject.toml                          # UV package config
├── .env                                    # Environment variables (REPO_BASE_PATH)
├── README.md
├── CLAUDE.md
├── start.bat                               # Start server in background
├── stop.bat                                # Stop running server
├── restart.bat                             # Restart server
├── status.bat                              # Check server status
├── start_hidden.vbs                        # Helper: run command completely hidden
├── .dashboard.pid                          # Auto-generated: stores server PID
├── dashboard.log                           # Auto-generated: server logs
│
├── src/
│   └── my_repos_dashboard/
│       ├── __init__.py
│       ├── __main__.py                     # Entry point for `uv run my-repos-dashboard`
│       ├── main.py                         # FastAPI app factory + entry point
│       │
│       ├── api/                            # Route handlers grouped by feature
│       │   ├── __init__.py
│       │   ├── projects.py                 # /projects, /stats
│       │   ├── actions.py                  # /open/*, /readme/*, /git/{action}
│       │   ├── git.py                      # /git/* (log, branches, recent-files, details)
│       │   ├── worktrees.py                # /wt/* endpoints
│       │   └── commands.py                 # /commands/* endpoints
│       │
│       ├── core/                           # Shared business logic
│       │   ├── __init__.py
│       │   ├── git_utils.py                # run_git, run_git_out, get_branch_sha
│       │   ├── worktree_ops.py             # get_merge_status, get_worktrees_for_repo
│       │   └── config.py                   # BASE_PATH from .env, settings, exception handler
│       │
│       └── models/                         # Pydantic schemas
│           ├── __init__.py
│           └── schemas.py                  # All request/response models
│
├── static/                                 # Frontend assets
│   └── index.html                          # HTML+CSS+JS
│
└── docs/                                   # Documentation
    └── image/
        └── dashboard.png
```

## Running the Application

### Windows Scripts (Recommended)

Double-click these batch files to manage the server:

| Script | Action | Window Behavior |
|--------|--------|-----------------|
| `start.bat` | Start server in background | Shows status for ~3 seconds, closes automatically |
| `stop.bat` | Stop running server | Shows status for ~2 seconds, closes automatically |
| `restart.bat` | Restart server (stop + start) | Shows status, closes when done |
| `status.bat` | Check if server is running | Keeps window open until you press a key |

**How it works:**
- `start.bat` runs the server completely in the background using VBScript (`start_hidden.vbs`)
- Server PID is stored in `.dashboard.pid` for reliable stopping
- Logs are written to `dashboard.log` for debugging
- Server runs continuously even after closing the launcher window
- `stop.bat` kills ALL Python processes (aggressive but reliable)

### Using UV Command Line

```bash
# Install dependencies
uv sync

# Start server with auto-reload (development)
uv run my-repos-dashboard --reload

# Or using uvicorn directly
uv run uvicorn my_repos_dashboard.main:app --reload
```

The server runs on `http://127.0.0.1:8000` by default.

## Architecture

### Backend (UV Package Structure)

**FastAPI app** with CORS enabled for all origins
- **`REPO_BASE_PATH`**: Loaded from `.env` file - path to the directory containing repos to scan
- **Git utilities** (`core/git_utils.py`): `run_git()`, `run_git_out()`, `get_branch_sha()`, `get_worktree_age()`
- **Worktree logic** (`core/worktree_ops.py`): Mirrors a separate `wtm.py` tool's logic for merge status (FRESH/MERGED/NOT MERGED)
- **ThreadPoolExecutor**: Used for parallel repo scanning (max 12 workers)

**Key endpoints:**
| Endpoint | Purpose |
|----------|---------|
| `GET /projects` | Scan BASE_PATH and return all repos with Git info |
| `GET /stats` | Get advanced statistics (top repos with sparklines, current/longest streaks, hourly heatmap, week-over-week comparison, uncommitted health) |
| `GET /open/{name}` | Open a repo in VS Code |
| `GET /open-terminal/{name}` | Open a PowerShell terminal in the repo directory |
| `GET /open-worktree?path=` | Open a worktree path in VS Code |
| `GET /readme/{name}` | Fetch README.md content |
| `POST /git/{name}/{action}` | Run git commands (pull, fetch, stash, stash-pop, reset, clean) |
| `GET /git/{name}/log` | Get git commit history (structured JSON) |
| `GET /git/{name}/branches` | Get latest 5 branches |
| `GET /git/{name}/recent-files` | Get files changed in recent commits (M/A/D/R) |
| `GET /commands/{name}` | Get saved custom commands for a repo |
| `POST /commands/{name}` | Save custom commands for a repo |
| `POST /commands/{name}/run` | Run a custom command |
| `GET /wt/{name}/list` | List worktrees for a repo |
| `GET /wt/{name}/default-suffix` | Get default chronological branch name |
| `POST /wt/{name}/create` | Create new worktree + branch |
| `POST /wt/{name}/remove` | Remove worktree (optionally delete branch) |
| `POST /wt/{name}/merge` | Merge worktree branch into parent |

### Frontend (`index.html`)

Single-file application with embedded CSS and JavaScript:
- **CSS**: CSS variables for theming, grid-based card layout, modal system
- **JS**: Fetch API for backend communication, custom markdown renderer
- **No build step**: Direct browser-compatible code

**Key UI components:**
- Project grid with Git status badges, worktree preview, action buttons (VS Code, Terminal, README)
- Recent files tooltip on hover (shows files changed in last 5 commits)
- Custom commands panel per repo (edit and run repo-specific commands)
- Worktree Manager modal with create/remove/merge functionality
- Git Actions modal with history, branches, pull, force reset, force clean
- Advanced Stats modal with:
  - Streak Hero cards with fire icons 🔥 (current & longest streaks)
  - Interactive hour-of-day heatmap (24-hour grid)
  - This Week vs. Last Week comparative bar charts
  - Uncommitted work health bar with status pulsing
  - 7-day sparklines for each repository
- README slide-out panel
- Toast notifications

### Launcher Scripts

**Server Management Scripts:**
- **`start.bat`**: Creates venv if needed, starts server in background via VBScript, saves PID for stopping
- **`stop.bat`**: Kills all Python processes to stop the server, removes PID file
- **`restart.bat`**: Calls stop.bat then start.bat for quick restart
- **`status.bat`**: Shows if dashboard is running with PID, URL, and log file location
- **`start_hidden.vbs`**: Helper script that runs the server completely hidden (no window)

**Auto-generated Files:**
- **`.dashboard.pid`**: Stores the server's process ID for reliable stopping
- **`dashboard.log`**: Server output/logs for debugging

## Development Notes

- **Dependencies**: `fastapi`, `uvicorn`, `python-dotenv`. Managed via `uv` - see `pyproject.toml`.
- **No frontend build process**: Edit `static/index.html` directly and refresh the browser.
- **REPO_BASE_PATH configuration**: Edit `.env` file at project root to change the directory to scan.
- **Git worktree merge status**: The `get_merge_status()` function determines if a worktree's branch is FRESH (no divergence), MERGED (commits exist in parent), or NOT MERGED (unique commits).
- **Git commands modal**: The git button opens a modal with safe operations (history, branches, pull) and dangerous operations (force reset, force clean). The branches endpoint returns up to 5 latest branches with current branch highlighting.
- **Recent files tooltip**: Uses `git diff --name-status HEAD~5..HEAD` to get files changed in last 5 commits. Lazy-loaded on first hover and cached per session.
- **Custom commands storage**: Stored in `BASE_PATH/commands.json` as `{"repo-name": [{"label": "test", "cmd": "npm test"}]}`. Commands run in the repo directory with output captured and displayed.
- **Advanced stats metrics**: The `/stats` endpoint calculates streaks (consecutive commit days), hourly distribution for heatmap, week-over-week comparison (last 7 days vs previous 7 days), and uncommitted work health (dirty repos with file counts).

## Testing Changes

After backend changes, the server auto-reloads if started with `--reload`. For frontend changes, simply refresh the browser (hard refresh if needed: Ctrl+Shift+R).
