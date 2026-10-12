"""Page « Permis de conduire » — évolution des permis délivrés, par catégorie (analyse attendue n° 2)."""
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

f = sidebar("permis")
a0, a1 = f["periode"]
P, M = L.parc(), L.permis()

perm, mode, base = f["permis"], f["mode"], f["base"]
if not perm:
    banner("Sélection vide : choisissez au moins une catégorie de permis dans les filtres.")
    st.stop()

yrs = list(range(a0, a1 + 1))
Mp = M.reindex(yrs)
valid = Mp.drop(index=2013, errors="ignore")                 # 2013 : donnée manquante, jamais interpolée
last = Mp["Total"].dropna()
tot_cum = valid["Total"].sum() if len(valid) else np.nan
cumA = 100 * valid["Moto (A)"].sum() / tot_cum if len(valid) and tot_cum else np.nan
cumB = 100 * valid["Voiture légère (B)"].sum() / tot_cum if len(valid) and tot_cum else np.nan
vt = valid["Total"].dropna()
variation_permis = 100 * (vt.iloc[-1] / vt.iloc[0] - 1) if len(vt) > 1 and vt.iloc[0] else np.nan
page_title(
    "fa-credit-card",
    "Permis de conduire",
    "Combien de permis sont délivrés, dans quelles catégories, et la formation suit-elle l'usage ?",
    takeaway=(
        f"{i0(vt.iloc[-1])} permis délivrés en {vt.index[-1]}, "
        f"{sp(variation_permis, 1)} depuis {vt.index[0]} (2013 exclu)."
        if len(vt) > 1 else "Une seule année exploitable dans la période ; aucune tendance calculable (2013 : donnée manquante)."
    ),
)

create_kpi_row([
    {"title": f"Permis délivrés ({last.index[-1] if len(last) else 'n.d.'})", "value": i0(last.iloc[-1]) if len(last) else "n.d.", "icon": "fa-suitcase-medical", "variant": "blue", "doc": "kpi_permis"},
    {"title": "Part du permis A (cumul)", "value": p1(cumA), "icon": "fa-users", "variant": "red", "doc": "kpi_permis"},
    {"title": "Part du permis B (cumul)", "value": p1(cumB), "icon": "fa-chart-pie", "variant": "green"},
    {"title": f"Pic annuel ({vt.idxmax() if len(vt) else 'n.d.'})", "value": i0(vt.max()) if len(vt) else "n.d.", "icon": "fa-gauge-high", "variant": "gray"},
])
export_permis = Mp[perm].copy()
export_permis.index.name = "annee"
download_csv("Télécharger les données filtrées (CSV)", export_permis.reset_index(), "permis_filtres.csv", "dl_permis")

LBL_MODE = {"Volumes": "volumes annuels", "Base 100": f"indice (base 100 = {base})", "Parts": "parts annuelles (%)"}

c1, c2 = st.columns([1.4, 1], gap="small")
with c1:
    with panel("permis_cat", f"Permis délivrés par catégorie — {LBL_MODE[mode]}", "fa-suitcase-medical", "permis_cat", height=344):
        stacked_series(Mp, perm, charts.C_PERMIS, "permis_ch", "permis", 285, mode, base, bars=True)
with c2:
    with panel("permis_part", f"Répartition cumulée par catégorie {a0}–{a1}", "fa-chart-pie", "permis_part", height=344):
        if len(valid) and tot_cum:
            share = (100 * valid[perm].sum() / tot_cum).sort_values()
            share_data = [(d1(v, 1), i0(valid[perm].sum().reindex(share.index).loc[c])) for c, v in share.items()]
            fig = go.Figure(go.Bar(y=share.index, x=share.values, orientation="h", marker_color=[charts.C_PERMIS[c] for c in share.index],
                                   customdata=share_data,
                                   hovertemplate=f"%{{y}} · {a0}–{a1} (2013 exclu)<br>Part des permis cumulés : <b>%{{customdata[0]}} %</b> (%{{customdata[1]}} permis)<br>Formule : catégorie / total cumulé × 100<extra></extra>"))
            charts.layout(fig, 285, legend=False, t=4); fig.update_yaxes(showgrid=False); fig.update_xaxes(title_text="% des permis délivrés (2013 exclu)", title_font=dict(size=11), ticksuffix=" %")
            charts.show(fig, "permis_part_ch")
        else:
            st.info("Aucune année exploitable sur cette période (2013 : donnée manquante).")

c3, c4 = st.columns([1.4, 1], gap="small")
with c3:
    with panel("part_immat_permis", "La formation suit-elle l'usage ? Part immatriculations vs part permis", "fa-star", "part_immat_permis", height=359):
        yy = [y for y in range(max(a0, 2007), a1 + 1) if y != 2013]
        sh_imm = 100 * P.loc[yy, "Deux-roues"] / P.loc[yy, "Total"]
        sh_per = 100 * M.loc[yy, "Moto (A)"] / M.loc[yy, "Total"]
        fig = go.Figure()
        immat_change = sh_imm.pct_change(fill_method=None) * 100
        permis_change = sh_per.pct_change(fill_method=None) * 100
        fig.add_trace(go.Scatter(x=yy, y=sh_imm, name="Deux-roues : part des immatriculations", mode="lines+markers", line=dict(color="#e8590c", width=3),
                                 customdata=[(d1(v, 1), d1(delta, 1)) for v, delta in zip(sh_imm, immat_change)],
                                 hovertemplate="Immatriculations · national<br>%{x} : part des deux-roues <b>%{customdata[0]} %</b><br>Variation annuelle : %{customdata[1]} % · formule : deux-roues / total × 100<extra></extra>"))
        fig.add_trace(go.Scatter(x=yy, y=sh_per, name="Permis A : part des permis délivrés", mode="lines+markers", line=dict(color="#10335c", width=3, dash="dot"),
                                 customdata=[(d1(v, 1), d1(delta, 1)) for v, delta in zip(sh_per, permis_change)],
                                 hovertemplate="Permis · national<br>%{x} : part du permis A <b>%{customdata[0]} %</b><br>Variation annuelle : %{customdata[1]} % · formule : permis A / total × 100<extra></extra>"))
        if len(yy) > 1:
            fig.add_annotation(x=yy[-1], y=(sh_imm.iloc[-1] + sh_per.iloc[-1]) / 2, text=f"écart {d1(sh_imm.iloc[-1] - sh_per.iloc[-1], 0)} pts", showarrow=False, xshift=-38, font=dict(size=12, color="#a3182c"))
        charts.layout(fig, 300, t=34); fig.update_yaxes(range=[0, 100], ticksuffix=" %", title_text="Part (%)", title_font=dict(size=11)); fig.update_xaxes(dtick=2)
        charts.show(fig, "parc_part")
with c4:
    with panel("permis_tcam", "Croissance annuelle moyenne (TCAM) par catégorie", "fa-arrow-trend-up", "permis_tcam", height=359):
        rows = []
        for c in perm:
            s = valid[c].dropna()
            if len(s) > 1 and s.iloc[0] > 0 and s.index[-1] > s.index[0]:
                n = s.index[-1] - s.index[0]
                rows.append((c, 100 * ((s.iloc[-1] / s.iloc[0]) ** (1 / n) - 1), s.index[0], s.index[-1]))
        if rows:
            rows.sort(key=lambda r: r[1])
            tcam_data = [(f"{r[2]}–{r[3]} · {i0(valid.loc[r[2], r[0]])} → {i0(valid.loc[r[3], r[0]])}", d1(r[1], 1)) for r in rows]
            fig = go.Figure(go.Bar(y=[r[0] for r in rows], x=[r[1] for r in rows], orientation="h", marker_color=[charts.C_PERMIS[r[0]] for r in rows],
                                   customdata=tcam_data, hovertemplate="%{y}<br>Période : %{customdata[0]} permis<br>TCAM : <b>%{customdata[1]} %/an</b><br>Formule : (valeur finale / initiale)^(1/n) − 1<extra></extra>"))
            charts.layout(fig, 300, legend=False, t=4); fig.update_yaxes(showgrid=False); fig.update_xaxes(title_text="% par an (années extrêmes de la période, 2013 exclu)", title_font=dict(size=11), ticksuffix=" %")
            charts.show(fig, "permis_tcam_ch")
        else:
            st.info("Choisissez une période d'au moins deux années exploitables et des catégories délivrées.")
flush_panel_css()
section_territoire("permis", f, f["region"], f["pref"], a0, a1)
flush_panel_css()
