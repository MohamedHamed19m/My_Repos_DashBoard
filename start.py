"""
Worktree Dashboard Launcher
Starts the FastAPI/uvicorn backend and opens the dashboard.
"""
import subprocess
import time
import webbrowser
import os
import sys
import shutil
import urllib.request
import urllib.error
from pathlib import Path

HERE       = Path(__file__).parent.absolute()
INDEX_FILE = HERE / "index.html"
SERVER_LOG = HERE / "server.log"
HOST       = "127.0.0.1"
PORT       = 8000
HEALTH_URL = f"http://{HOST}:{PORT}/projects"


def wait_for_server(timeout: int = 15) -> bool:
    """Poll until the server responds or timeout is reached."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(HEALTH_URL, timeout=1)
            return True
        except Exception:
            time.sleep(0.3)
    return False


def build_server_cmd() -> list:
    """Use uv if available, otherwise fall back to uvicorn directly."""
    if shutil.which("uv"):
        return [
            "uv", "run",
            "--with", "fastapi",
            "--with", "uvicorn",
            "uvicorn", "main:app",
            "--host", HOST,
            "--port", str(PORT),
        ]
    elif shutil.which("uvicorn"):
        return ["uvicorn", "main:app", "--host", HOST, "--port", str(PORT)]
    else:
        print("  [ERROR] Neither 'uv' nor 'uvicorn' found in PATH.")
        print("  Install with:  pip install uvicorn fastapi")
        sys.exit(1)


def main():
    print()
    print("  ┌─────────────────────────────────────┐")
    print("  │     Worktree Dashboard Launcher     │")
    print("  └─────────────────────────────────────┘")
    print()

    # ── 1. Start server ──────────────────────────────
    cmd = build_server_cmd()
    print(f"[1/3] Starting backend  ({' '.join(cmd[:3])}…)")

    log_file = open(SERVER_LOG, "w")
    server = subprocess.Popen(
        cmd,
        cwd=HERE,
        stdout=log_file,
        stderr=log_file,
    )

    # ── 2. Wait for server to be ready ───────────────
    print("[2/3] Waiting for server to be ready…", end="", flush=True)
    ready = wait_for_server(timeout=15)

    if not ready or server.poll() is not None:
        print(" FAILED")
        log_file.flush()
        print(f"\n  [ERROR] Server did not start. Check {SERVER_LOG} for details.")
        with open(SERVER_LOG) as f:
            print(f.read()[-1000:])
        server.terminate()
        return 1

    print(f" ready  →  http://{HOST}:{PORT}")

    # ── 3. Open dashboard ────────────────────────────
    print("[3/3] Opening dashboard…")
    webbrowser.open(f"file:///{INDEX_FILE.as_posix()}")

    print()
    print("  ─────────────────────────────────────────")
    print(f"  Dashboard:  file:///{INDEX_FILE.as_posix()}")
    print(f"  API:        http://{HOST}:{PORT}")
    print(f"  Logs:       {SERVER_LOG}")
    print("  Press Ctrl+C to stop")
    print("  ─────────────────────────────────────────")
    print()

    try:
        server.wait()
    except KeyboardInterrupt:
        print("\n  Shutting down…")
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
        log_file.close()
        print("  ✓ Server stopped.")

    return 0


if __name__ == "__main__":
    sys.exit(main())