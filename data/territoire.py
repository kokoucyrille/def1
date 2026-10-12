"""Données par territoire (région / préfecture) des pages Immatriculations, Permis et Sécurité routière.

Les séries ouvertes d'immatriculations, de permis et d'accidents sont NATIONALES (aucun découpage territorial). Ces pages affichent donc :
  - un contexte territorial réellement disponible (population, auto-écoles, routes classées) ;
  - les séries thématiques par territoire UNIQUEMENT si un fichier data/processed/donnees_territoire.csv est fourni
    (colonnes : theme, annee, region, prefecture, valeur ; prefecture vide = valeur au niveau région).
Aucune valeur n'est estimée ni répartie au prorata de la population.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from data import loader as L

TERR_PATH = L.PROC / "donnees_territoire.csv"
TERR_COLS = ["theme", "annee", "region", "prefecture", "valeur"]
# thèmes attendus dans le fichier, par page : {code du fichier: libellé}
THEMES = {
    "immat": {"immatriculations": "Immatriculations"},
    "permis": {"permis": "Permis délivrés"},
    "securite": {"accidents": "Accidents", "blesses": "Blessés", "morts": "Morts"},
}
ALL_THEMES = {k: v for d in THEMES.values() for k, v in d.items()}


def _i(v) -> str:
    return L.fmt_int(v) if np.isfinite(v) else "n.d."


def _d(n: int):
    return lambda v: L.fmt_dec(v, n) if np.isfinite(v) else "n.d."


def _pct(v) -> str:
    return L.fmt_pct(100 * v, 0) if np.isfinite(v) else "aucune route classée"


# couches de contexte : libellé -> (colonne de base(), unité, format, palette de la carte)
CTX = {
    "Population (RGPH 2022)": ("population", "habitants", _i, "YlGnBu"),
    "Auto-écoles agréées": ("agreees", "auto-écoles agréées", _i, "YlGnBu"),
    "Auto-écoles non agréées": ("non_agr", "auto-écoles non agréées", _i, "YlGnBu"),
    "Auto-écoles (total)": ("total", "auto-écoles", _i, "YlGnBu"),
    "Auto-écoles pour 100 000 hab.": ("ae_100k", "auto-écoles / 100 000 hab.", _d(2), "YlGnBu"),
    "Habitants par auto-école": ("hab_par_ae", "habitants par auto-école", _i, "YlOrRd"),
    "Routes classées (km)": ("km", "km de routes classées", _d(0), "YlGnBu"),
    "Routes classées pour 10 000 hab. (km)": ("km_10k", "km / 10 000 hab.", _d(2), "YlGnBu"),
    "Routes non revêtues (km)": ("km_non_revetu", "km non revêtus", _d(0), "YlOrRd"),
    "Part de routes non revêtues": ("part_non_revetue", "part non revêtue", _pct, "YlOrRd"),
}
CTX_PAGE = {
    "immat": ["Population (RGPH 2022)", "Routes classées pour 10 000 hab. (km)", "Routes classées (km)"],
    "permis": ["Auto-écoles agréées", "Auto-écoles non agréées", "Auto-écoles (total)", "Auto-écoles pour 100 000 hab.", "Habitants par auto-école", "Population (RGPH 2022)"],
    "securite": ["Population (RGPH 2022)", "Routes classées (km)", "Routes classées pour 10 000 hab. (km)", "Routes non revêtues (km)", "Part de routes non revêtues"],
}


@st.cache_data(show_spinner=False)
def base() -> pd.DataFrame:
    """Une ligne par préfecture : population, routes classées, auto-écoles (agréées / non agréées)."""
    t = L.terr_table("Préfecture")[["cle", "prefecture", "region", "population", "km", "km_revetu", "km_non_revetu", "km_10k", "part_non_revetue"]]
    a = L.ae_repartition("Préfecture")[["region", "prefecture", "agreees", "non_agr", "total", "ae_100k", "hab_par_ae"]]
    d = t.merge(a, on=["region", "prefecture"], how="left")
    d["hab_par_ae"] = d["hab_par_ae"].replace([np.inf, -np.inf], np.nan)
    d["region"] = pd.Categorical(d["region"], L.ORDRE_REGIONS, ordered=True)
    return d.sort_values(["region", "prefecture"]).reset_index(drop=True).assign(region=lambda x: x.region.astype(str))


@st.cache_data(show_spinner=False)
def _lire(path: str, mtime: float) -> tuple[pd.DataFrame | None, str | None]:
    try:
        d = pd.read_csv(path, encoding="utf-8-sig", sep=None, engine="python", dtype=str)
    except Exception as e:  # noqa: BLE001 — message affiché dans la page
        return None, f"Fichier illisible : {e}"
    d.columns = [str(c).strip().lower() for c in d.columns]
    manque = [c for c in TERR_COLS if c not in d.columns]
    if manque:
        return None, f"Colonnes manquantes : {', '.join(manque)} (attendues : {', '.join(TERR_COLS)})."
    d = d[TERR_COLS].copy()
    for c in ("theme", "region", "prefecture"):
        d[c] = d[c].fillna("").astype(str).str.strip()
    d["theme"] = d["theme"].str.lower()
    d["annee"] = pd.to_numeric(d["annee"], errors="coerce")
    d["valeur"] = pd.to_numeric(d["valeur"].astype(str).str.replace(" ", "").str.replace(",", "."), errors="coerce")
    d = d.dropna(subset=["annee", "valeur"])
    d["annee"] = d["annee"].astype(int)
    inconnus = sorted(set(d.theme) - set(ALL_THEMES))
    if inconnus:
        return None, f"Thèmes inconnus : {', '.join(inconnus)} (attendus : {', '.join(ALL_THEMES)})."
    p = L.prefs()
    mauvaise_pref = sorted(set(d.prefecture[d.prefecture != ""]) - set(p.prefecture))
    if mauvaise_pref:
        return None, f"Préfectures inconnues : {', '.join(mauvaise_pref[:8])}{'…' if len(mauvaise_pref) > 8 else ''} (noms RGPH attendus)."
    # région : déduite de la préfecture quand elle est fournie
    reg_de = dict(zip(p.prefecture, p.region))
    d["region"] = np.where(d.prefecture != "", d.prefecture.map(reg_de), d.region)
    mauvaise_reg = sorted(set(d.region[d.region != ""]) - set(L.ORDRE_REGIONS))
    if mauvaise_reg:
        return None, f"Régions inconnues : {', '.join(mauvaise_reg)} (attendues : {', '.join(L.ORDRE_REGIONS)})."
    d = d[d.region != ""]
    if d.empty:
        return None, "Le fichier ne contient aucune ligne exploitable (région ou préfecture manquante, valeurs vides)."
    return d, None


def donnees() -> tuple[pd.DataFrame | None, str | None]:
    """(table, message d'erreur). (None, None) : fichier absent."""
    if not TERR_PATH.exists():
        return None, None
    return _lire(str(TERR_PATH), TERR_PATH.stat().st_mtime)


def theme_dispo(theme: str) -> bool:
    d, _ = donnees()
    return d is not None and (d.theme == theme).any()


def serie_theme(theme: str, a0: int, a1: int) -> dict | None:
    """Somme de la période [a0, a1] par préfecture (niveau « préfecture ») ou par région (niveau « région ») ; None si aucune donnée.
    Si un thème contient des lignes au niveau préfecture, les lignes au niveau région sont ignorées (jamais de double compte)."""
    d, _ = donnees()
    if d is None:
        return None
    d = d[(d.theme == theme) & d.annee.between(a0, a1)]
    if d.empty:
        return None
    pf = d[d.prefecture != ""]
    if len(pf):
        return {"niveau": "préfecture", "valeurs": pf.groupby("prefecture").valeur.sum(), "annees": sorted(pf.annee.unique())}
    return {"niveau": "région", "valeurs": d.groupby("region").valeur.sum(), "annees": sorted(d.annee.unique())}


def couches(page: str) -> list[str]:
    th = [f"{lib} (période)" for k, lib in THEMES[page].items() if theme_dispo(k)] + [f"{lib} pour 100 000 hab." for k, lib in THEMES[page].items() if theme_dispo(k)]
    return th + CTX_PAGE[page]


def couche(page: str, nom: str, a0: int, a1: int) -> dict:
    """Résout une couche : {df (base + colonne val), label, unite, fmt, palette, niveau, theme}."""
    b = base().copy()
    if nom in CTX:
        col, unite, fmt, pal = CTX[nom]
        b["val"] = b[col].astype(float)
        return dict(df=b, label=nom, unite=unite, fmt=fmt, palette=pal, niveau="préfecture", theme=None, region_val=None)
    pour100k = nom.endswith("pour 100 000 hab.")
    lib = nom.replace(" pour 100 000 hab.", "").replace(" (période)", "")
    k = next(k for k, v in THEMES[page].items() if v == lib)
    s = serie_theme(k, a0, a1)
    pal = "YlOrRd" if k in ("accidents", "blesses", "morts") else "YlGnBu"
    if s is None:
        b["val"] = np.nan
        return dict(df=b, label=nom, unite=lib.lower(), fmt=_i, palette=pal, niveau="préfecture", theme=k, region_val=None)
    if s["niveau"] == "préfecture":
        b["val"] = b.prefecture.map(s["valeurs"]).astype(float)
        if pour100k:
            b["val"] = 1e5 * b["val"] / b["population"]
    else:                                                    # valeur régionale reportée sur les préfectures de la région
        pop_reg = b.groupby("region").population.sum()
        v = b.region.map(s["valeurs"]).astype(float)
        b["val"] = 1e5 * v / b.region.map(pop_reg) if pour100k else v
    return dict(df=b, label=nom, unite=(f"{lib.lower()} / 100 000 hab." if pour100k else lib.lower()), fmt=(_d(1) if pour100k else _i), palette=pal,
                niveau=s["niveau"], theme=k, region_val=s["valeurs"] if s["niveau"] == "région" else None, serie=s)
