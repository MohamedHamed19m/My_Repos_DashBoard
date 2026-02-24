"""Pinned repos API endpoints for managing repository pin status."""

from __future__ import annotations

import json
import os

from fastapi import APIRouter

from ..core.config import BASE_PATH

router = APIRouter(tags=["pinned"])

# Pinned repos storage file (in .my_dashboard directory)
PINNED_DIR = os.path.join(BASE_PATH, ".my_dashboard")
PINNED_FILE = os.path.join(PINNED_DIR, "pinned_repos.json")


def load_pinned() -> set[str]:
    """Load pinned repos from the pinned_repos.json file."""
    try:
        if os.path.exists(PINNED_FILE):
            with open(PINNED_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("pinned", []))
    except Exception:
        pass
    return set()


def save_pinned(data: dict):
    """Save pinned repos to the pinned_repos.json file."""
    os.makedirs(PINNED_DIR, exist_ok=True)
    with open(PINNED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


@router.get("/pinned")
def get_pinned():
    """Get list of pinned repos."""
    return {"pinned": list(load_pinned())}


@router.post("/pinned/{name}")
def toggle_pinned(name: str):
    """Toggle pin status for a repo."""
    pinned = load_pinned()
    if name in pinned:
        pinned.remove(name)
        is_pinned = False
    else:
        pinned.add(name)
        is_pinned = True
    save_pinned({"pinned": list(pinned)})
    return {"success": True, "isPinned": is_pinned}
