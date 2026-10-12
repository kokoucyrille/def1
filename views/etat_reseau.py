"""Page « État du réseau » — état du réseau routier par région, par catégorie de voie et par tronçon, 2020 (analyse attendue n° 4)."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from components import charts, maps
from components.exports import download_csv
from components.filters import sidebar
from components.kpi_cards import create_kpi_row
from components.ui import banner, flush_panel_css, page_title, panel
from data import loader as L
from data.loader import ETAT_COULEURS, ETAT_LIBELLES, fmt_dec as d1, fmt_pct as p1

f = sidebar("etat_reseau")
region = f["region"]
if not f["etats"]:
    banner("Sélection vide : choisissez au moins un état dans les filtres.")
    st.stop()

CAT_LBL = {"ROUTES REVETUES": "Routes revêtues", "ROUTES EN TERRES": "Routes en terre", "VOIRIES REVETUES": "Voiries revêtues", "VOIRIES EN TERRES": "Voiries en terre"}
nat = L.table("reseau_etat_national").set_index("categorie").rename(index=CAT_LBL)
cat = f["cat"]
nat_sel = nat if cat == "Toutes les catégories" else nat.loc[[cat]]
tot_km = nat_sel["TOTAL"].sum()
pc = {e: 100 * nat_sel[e].sum() / tot_km for e in ETAT_COULEURS}
cat_lbl = cat if cat != "Toutes les catégories" else "toutes catégories"
page_title(
    "fa-gauge-high",
    "État du réseau",
    "Dans quel état est le réseau routier : par région, par catégorie de voie et par tronçon (2020) ?",
    takeaway=f"{p1(pc['MAUVAIS'])} en mauvais état ({cat_lbl}, 2020) ; la tendance pluriannuelle n'est pas disponible.",
)

create_kpi_row([
    {"title": f"Bon état (2020) · {cat_lbl}", "value": p1(pc["BON"]), "icon": "fa-gauge-high", "variant": "green", "doc": "kpi_pct_bon"},
    {"title": "État moyen (2020)", "value": p1(pc["MOYEN"]), "icon": "fa-layer-group", "variant": "yellow"},
    {"title": "Mauvais état (2020)", "value": p1(pc["MAUVAIS"]), "icon": "fa-suitcase-medical", "variant": "red", "doc": "kpi_pct_mauvais"},
    {"title": "Travaux en cours (2020)", "value": p1(pc["TRAVAUX"]), "icon": "fa-gear", "variant": "gray"},
])

# ---- Rangée 1 : état des routes jointes par région + état par catégorie de voie -----------------
c1, c2 = st.columns([1.2, 1], gap="small")
with c1:
    with panel("res_etat_region", "Part des routes en mauvais état par région", "fa-location-dot", "res_etat_region", height=359):
        er = L.table("etat_reseau_region_indicatif").set_index("region").reindex(L.ORDRE_REGIONS)
        op = [1.0 if (region is None or r_ == region) else 0.35 for r_ in er.index]
        fig = go.Figure()
        y_mauvais = 100 * er["part_mauvais"]
        regional_hover = [
            (
                "non renseigné" if not row.couverture else d1(100 * row.part_mauvais, 1),
                d1(100 * row.couverture, 1),
            )
            for _, row in er.iterrows()
        ]
        fig.add_trace(go.Bar(
            x=er.index,
            y=y_mauvais,
            name="Mauvais état",
            marker=dict(color=[ETAT_COULEURS["MAUVAIS"] if v.couverture > 0 else "#aeb8bf" for _, v in er.iterrows()],
                        opacity=op),
            customdata=regional_hover,
            hovertemplate="%{x} · état réseau 2020<br>Mauvais état : <b>%{customdata[0]} %</b> des routes avec état connu<br>Couverture jointure : %{customdata[1]} %<br>Formule : km mauvais / km appariés<extra></extra>",
        ))
        charts.layout(fig, 300, t=34)
        for r_, v in er.iterrows():
            fig.add_annotation(x=r_, y=(105 if v.couverture > 0 else 3), yref="y",
                               text=("non renseigné" if v.couverture == 0 else f"couverture {d1(100 * v.couverture, 0)} %"),
                               showarrow=False, font=dict(size=10, color="#4a6572"), yshift=8 if v.couverture > 0 else 0)
        fig.update_yaxes(range=[0, 115], ticksuffix=" %", title_text="Part en mauvais état (routes avec état connu)", title_font=dict(size=11)); fig.update_xaxes(tickangle=-20)
        charts.show(fig, "res_estim_ch")
        st.caption("L'état est connu par tronçon, pas par région. La part ne porte que sur les tronçons appariés ; aucune valeur n'est imputée.")
with c2:
    with panel("res_etat_cat", "État du réseau par catégorie de voie (2020)", "fa-gauge-high", "res_etat_cat", height=359):
        fig = go.Figure()
        for e in f["etats"]:
            y = nat_sel[e].fillna(0)
            custom = [(d1(v, 1), d1(100 * v / nat_sel.loc[idx, "TOTAL"], 1)) for idx, v in y.items()]
            fig.add_trace(go.Bar(y=nat_sel.index, x=y, name=ETAT_LIBELLES[e], orientation="h", marker_color=ETAT_COULEURS[e], customdata=custom,
                                 hovertemplate=f"%{{y}} · national, 2020<br>{ETAT_LIBELLES[e]} : <b>%{{customdata[0]}} km</b> (%{{customdata[1]}} % de la catégorie)<br>Formule : km de cet état / total km de la catégorie × 100<extra></extra>"))
        charts.layout(fig, 300, t=34, barmode="stack"); fig.update_yaxes(showgrid=False, autorange="reversed"); fig.update_xaxes(title_text="km (2020)", title_font=dict(size=11))
        charts.show(fig, "res_etat_ch")

# ---- Rangée 2 : explorateur de tronçons : carte (tracés) et classement graphique ----------------
with panel("res_explorateur", "Explorateur de tronçons (84 tronçons nommés, 2020)", "fa-map", "res_explorateur", height=520):
    tr = L.table("reseau_etat_troncons").copy()
    tr["categorie"] = tr["categorie"].map(CAT_LBL)
    if cat != "Toutes les catégories":
        tr = tr[tr["categorie"] == cat]
    if f["q"]:
        tr = tr[tr["troncon"].str.contains(f["q"], case=False, regex=False)]
    tr_export_source = tr.copy()
    for e in ("BON", "MOYEN", "MAUVAIS", "TRAVAUX"):
        tr[e] = tr[e].fillna(0.0)
    tr["dominant"] = tr[["BON", "MOYEN", "MAUVAIS", "TRAVAUX"]].idxmax(axis=1)
    tr = tr[tr["dominant"].isin(f["etats"])] if len(f["etats"]) < 4 else tr
    export_troncons = tr_export_source.loc[tr.index, ["troncon", "categorie", "BON", "MOYEN", "MAUVAIS", "TRAVAUX"]].copy()
    download_csv("Télécharger les données filtrées (CSV)", export_troncons, "etat_reseau_troncons_filtres.csv", "dl_etat_reseau")
    if tr.empty:
        st.info("Aucun tronçon pour cette sélection (les voiries n'ont qu'une ligne nationale, sans tronçon nommé).")
    else:
        c_map, c_bar = st.columns([1.1, 1], gap="small")
        with c_map:
            fig = maps.fond_prefectures(go.Figure())
            maps.outline_region(fig, region)                       # contour de la région choisie, sous les tracés
            n_trace = maps.add_troncons(fig, tr)
            charts.layout(fig, 400, legend=True, t=0, b=0, l=0, r=0, dragmode="pan")
            vue = maps.view(region, None, 400, 440)                # cadrage sur la région choisie, sinon sur tout le pays
            if not region:
                vue["zoom"] += 0.3
            fig.update_layout(map=vue, showlegend=True, legend=dict(orientation="v", x=0.0, y=1.0, xanchor="left", yanchor="top", bgcolor="rgba(255,255,255,0.85)", font=dict(size=10.5)))
            charts.show(fig, "res_troncons_map")
        with c_bar:
            top = tr.sort_values("MAUVAIS", ascending=False).head(14).iloc[::-1]
            lab = [t if len(t) <= 34 else t[:33] + "…" for t in top["troncon"]]
            fig = go.Figure()
            for e in f["etats"]:
                custom = [(name, d1(value, 1)) for name, value in zip(top["troncon"], top[e])]
                fig.add_trace(go.Bar(y=lab, x=top[e], orientation="h", name=ETAT_LIBELLES[e], marker_color=ETAT_COULEURS[e], customdata=custom,
                                     hovertemplate="<b>%{customdata[0]}</b> · état réseau 2020<br>" + ETAT_LIBELLES[e] + " : %{customdata[1]} km<extra></extra>"))
            charts.layout(fig, 400, t=26, barmode="stack"); fig.update_yaxes(showgrid=False, tickfont=dict(size=10)); fig.update_xaxes(title_text="km (2020)", title_font=dict(size=11))
            charts.show(fig, "res_troncons_bar")
        st.markdown(f'<div class="note">{n_trace} des {len(tr)} tronçons affichés ont un tracé et figurent sur la carte (couleur = état dominant, survol = détail par état) ; '
                    f'les {len(tr) - n_trace} autres n\'ont pas d\'identifiant dans les routes classées et ne figurent que dans le classement (14 plus forts km en mauvais état).</div>', unsafe_allow_html=True)
flush_panel_css()
