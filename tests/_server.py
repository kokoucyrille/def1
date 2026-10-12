"""Lance un serveur Streamlit local pour les tests navigateur (Playwright)."""
from __future__ import annotations

import contextlib
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextlib.contextmanager
def streamlit_server():
    port = free_port()
    p = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", str(port), "--server.headless", "true",
                          "--browser.gatherUsageStats", "false"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/_stcore/health", timeout=1); break
            except Exception:
                time.sleep(0.5)
        yield f"http://127.0.0.1:{port}"
    finally:
        p.terminate()
        with contextlib.suppress(Exception):
            p.wait(timeout=10)
