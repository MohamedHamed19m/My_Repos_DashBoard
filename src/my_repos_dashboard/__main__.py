"""Command-line entry point for running the dashboard server.

This module allows running the dashboard with: uv run my-repos-dashboard
"""

from __future__ import annotations

import sys


def main():
    """Main entry point for running the dashboard server."""
    import uvicorn

    from .main import app

    # Check for --reload flag
    reload = "--reload" in sys.argv

    if reload:
        uvicorn.run(
            "my_repos_dashboard.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
        )
    else:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
        )


if __name__ == "__main__":
    main()
