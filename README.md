# 🛠️ Local Worktree Dashboard

A lightweight, self-hosted web dashboard to manage local repositories and workflows. Built with a **FastAPI** backend and a modern **Glassmorphism** frontend.

## 🚀 Features
- **Project Grid:** Auto-scans your project directory with Git status badges.
- **Direct Launch:** Open any project in VS Code or PowerShell terminal with a single click.
- **Git Actions:** History, branches, pull, force reset, force clean — all in one modal.
- **Worktree Manager:** Create, remove, and merge Git worktrees with visual status.
- **Advanced Activity Stats:**
  - Top repos with 7-day sparklines
  - Streak Hero cards (current & longest streaks) with fire icons 🔥
  - Hour-of-day interactive heatmap
  - This Week vs. Last Week comparison
  - Uncommitted work health bar with status pulsing
- **Recent Files:** Hover over commit line to see files changed in recent commits.
- **Custom Commands:** Define per-repo commands (test, build, deploy) and run them with one click.
- **Documentation Viewer:** Preview READMEs directly in the browser.
- **Clean UI:** Dark-mode optimized with glassmorphism design.

## 🛠️ Tech Stack
- **Backend:** Python 3.12+ via `FastAPI`
- **Package Management:** `uv` (Astral)
- **Frontend:** Vanilla HTML5, CSS3 (Grid/Flexbox), and JavaScript (Fetch API)

## 📸 Screenshots

### Dashboard View
![Dashboard Screenshot](docs/image/dashboard.png)

The main dashboard interface displaying the project grid with glassmorphism design, dark-mode optimization, and quick-launch capabilities for your local repositories.

## 🚦 Getting Started

1. **Clone and navigate to the project:**
   ```bash
   cd my-repos-dashboard
   ```

2. **Configure your repository path:**
   Edit `.env` file and set `REPO_BASE_PATH` to your projects directory:
   ```env
   REPO_BASE_PATH=C:\Users\user\Desktop\test\0_my_repo
   ```

3. **Install dependencies and start the server:**
   ```bash
   # Using uv (recommended)
   uv sync
   uv run my-repos-dashboard

   # Or with auto-reload for development
   uv run my-repos-dashboard --reload

   # Or using uvicorn directly
   uv run uvicorn my_repos_dashboard.main:app --reload
   ```

4. **Windows users:** Double-click `start.bat` to launch the dashboard.

## 🛑 Server Management (Windows)

The dashboard comes with easy-to-use batch scripts:

| Script | Action |
|--------|--------|
| `start.bat` | Start dashboard in background (closes window automatically) |
| `stop.bat` | Stop any running dashboard server |
| `restart.bat` | Quick restart (stop + start) |
| `status.bat` | Check if dashboard is running |

**Double-click any of these files to run them.**

### How It Works
- `start.bat` runs the server in the background and closes the window
- A log file is created at `dashboard.log` for debugging
- The server's PID is stored in `.dashboard.pid` for easy stopping
- `stop.bat` uses the PID (or searches for the process) to stop the server cleanly

### Manual Control (Terminal)
```bash
# Start with auto-reload
uv run my-repos-dashboard --reload

# Stop with Ctrl+C when running in foreground
# Or use stop.bat when running in background
```

### Troubleshooting

**Server won't start?**
1. Check the log file for errors: `type dashboard.log`
2. Ensure `uv` is installed and in your PATH: `uv --version`
3. Verify `.env` file exists with correct `REPO_BASE_PATH`
4. If stuck, delete `.dashboard.pid` and try `start.bat` again

**Important:**
- Always use `uv run my-repos-dashboard` to start the server (not `uvicorn` directly)
- The `start_hidden.vbs` helper must use UV commands - never call `.venv` executables directly
- UV manages the virtual environment automatically