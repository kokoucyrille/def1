"""
Recette en environnement vierge : crée un venv, installe UNIQUEMENT requirements.txt, démarre l'application et charge les 8 pages dans Chromium.
    python tools/check_clean_env.py        (nécessite Internet pour pip et playwright installé côté système)
Cette recette a détecté une dépendance cachée (scipy, appelé par pandas pour Spearman) : désormais calculé sans scipy.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["", "immatriculations", "permis", "securite-routiere", "etat-reseau", "routes-auto-ecoles", "diagnostic-recommandations", "donnees-methode"]


def main() -> int:
    tmp = Path(tempfile.mkdtemp())
    subprocess.run([sys.executable, "-m", "venv", str(tmp / "venv")], check=True)
    py = str(tmp / "venv" / "bin" / "python")
    subprocess.run([py, "-m", "pip", "install", "-q", "-r", str(ROOT / "requirements.txt")], check=True)
    port = 8612
    srv = subprocess.Popen([py, "-m", "streamlit", "run", "app.py", "--server.port", str(port), "--server.headless", "true", "--browser.gatherUsageStats", "false"],
                           cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    bad = 0
    try:
        for _ in range(60):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/_stcore/health", timeout=1); break
            except Exception:
                time.sleep(0.5)
        with sync_playwright() as p:
            b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1670, "height": 942})
            for n in PAGES:
                t = time.time(); pg.goto(f"http://127.0.0.1:{port}/{n}", wait_until="networkidle")
                try:
                    pg.wait_for_selector(".page-title", timeout=60000)
                    exc = pg.locator('[data-testid="stException"]').count()
                except Exception:
                    exc = 1
                bad += exc > 0
                print(f"{n or 'vue-ensemble':18s} {time.time() - t:4.1f} s · exceptions : {exc}")
            b.close()
    finally:
        srv.terminate()
    print("recette environnement vierge :", "OK" if not bad else f"{bad} page(s) en erreur")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
