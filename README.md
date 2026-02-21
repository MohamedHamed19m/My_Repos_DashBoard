# 🛠️ Local Worktree Dashboard

A lightweight, self-hosted web dashboard to manage local repositories and workflows. Built with a **FastAPI** backend and a modern **Glassmorphism** frontend.

## 🚀 Features
- **Project Grid:** Auto-scans your project directory with Git status badges.
- **Direct Launch:** Open any project in VS Code with a single click.
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

1. **Start the Backend:**
   ```bash
   uv run --with fastapi --with uvicorn uvicorn main:app --reload