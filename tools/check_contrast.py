"""
Audit de contraste WCAG AA dans le navigateur : python tools/check_contrast.py
Pour chaque texte visible : couleur du texte vs fond effectif (premier ancêtre opaque) ; seuil 4,5:1 (3:1 si grand texte).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tests"))
from _server import streamlit_server  # noqa: E402

PAGES = ["", "immatriculations", "permis", "securite-routiere", "etat-reseau", "routes-auto-ecoles", "diagnostic-recommandations", "donnees-methode"]
JS = r"""() => {
  const parse = c => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(',').map(x => parseFloat(x)); return {r:p[0], g:p[1], b:p[2], a: p.length > 3 ? p[3] : 1}; };
  const lum = ({r,g,b}) => { const f = v => { v/=255; return v <= .03928 ? v/12.92 : Math.pow((v+.055)/1.055, 2.4); }; return .2126*f(r)+.7152*f(g)+.0722*f(b); };
  const bgOf = el => { let e = el; let acc = null;
    while (e) { const c = parse(getComputedStyle(e).backgroundColor); if (c && c.a > 0) { if (c.a >= .99) return acc ? mix(acc, c) : c; acc = acc ? acc : c; } e = e.parentElement; }
    return {r:255,g:255,b:255,a:1}; };
  const mix = (top, base) => ({r: top.r*top.a + base.r*(1-top.a), g: top.g*top.a + base.g*(1-top.a), b: top.b*top.a + base.b*(1-top.a), a:1});
  const out = {};
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n; while ((n = walker.nextNode())) {
    const t = n.textContent.trim(); if (!t) continue;
    const el = n.parentElement; if (!el || el.closest('script,style,svg,.js-plotly-plot,.tip,[data-testid="stDataFrame"],[data-testid="stSliderThumbValue"]')) continue;
    const cs = getComputedStyle(el); if (cs.visibility === 'hidden' || cs.display === 'none' || parseFloat(cs.opacity) < .5) continue;
    const r = el.getBoundingClientRect(); if (r.width < 2 || r.height < 2) continue;
    const fg = parse(cs.color); if (!fg) continue; let bg = bgOf(el);
    const fgm = fg.a < 1 ? mix(fg, bg) : fg;
    const L1 = lum(fgm), L2 = lum(bg); const ratio = (Math.max(L1,L2)+.05)/(Math.min(L1,L2)+.05);
    const size = parseFloat(cs.fontSize), bold = parseInt(cs.fontWeight) >= 700; const large = size >= 24 || (size >= 18.66 && bold);
    const need = large ? 3 : 4.5;
    if (ratio < need) { const k = `${cs.color}|${bg.r|0},${bg.g|0},${bg.b|0}|${el.className.toString().slice(0,40)}`;
      out[k] = out[k] || {ratio: +ratio.toFixed(2), need, fg: cs.color, bg: `rgb(${bg.r|0},${bg.g|0},${bg.b|0})`, cls: el.className.toString().slice(0,60), tag: el.tagName, size, sample: t.slice(0,40), n: 0}; out[k].n++; }
  }
  // textes des graphiques Plotly (SVG) : fill du <text> vs fond du panneau
  document.querySelectorAll('.js-plotly-plot svg text').forEach(tx => {
    const t = tx.textContent.trim(); if (!t) return;
    const cs = getComputedStyle(tx); if (cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return;
    const r = tx.getBoundingClientRect(); if (r.width < 2) return;
    const fg = parse(cs.fill); if (!fg) return; const fo = parseFloat(cs.fillOpacity); fg.a = (isNaN(fo) ? 1 : fo) * (fg.a);
    const bg = bgOf(tx.closest('.js-plotly-plot')); const fgm = fg.a < 1 ? mix(fg, bg) : fg;
    const L1 = lum(fgm), L2 = lum(bg); const ratio = (Math.max(L1,L2)+.05)/(Math.min(L1,L2)+.05);
    const size = parseFloat(cs.fontSize); const need = size >= 24 ? 3 : 4.5;
    if (ratio < need) { const k = `svg|${cs.fill}|${bg.r|0},${bg.g|0},${bg.b|0}`; out[k] = out[k] || {ratio: +ratio.toFixed(2), need, fg: cs.fill, bg: `rgb(${bg.r|0},${bg.g|0},${bg.b|0})`, cls: 'plotly-svg', tag: 'text', size, sample: t.slice(0,40), n: 0}; out[k].n++; }
  });
  return Object.values(out);
}"""


def main() -> int:
    bad = []
    with streamlit_server() as base, sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1670, "height": 1400})
        for name in PAGES:
            pg.goto(f"{base}/{name}", wait_until="networkidle"); pg.wait_for_selector(".page-title"); time.sleep(4)
            for r in pg.evaluate(JS):
                bad.append((name or "vue-ensemble", r))
        b.close()
    seen = set()
    for page, r in sorted(bad, key=lambda x: x[1]["ratio"]):
        k = (r["fg"], r["bg"], r["cls"])
        if k in seen:
            continue
        seen.add(k)
        print(f"{page:18s} {r['ratio']:5.2f} (< {r['need']})  fg {r['fg']:22s} bg {r['bg']:18s} .{r['cls'][:40]:40s} {r['size']}px  « {r['sample']} » ×{r['n']}")
    print(f"{len(seen)} combinaisons sous le seuil AA")
    return 1 if seen else 0


if __name__ == "__main__":
    sys.exit(main())
