"""Page « Immatriculations » — évolution des véhicules immatriculés : voitures, deux-roues, poids lourds (analyse attendue n° 1)."""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from components import charts
from components.exports import download_csv
from components.filters import sidebar
from components.territoire import section as section_territoire
from components.kpi_cards import create_kpi_row
from components.series import stacked_series
from components.ui import banner, flush_panel_css, page_title, panel
from data import loader as L
from data.loader import fmt_dec as d1, fmt_int as i0, fmt_pct as p1, fmt_signed_pct as sp

f = sidebar("immat")
a0, a1 = f["periode"]
P = L.parc()
veh, mode, base = f["veh"], f["mode"], f["base"]
if not veh:
    banner("Sélection vide : choisissez au moins une catégorie de véhicules dans les filtres.")
    st.stop()

yrs = list(range(a0, a1 + 1))
Pp = P.loc[yrs]
tot_a1 = Pp["Total"].iloc[-1]
tot_a0 = Pp["Total"].iloc[0]
variation_total = 100 * (tot_a1 / tot_a0 - 1) if tot_a0 else np.nan
page_title(
    "fa-chart-line",
    "Immatriculations",
    "Comment le parc de véhicules a-t-il évolué : voitures, deux-roues, poids lourds et autres catégories ?",
    takeaway=(
        f"{i0(tot_a1)} véhicules en {a1}, soit {sp(variation_total, 1)} depuis {a0}."
        if a1 > a0 else f"{i0(tot_a1)} véhicules en {a1} ; une année ne suffit pas à établir une tendance."
    ),
)


def part(cat: str) -> float:
    return 100 * Pp[cat].iloc[-1] / tot_a1


create_kpi_row([
    {"title": f"Véhicules immatriculés {a1}", "value": i0(tot_a1), "icon": "fa-database", "variant": "green", "doc": "kpi_immat"},
    {"title": f"Part des deux-roues {a1}", "value": p1(part("Deux-roues")), "icon": "fa-chart-pie", "variant": "yellow", "doc": "kpi_part2r"},
    {"title": f"Part des voitures {a1}", "value": p1(part("Voitures")), "icon": "fa-users", "variant": "blue"},
    {"title": f"Part des poids lourds {a1}", "value": p1(part("Poids lourds")), "icon": "fa-gauge-high", "variant": "gray"},
])
export_parc = Pp[veh].copy()
export_parc.index.name = "annee"
download_csv("Télécharger les données filtrées (CSV)", export_parc.reset_index(), "immatriculations_filtrees.csv", "dl_immat")

LBL_MODE = {"Volumes": "volumes annuels", "Base 100": f"indice (base 100 = {base})", "Parts": "parts annuelles (%)"}

c1, c2 = st.columns([1.4, 1], gap="small")
with c1:
    with panel("parc_aires", f"Véhicules immatriculés — {LBL_MODE[mode]}", "fa-chart-simple", "parc_aires", height=359):
        stacked_series(Pp, veh, charts.C_VEH, "parc_aires_ch", "véhicules", 300, mode, base)
with c2:
    with panel("parc_base100", f"Base 100 ({base}) et TCAM", "fa-arrow-trend-up", "parc_base100", height=359):
        n = max(a1 - base, 1)
        fig = go.Figure()
        for c in veh:
            s = Pp[c].loc[base:]
            if len(s) and s.iloc[0] > 0:
                tcam = (s.iloc[-1] / s.iloc[0]) ** (1 / n) - 1
                custom = [(d1(100 * value / s.iloc[0], 0), i0(value)) for value in s]
                fig.add_trace(go.Scatter(x=s.index, y=100 * s / s.iloc[0], mode="lines", name=f"{c} ({'+' if tcam >= 0 else '−'}{d1(abs(100 * tcam))} %/an)",
                                         line=dict(color=charts.C_VEH[c], width=2.4), customdata=custom,
                                         hovertemplate=f"{c}<br>%{{x}} : indice <b>%{{customdata[0]}}</b> (base {base} = 100)<br>Valeur : %{{customdata[1]}} véhicules<br>TCAM : ({i0(s.iloc[-1])}/{i0(s.iloc[0])})^(1/{n}) − 1 = {d1(100 * tcam)} %/an<extra></extra>"))
        charts.layout(fig, 300, t=34)
        fig.update_layout(legend=dict(font=dict(size=10.5)))
        if (Pp.loc[base:, veh].max().max() / max(Pp.loc[base, veh].min(), 1)) > 12:
            fig.update_yaxes(type="log", tickvals=[50, 100, 200, 500, 1000, 2000, 5000], ticktext=["50", "100", "200", "500", "1 000", "2 000", "5 000"], title_text="Indice (échelle log)", title_font=dict(size=10.5))
        else:
            fig.update_yaxes(title_text="Indice", title_font=dict(size=10.5))
        charts.show(fig, "parc_b100")

c3, c4 = st.columns([1, 1], gap="small")
with c3:
    with panel("parc_contrib", f"Contribution à la hausse {a0}–{a1}", "fa-layer-group", "parc_contrib", height=344):
        delta = (Pp.loc[a1, veh] - Pp.loc[a0, veh])
        dtot = Pp.loc[a1, "Total"] - Pp.loc[a0, "Total"]
        share = (100 * delta / dtot).sort_values() if dtot != 0 else delta * np.nan
        contribution_data = [(d1(v, 1), i0(delta.reindex(share.index).loc[c])) for c, v in share.items()]
        fig = go.Figure(go.Bar(y=share.index, x=share.values, orientation="h", marker_color=[charts.C_VEH[c] for c in share.index],
                               customdata=contribution_data,
                               hovertemplate=f"%{{y}}<br>{a0}–{a1} : contribution <b>%{{customdata[0]}} %</b> (%{{customdata[1]}} véhicules)<br>Formule : variation de la catégorie / variation totale × 100<extra></extra>"))
        charts.layout(fig, 285, legend=False, t=4); fig.update_yaxes(showgrid=False); fig.update_xaxes(title_text="% de la hausse totale", title_font=dict(size=11), ticksuffix=" %")
        charts.show(fig, "parc_contrib_ch")
with c4:
    with panel("parc_cylindree", "Deux-roues par cylindrée (2013–2019)", "fa-gauge-high", "parc_cylindree", height=344):
        cy = L.table("parc_deux_roues_cylindree").set_index("annee")
        fig = go.Figure()
        for c, col in (("50 à 125 cm³", "#e8590c"), ("Plus de 125 cm³", "#7a2e0a")):
            change = cy[c].pct_change(fill_method=None) * 100
            custom = [(i0(value), d1(delta, 1)) for value, delta in zip(cy[c], change)]
            fig.add_trace(go.Bar(x=cy.index, y=cy[c], name=c, marker_color=col,
                                 customdata=custom,
                                 hovertemplate=f"{c} · %{{x}}<br><b>%{{customdata[0]}}</b> engins<br>Variation annuelle : %{{customdata[1]}} %<extra></extra>"))
        charts.layout(fig, 285, t=34, barmode="stack"); fig.update_xaxes(dtick=1)
        charts.show(fig, "parc_cyl")
flush_panel_css()
section_territoire("immat", f, f["region"], f["pref"], a0, a1)
flush_panel_css()
