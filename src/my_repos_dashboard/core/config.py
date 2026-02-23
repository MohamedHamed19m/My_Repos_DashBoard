"""Configuration and app factory for the My Repos Dashboard."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Load environment variables from .env
load_dotenv()

# Robust project root detection (works both installed and dev)
try:
    # When installed as package
    import my_repos_dashboard
    PROJECT_ROOT = Path(my_repos_dashboard.__file__).parent.parent.parent
except ImportError:
    # When running from src/ during development
    PROJECT_ROOT = Path(__file__).parent.parent.parent

STATIC_DIR = PROJECT_ROOT / "static"
BASE_PATH = os.getenv("REPO_BASE_PATH", r"C:\Users\user\Desktop\test\0_my_repo")
COMMANDS_FILE = os.path.join(BASE_PATH, "commands.json")


# Create FastAPI app instance
app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"success": False, "output": f"Server error: {str(exc)}"},
    )


__all__ = [
    "PROJECT_ROOT",
    "STATIC_DIR",
    "BASE_PATH",
    "COMMANDS_FILE",
    "app",
]
