"""
Calculs territoriaux (pandas/numpy seulement) : agrégation routes + auto-écoles + population,
diagnostic à deux dimensions (infrastructure, formation) et test de robustesse.

Utilisé par tools/build_data.py (pré-calcul) ET par l'application (filtres interactifs).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SEUIL_QUINTILE = 0.80          # seuils fixes (non réglables)
SEUIL_TERCILE = 2 / 3
ORDRE_REGIONS = ["Grand Lomé", "Maritime", "Plateaux", "Centrale", "Kara", "Savanes"]


def routes_revetues(det: pd.DataFrame, definition: str = "observe") -> pd.Series:
    """Masque « revêtue ». observe : revêtement observé ∈ {Bitume, Béton, Pavé} ;
    admin : type « Route nationale revêtue » ; voiries urbaines et pistes selon le revêtement observé."""
    if definition == "admin":
        return (det["route_type"] == "Route nationale revêtue") | ((det["route_type"] != "Route nationale non revêtue") & det["revetue_observe"])
    return det["revetue_observe"]


def table_territoire(pref: pd.DataFrame, det: pd.DataFrame, ae: pd.DataFrame, niveau: str = "Préfecture",
                     ae_mode: str = "Toutes", definition: str = "observe", types: list[str] | None = None) -> pd.DataFrame:
    """Une ligne par préfecture (ou par région) : population, linéaire classé, ratios, auto-écoles."""
    d = det if not types else det[det["route_type"].isin(types)]
    d = d.assign(rev=routes_revetues(d, definition))
    base = pref[["cle", "prefecture", "region", "population"]].copy()
    km = d.groupby("cle_pref").apply(lambda x: pd.Series({"km": x["km"].sum(), "km_revetu": x.loc[x["rev"], "km"].sum()}), include_groups=False)
    t = base.merge(km, left_on="cle", right_index=True, how="left").fillna({"km": 0.0, "km_revetu": 0.0})
    a = ae if ae_mode == "Toutes" else ae[ae["agreee"]]
    n_ae = a.groupby("cle_pref").size().rename("ae")
    n_agr = ae[ae["agreee"]].groupby("cle_pref").size().rename("ae_agreees")
    n_all = ae.groupby("cle_pref").size().rename("ae_toutes")
    t = t.merge(n_ae, left_on="cle", right_index=True, how="left").merge(n_agr, left_on="cle", right_index=True, how="left") \
         .merge(n_all, left_on="cle", right_index=True, how="left")
    t[["ae", "ae_agreees", "ae_toutes"]] = t[["ae", "ae_agreees", "ae_toutes"]].fillna(0).astype(int)
    if niveau == "Région":
        t = t.groupby("region", as_index=False).agg(population=("population", "sum"), km=("km", "sum"), km_revetu=("km_revetu", "sum"),
                                                  ae=("ae", "sum"), ae_agreees=("ae_agreees", "sum"), ae_toutes=("ae_toutes", "sum"))
        t["cle"] = t["region"]; t["prefecture"] = t["region"]
    t["km_non_revetu"] = t["km"] - t["km_revetu"]
    t["km_10k"] = t["km"] / t["population"] * 1e4
    t["part_non_revetue"] = np.where(t["km"] > 0, t["km_non_revetu"] / t["km"].where(t["km"] > 0), np.nan)
    t["hab_par_ae"] = np.where(t["ae"] > 0, t["population"] / t["ae"].where(t["ae"] > 0), np.inf)
    t["ae_agr_100k"] = t["ae_agreees"] / t["population"] * 1e5
    t["zero_route"] = t["km"] <= 0
    t["zero_ae"] = t["ae"] <= 0
    t["niveau"] = niveau
    return t.reset_index(drop=True)


def _rang_defavorable(s: pd.Series, haut_defavorable: bool) -> pd.Series:
    v = s if haut_defavorable else -s
    return v.rank(pct=True, method="average")           # (0, 1] ; 1 = le plus défavorable


def diagnostic(t: pd.DataFrame, w_infra: float = 0.5, zeros_a_part: bool = False) -> pd.DataFrame:
    """Scores d'infrastructure, de formation et score pondéré (rangs percentiles, 1 = défavorable).
    zeros_a_part=True : les unités sans route classée ou sans auto-école (« zéros structurels ») sont retirées du classement
    (score NaN) et les rangs sont calculés sur les seules unités mesurées : le quintile ne mesure plus l'absence totale."""
    if zeros_a_part:
        z = t["zero_route"] | t["zero_ae"]
        d = diagnostic(t[~z], w_infra, False)
        out = t.merge(d[["cle", "score_infra", "score_formation", "score", "quintile_defavorable", "double_deficit", "rang"]], on="cle", how="left")
        out["quintile_defavorable"] = out["quintile_defavorable"].fillna(False).astype(bool)
        out["double_deficit"] = out["double_deficit"].fillna(False).astype(bool)
        out["zero_structurel"] = z.values
        return out
    d = t.copy()
    r_km = _rang_defavorable(d["km_10k"], False)
    r_nr = _rang_defavorable(d["part_non_revetue"].fillna(np.inf), True)
    r_nr = r_nr.where(~d["zero_route"], 1.0)             # zéro route classée : rang le plus défavorable (zéro structurel)
    d["score_infra"] = (r_km + r_nr) / 2
    r_h = _rang_defavorable(d["hab_par_ae"], True).where(~d["zero_ae"], 1.0)
    r_a = _rang_defavorable(d["ae_agr_100k"], False).where(~d["zero_ae"], 1.0)
    d["score_formation"] = (r_h + r_a) / 2
    d["score"] = w_infra * d["score_infra"] + (1 - w_infra) * d["score_formation"]
    d["quintile_defavorable"] = d["score"] >= SEUIL_QUINTILE
    d["double_deficit"] = (d["score_infra"] >= SEUIL_TERCILE) & (d["score_formation"] >= SEUIL_TERCILE)
    d["rang"] = d["score"].rank(ascending=False, method="min").astype(int)
    d["zero_structurel"] = d["zero_route"] | d["zero_ae"]
    return d


def robustesse(pref: pd.DataFrame, det: pd.DataFrame, ae: pd.DataFrame, niveau: str = "Préfecture",
               definition: str = "observe", zeros_a_part: bool = False) -> pd.DataFrame:
    """Nombre d'unités dans le quintile défavorable selon pondération (20/80, 50/50, 80/20) et auto-écoles (toutes/agréées)."""
    lignes, membres = [], {}
    base = diagnostic(table_territoire(pref, det, ae, niveau, "Toutes", definition), 0.5)
    zeros = set(base.loc[base["zero_structurel"], "prefecture"])
    for mode in ("Toutes", "Agréées"):
        t = table_territoire(pref, det, ae, niveau, mode, definition)
        for w in (0.2, 0.5, 0.8):
            dd = diagnostic(t, w, zeros_a_part)
            sel = set(dd.loc[dd["quintile_defavorable"], "prefecture"])
            membres[(mode, w)] = sel
            lignes.append({"auto_ecoles": mode, "poids_infra": w, "label": f"{round(w * 100)}/{round((1 - w) * 100)}",
                           "n_quintile": len(sel), "unites": ", ".join(sorted(sel))})
    r = pd.DataFrame(lignes)
    r["n_quintile_hors_zero"] = [int(len(set(u.split(", ")) - zeros)) if u else 0 for u in r["unites"]]
    stables = set.intersection(*membres.values()) if membres else set()
    r.attrs["stables"] = sorted(stables)
    r.attrs["union"] = sorted(set.union(*membres.values()))
    return r


def consensus(pref: pd.DataFrame, det: pd.DataFrame, ae: pd.DataFrame, niveau: str = "Préfecture", definition: str = "observe",
              zeros_a_part: bool = False) -> pd.DataFrame:
    """Diagnostic de consensus : moyenne des scores sur les 6 configurations (pondération 20/80, 50/50, 80/20 × auto-écoles toutes/agréées)
    et fréquence d'appartenance au quintile défavorable (`n_quintile`, de 0 à 6). Moins dépendant du choix du curseur."""
    frames = []
    for mode in ("Toutes", "Agréées"):
        t = table_territoire(pref, det, ae, niveau, mode, definition)
        for w in (0.2, 0.5, 0.8):
            d = diagnostic(t, w, zeros_a_part)[["prefecture", "score", "score_infra", "score_formation", "quintile_defavorable"]]
            frames.append(d)
    a = pd.concat(frames)
    g = a.groupby("prefecture").agg(score=("score", "mean"), score_infra=("score_infra", "mean"), score_formation=("score_formation", "mean"),
                                    n_quintile=("quintile_defavorable", "sum"))
    out = diagnostic(table_territoire(pref, det, ae, niveau, "Toutes", definition), 0.5, zeros_a_part).drop(columns=["score", "score_infra", "score_formation", "quintile_defavorable", "double_deficit", "rang"])
    out = out.merge(g, left_on="prefecture", right_index=True)
    out["quintile_defavorable"] = out["score"].fillna(-1) >= SEUIL_QUINTILE
    out["double_deficit"] = (out["score_infra"].fillna(-1) >= SEUIL_TERCILE) & (out["score_formation"].fillna(-1) >= SEUIL_TERCILE)
    out["rang"] = out["score"].rank(ascending=False, method="min").astype("Int64")
    out["n_quintile"] = out["n_quintile"].astype(int)
    return out.reset_index(drop=True)
