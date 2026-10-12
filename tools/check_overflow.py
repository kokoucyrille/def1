"""Détecte les panneaux dont le contenu dépasse la hauteur fixe : python tools/check_overflow.py [port]"""
import sys, time
from playwright.sync_api import sync_playwright
PORT = sys.argv[1] if len(sys.argv) > 1 else "8501"
PAGES = ["", "immatriculations", "permis", "securite-routiere", "etat-reseau", "routes-auto-ecoles", "diagnostic-recommandations"]
JS = """() => [...document.querySelectorAll('[class*="st-key-panel_"]')].map(p => {
  const r = p.getBoundingClientRect(); let bottom = 0;
  p.querySelectorAll('*').forEach(e => { const b = e.getBoundingClientRect(); if (b.height > 0 && b.width > 0 && !e.closest('.tip')) bottom = Math.max(bottom, b.bottom); });
  if (p.querySelector('[data-testid="stDataFrame"]')) return {key: 'dataframe', h: 0, over: 0};
  const key = [...p.classList].find(c => c.startsWith('st-key-panel_'));
  return {key, h: Math.round(r.height), over: Math.round(bottom - r.bottom)}; })"""
bad = 0
with sync_playwright() as p:
    b = p.chromium.launch()
    for w, h in ((1670, 942), (1366, 768)):
        pg = b.new_page(viewport={"width": w, "height": 2400})
        for name in PAGES:
            pg.goto(f"http://localhost:{PORT}/{name}", wait_until="networkidle"); pg.wait_for_selector(".page-title"); time.sleep(4)
            for r in pg.evaluate(JS):
                if r["over"] > 10:
                    bad += 1; print(f"{w}  {name or 'vue-ensemble':18s} {r['key']:34s} hauteur {r['h']}  dépasse de {r['over']} px")
    b.close()
print("panneaux en débordement :", bad)
