"""Page « Vue d'ensemble » — résumé des six analyses attendues ; chaque autre menu approfondit l'une d'elles."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import charts, maps
from components.exports import download_csv
from components.filters import sidebar
from components.kpi_cards import create_kpi_row
from components.styles import THEME
from components.ui import flush_panel_css, page_title, panel
from data import loader as L
from data.loader import fmt_dec as d1, fmt_int as i0, fmt_pct as p1, fmt_signed_pct as sp

f = sidebar("vue_ensemble")
year, region, pref = f["annee"], f["region"], f["pref"]
P, M, S, F = L.parc(), L.permis(), L.securite(), L.facts()
tp = L.terr_table("Préfecture")
prev_year = year - 1
acc_now = S.loc[year, "accidents"]
acc_prev = S.loc[prev_year, "accidents"] if prev_year in S.index else np.nan
acc_delta = 100 * (acc_now / acc_prev - 1) if np.isfinite(acc_prev) and acc_prev else np.nan
page_title(
    "fa-chart-simple",
    "Vue d'ensemble",
    "Mobilité et sécurité routière au Togo en un coup d'œil : un chiffre clé par analyse attendue, détaillé dans chaque menu.",
    takeaway=(
        f"{i0(acc_now)} accidents en {year}, {sp(acc_delta, 1)} par rapport à {prev_year}."
        if np.isfinite(acc_delta) else f"{i0(acc_now)} accidents en {year} ; pas de comparaison disponible avec l'année précédente."
    ),
)

# ---- chiffres de l'année de référence : un par analyse attendue ---------------------------------
tot = P.loc[year, "Total"]
permis_y = M.loc[year, "Total"]
km = tp[tp.prefecture == pref].km.sum() if pref else (tp[tp.region == region].km.sum() if region else tp.km.sum())
nat_ = L.table("reseau_etat_national")
pct_mauvais = 100 * nat_["MAUVAIS"].sum() / nat_["TOTAL"].sum()
create_kpi_row([
    {"title": f"Véhicules immatriculés {year} · national", "value": i0(tot), "icon": "fa-database", "variant": "green", "doc": "kpi_immat"},
    {"title": f"Permis délivrés {year} · national", "value": i0(permis_y) if np.isfinite(permis_y) else "n.d.", "icon": "fa-suitcase-medical", "variant": "blue", "doc": "kpi_permis"},
    {"title": f"Accidents {year} · national", "value": i0(S.loc[year, "accidents"]), "icon": "fa-gauge-high", "variant": "gray", "doc": "kpi_acc"},
    {"title": f"Morts {year} · national", "value": i0(S.loc[year, "morts"]), "icon": "fa-users", "variant": "red", "doc": "kpi_morts"},
    {"title": "Réseau en mauvais état (2020) · national", "value": p1(pct_mauvais), "icon": "fa-layer-group", "variant": "yellow", "doc": "kpi_pct_mauvais"},
    {"title": f"Routes classées (km){' · ' + (pref or region) if (pref or region) else ''}", "value": i0(km), "icon": "fa-map", "variant": "green", "doc": "kpi_km"},
])
overview_export = pd.DataFrame([
    {"Indicateur": "Immatriculations", "Année": year, "Valeur": tot, "Territoire": "national"},
    {"Indicateur": "Permis délivrés", "Année": year, "Valeur": permis_y, "Territoire": "national"},
    {"Indicateur": "Accidents", "Année": year, "Valeur": S.loc[year, "accidents"], "Territoire": "national"},
    {"Indicateur": "Morts", "Année": year, "Valeur": S.loc[year, "morts"], "Territoire": "national"},
    {"Indicateur": "Routes classées (km)", "Année": year, "Valeur": km, "Territoire": pref or region or "Togo"},
    {"Indicateur": "Réseau en mauvais état (%)", "Année": 2020, "Valeur": pct_mauvais, "Territoire": "national"},
])
download_csv("Télécharger les données filtrées (CSV)", overview_export, "vue_ensemble_filtre.csv", "dl_vue_ensemble")

# ---- Rangée 1 : carte + courbes base 100 -------------------------------------------------------
c1, c2 = st.columns([1.3, 1.1], gap="small")
with c1:
    with panel("acc_carte", "Routes classées par habitant (préfectures)", "fa-map", "acc_carte", height=399):
        charts.show(maps.choropleth(tp, "km_10k", "km / 10 000 hab.", lambda v: d1(v, 2), 340, "YlGnBu", region=region,
                                    hover_extra="Formule : km classés / population RGPH 2022 × 10 000",
                                    show_scale=True, zoom_region=region, selected=pref), "acc_map")
with c2:
    with panel("acc_courbes", "Indice base 100 (2010) : immatriculations, permis, accidents, morts", "fa-chart-line", "acc_courbes", height=399):
        yrs = list(range(2010, 2023))
        series = {"Immatriculations": P.loc[yrs, "Total"], "Permis délivrés": M.reindex(yrs)["Total"], "Accidents": S.loc[yrs, "accidents"], "Morts": S.loc[yrs, "morts"]}
        units = {"Immatriculations": "véhicules", "Permis délivrés": "permis", "Accidents": "accidents", "Morts": "morts"}
        cols = {"Immatriculations": "#1488ee", "Permis délivrés": "#0d8a7a", "Accidents": "#e8590c", "Morts": "#b3122d"}
        fig = go.Figure()
        for n, s in series.items():
            idx = 100 * s / s.iloc[0]
            change = s.pct_change(fill_method=None) * 100
            custom = [
                (d1(v, 0), i0(raw), d1(delta, 1))
                for v, raw, delta in zip(idx, s, change)
            ]
            fig.add_trace(go.Scatter(x=yrs, y=idx, name=n, mode="lines+markers", connectgaps=False, line=dict(color=cols[n], width=2.4), marker=dict(size=5),
                                     customdata=custom, hovertemplate=f"{n} · national · %{{x}}<br>Indice : <b>%{{customdata[0]}}</b> (base 2010 = 100)<br>Valeur : %{{customdata[1]}} {units[n]} · variation annuelle : %{{customdata[2]}} %<br>Formule : valeur / valeur 2010 × 100<extra></extra>"))
        fig.add_vline(x=year, line=dict(color="#10335c", width=1, dash="dot"))
        fig.add_annotation(x=2013, y=100 * M.loc[2012, "Total"] / M.loc[2010, "Total"], text="2013 manquant", showarrow=True, ay=-28, ax=0, font=dict(size=10.5, color="#4a6572"))
        charts.layout(fig, 340, t=30)
        fig.update_xaxes(dtick=2); fig.update_yaxes(title_text="Indice (2010 = 100)", title_font=dict(size=11))
        charts.show(fig, "acc_lines")

# ---- Rangée 2 : classement des régions + donut --------------------------------------------------
c3, c4 = st.columns([1, 1], gap="small")
with c3:
    with panel("acc_classement", "Régions : déficit d'infrastructure et de formation", "fa-chart-simple", "acc_classement", height=329):
        dg = L.diag_table("Région", "Toutes", "observe", 0.5).sort_values("score")
        op = [1.0 if (region is None or r_ == region) else 0.35 for r_ in dg["region"]]
        fig = go.Figure()
        for col, nom, c in (("score_infra", "Infrastructure", "#0a5ec0"), ("score_formation", "Formation", "#e8590c")):
            custom = [d1(v, 2) for v in dg[col]]
            fig.add_trace(go.Bar(y=dg["region"], x=dg[col], name=nom, orientation="h", marker=dict(color=c, opacity=op),
                                 customdata=custom,
                                 hovertemplate=f"%{{y}}<br>Score {nom.lower()} : <b>%{{customdata}}</b> / 1 (1 = le plus défavorable)<br>Calcul : rang relatif de déficit par indicateur<extra></extra>"))
        charts.layout(fig, 270, t=28, barmode="group")
        fig.update_xaxes(range=[0, 1], title_text="Score (0 à 1, 1 = le plus défavorable)", title_font=dict(size=11)); fig.update_yaxes(showgrid=False)
        charts.show(fig, "acc_rank")
with c4:
    with panel("acc_donut", f"Structure des immatriculations {year}", "fa-chart-pie", "acc_donut", height=329):
        cats = ["Deux-roues", "Voitures", "Camionnettes", "Poids lourds", "Autocars/Autobus"]
        pie_values = [P.loc[year, c] for c in cats]
        pie_custom = [i0(v) for v in pie_values]
        fig = go.Figure(go.Pie(labels=cats, values=pie_values, customdata=pie_custom, hole=0.58, sort=False, marker=dict(colors=[charts.C_VEH[c] for c in cats], line=dict(color="#fff", width=2)),
                               textinfo="percent", textposition="outside", textfont=dict(size=12, color="#10335c"), hovertemplate=f"%{{label}} · {year}<br><b>%{{customdata}}</b> véhicules (%{{percent}} du total)<br>Formule : catégorie / total des catégories × 100<extra></extra>"))
        fig.add_annotation(text=f"<b>{i0(tot)}</b><br>véhicules", x=0.5, y=0.5, showarrow=False, font=dict(size=15, color="#0a4a9a"))
        charts.layout(fig, 270, t=4, legend=True)
        fig.update_layout(legend=dict(orientation="v", x=1.0, y=0.5, xanchor="right", yanchor="middle"))
        charts.show(fig, "acc_donut")
flush_panel_css()
