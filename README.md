# 🛠️ Local Worktree Dashboard

A lightweight, self-hosted web dashboard to manage local repositories and workflows. Built with a **FastAPI** backend and a modern **Glassmorphism** frontend.

## 🚀 Features
- **Project Grid:** Auto-scans your project directory.
- **Direct Launch:** Open any project in VS Code with a single click.
- **Documentation Viewer:** (In-progress) Preview READMEs directly in the browser.
- **Clean UI:** Dark-mode optimized for developers.

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