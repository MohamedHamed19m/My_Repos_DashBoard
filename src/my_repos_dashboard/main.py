"""Main FastAPI application entry point.

This module imports the app factory from core.config and includes all routers.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Import app factory (already configured with CORS and exception handler)
from .core.config import app, STATIC_DIR

# Import all routers (no circular imports - routers don't import main)
from .api import projects, actions, git, worktrees, commands, context

# Include all routers
app.include_router(projects.router)
app.include_router(actions.router)
app.include_router(git.router)
app.include_router(worktrees.router)
app.include_router(commands.router)
app.include_router(context.router)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def serve_index():
    """Serve the main dashboard page."""
    return FileResponse(str(STATIC_DIR / "index.html"))


# Export app for uvicorn direct import
__all__ = ["app"]
