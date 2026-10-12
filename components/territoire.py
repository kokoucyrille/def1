"""Section « Données par territoire » des pages Immatriculations, Permis et Sécurité routière :
carte colorée par préfecture (zoom sur la région filtrée, clic = sélection) et les chiffres clés du territoire choisi, propres à chaque menu."""
from __future__ import annotations

import numpy as np
import streamlit as st

from components import charts, maps
from components.filters import set_territory
from components.kpi_cards import create_kpi_card
from components.ui import banner, page_title, panel
from data import territoire as T
from data.loader import fmt_int as i0, fmt_pct as p1


def _scope(b, region, pref):
    if pref:
        return b[b.prefecture == pref]
    return b[b.region == region] if region else b


def _cartes(page: str, sc, a0: int, a1: int, f: dict, pref: str | None, region: str | None) -> list[tuple[str, str, str, str]]:
    """KPI du territoire choisi, en lien avec le menu : (titre, valeur, icône, couleur)."""
    pop, km, kmn = sc.population.sum(), sc.km.sum(), sc.km_non_revetu.sum()
    agr, non = int(sc.agreees.sum()), int(sc.non_agr.sum())
    if page == "immat":
        cards = [("Population (RGPH 2022)", i0(pop), "fa-users", "blue"), ("Routes classées (km)", i0(km), "fa-map", "yellow")]
    elif page == "permis":
        tot = agr + non
        cards = [("Auto-écoles agréées / non agréées", f"{i0(agr)} / {i0(non)}", "fa-building-columns", "green"),
                 ("Habitants par auto-école", i0(pop / tot) if tot else "aucune", "fa-users", "blue")]
    else:
        cards = [("Routes non revêtues (km)", i0(kmn), "fa-map", "yellow"), ("Part de routes non revêtues", p1(100 * kmn / km, 0) if km > 0 else "n.d.", "fa-layer-group", "red"),
                 ("Population exposée (RGPH 2022)", i0(pop), "fa-users", "blue")]
    # série thématique du menu (immatriculations, permis, accidents…) : affichée seulement si un fichier territorial la fournit
    k = {"Accidents": "accidents", "Blessés": "blesses", "Morts": "morts"}.get(f.get("indic")) if page == "securite" else list(T.THEMES[page])[0]
    ser = T.serie_theme(k, a0, a1) if k else None
    if ser is not None:
        lib = T.ALL_THEMES[k]
        if ser["niveau"] == "préfecture":
            cards.append((f"{lib} {a0}–{a1}", i0(ser["valeurs"].reindex(sc.prefecture).sum()), "fa-database", "purple"))
        elif not pref:
            v = ser["valeurs"].get(region) if region else ser["valeurs"].sum()
            if v is not None and np.isfinite(v):
                cards.append((f"{lib} {a0}–{a1}", i0(v), "fa-database", "purple"))
    return cards


def section(page: str, f: dict, region: str | None, pref: str | None, a0: int, a1: int) -> None:
    page_title("fa-map", "Contexte territorial", "La carte et les chiffres décrivent le contexte disponible ; les séries nationales ne sont pas ventilées par territoire.", section=True)
    _, err = T.donnees()
    if err:
        banner(f"Fichier donnees_territoire.csv non exploitable. {err}")
    cinfo = T.couche(page, f["couche"], a0, a1)
    b, df = T.base(), cinfo["df"]
    cards = _cartes(page, _scope(b, region, pref), a0, a1, f, pref, region)
    H = max(430, 138 * len(cards) + 30)
    c1, c2 = st.columns([1.35, 1], gap="small")
    with c1:
        with panel(f"terr_carte_{page}", f"{cinfo['label']} — par préfecture", "fa-map", f"terr_carte_{page}", height=H):
            fig = maps.choropleth(df, "val", cinfo["unite"], cinfo["fmt"], H - 59, cinfo["palette"], selected=pref, region=region, zoom_region=region, width=720)
            v = charts.clicked_value(charts.show(fig, f"terr_map_{page}", select=True))
            if v and v != pref and v in set(df.prefecture):
                set_territory(v); st.rerun()
    with c2:
        for t, v_, ic, var in cards:
            st.markdown(create_kpi_card(f"{t} · {pref or region or 'Togo'}", v_, ic, var), unsafe_allow_html=True)
