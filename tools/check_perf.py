"""Performance perçue : temps jusqu'au dessin complet des graphiques (caches chauds) et réponse à un filtre. python tools/check_perf.py"""
import sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tests"))
from _server import streamlit_server  # noqa: E402

PAGES = (("", 3), ("immatriculations", 4), ("permis", 4), ("securite-routiere", 4), ("etat-reseau", 3), ("routes-auto-ecoles", 6), ("diagnostic-recommandations", 3))
LIMITE = 3.5   # secondes (objectif 3 s, marge de mesure)
with streamlit_server() as base, sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1670, "height": 942}); pire = 0
    t0 = time.time(); pg.goto(base + "/", wait_until="networkidle"); pg.wait_for_selector(".page-title"); print(f"premier chargement à froid : {time.time() - t0:.1f} s"); time.sleep(2)
    for path, nb in PAGES:
        ts = []
        for _ in range(3):
            t = time.time(); pg.goto(f"{base}/{path}", wait_until="commit")
            pg.wait_for_function(f"document.querySelectorAll('.js-plotly-plot .main-svg').length >= {nb}", timeout=30000); ts.append(time.time() - t)
        pire = max(pire, max(ts)); print(f"{path or 'vue-ensemble':18s} graphiques dessinés en {min(ts):.1f}–{max(ts):.1f} s")
    pg.goto(base + "/", wait_until="networkidle"); pg.wait_for_selector(".page-title"); time.sleep(2)
    t = time.time(); pg.locator('section[data-testid="stSidebar"] [data-testid="stSelectbox"]').first.click(); pg.get_by_role("option", name="2015").click()
    pg.wait_for_function("document.body.innerText.includes('Accidents 2015')", timeout=10000); rep = time.time() - t
    print(f"réponse à un filtre : {rep:.2f} s"); b.close()
assert pire <= LIMITE and rep <= 1.5, f"performance insuffisante (pire page {pire:.1f} s, filtre {rep:.2f} s)"
print("performance : OK")
