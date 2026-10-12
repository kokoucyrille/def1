"""Page « Diagnostic & recommandations » — où cumule-t-on les déficits d'infrastructure et de formation (objectifs O4 et O5),
puis trois priorités chiffrées, recomposées par région (objectif O5). Les deux sections partagent les filtres de la sidebar."""
from __future__ import annotations

import html
import json

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from components import charts, maps
from components.exports import download_csv
from components.filters import set_region, set_territory, sidebar
from components.kpi_cards import create_kpi_row
from components.recommendation_cards import create_priority_card
from components.styles import THEME
from components.ui import banner, flush_panel_css, page_title, panel
from data import diag as D, loader as L
from data.loader import fmt_dec as d1, fmt_int as i0, fmt_pct as p1

f = sidebar("diagnostic")
niveau, region, w, theme = f["niveau"], f["region"], f["poids"] / 100, f["theme"]
mode = "Toutes" if f["ae"] == "Toutes" else "Agréées"
thr = D.SEUIL_QUINTILE if f["seuil"].startswith("Quintile") else D.SEUIL_TERCILE
thr_lbl = "quintile défavorable (≥ 0,80)" if thr == D.SEUIL_QUINTILE else "tercile défavorable (≥ 2/3)"
consensus = f["score_mode"].startswith("Consensus")
apart = f["zeros"].startswith("Classés")
dgt = L.consensus_table(niveau, "observe", apart) if consensus else L.diag_table(niveau, mode, "observe", w, apart)
dgr = (L.consensus_table("Région", "observe", apart) if consensus else L.diag_table("Région", mode, "observe", w, apart)).sort_values("score", ascending=False)
poids_txt = "consensus des 6 configurations" if consensus else f"{round(w * 100)}/{round((1 - w) * 100)}"
view = dgt if (niveau == "Région" or not region) else dgt[dgt.region == region]
flag = view["score"].fillna(-1) >= thr
q = int((view["score"].fillna(-1) >= D.SEUIL_QUINTILE).sum())
rob = L.robustesse_table(niveau, "observe", apart)
stables = rob.attrs["stables"]
_r50 = rob[(rob.label == "50/50") & (rob.auto_ecoles == "Toutes")].iloc[0]
hz0, nq0 = _r50.n_quintile_hors_zero, _r50.n_quintile
unit_lbl = "préfecture(s)" if niveau == "Préfecture" else "région(s)"
dd = view[view.double_deficit]
ranked = view.dropna(subset=["score"]).sort_values("score", ascending=False)
top_priority = ranked.iloc[0]
if top_priority.zero_route:
    priority_action = "inventorier et programmer les routes et voiries à classer"
elif top_priority.zero_ae:
    priority_action = "créer une antenne agréée ou une auto-école mobile"
elif top_priority.score_formation >= top_priority.score_infra:
    priority_action = "étendre l'offre de formation agréée"
else:
    priority_action = "prioriser l'entretien périodique du réseau"
page_title(
    "fa-location-crosshairs",
    "Diagnostic et recommandations",
    "Infrastructure et formation : où les déficits se cumulent, puis les trois priorités qui en découlent.",
    takeaway=f"{top_priority.prefecture} est la priorité n° 1 (score {d1(top_priority.score, 2)}/1) ; action associée : {priority_action}.",
)
if apart and niveau == "Préfecture":
    import json as _json
    sens = _json.loads((L.PROC / "sensibilite_rattachement.json").read_text(encoding="utf-8"))
    banner("Réserve : avec un rattachement géographique (position des routes et auto-écoles dans les contours indicatifs) plutôt qu'administratif, "
           f"le quintile des unités mesurées devient « {', '.join(sens['quintile_hors_zeros_geographique']) or 'aucune unité'} » au lieu de « {', '.join(sens['quintile_hors_zeros_attributs'])} » "
           f"({sens['tronçons_rattaches_differemment']} tronçons et {sens['auto_ecoles_rattachees_differemment']} auto-écoles rattachés différemment). Ces préfectures sont des pistes à confirmer, pas des conclusions.")

create_kpi_row([
    {"title": "Double déficit", "value": str(len(dd)), "icon": "fa-location-crosshairs", "variant": "red", "doc": "kpi_double"},
    {"title": "Zéros structurels", "value": str(int(view.zero_structurel.sum())), "icon": "fa-database", "variant": "gray", "doc": "kpi_zeros"},
    {"title": "Région la plus défavorable", "value": dgr.iloc[0]["region"], "icon": "fa-map", "variant": "yellow", "doc": "kpi_region_def"},
    {"title": f"{'Préfectures' if niveau == 'Préfecture' else 'Régions'} du quintile défavorable", "value": str(q), "icon": "fa-gauge-high", "variant": "purple", "doc": "kpi_quintile"},
])
download_csv(
    "Télécharger les données filtrées (CSV)",
    view.replace([np.inf, -np.inf], np.nan),
    "diagnostic_filtre.csv",
    "dl_diagnostic",
)

c1, c2 = st.columns([1.2, 1], gap="small")
with c1:
    with panel("diag_score", f"Carte du score pondéré ({niveau.lower()})", "fa-map", "diag_score", height=434):
        pm = L.prefs()[["cle", "prefecture", "region"]]
        if niveau == "Région":
            mp = pm.merge(dgt[["region", "score"]], on="region")
        else:
            mp = pm.merge(dgt[["cle", "score"]], on="cle")
        flagged = set(mp.loc[mp.score.fillna(-1) >= thr, "cle"])
        sel_pref = st.session_state.get("shared_pref")
        sel_pref = None if sel_pref == L.ALL_PREFS else sel_pref
        fig = maps.choropleth(mp, "score", "score (1 = défavorable)", lambda v: d1(v, 2), 370, "YlOrRd", zmin=0, zmax=1, contour_cles=flagged,
                              selected=sel_pref if niveau == "Préfecture" else None, region=region,
                              hover_extra=f"Formule : {round(w * 100)}/{round((1 - w) * 100)} infrastructure/formation ; population RGPH 2022",
                              zoom_region=region, width=700)
        sel = charts.show(fig, "diag_map", select=niveau == "Préfecture")
        v = charts.clicked_value(sel) if niveau == "Préfecture" else None
        if v and v != sel_pref:
            set_territory(v); st.rerun()
with c2:
    with panel("diag_classement", f"Top 5 des priorités · score {round(w * 100)}/{round((1 - w) * 100)}", "fa-chart-simple", "diag_classement", height=434):
        top = ranked.head(5).iloc[::-1]
        fig = go.Figure()
        infra_contrib = [(d1(score, 2), d1(w * score, 2)) for score in top.score_infra]
        formation_contrib = [(d1(score, 2), d1((1 - w) * score, 2)) for score in top.score_formation]
        fig.add_trace(go.Bar(y=top.prefecture, x=w * top.score_infra, orientation="h", name="Infrastructure (pondérée)", marker_color="#0a5ec0", customdata=infra_contrib,
                             hovertemplate="%{y} · classement filtré<br>Infrastructure : score %{customdata[0]} / 1 · contribution %{customdata[1]}<br>Formule : score infrastructure × pondération sélectionnée<extra></extra>"))
        fig.add_trace(go.Bar(y=top.prefecture, x=(1 - w) * top.score_formation, orientation="h", name="Formation (pondérée)", marker_color="#e8590c", customdata=formation_contrib,
                             hovertemplate="%{y} · classement filtré<br>Formation : score %{customdata[0]} / 1 · contribution %{customdata[1]}<br>Formule : score formation × pondération sélectionnée<extra></extra>"))
        for p_, sc, z in zip(top.prefecture, top.score, top.zero_structurel):
            fig.add_annotation(y=p_, x=sc, text=f" {d1(sc, 2)}" + (" · zéro structurel" if z else ""), showarrow=False, xanchor="left", font=dict(size=10.5, color="#a3182c" if z else "#4a6572"))
        charts.layout(fig, 375, t=32, barmode="stack", r=70); fig.update_xaxes(range=[0, 1.25], title_text="Score (0 à 1)", title_font=dict(size=11)); fig.update_yaxes(showgrid=False, tickfont=dict(size=10.5))
        charts.show(fig, "diag_rank")

c3, c4 = st.columns([1.2, 1], gap="small")
with c3:
    with panel("diag_nuage", "Routes par habitant × habitants par auto-école", "fa-chart-line", "diag_nuage", height=439):
        v2 = view.copy()
        finite = v2.hab_par_ae.replace(np.inf, np.nan)
        ymax = float(finite.max()) * 1.6
        v2["y"] = v2.hab_par_ae.where(~v2.zero_ae, ymax)
        fig = go.Figure()
        for lab, m, col, sym in (("Hors seuil", ~flag & ~v2.zero_ae, "#8a99a8", "circle"), (f"Dans le {thr_lbl.split(' (')[0]}", flag & ~v2.zero_ae, "#f20e36", "circle"),
                                 ("Zéro auto-école (zéro structurel)", v2.zero_ae, "#10335c", "x")):
            g = v2[m]
            scatter_data = [
                (d1(km, 2), "aucune auto-école" if zero else i0(hab), i0(pop), d1(score, 2))
                for km, zero, hab, pop, score in zip(g.km_10k, g.zero_ae, g.hab_par_ae, g.population, g.score)
            ]
            fig.add_trace(go.Scatter(x=g.km_10k, y=g.y, mode="markers", name=lab, text=g.prefecture, customdata=scatter_data,
                                     marker=dict(size=np.clip(np.sqrt(g.population) / 25, 7, 26), color=col, symbol=sym, opacity=0.85, line=dict(color="#fff", width=1)),
                                     hovertemplate="<b>%{text}</b> · RGPH 2022<br>km / 10 000 hab. : %{customdata[0]}<br>Hab. / auto-école : %{customdata[1]} · population %{customdata[2]}<br>Score : %{customdata[3]} / 1 · formule : score infrastructure/formation pondéré<extra></extra>"))
        charts.layout(fig, 380, t=34); fig.update_xaxes(title_text="km de routes classées / 10 000 hab. (bas = défavorable)", title_font=dict(size=11), showgrid=True, gridcolor=charts.GRID)
        fig.update_yaxes(title_text="Habitants par auto-école (haut = défavorable)", title_font=dict(size=11), type="log",
                         tickvals=[v for v in (10000, 30000, 100000, 300000) if v < ymax * 0.8] + [ymax], ticktext=[i0(v) for v in (10000, 30000, 100000, 300000) if v < ymax * 0.8] + ["aucune auto-école"])
        fig.add_annotation(x=0, y=1.0, xref="x domain", yref="y domain", text="↖ double déficit", showarrow=False, xanchor="left", yanchor="top", font=dict(size=11, color="#a3182c"))
        charts.show(fig, "diag_scatter")
with c4:
    with st.expander("Options avancées", expanded=False):
        with panel("diag_robustesse", "Robustesse du classement", "fa-gear", "diag_robustesse", height=439):
            t = rob.assign(auto_ecoles=rob.auto_ecoles)
            piv = t.pivot(index="label", columns="auto_ecoles", values="n_quintile").reindex(["20/80", "50/50", "80/20"])
            fig = go.Figure()
            for c, col in (("Toutes", "#0a5ec0"), ("Agréées", "#e8590c")):
                fig.add_trace(go.Bar(x=piv.index, y=piv[c], name=f"Auto-écoles : {c.lower()}", marker_color=col, text=piv[c], textposition="outside",
                                     hovertemplate="Pondération infrastructure/formation %{x}<br>" + c + " : <b>%{y}</b> unité(s) dans le quintile défavorable<br>Formule : score ≥ seuil quintile défavorable<extra></extra>"))
            charts.layout(fig, 200, t=32, barmode="group"); fig.update_yaxes(rangemode="tozero", title_text="Unités dans le quintile", title_font=dict(size=10.5)); fig.update_xaxes(title_text="Pondération infrastructure/formation", title_font=dict(size=10.5))
            charts.show(fig, "diag_rob")
            cons_t = L.consensus_table(niveau, "observe", apart)
            freq = cons_t[cons_t.n_quintile >= 3].sort_values(["n_quintile", "score"], ascending=False).head(10)
            chips = "".join(f'<span class="chip{" z" if n == 6 else ""}">{p_} {n}/6</span>' for p_, n in zip(freq.prefecture, freq.n_quintile))
            st.markdown('<div class="note"><b>Fréquence dans le quintile défavorable (sur 6 configurations) :</b> ' + (chips or "aucune unité à ≥ 3/6") + "</div>", unsafe_allow_html=True)
            hz = rob[(rob.label == "50/50") & (rob.auto_ecoles == "Toutes")].n_quintile_hors_zero.iloc[0]

# ---- Section 2 : recommandations (mêmes filtres de région que le diagnostic ci-dessus) -----------------------
page_title("fa-lightbulb", "Recommandations", "Trois priorités pour une mobilité plus sûre, chiffrées à partir des données.", section=True)
RECO = json.loads((L.PROC / "recommandations.json").read_text(encoding="utf-8"))
reco = RECO[region or "Toutes les régions"]
st.markdown(f'<div class="note" style="margin:-8px 0 10px 0">Territoire : <b>{html.escape(region or "toutes les régions")}</b> — thème : <b>{html.escape(theme)}</b>. Chaque constat est calculé ; les territoires cités viennent du diagnostic ci-dessus.</div>', unsafe_allow_html=True)
COLORS = [THEME["green"], THEME["blue_link"], THEME["blue_link"]]
ICONS = ['<i class="fa-solid fa-suitcase-medical"></i>', '<i class="fa-solid fa-users"></i>', '<i class="fa-solid fa-layer-group"></i>']
shown = 0
for i, th in enumerate(reco["themes"]):
    if theme != "Tous les thèmes" and th["id"] != theme:
        continue
    acts = []
    for a in th["actions"]:
        lines = [("Constat chiffré", a["constat"]), ("Où", a["ou"]), ("Action", a["action"]), ("Indicateur de suivi", a["indicateur"]), ("Horizon", a["horizon"])]
        body = "".join(f'<span class="reco-line"><span class="k">{k}</span><span>{html.escape(v)}</span></span>' for k, v in lines)
        acts.append((a["tag"], a["label"], body))
    st.markdown(create_priority_card(ICONS[i], th["title"], COLORS[i], f"PRIORITÉ {i + 1}", acts, tip=""), unsafe_allow_html=True)
    locations: list[tuple[str, str]] = []
    cited_text = " ".join(action["ou"] for action in th["actions"])
    for name in L.ORDRE_REGIONS:
        if name.casefold() in cited_text.casefold():
            locations.append((name, "region"))
    for name in L.prefs().prefecture:
        if name.casefold() in cited_text.casefold():
            locations.append((name, "pref"))
    if locations:
        button_cols = st.columns(min(4, len(locations)))
        for location_idx, (name, kind) in enumerate(locations):
            with button_cols[location_idx % len(button_cols)]:
                if st.button(f"Voir {name}", key=f"reco_{th['id']}_{location_idx}", type="secondary"):
                    if kind == "pref":
                        set_territory(name)
                    else:
                        set_region(name)
    shown += 1
if not shown:
    banner("Aucune priorité pour ce thème.")
st.markdown(f'<div class="reco-card"><div class="reco-head"><div class="reco-ico"><i class="fa-solid fa-circle-info"></i></div>'
            f'<span class="reco-title" style="color:#c8102e">Ce que les données ne permettent pas de décider</span></div>'
            '<div class="reco-rows"><div class="reco-row"><span class="reco-text">'
            '<span class="reco-line"><span class="k">Sécurité par territoire</span><span>Accidents, blessés et morts n\'existent qu\'au niveau national : aucune action ne peut être localisée par préfecture sur cette base.</span></span>'
            '<span class="reco-line"><span class="k">État du réseau</span><span>Une seule année (2020), sans région ; la jointure aux routes classées couvre de 0 % (Grand Lomé) à 90,6 % (Kara) : estimation indicative, hors score.</span></span>'
            '<span class="reco-line"><span class="k">Conducteurs réels</span><span>Les permis sont un flux annuel délivré aux examens, pas un nombre de conducteurs ; la conduite sans permis n\'est pas mesurée.</span></span>'
            '<span class="reco-line"><span class="k">Offre de formation</span><span>Le recensement des auto-écoles est possiblement incomplet hors Grand Lomé : un zéro peut être une absence d\'enregistrement.</span></span>'
            '<span class="reco-line"><span class="k">Causalité</span><span>Les corrélations (ex. deux-roues et morts, ρ faible sur 13 années) ne prouvent aucun effet.</span></span>'
            '</span></div></div></div>', unsafe_allow_html=True)
flush_panel_css()
