"""Pydantic schemas for request and response models."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class CommandsBody(BaseModel):
    """Request body for saving commands."""
    commands: list  # [{"label": str, "cmd": str}]


class RunCommandBody(BaseModel):
    """Request body for running a command."""
    cmd: str


class CreateWT(BaseModel):
    """Request body for creating a worktree."""
    suffix: str


class RemoveWTBody(BaseModel):
    """Request body for removing a worktree."""
    worktree_path: str
    branch: Optional[str] = None
    delete_branch: bool = False


class MergeWTBody(BaseModel):
    """Request body for merging a worktree."""
    branch: str
    worktree_path: str
    cleanup: bool = False
    delete_branch: bool = False


class ScratchpadBody(BaseModel):
    """Request body for saving scratchpad content."""
    content: str


__all__ = [
    "CommandsBody",
    "RunCommandBody",
    "CreateWT",
    "RemoveWTBody",
    "MergeWTBody",
    "ScratchpadBody",
]
