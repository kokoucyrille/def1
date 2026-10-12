"""Captures d'écran de chaque page (Playwright/Chromium) : python tools/capture.py [port]"""
import sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = sys.argv[1] if len(sys.argv) > 1 else "8501"
PAGES = ["vue-ensemble", "immatriculations", "permis", "securite-routiere", "etat-reseau", "routes-auto-ecoles", "diagnostic-recommandations", "donnees-methode"]
OUT = Path(__file__).resolve().parent.parent / "docs" / "captures"
OUT.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch()
    for (w, h) in ((1670, 942), (1366, 768)):
        pg = b.new_page(viewport={"width": w, "height": h})
        for name in PAGES:
            pg.goto(f"http://localhost:{PORT}/{"" if name == "vue-ensemble" else name}", wait_until="networkidle")
            pg.wait_for_selector(".page-title", timeout=60000); time.sleep(3.5)
            pg.screenshot(path=str(OUT / f"{name}_{w}x{h}.png"))
            # version haute : tout le contenu de la page (défilement interne de Streamlit)
            H = pg.evaluate("document.querySelector('[data-testid=stMain]').scrollHeight")
            pg.set_viewport_size({"width": w, "height": max(h, min(H + 140, 3200))}); time.sleep(2.5)
            pg.screenshot(path=str(OUT / f"{name}_{w}_pleine.png"))
            pg.set_viewport_size({"width": w, "height": h})
    b.close()
print("captures OK")
