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
| `GET /open/{name}` | Open a repo in VS Code |
| `GET /open-worktree?path=` | Open a worktree path in VS Code |
| `GET /readme/{name}` | Fetch README.md content |
| `POST /git/{name}/{action}` | Run git commands (pull, fetch, stash, stash-pop) |
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
- Project grid with Git status badges, worktree preview, action buttons
- Worktree Manager modal with create/remove/merge functionality
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

## Testing Changes

After backend changes, the server auto-reloads if started with `--reload`. For frontend changes, simply refresh the browser (hard refresh if needed: Ctrl+Shift+R).
