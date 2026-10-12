"""
Tests navigateur (Playwright + Chromium) : python tests/browser_test.py
  1. clic réel sur la carte -> la fiche territoire change de préfecture (et le classement)
  2. aucune icône ⓘ / infobulle sur les KPI, titres de sections et de filtres (8 pages)
  3. cadrage : la carte de Togo n'est jamais rognée (Vue d'ensemble, Routes & auto-écoles, Diagnostic) à 1670×942 et 1366×768
"""
from __future__ import annotations

import io
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _server import streamlit_server  # noqa: E402


def open_page(pg, base, path):
    pg.goto(f"{base}/{path}", wait_until="networkidle")
    pg.wait_for_selector(".page-title", timeout=60000)
    time.sleep(4)


def polygon_pixels(img, n=4):
    """Choisit n pixels bien espacés à l'intérieur de polygones colorés (hors colorbar/légende), sans supposer de position."""
    a = np.array(img.convert("RGB")).astype(int)
    h, w, _ = a.shape
    sat = (a.max(axis=2) - a.min(axis=2)) > 25
    sat[:, :95] = False; sat[:, int(w * 0.72):] = False          # colorbar à gauche, légende en surimpression à droite
    # on évite les lignes/points de couche : un vrai polygone est une zone large (voisinage 9×9 entièrement coloré)
    from numpy.lib.stride_tricks import sliding_window_view
    full = sliding_window_view(sat, (9, 9)).all(axis=(2, 3))
    ys, xs = np.where(full)
    if len(ys) == 0:
        return []
    order = np.argsort(ys)
    picks = []
    for i in np.linspace(0, len(ys) - 1, n * 6).astype(int):
        y, x = ys[order[i]] + 4, xs[order[i]] + 4
        if all(abs(y - py) > h * 0.12 for _, py in picks):
            picks.append((int(x), int(y)))
        if len(picks) == n:
            break
    return picks


def _titre(pg):
    return pg.inner_text(".st-key-panel_carte_fiche .panel-title").split("\n")[0]


def _clic(pg, box, fx, fy):
    pg.mouse.move(box["x"] + box["width"] * fx, box["y"] + box["height"] * fy); time.sleep(0.5)
    pg.mouse.down(); time.sleep(0.1); pg.mouse.up(); time.sleep(3.2)


def test_clic_carte(pg, base):
    """Clic réel dans le pays (toutes couches affichées) -> la fiche et la sidebar passent à la préfecture cliquée ; idem sur le classement."""
    open_page(pg, base, "routes-auto-ecoles")
    assert "National" in _titre(pg)
    el = pg.query_selector('.st-key-panel_carte_main [data-testid="stPlotlyChart"]')
    box = el.bounding_box()
    pts = polygon_pixels(Image.open(io.BytesIO(el.screenshot())), n=4)      # pixels réellement colorés par un polygone : indépendant de la mise en page
    assert len(pts) >= 3, "aucun polygone détecté sur la carte"
    ok = []
    for px, py in pts:
        _clic(pg, box, px / box["width"], py / box["height"])
        t = _titre(pg)
        if "National" not in t:
            nom = t.split("—")[-1].strip()
            vals = pg.eval_on_selector_all('section[data-testid="stSidebar"] [data-testid="stSelectbox"]', 'els => els.map(e => (e.querySelector("input") || {}).value)')
            assert nom in vals, f"sidebar non synchronisée : {nom} absent de {vals}"
            ok.append(nom)
        pg.click("text=Réinitialiser"); time.sleep(3)
    assert len(ok) >= len(pts) - 1, f"clic carte : {len(ok)}/{len(pts)} sélections réussies"
    print(f"OK clic carte -> {ok}")
    # classement : clic sur une barre
    rb = pg.query_selector('.st-key-panel_carte_classement [data-testid="stPlotlyChart"]').bounding_box()
    sel = None
    for fy in (0.92, 0.82, 0.72, 0.62, 0.52, 0.42):      # on ne clique que sur une barre réellement survolée (infobulle Plotly affichée)
        pg.mouse.move(rb["x"] + rb["width"] * 0.45, rb["y"] + rb["height"] * fy); time.sleep(0.8)
        if not pg.evaluate("(document.querySelector('.st-key-panel_carte_classement .hoverlayer')?.textContent || '').length > 0"):
            continue
        pg.mouse.down(); time.sleep(0.15); pg.mouse.up(); time.sleep(4)
        if "National" not in _titre(pg):
            sel = _titre(pg); break
    assert sel, "clic sur le classement : aucune sélection"
    print(f"OK clic classement -> {sel}")


def test_aucune_infobulle(pg, base):
    """Plus aucune icône ⓘ (KPI, titres de sections, titres de filtres) sur les pages."""
    for path in ("", "immatriculations", "permis", "securite-routiere", "etat-reseau", "routes-auto-ecoles", "diagnostic-recommandations"):
        open_page(pg, base, path)
        assert pg.locator(".tip").count() == 0, f"infobulle ⓘ encore présente ({path or 'vue-ensemble'})"
        assert pg.locator(".kpi").count() == 0 or pg.locator(".kpi .kpi__title").count() > 0
    print("OK : aucune infobulle ⓘ sur les 8 pages")


def togo_bbox(img, excl_left=90, excl_right=0):  # excl_left : colorbar / légende en surimpression
    a = np.array(img.convert("RGB")).astype(int)
    mask = (a.max(axis=2) - a.min(axis=2)) > 60
    mask[:, :excl_left] = False
    if excl_right:
        mask[:, -excl_right:] = False
    ys = np.where(mask.sum(axis=1) > 3)[0]
    return ys.min(), ys.max(), a.shape[0]


def test_cadrage_cartes(browser, base):
    cas = (("", "acc_carte", 0, 90), ("routes-auto-ecoles", "carte_main", 230, 90), ("diagnostic-recommandations", "diag_score", 0, 90), ("etat-reseau", "res_explorateur", 0, 190))
    for w, h in ((1670, 942), (1366, 768)):
        pg = browser.new_page(viewport={"width": w, "height": h})
        for path, key, excl_r, excl_l in cas:
            open_page(pg, base, path)
            el = pg.query_selector(f'.st-key-panel_{key} [data-testid="stPlotlyChart"]')
            el.scroll_into_view_if_needed(); time.sleep(1.5)
            y0, y1, H = togo_bbox(Image.open(io.BytesIO(el.screenshot())), excl_left=excl_l, excl_right=excl_r)
            assert y0 > 4 and y1 < H - 5, f"carte rognée ({key}, {w}×{h}) : emprise {y0}-{y1} sur {H} px"
            print(f"OK cadrage {key} {w}x{h} : emprise {y0}-{y1} / {H} px")
        pg.close()


def test_osm_repli_hors_connexion(pg, base):
    """Option Folium : hors connexion (CDN bloqué), un message clair s'affiche dans la carte au lieu d'une zone vide."""
    pg.route("**/*", lambda route: route.abort() if not route.request.url.startswith(base) and not route.request.url.startswith("about:") and not route.request.url.startswith("data:") else route.continue_())
    open_page(pg, base, "routes-auto-ecoles")
    cb = pg.locator('section[data-testid="stSidebar"] input[type=checkbox]').first
    txt = pg.locator('section[data-testid="stSidebar"]').get_by_text("Fond OpenStreetMap (Internet requis)")
    assert txt.is_visible(), "le libellé de la case OSM n'est pas visible"
    txt.click(); time.sleep(7)
    assert cb.is_checked(), "case « Fond OpenStreetMap » non cochée"
    fr = pg.frame_locator("iframe").first
    fr.locator("#osm-offline").wait_for(state="visible", timeout=15000)
    assert "indisponible hors connexion" in fr.locator("#osm-offline").inner_text()
    print("OK carte OSM : repli propre hors connexion (message affiché)")


if __name__ == "__main__":
    with streamlit_server() as base, sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1670, "height": 942})
        test_aucune_infobulle(pg, base)
        test_clic_carte(pg, base)
        test_cadrage_cartes(b, base)
        test_osm_repli_hors_connexion(b.new_page(viewport={"width": 1670, "height": 942}), base)
        b.close()
    print("tests navigateur : OK")
