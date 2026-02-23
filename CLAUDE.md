# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Local Worktree Dashboard** - a web application for managing local Git repositories and Git worktrees. It consists of a FastAPI backend (`main.py`) serving as a Git operations API, and a vanilla HTML/CSS/JS frontend (`index.html`) with a dark glassmorphism UI.

## Running the Application

**Recommended: Use the Python launcher**
```bash
python start.py
```
This script handles:
1. Starting the uvicorn server (prefers `uv run`, falls back to `uvicorn`)
2. Waiting for the server to be ready
3. Opening the dashboard in the browser
4. Graceful shutdown on Ctrl+C

**Windows:**
```cmd
start.bat
```

**Manual server start (for development with auto-reload):**
```bash
uv run --with fastapi --with uvicorn uvicorn main:app --reload
# Or if uvicorn is installed directly:
uvicorn main:app --reload
```

The server runs on `http://127.0.0.1:8000` by default.

## Architecture

### Backend (`main.py`)

- **FastAPI app** with CORS enabled for all origins
- **`BASE_PATH`**: Hardcoded path to the parent directory containing repos to scan (line 33)
- **Git utilities**: `run_git()`, `run_git_out()`, `get_branch_sha()`, `get_merge_status()`
- **Worktree logic**: Mirrors a separate `wtm.py` tool's logic for merge status (FRESH/MERGED/NOT MERGED)
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

- **`start.py`**: Cross-platform launcher with server health checking
- **`start.bat`**: Windows-only batch launcher

## Development Notes

- **Dependencies**: `fastapi`, `uvicorn`. Use `uv` for managed dependencies, or install directly with pip.
- **No frontend build process**: Edit `index.html` directly and refresh the browser.
- **BASE_PATH configuration**: Update `BASE_PATH` in `main.py` line 33 to scan a different directory.
- **Git worktree merge status**: The `get_merge_status()` function determines if a worktree's branch is FRESH (no divergence), MERGED (commits exist in parent), or NOT MERGED (unique commits).
- **Git commands modal**: The git button opens a modal with safe operations (history, branches, pull) and dangerous operations (force reset, force clean). The branches endpoint returns up to 5 latest branches with current branch highlighting.
- **Recent files tooltip**: Uses `git diff --name-status HEAD~5..HEAD` to get files changed in last 5 commits. Lazy-loaded on first hover and cached per session.
- **Custom commands storage**: Stored in `BASE_PATH/commands.json` as `{"repo-name": [{"label": "test", "cmd": "npm test"}]}`. Commands run in the repo directory with output captured and displayed.
- **Advanced stats metrics**: The `/stats` endpoint calculates streaks (consecutive commit days), hourly distribution for heatmap, week-over-week comparison (last 7 days vs previous 7 days), and uncommitted work health (dirty repos with file counts).

## Testing Changes

After backend changes, the server auto-reloads if started with `--reload`. For frontend changes, simply refresh the browser (hard refresh if needed: Ctrl+Shift+R).
