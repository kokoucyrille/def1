"""Page « Sécurité routière » — accidents, blessés et morts, rapportés aux véhicules et à la population (objectif O2)."""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from components import charts
from components.exports import download_csv
from components.filters import sidebar
from components.territoire import section as section_territoire
from components.kpi_cards import create_kpi_row
from components.ui import flush_panel_css, page_title, panel
from data import loader as L
from data.loader import fmt_dec as d1, fmt_int as i0, fmt_pct as p1, fmt_signed_pct as sp

f = sidebar("securite")
a0, a1 = f["periode"]
indic, base = f["indic"], f["base"]
P, S, F = L.parc(), L.securite(), L.facts()
yrs = list(range(a0, a1 + 1))
s = S.loc[yrs]
KEY = {"Accidents": "accidents", "Blessés": "blesses", "Morts": "morts"}[indic]
UNIT = {"accidents": "accidents", "blesses": "blessés", "morts": "morts"}[KEY]
period_values = s[KEY].dropna()
period_change = 100 * (period_values.iloc[-1] / period_values.iloc[0] - 1) if len(period_values) > 1 and period_values.iloc[0] else np.nan
page_title(
    "fa-suitcase-medical",
    "Sécurité routière",
    "Combien d'accidents, de blessés et de morts, rapportés à la population et au parc de véhicules (national, annuel) ?",
    takeaway=(
        f"{i0(period_values.iloc[-1])} {UNIT} en {period_values.index[-1]}, "
        f"{sp(period_change, 1)} depuis {period_values.index[0]} (série nationale)."
        if len(period_values) > 1 else "Une seule année exploitable dans la période ; aucune tendance calculable."
    ),
)
acc_x = s.accidents.iloc[-1] / s.accidents.iloc[0]
mv = 100 * (s.morts.iloc[-1] / s.morts.iloc[0] - 1)
grav0, grav1 = 100 * s.morts.iloc[0] / s.accidents.iloc[0], 100 * s.morts.iloc[-1] / s.accidents.iloc[-1]
rho_df = P.loc[yrs, ["Deux-roues"]].join(s[KEY]).dropna()
rho = rho_df["Deux-roues"].rank().corr(rho_df[KEY].rank()) if len(rho_df) > 2 else np.nan

create_kpi_row([
    {"title": f"Accidents {a1}", "value": i0(s.accidents.iloc[-1]), "icon": "fa-gauge-high", "variant": "gray", "doc": "kpi_acc"},
    {"title": f"Blessés {a1}", "value": i0(s.blesses.iloc[-1]), "icon": "fa-suitcase-medical", "variant": "yellow", "doc": "kpi_blesses"},
    {"title": f"Morts {a1}", "value": i0(s.morts.iloc[-1]), "icon": "fa-users", "variant": "red", "doc": "kpi_morts"},
    {"title": f"Morts / 100 000 hab. {a1} (indic.)", "value": d1(1e5 * s.morts.iloc[-1] / F["pop"]), "icon": "fa-users-viewfinder", "variant": "purple", "doc": "kpi_morts100k"},
    {"title": f"Morts / 100 accidents {a1}", "value": d1(grav1), "icon": "fa-arrow-trend-up", "variant": "blue", "doc": "kpi_morts100acc"},
])
security_export = s[["accidents", "blesses", "morts"]].copy()
security_export["indicateur_selectionne"] = s[KEY]
security_export["base_selectionnee"] = base
security_export.index.name = "annee"
download_csv("Télécharger les données filtrées (CSV)", security_export.reset_index(), "securite_filtree.csv", "dl_securite")


def mark_low(fig, col="accidents"):
    for y in (2010, 2015):
        if y in s.index:
            fig.add_annotation(x=y, y=s.loc[y, col], text=f"{y} : année basse", showarrow=True, ay=-30, ax=0, font=dict(size=10.5, color="#4a6572"), arrowcolor="#8a99a8")


c1, c2 = st.columns([1.5, 1], gap="small")
with c1:
    with panel("sec_serie", "Accidents, blessés et morts", "fa-chart-line", "sec_serie", height=359):
        fig = go.Figure()
        for k, n in (("accidents", "Accidents"), ("blesses", "Blessés")):
            change = s[k].pct_change(fill_method=None) * 100
            custom = [(i0(v), d1(delta, 1)) for v, delta in zip(s[k], change)]
            fig.add_trace(go.Scatter(x=yrs, y=s[k], name=n, mode="lines+markers", line=dict(color=charts.C_SEC[k], width=2.6),
                                     customdata=custom,
                                     hovertemplate=f"{n} · national<br>%{{x}} : <b>%{{customdata[0]}}</b> {n.lower()}<br>Variation vs année précédente : %{{customdata[1]}} %<extra></extra>"))
        change_morts = s["morts"].pct_change(fill_method=None) * 100
        fig.add_trace(go.Scatter(x=yrs, y=s["morts"], name="Morts (axe droit)", mode="lines+markers", yaxis="y2", line=dict(color=charts.C_SEC["morts"], width=2.6, dash="dot"),
                                 customdata=[(i0(v), d1(delta, 1)) for v, delta in zip(s["morts"], change_morts)],
                                 hovertemplate="Morts · national<br>%{x} : <b>%{customdata[0]}</b> morts<br>Variation vs année précédente : %{customdata[1]} %<extra></extra>"))
        charts.layout(fig, 300, t=34)
        fig.update_layout(yaxis2=dict(overlaying="y", side="right", showgrid=False, title=dict(text="Morts", font=dict(size=11, color="#3a5566")), tickfont=dict(size=11.5, color="#3a5566"), rangemode="tozero", dtick=200))
        fig.update_yaxes(title_text="Accidents et blessés", title_font=dict(size=11), rangemode="tozero", selector=dict(overlaying=None)); fig.update_xaxes(dtick=1 if len(yrs) < 9 else 2)
        mark_low(fig); charts.show(fig, "sec_serie_ch")
with c2:
    with panel("sec_gravite", "Gravité des accidents", "fa-gauge-high", "sec_gravite", height=359):
        g1 = 100 * s.morts / s.accidents; g2 = s.blesses / s.accidents
        fig = go.Figure()
        grav_change1 = g1.pct_change(fill_method=None) * 100
        grav_change2 = g2.pct_change(fill_method=None) * 100
        fig.add_trace(go.Scatter(x=yrs, y=g1, name="Morts / 100 accidents", mode="lines+markers", line=dict(color="#b3122d", width=2.6),
                                 customdata=[(d1(v, 1), d1(delta, 1)) for v, delta in zip(g1, grav_change1)],
                                 hovertemplate="Morts / 100 accidents · national<br>%{x} : <b>%{customdata[0]}</b><br>Variation vs année précédente : %{customdata[1]} %<br>Formule : morts / accidents × 100<extra></extra>"))
        fig.add_trace(go.Scatter(x=yrs, y=g2, name="Blessés / accident (axe droit)", mode="lines+markers", yaxis="y2", line=dict(color="#e8590c", width=2.6, dash="dot"),
                                 customdata=[(d1(v, 2), d1(delta, 1)) for v, delta in zip(g2, grav_change2)],
                                 hovertemplate="Blessés / accident · national<br>%{x} : <b>%{customdata[0]}</b><br>Variation vs année précédente : %{customdata[1]} %<br>Formule : blessés / accidents<extra></extra>"))
        charts.layout(fig, 300, t=34)
        fig.update_layout(yaxis2=dict(overlaying="y", side="right", showgrid=False, tickfont=dict(size=11.5, color="#3a5566"), rangemode="tozero", dtick=0.5))
        fig.update_yaxes(rangemode="tozero", selector=dict(overlaying=None)); fig.update_xaxes(dtick=2)
        charts.show(fig, "sec_grav_ch")

c3, c4 = st.columns([1.2, 1], gap="small")
with c3:
    if base == "Pour 10 000 véhicules":
        ratio = 1e4 * s[KEY] / P.loc[yrs, "Total"]; lab = f"{indic} pour 10 000 véhicules immatriculés"; doc = "sec_ratio_veh"; ttl = f"{indic} pour 10 000 véhicules"
    elif base.startswith("Pour 100 000"):
        ratio = 1e5 * s[KEY] / F["pop"]; lab = f"{indic} pour 100 000 hab. (population 2022)"; doc = "sec_hab"; ttl = f"{indic} pour 100 000 hab. (pop. 2022)"
    else:
        ratio = s[KEY]; lab = f"{indic} (valeurs brutes)"; doc = "sec_ratio_veh"; ttl = f"{indic} — valeurs brutes"
    with panel("sec_ratio", ttl, "fa-chart-simple", doc, height=349):
        ratio_change = ratio.pct_change(fill_method=None) * 100
        ratio_custom = [(d1(v, 1), d1(delta, 1)) for v, delta in zip(ratio, ratio_change)]
        ratio_formula = ('indicateur / immatriculations × 10 000' if doc == 'sec_ratio_veh' and base != 'Brut'
                         else ('indicateur / population 2022 × 100 000' if base.startswith('Pour 100') else 'valeur annuelle'))
        fig = go.Figure(go.Bar(x=yrs, y=ratio, customdata=ratio_custom, marker_color=charts.C_SEC[KEY],
                               hovertemplate=f"%{{x}} · national<br>{lab} : <b>%{{customdata[0]}}</b><br>Variation vs année précédente : %{{customdata[1]}} %<br>Formule : {ratio_formula}<extra></extra>"))
        charts.layout(fig, 290, legend=False, t=6); fig.update_xaxes(dtick=1 if len(yrs) < 9 else 2); fig.update_yaxes(title_text=lab, title_font=dict(size=10.5))
        mark_low_x = [y for y in (2010, 2015) if y in yrs]
        charts.show(fig, "sec_ratio_ch")
with c4:
    with panel("sec_corr", f"Deux-roues et {indic.lower()}", "fa-users-viewfinder", "sec_corr", height=349):
        scatter_data = [(i0(x), i0(y)) for x, y in zip(rho_df["Deux-roues"], rho_df[KEY])]
        fig = go.Figure(go.Scatter(x=rho_df["Deux-roues"], y=rho_df[KEY], mode="markers+text", text=[str(y) for y in rho_df.index], textposition="top center", textfont=dict(size=10),
                                   marker=dict(size=9, color=charts.C_SEC[KEY], line=dict(color="#fff", width=1)),
                                   customdata=scatter_data,
                                   hovertemplate=f"%{{text}} · national<br>Deux-roues immatriculés : <b>%{{customdata[0]}}</b><br>{indic} : <b>%{{customdata[1]}}</b><extra></extra>"))
        charts.layout(fig, 290, legend=False, t=6); fig.update_xaxes(title_text="Immatriculations de deux-roues", title_font=dict(size=10.5), showgrid=True, gridcolor=charts.GRID)
        fig.update_yaxes(title_text=indic, title_font=dict(size=10.5))
        charts.show(fig, "sec_corr_ch")
flush_panel_css()
section_territoire("securite", f, f["region"], f["pref"], a0, a1)
flush_panel_css()
