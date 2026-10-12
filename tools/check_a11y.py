"""
Audit d'accessibilité automatique (axe-core, règles WCAG 2.x A/AA) sur les 8 pages : python tools/check_a11y.py
Nécessite : pip install axe-playwright-python playwright   (axe.min.js est embarqué dans le paquet : pas d'accès réseau)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import axe_playwright_python
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tests"))
from _server import streamlit_server  # noqa: E402

PAGES = ["", "immatriculations", "permis", "securite-routiere", "etat-reseau", "routes-auto-ecoles", "diagnostic-recommandations", "donnees-methode"]
AXE = (Path(axe_playwright_python.__file__).parent / "axe.min.js").read_text(encoding="utf-8")
TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]


def main() -> int:
    total = {}
    with streamlit_server() as base, sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1670, "height": 1400})
        for name in PAGES:
            pg.goto(f"{base}/{name}", wait_until="networkidle"); pg.wait_for_selector(".page-title"); time.sleep(4)
            pg.evaluate(AXE)
            res = pg.evaluate("async (tags) => await axe.run(document, {runOnly: {type: 'tag', values: tags}, resultTypes: ['violations']})", TAGS)
            for v in res["violations"]:
                # Exception documentée : `aria-expanded` posé par Streamlit sur sa propre <section> de sidebar (composant du framework, non modifiable ici)
                v["nodes"] = [n for n in v["nodes"] if not (v["id"] == "aria-allowed-attr" and 'data-testid="stSidebar"' in n["html"])]
                if not v["nodes"]:
                    continue
                k = (v["id"], v["impact"], v["help"])
                d = total.setdefault(k, {"pages": set(), "n": 0, "ex": []})
                d["pages"].add(name or "vue-ensemble"); d["n"] += len(v["nodes"])
                if len(d["ex"]) < 2:
                    d["ex"].append(v["nodes"][0]["html"][:140])
        b.close()
    for (i, imp, h), d in sorted(total.items(), key=lambda x: x[0][1] or ""):
        print(f"[{imp}] {i} — {h} · {d['n']} élément(s) · pages : {', '.join(sorted(d['pages']))}")
        for e in d["ex"]:
            print("      ", e)
    print(f"{len(total)} type(s) de violation")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
