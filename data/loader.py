"""Lecture des tables pré-calculées (data/processed) + formats français + chiffres clés (`facts`)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

PROC = Path(__file__).resolve().parent / "processed"
NBSP = "\u00a0"
ALL_REGIONS, ALL_PREFS = "Toutes les régions", "Toutes les préfectures"
ORDRE_REGIONS = ["Grand Lomé", "Maritime", "Plateaux", "Centrale", "Kara", "Savanes"]
ETAT_COULEURS = {"BON": "#016b4b", "MOYEN": "#fdcf00", "MAUVAIS": "#f20e36", "TRAVAUX": "#a2b8cc"}
ETAT_LIBELLES = {"BON": "Bon état", "MOYEN": "État moyen", "MAUVAIS": "Mauvais état", "TRAVAUX": "Travaux en cours"}


# ------------------------------------------------------------------------------ formats français
def fmt_int(v) -> str:
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "n.d."
    return f"{int(round(float(v))):,}".replace(",", NBSP)


def fmt_dec(v, n: int = 1) -> str:
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "n.d."
    return f"{float(v):,.{n}f}".replace(",", NBSP).replace(".", ",")


def fmt_pct(v, n: int = 1) -> str:
    s = fmt_dec(v, n)
    return s if s == "n.d." else f"{s}{NBSP}%"


def fmt_signed_pct(v, n: int = 0) -> str:
    s = fmt_dec(abs(v), n)
    return f"{'+' if v >= 0 else '−'}{s}{NBSP}%"


# ------------------------------------------------------------------------------ lecture des tables
@st.cache_data(show_spinner=False)
def table(name: str) -> pd.DataFrame:
    return pd.read_csv(PROC / f"{name}.csv")


@st.cache_data(show_spinner=False)
def geojson(name: str) -> dict:
    return json.loads((PROC / f"{name}.geojson").read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def parc() -> pd.DataFrame:
    return table("parc").set_index("annee")


@st.cache_data(show_spinner=False)
def permis() -> pd.DataFrame:
    return table("permis").set_index("annee")


@st.cache_data(show_spinner=False)
def securite() -> pd.DataFrame:
    return table("securite").set_index("annee")


def prefs() -> pd.DataFrame:
    return table("population_prefectures")


def prefectures_of(region: str | None) -> list[str]:
    p = prefs()
    p = p if not region or region == ALL_REGIONS else p[p.region == region]
    return sorted(p.prefecture)


@st.cache_data(show_spinner=False)
def pop_pays() -> int:
    return int(prefs().population.sum())


# ------------------------------------------------------------------------------ auto-écoles : répartition agréées / non agréées
@st.cache_data(show_spinner=False)
def ae_repartition(niveau: str = "Préfecture") -> pd.DataFrame:
    """Auto-écoles par région ou préfecture : agréées (dont antennes), non agréées, total, part agréée, ratios à la population.
    « Agréée » = statut Agréée + Agréée (antenne), comme partout dans le tableau de bord. Niveau « Région » = somme des préfectures (agrégé)."""
    a, p = table("auto_ecoles"), prefs()
    c = a.assign(agr_princ=(a.statut == "Agréée"), antenne=(a.statut == "Agréée (antenne)"), non_agr=(a.statut == "Non agréée")).groupby("cle_pref")[["agr_princ", "antenne", "non_agr"]].sum()
    d = p[["region", "prefecture", "cle", "population"]].merge(c, left_on="cle", right_index=True, how="left").fillna({"agr_princ": 0, "antenne": 0, "non_agr": 0})
    keys = ["region"] if niveau == "Région" else ["region", "prefecture"]
    g = d.groupby(keys, as_index=False)[["population", "agr_princ", "antenne", "non_agr"]].sum()
    g[["agr_princ", "antenne", "non_agr"]] = g[["agr_princ", "antenne", "non_agr"]].astype(int)
    g["agreees"] = g.agr_princ + g.antenne
    g["total"] = g.agreees + g.non_agr
    g["part_agreees"] = np.where(g.total > 0, 100 * g.agreees / g.total.where(g.total > 0, 1), np.nan)
    g["hab_par_ae"] = np.where(g.total > 0, g.population / g.total.where(g.total > 0, 1), np.nan)
    g["ae_100k"] = 1e5 * g.total / g.population
    g["agr_100k"] = 1e5 * g.agreees / g.population
    g["non_agr_100k"] = 1e5 * g.non_agr / g.population
    if niveau == "Région":
        g = g.set_index("region").reindex(ORDRE_REGIONS).reset_index()
    return g


# ------------------------------------------------------------------------------ chiffres clés
@st.cache_data(show_spinner=False)
def facts() -> dict:
    """Tous les chiffres cités dans les infobulles, messages clés et recommandations (calculés, jamais saisis)."""
    from data import diag
    P, M, S = parc(), permis(), securite()
    F: dict = {}
    F["pop"] = pop_pays()
    F["immat22"], F["immat02"] = P.loc[2022, "Total"], P.loc[2002, "Total"]
    F["ratio_22_02"] = F["immat22"] / F["immat02"]
    F["immat_x10"] = F["immat22"] / P.loc[2010, "Total"]
    F["part2r_22"] = 100 * P.loc[2022, "Deux-roues"] / F["immat22"]
    F["part2r_02"] = 100 * P.loc[2002, "Deux-roues"] / F["immat02"]
    F["part_hausse_2r"] = 100 * (P.loc[2022, "Deux-roues"] - P.loc[2002, "Deux-roues"]) / (F["immat22"] - F["immat02"])
    F["voitures22"], F["pl22"], F["deuxr22"] = P.loc[2022, "Voitures"], P.loc[2022, "Poids lourds"], P.loc[2022, "Deux-roues"]
    F["chute2020"] = 100 * (P.loc[2020, "Total"] / P.loc[2019, "Total"] - 1)
    h13 = M.drop(index=2013)
    F["permis22"], F["permisA22"] = M.loc[2022, "Total"], M.loc[2022, "Moto (A)"]
    F["part_A22"] = 100 * F["permisA22"] / F["permis22"]
    F["permisA_cumul"], F["permis_cumul"] = h13["Moto (A)"].sum(), h13["Total"].sum()
    F["part_A_cumul"] = 100 * F["permisA_cumul"] / F["permis_cumul"]
    F["acc22"], F["bl22"], F["morts22"] = S.loc[2022, "accidents"], S.loc[2022, "blesses"], S.loc[2022, "morts"]
    F["acc10"], F["bl10"], F["morts10"] = S.loc[2010, "accidents"], S.loc[2010, "blesses"], S.loc[2010, "morts"]
    F["acc_x"] = F["acc22"] / F["acc10"]
    F["morts_var"] = 100 * (F["morts22"] / F["morts10"] - 1)
    F["morts100k22"] = 1e5 * F["morts22"] / F["pop"]
    F["acc10kveh22"] = 1e4 * F["acc22"] / F["immat22"]
    F["morts100acc22"], F["morts100acc10"] = 100 * F["morts22"] / F["acc22"], 100 * F["morts10"] / F["acc10"]
    j = pd.concat([P["Deux-roues"], S["morts"]], axis=1, join="inner").dropna()
    F["spearman"], F["spearman_n"] = j["Deux-roues"].rank().corr(j["morts"].rank()), len(j)
    nat = table("reseau_etat_national").set_index("categorie")
    rr = nat.loc["ROUTES REVETUES"]
    F["pct_bon_rev"], F["pct_mauvais_rev"], F["pct_travaux_rev"] = (100 * rr[k] / rr["TOTAL"] for k in ("BON", "MAUVAIS", "TRAVAUX"))
    F["km_rev_total"] = rr["TOTAL"]
    tr = table("territoire_regions").set_index("region")
    F["km_total"], F["km_10k_nat"] = tr.km.sum(), tr.km.sum() / F["pop"] * 1e4
    F["gl_part_pop"] = 100 * tr.loc["Grand Lomé", "population"] / F["pop"]
    F["gl_part_km"] = 100 * tr.loc["Grand Lomé", "km"] / tr.km.sum()
    F["gl_part_ae"] = 100 * tr.loc["Grand Lomé", "ae_toutes"] / tr.ae_toutes.sum()
    F["ae_total"], F["ae_agreees"] = int(tr.ae_toutes.sum()), int(tr.ae_agreees.sum())
    tp = table("territoire_prefectures")
    F["n_sans_ae"], F["n_sans_route"] = int(tp.zero_ae.sum()), int(tp.zero_route.sum())
    F["sans_ae"] = sorted(tp.loc[tp.zero_ae, "prefecture"])
    F["sans_route"] = sorted(tp.loc[tp.zero_route, "prefecture"])
    F["hab_par_ae_nat"] = F["pop"] / F["ae_total"]
    ar, ap = ae_repartition("Région").set_index("region"), ae_repartition("Préfecture")
    F["ae_non_agreees"] = F["ae_total"] - F["ae_agreees"]
    F["ae_part_agr"] = 100 * F["ae_agreees"] / F["ae_total"]
    F["ae_gl_part_agr"] = ar.loc["Grand Lomé", "part_agreees"]
    hors = ar.drop(index="Grand Lomé")
    F["ae_hors_gl_part_agr"] = 100 * hors.agreees.sum() / hors.total.sum()
    F["ae_hors_gl_total"] = int(hors.total.sum())
    F["ae_n_pref_avec"] = int((ap.total > 0).sum())
    top = ap.sort_values("total", ascending=False).iloc[0]
    F["ae_top_pref"], F["ae_top_pref_n"] = top.prefecture, int(top.total)
    F["ae_reg_sans_agr"] = [r for r in ar.index if ar.loc[r, "agreees"] == 0]

    # ---- repères pour les infobulles « Détails » (calculés sur toutes les données, hors filtres)
    F["immat_pic_an"] = int(P["Total"].idxmax()); F["immat_pic"] = P["Total"].max()
    F["immat_creux_an"] = int(P.loc[2002:, "Total"].idxmin()); F["immat_creux"] = P.loc[2002:, "Total"].min()
    F["immat90"] = P.loc[1990, "Total"]
    cats = ["Deux-roues", "Voitures", "Camionnettes", "Poids lourds", "Autocars/Autobus"]
    F["tcam"] = {c: 100 * ((P.loc[2022, c] / P.loc[2002, c]) ** (1 / 20) - 1) for c in cats}
    F["contrib"] = {c: 100 * (P.loc[2022, c] - P.loc[2002, c]) / (F["immat22"] - F["immat02"]) for c in cats}
    F["permis_pic_an"] = int(h13["Total"].idxmax()); F["permis_pic"] = h13["Total"].max()
    F["permis_creux_an"] = int(h13["Total"].idxmin()); F["permis_creux"] = h13["Total"].min()
    F["permisB_part_cumul"] = 100 * h13["Voiture légère (B)"].sum() / h13["Total"].sum()
    F["part_A_pic_an"] = int((h13["Moto (A)"] / h13["Total"]).idxmax()); F["part_A_pic"] = 100 * (h13["Moto (A)"] / h13["Total"]).max()
    F["acc_pic_an"] = int(S["accidents"].idxmax()); F["acc_pic"] = S["accidents"].max()
    F["acc_min_an"] = int(S["accidents"].idxmin()); F["acc_min"] = S["accidents"].min()
    F["morts_pic_an"] = int(S["morts"].idxmax()); F["morts_pic"] = S["morts"].max()
    F["morts_min_an"] = int(S["morts"].idxmin()); F["morts_min"] = S["morts"].min()
    g100 = 100 * S["morts"] / S["accidents"]
    F["grav_max_an"], F["grav_max"] = int(g100.idxmax()), g100.max()
    F["grav_min_an"], F["grav_min"] = int(g100.idxmin()), g100.min()
    r10k = 1e4 * S["accidents"] / P.loc[S.index, "Total"]
    F["r10k_max_an"], F["r10k_max"] = int(r10k.idxmax()), r10k.max()
    F["r10k_min_an"], F["r10k_min"] = int(r10k.idxmin()), r10k.min()
    F["bl_par_acc22"] = F["bl22"] / F["acc22"]
    cy = table("parc_deux_roues_cylindree").set_index("annee")
    F["cyl_pic_an"], F["cyl_pic"] = int(cy["Total 2 Roues"].idxmax()), cy["Total 2 Roues"].max()
    F["cyl_part125_19"] = 100 * cy.loc[2019, "50 à 125 cm³"] / cy.loc[2019, "Total 2 Roues"]
    nat = table("reseau_etat_national").set_index("categorie")
    F["km_terre"] = nat.loc["ROUTES EN TERRES", "TOTAL"]; F["pct_mauvais_terre"] = 100 * nat.loc["ROUTES EN TERRES", "MAUVAIS"] / F["km_terre"]
    F["pct_travaux_terre"] = 100 * nat.loc["ROUTES EN TERRES", "TRAVAUX"] / F["km_terre"]
    tron = table("reseau_etat_troncons")
    tr_rev = tron[tron.categorie == "ROUTES REVETUES"].sort_values("MAUVAIS", ascending=False)
    F["n_tron_rev"], F["n_tron_terre"] = int((tron.categorie == "ROUTES REVETUES").sum()), int((tron.categorie == "ROUTES EN TERRES").sum())
    F["tron_top"], F["tron_top_km"] = tr_rev.iloc[0]["troncon"], tr_rev.iloc[0]["MAUVAIS"]
    F["tron_apparies"] = int(tron["apparie_routes_classees"].sum())
    tr = table("territoire_regions").set_index("region")
    F["km10k_min_reg"], F["km10k_min"] = tr["km_10k"].idxmin(), tr["km_10k"].min()
    F["km10k_max_reg"], F["km10k_max"] = tr["km_10k"].idxmax(), tr["km_10k"].max()
    F["non_rev_nat"] = 100 * tr["km_non_revetu"].sum() / tr["km"].sum()
    tp2 = table("territoire_prefectures")
    pos = tp2[tp2.km > 0]
    F["km10k_pref_max"], F["km10k_pref_max_v"] = pos.loc[pos.km_10k.idxmax(), "prefecture"], pos.km_10k.max()
    F["hab_ae_min_reg"] = (tr["population"] / tr["ae_toutes"]).idxmin(); F["hab_ae_min"] = (tr["population"] / tr["ae_toutes"]).min()
    F["hab_ae_max_reg"] = (tr["population"] / tr["ae_toutes"]).idxmax(); F["hab_ae_max"] = (tr["population"] / tr["ae_toutes"]).max()
    F["n_routes"] = 799
    rd = table("routes_detail")
    F["km_contra"] = rd[(rd.route_type == "Route nationale non revêtue") & rd.revetue_observe].km.sum()
    F["types_ordre"] = rd.groupby("route_type").km.sum().sort_values(ascending=False).round(0).to_dict()
    er = table("etat_reseau_region_indicatif").set_index("region")
    F["cov_min_reg"], F["cov_min"] = er["couverture"].idxmin(), 100 * er["couverture"].min()
    F["cov_max_reg"], F["cov_max"] = er["couverture"].idxmax(), 100 * er["couverture"].max()
    F["mauvais_est_max_reg"] = er["part_mauvais"].idxmax(); F["mauvais_est_max"] = 100 * er["part_mauvais"].max()
    dd = table("diagnostic_prefectures")
    F["n_quintile"] = int(dd.quintile_defavorable.sum()); F["n_double"] = int(dd.double_deficit.sum())
    F["double_noms"] = sorted(dd.loc[dd.double_deficit, "prefecture"])
    dr = table("diagnostic_regions").sort_values("score", ascending=False)
    F["reg_def"], F["reg_def_score"] = dr.iloc[0]["region"], dr.iloc[0]["score"]
    F["reg_fav"], F["reg_fav_score"] = dr.iloc[-1]["region"], dr.iloc[-1]["score"]
    import json as _json
    F["stables"] = _json.loads((PROC / "robustesse_stables.json").read_text(encoding="utf-8"))["stables"]
    return F


def indic_badge() -> str:
    return '<span class="badge-ind">Indicatif</span>'


@st.cache_data(show_spinner=False)
def terr_table(niveau: str = "Préfecture", ae_mode: str = "Toutes", defn: str = "observe", types: tuple = ()) -> pd.DataFrame:
    """Table territoriale (population, linéaire, auto-écoles, ratios) recalculée à partir de routes_detail et auto_ecoles."""
    from data import diag
    return diag.table_territoire(prefs(), table("routes_detail"), table("auto_ecoles"), niveau, ae_mode, defn, list(types) or None)


@st.cache_data(show_spinner=False)
def consensus_table(niveau: str, defn: str = "observe", zeros_a_part: bool = False) -> pd.DataFrame:
    from data import diag
    return diag.consensus(prefs(), table("routes_detail"), table("auto_ecoles"), niveau, defn, zeros_a_part)


@st.cache_data(show_spinner=False)
def diag_table(niveau: str, ae_mode: str, defn: str, poids_infra: float, zeros_a_part: bool = False) -> pd.DataFrame:
    from data import diag
    return diag.diagnostic(terr_table(niveau, ae_mode, defn), poids_infra, zeros_a_part)


@st.cache_data(show_spinner=False)
def robustesse_table(niveau: str, defn: str = "observe", zeros_a_part: bool = False) -> pd.DataFrame:
    from data import diag
    return diag.robustesse(prefs(), table("routes_detail"), table("auto_ecoles"), niveau, defn, zeros_a_part)


@st.cache_data(show_spinner=False)
def routes_score_table() -> pd.DataFrame:
    """Table de contexte routier et score, réutilisée sur la carte et les classements."""
    base = terr_table("Préfecture")
    scores = diag_table("Préfecture", "Toutes", "observe", 0.5)
    return base.merge(scores[["cle", "score", "rang", "zero_structurel"]], on="cle").replace([np.inf, -np.inf], np.nan)
