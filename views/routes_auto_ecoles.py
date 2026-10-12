"""Page « Routes & auto-écoles » — répartition des routes classées et des auto-écoles, par préfecture et par habitant (analyse attendue n° 5)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import charts, maps
from components.exports import download_csv
from components.filters import INDIC_CARTE, set_territory, sidebar
from components.kpi_cards import create_kpi_row
from components.ui import banner, flush_panel_css, page_title, panel
from data import loader as L
from data.loader import fmt_dec as d1, fmt_int as i0, fmt_pct as p1

f = sidebar("routes_ae")
region, pref_sel = f["region"], f["pref"]
F = L.facts()
if not f["types"]:
    banner("Sélection vide : choisissez au moins un type de route dans les filtres.")
    st.stop()
defn = "observe" if f["defn"] == "Revêtement observé" else "admin"

df = L.routes_score_table()
INDIC = {  # libellé -> (colonne, unité, format, échelle, sens défavorable : True = valeur haute défavorable)
    INDIC_CARTE[0]: ("km_10k", "km / 10 000 hab.", lambda v: d1(v, 2), "YlGnBu", False),
    INDIC_CARTE[1]: ("part_non_revetue", "part non revêtue", lambda v: p1(100 * v, 0) if np.isfinite(v) else "aucune route classée", "YlOrRd", True),
    INDIC_CARTE[2]: ("hab_par_ae", "hab. / auto-école", lambda v: i0(v) if np.isfinite(v) else "aucune auto-école (zéro structurel)", "YlOrRd", True),
    INDIC_CARTE[3]: ("ae_agr_100k", "agréées / 100 000 hab.", lambda v: d1(v, 2), "YlGnBu", False),
    INDIC_CARTE[4]: ("score", "score (1 = défavorable)", lambda v: d1(v, 2), "YlOrRd", True),
    INDIC_CARTE[5]: ("population", "habitants", lambda v: i0(v), "Blues", False),
}
col, unit, fmt, scale, bad_high = INDIC[f["indic"]]
FORMULA = {
    "km_10k": "km classés / population RGPH 2022 × 10 000",
    "part_non_revetue": "km non revêtus / km classés × 100",
    "hab_par_ae": "population RGPH 2022 / auto-écoles recensées",
    "ae_agr_100k": "auto-écoles agréées / population × 100 000",
    "score": "moyenne pondérée des rangs relatifs infrastructure et formation",
    "population": "population RGPH 2022",
}

sub = df if not region else df[df.region == region]
sel_row = df[df.prefecture == pref_sel].iloc[0] if pref_sel else None
terr_lbl = pref_sel or region or "National"
ranked_indicator = sub.assign(_sort=sub[col].fillna(np.inf if bad_high else -np.inf)).sort_values("_sort", ascending=not bad_high)
worst_indicator = ranked_indicator.iloc[0]
worst_value = fmt(worst_indicator[col]) if np.isfinite(worst_indicator[col]) else "non renseigné"
page_title(
    "fa-map",
    "Routes & auto-écoles",
    "Comment les routes classées et les auto-écoles se répartissent-elles par région et par préfecture, rapportées à la population ?",
    takeaway=f"{worst_indicator.prefecture} est la priorité pour « {f['indic']} » : {worst_value} {unit}.",
)

# ---- KPI du territoire sélectionné (national par défaut) ----------------------------------------
g0 = df[df.prefecture == pref_sel] if pref_sel else sub
km0, pop0, ae0 = g0.km.sum(), g0.population.sum(), g0.ae_toutes.sum()
nr0 = g0.km_non_revetu.sum() / km0 if km0 else np.nan
create_kpi_row([
    {"title": f"Routes classées (km) · {terr_lbl}", "value": i0(km0), "icon": "fa-map", "variant": "green", "doc": "kpi_km"},
    {"title": f"Part non revêtue · {terr_lbl}", "value": p1(100 * nr0, 0) if np.isfinite(nr0) else "n.d.", "icon": "fa-layer-group", "variant": "yellow"},
    {"title": f"Auto-écoles recensées · {terr_lbl}", "value": i0(ae0), "icon": "fa-building-columns", "variant": "blue"},
    {"title": f"Habitants par auto-école · {terr_lbl}", "value": i0(pop0 / ae0) if ae0 else "aucune", "icon": "fa-users", "variant": "red"},
])

# ---- Rangée 1 : carte interactive + fiche territoire et classement ------------------------------
c_left, c_right = st.columns([1.6, 1], gap="small")
with c_left:
    with panel("carte_main", f"Carte — {f['indic']}", "fa-map", "carte_main", height=579):
        if f["osm"]:
            from components import map_osm
            map_osm.render(df, col, unit, fmt, f, region, pref_sel, 520)
        else:
            fig = maps.choropleth(df, col, unit, fmt, 520, scale, selected=pref_sel, region=region if not pref_sel else None,
                                  hover_extra=f"Formule : {FORMULA[col]}", zoom_region=region, width=700)
            if "Réseau routier" in f["couches"]:
                maps.add_roads(fig, f["types"], region, pref_sel)
            if "Auto-écoles" in f["couches"]:
                ae = L.table("auto_ecoles")
                ae = ae if f["statut"] == "Toutes" else ae[ae["agreee"] == (f["statut"] == "Agréées")]
                ae = ae if not region else ae[ae.region == region]
                ae = ae if not pref_sel else ae[ae.prefecture == pref_sel]
                maps.add_ae(fig, ae)
            fig.update_layout(showlegend=True, legend=dict(orientation="v", x=0.995, y=0.995, xanchor="right", yanchor="top", bgcolor="rgba(255,255,255,0.88)", bordercolor="#d7e5ea", borderwidth=1, font=dict(size=11)))
            sel = charts.show(fig, "carte_map", select=True)
            v = charts.clicked_value(sel) or charts.clicked_value(sel, "location")
            v = (df.loc[df.cle == v, "prefecture"].iloc[0] if v in set(df.cle) else v)
            if v and v != pref_sel and v in set(df.prefecture):
                set_territory(v); st.rerun()

with c_right:
    with panel("carte_fiche", f"Fiche territoire — {pref_sel or region or 'National'}", "fa-location-crosshairs", "carte_fiche", height=241):
        if pref_sel:
            r = sel_row; pop, km, k10, nr = r.population, r.km, r.km_10k, r.part_non_revetue
            ae_n, ae_a, hab, rang = r.ae_toutes, r.ae_agreees, r.hab_par_ae, f"{int(r.rang)} / 39"
            zs = ["aucune route classée"] * bool(r.zero_route) + ["aucune auto-école"] * bool(r.zero_ae)
        else:
            g = sub if region else df
            pop, km, ae_n, ae_a = g.population.sum(), g.km.sum(), g.ae_toutes.sum(), g.ae_agreees.sum()
            k10, nr = km / pop * 1e4, (g.km_non_revetu.sum() / km if km else np.nan)
            hab, rang = (pop / ae_n if ae_n else np.nan), ("—" if not region else f"{int(L.diag_table('Région', 'Toutes', 'observe', 0.5).set_index('region').loc[region, 'rang'])} / 6 (régions)")
            zs = []
        st.markdown('<div class="fiche">' + "".join(f"<div>{a}</div><div>{b}</div>" for a, b in [
            ("Population (RGPH 2022)", i0(pop)), ("Routes classées (km)", i0(km)), ("km / 10 000 hab.", d1(k10, 2)),
            ("Part non revêtue", p1(100 * nr, 0) if np.isfinite(nr) else "n.d."), ("Auto-écoles (dont agréées)", f"{i0(ae_n)} ({i0(ae_a)})"),
            ("Habitants par auto-école", i0(hab) if np.isfinite(hab) else "aucune"), ("Rang du score (1 = défavorable)", rang)]) + "</div>", unsafe_allow_html=True)
        if zs:
            st.markdown("".join(f'<span class="chip z">zéro structurel : {z}</span>' for z in zs), unsafe_allow_html=True)
    with panel("carte_classement", f"Classement — {f['indic'][:34]}", "fa-chart-simple", "carte_classement", height=324):
        key = sub[col].fillna(np.inf if bad_high else -np.inf)
        w = sub.assign(_k=key).sort_values("_k", ascending=not bad_high).head(10).iloc[::-1]
        vals = w[col].fillna(0)
        rank_data = [(fmt(v) if np.isfinite(v) else ("aucune auto-école" if col == "hab_par_ae" else "non renseigné"), str(r)) for v, r in zip(w[col], w.rang)]
        fig = go.Figure(go.Bar(y=w.prefecture, x=vals, orientation="h", customdata=rank_data,
                               marker_color=["#f20e36" if p == pref_sel else "#0a5ec0" for p in w.prefecture],
                               text=[fmt(v) if np.isfinite(v) else "zéro" for v in w[col]], textposition="outside", cliponaxis=False,
                               hovertemplate=f"%{{y}} · rang %{{customdata[1]}} / 39<br>{unit} : <b>%{{customdata[0]}}</b><br>Formule : {FORMULA[col]}<extra></extra>"))
        charts.layout(fig, 240, legend=False, t=2, r=60); fig.update_yaxes(showgrid=False, tickfont=dict(size=10.5)); fig.update_xaxes(visible=False)
        sel2 = charts.show(fig, "carte_rank", select=True)
        v2 = charts.clicked_value(sel2)
        if v2 and v2 != pref_sel:
            set_territory(v2); st.rerun()

# ---- Rangée 2 : linéaire classé par territoire + types de routes et revêtements -----------------
tt_f = L.terr_table("Préfecture", "Toutes", defn, tuple(f["types"]))
tsel = tt_f if not region else tt_f[tt_f.region == region]
tsel = tsel if not pref_sel else tsel[tsel.prefecture == pref_sel]
tsel_export = tsel.copy()
download_csv("Télécharger les données filtrées (CSV)", tsel_export, "routes_auto_ecoles_filtrees.csv", "dl_routes_ae")
c3, c4 = st.columns([1.2, 1], gap="small")
with c3:
    with panel("res_territoire", f"Réseau classé par territoire — {terr_lbl}", "fa-map", "res_territoire", height=359):
        if region and not pref_sel:
            gt, ttl = tsel.sort_values("km", ascending=False), "prefecture"
        elif pref_sel:
            gt, ttl = tsel, "prefecture"
        else:
            gt, ttl = L.terr_table("Région", "Toutes", defn, tuple(f["types"])).set_index("region").reindex(L.ORDRE_REGIONS).reset_index(), "region"
        name = gt[ttl]
        fig = go.Figure()
        km_data = [(i0(v), r) for v, r in zip(gt.km_revetu, gt[ttl])]
        non_data = [(i0(v), r) for v, r in zip(gt.km_non_revetu, gt[ttl])]
        km10k_data = [(d1(v, 2), r) for v, r in zip(gt.km_10k, gt[ttl])]
        fig.add_trace(go.Bar(x=name, y=gt.km_revetu, name="Revêtues", marker_color="#10335c", customdata=km_data,
                             hovertemplate="%{customdata[1]}<br>Routes revêtues : <b>%{customdata[0]} km</b><extra></extra>"))
        fig.add_trace(go.Bar(x=name, y=gt.km_non_revetu, name="Non revêtues", marker_color="#c9a227", customdata=non_data,
                             hovertemplate="%{customdata[1]}<br>Routes non revêtues : <b>%{customdata[0]} km</b><extra></extra>"))
        fig.add_trace(go.Scatter(x=name, y=gt.km_10k, name="km / 10 000 hab. (axe droit)", yaxis="y2", mode="markers", marker=dict(size=10, color="#e8590c", symbol="diamond", line=dict(color="#fff", width=1)),
                                 customdata=km10k_data,
                                 hovertemplate="%{customdata[1]} · région<br>km / 10 000 hab. : <b>%{customdata[0]}</b><br>Formule : km classés / population RGPH 2022 × 10 000<extra></extra>"))
        charts.layout(fig, 300, t=34, barmode="stack")
        fig.update_layout(yaxis2=dict(overlaying="y", side="right", showgrid=False, rangemode="tozero", tickfont=dict(size=11.5, color="#3a5566")))
        fig.update_xaxes(tickangle=-35 if len(gt) > 6 else 0); fig.update_yaxes(title_text="km de routes classées", title_font=dict(size=11), selector=dict(overlaying=None))
        charts.show(fig, "res_terr_ch")
with c4:
    with panel("res_types", f"Types de routes et revêtements — {terr_lbl}", "fa-layer-group", "res_types", height=359):
        d = L.table("routes_detail")
        d = d[d.route_type.isin(f["types"])]
        d = d if not region else d[d.region == region]
        d = d if not pref_sel else d[d.prefecture == pref_sel]
        gd = d.groupby(["route_type", "route_recouvrement"], as_index=False).km.sum()
        pal = {"Bitume": "#10335c", "Béton": "#4b6a9b", "Pavé": "#8fa8c8", "Terre amenagée": "#c9a227", "Terre non amenagée": "#a0522d", "Gravier amenagé": "#6c8f55", "Gravier non amenagé": "#9bb88a"}
        if gd.empty or gd.km.sum() <= 0:
            charts.show(charts.empty_fig(300, "Aucune route classée pour cette sélection"), "res_types_ch")
        else:
            # deux cercles : répartition des kilomètres par type de route et par revêtement observé
            tot_km = gd.km.sum()
            gt_ = gd.groupby("route_type").km.sum().sort_values(ascending=False)
            gr_ = gd.groupby("route_recouvrement").km.sum().sort_values(ascending=False)
            court = lambda t_: t_.replace("Route nationale", "RN")      # noqa: E731
            fig = go.Figure()
            ctr = lambda t_: dict(text=t_, position="middle center", font=dict(size=10.5, color="#10335c"))      # noqa: E731 — texte centré dans le trou du cercle
            fig.add_trace(go.Pie(labels=[court(t_) for t_ in gt_.index], values=gt_.values, hole=0.55, sort=False, direction="clockwise", domain=dict(x=[0.0, 0.48], y=[0.3, 0.92]), title=ctr(f"<b>{i0(tot_km)}</b><br>km classés"),
                                 marker=dict(colors=[charts.C_TYPE.get(t_, "#8a99a8") for t_ in gt_.index], line=dict(color="#ffffff", width=2)), texttemplate="%{percent:.0%}", textposition="inside", textfont=dict(size=11, color="#ffffff"),
                                 hovertext=[f"<b>{t_}</b><br>{d1(v, 1)} km · {p1(100 * v / tot_km, 0)} du linéaire classé" for t_, v in gt_.items()], hoverinfo="text"))
            fig.add_trace(go.Pie(labels=list(gr_.index), values=gr_.values, hole=0.55, sort=False, direction="clockwise", domain=dict(x=[0.52, 1.0], y=[0.3, 0.92]), title=ctr("<b>revêtement</b><br>observé"),
                                 marker=dict(colors=[pal.get(r_, "#8a99a8") for r_ in gr_.index], line=dict(color="#ffffff", width=2)), texttemplate="%{percent:.0%}", textposition="inside", textfont=dict(size=11, color="#ffffff"),
                                 hovertext=[f"<b>{r_}</b><br>{d1(v, 1)} km · {p1(100 * v / tot_km, 0)} du linéaire classé" for r_, v in gr_.items()], hoverinfo="text"))
            charts.layout(fig, 300, t=22, b=2, l=4, r=4, uniformtext=dict(minsize=9, mode="hide"))
            fig.update_layout(legend=dict(orientation="h", x=0.5, xanchor="center", y=0.0, yanchor="bottom", font=dict(size=10), tracegroupgap=0))
            for x_, t_ in ((0.24, "Par type de route"), (0.76, "Par revêtement observé")):
                fig.add_annotation(x=x_, y=1.0, xref="paper", yref="paper", text=f"<b>{t_}</b>", showarrow=False, font=dict(size=11.5, color="#3a5566"), yanchor="bottom")
            charts.show(fig, "res_types_ch")

# ---- Rangée 3 : « Tableau région → préfecture » en version graphique (treemap + heatmap) ----------
lead = sub.copy()
n_lead = len(lead)
h_chart = max(360, 15 * n_lead + 92)
reg_tab = L.terr_table("Région").set_index("region")
reg_diag = L.diag_table("Région", "Toutes", "observe", 0.5).set_index("region")


def _hover(r) -> str:
    nr_ = f"{p1(100 * r.part_non_revetue, 0)}" if np.isfinite(r.part_non_revetue) else "aucune route classée"
    ae_ = f"{i0(r.hab_par_ae)} hab. / auto-école" if np.isfinite(r.hab_par_ae) else "aucune auto-école"
    return (f"<b>{r.prefecture} · {r.region}</b> · RGPH 2022<br>{unit} : {fmt(r[col])}<br>Rang : {i0(r.rang)} / 39 préfectures<br>Formule : {FORMULA[col]}")


c5, c6 = st.columns([1.15, 1], gap="small")
with c5:
    with panel("carte_treemap", f"Région → préfecture — {f['indic'][:34]}", "fa-layer-group", "carte_treemap", height=h_chart + 59):
        finite = lead[col].replace([np.inf, -np.inf], np.nan).dropna()
        lo, hi = (float(np.nanpercentile(finite, 5)), float(np.nanpercentile(finite, 95))) if len(finite) > 1 else (0.0, 1.0)
        if hi <= lo:
            lo, hi = float(finite.min()) if len(finite) else 0.0, (float(finite.max()) if len(finite) else 1.0) + 1e-9
        worst = hi if bad_high else lo
        ids, labels, parents, values, colors, hov, lw, lc = [], [], [], [], [], [], [], []
        for rg in [r for r in L.ORDRE_REGIONS if r in set(lead.region)]:
            gr = lead[lead.region == rg]
            rv = float(reg_diag.loc[rg, "score"]) if col == "score" else float(reg_tab.loc[rg, col])
            ids.append(rg); labels.append(rg); parents.append(""); values.append(float(gr.population.sum()))
            colors.append(float(np.clip(rv if np.isfinite(rv) else worst, lo, hi)))
            rr = reg_tab.loc[rg]
            hov.append(f"<b>{rg}</b> (région)<br>Population : {i0(rr.population)}<br>Routes classées : {i0(rr.km)} km ({d1(rr.km_10k, 2)} km / 10 000 hab.)<br>Auto-écoles : {i0(rr.ae_toutes)} (dont {i0(rr.ae_agreees)} agréées)")
            lw.append(1); lc.append("#ffffff")
            for _, r in gr.sort_values("population", ascending=False).iterrows():
                v = r[col]
                ids.append(f"{rg}|{r.prefecture}"); labels.append(r.prefecture); parents.append(rg); values.append(float(r.population))
                colors.append(float(np.clip(v if np.isfinite(v) else worst, lo, hi)))
                hov.append(_hover(r) + f"<br><i>{unit} : {fmt(v)}</i>")
                sel_ = r.prefecture == pref_sel
                lw.append(3 if sel_ else 1); lc.append("#f20e36" if sel_ else "#ffffff")
        fig = go.Figure(go.Treemap(ids=ids, labels=labels, parents=parents, values=values, branchvalues="total", sort=False, hovertext=hov, hoverinfo="text", textinfo="label",
                                   textfont=dict(size=12), tiling=dict(pad=2), pathbar=dict(visible=False), root_color="rgba(0,0,0,0)",
                                   marker=dict(colors=colors, colorscale=scale, cmin=lo, cmax=hi, line=dict(color=lc, width=lw), pad=dict(t=24, l=2, r=2, b=2),
                                               colorbar=dict(thickness=10, len=0.6, title=dict(text=unit[:24], side="right"), tickfont=dict(size=10)))))
        charts.layout(fig, h_chart, legend=False, t=4, b=4, l=4, r=4)
        charts.show(fig, "carte_treemap_ch")
with c6:
    with panel("carte_heatmap", "Profil des préfectures — rang par indicateur", "fa-chart-simple", "carte_heatmap", height=h_chart + 59):
        HM = [("km_10k", "km /<br>10 000 hab.", False, lambda v: f"{d1(v, 2)} km / 10 000 hab."),
              ("part_non_revetue", "Part non<br>revêtue", True, lambda v: f"{p1(100 * v, 0)} non revêtue" if np.isfinite(v) else "aucune route classée"),
              ("hab_par_ae", "Hab. par<br>auto-école", True, lambda v: f"{i0(v)} hab. / auto-école" if np.isfinite(v) else "aucune auto-école"),
              ("ae_agr_100k", "Agréées /<br>100 000 hab.", False, lambda v: f"{d1(v, 2)} agréées / 100 000 hab."),
              ("score", "Score<br>diagnostic", True, lambda v: f"score {d1(v, 2)}")]
        base_ = df.set_index("prefecture")

        def unfav(c_: str, bad: bool):
            s = base_[c_].replace([np.inf, -np.inf], np.nan)
            n_ = s.notna().sum()
            # rang percentile sur les 39 préfectures ; les ex æquo prennent le rang le plus défavorable (ex. tous les zéros)
            u = (s.rank(method="max") - 1) / max(n_ - 1, 1) if bad else 1 - (s.rank(method="min") - 1) / max(n_ - 1, 1)
            return u.mask(s.isna(), 1.0) if c_ == "hab_par_ae" else u     # zéro auto-école = zéro structurel = rang le plus défavorable

        U = {c_: unfav(c_, bad) for c_, _, bad, _ in HM}
        order = {r: i for i, r in enumerate(L.ORDRE_REGIONS)}
        hm = lead.assign(_r=lead.region.map(order)).sort_values(["_r", "score"], ascending=[True, False]).reset_index(drop=True)
        z = [[(float(U[c_][p]) if np.isfinite(U[c_][p]) else None) for c_, _, _, _ in HM] for p in hm.prefecture]
        txt = [[f"<b>{r.prefecture}</b> · {r.region}<br>{ft(r[c_])}" + (f"<br>Déficit relatif : {d1(U[c_][r.prefecture], 2)} (0 = favorable, 1 = le plus défavorable)" if np.isfinite(U[c_][r.prefecture]) else "")
                + "<br>Formule : rang percentile relatif aux 39 préfectures"
                for c_, _, _, ft in HM] for _, r in hm.iterrows()]
        fig = go.Figure(go.Heatmap(z=z, x=[h[1] for h in HM], y=list(hm.prefecture), text=txt, hovertemplate="%{text}<extra></extra>", colorscale="YlOrRd", zmin=0, zmax=1, xgap=2, ygap=2,
                                   colorbar=dict(orientation="h", x=0.5, xanchor="center", y=-0.02, yanchor="top", len=0.5, thickness=8, tickvals=[0, 1], ticktext=["favorable", "défavorable"], tickfont=dict(size=10))))
        charts.layout(fig, h_chart, legend=False, t=44, b=48, l=4, r=92)
        fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(size=10.5), dtick=1)
        fig.update_xaxes(side="top", showgrid=False, tickfont=dict(size=10.5))
        for rg, blk in hm.groupby("region", sort=False):
            i0_, i1_ = blk.index.min(), blk.index.max()
            if i0_ > 0:
                fig.add_shape(type="line", xref="paper", x0=0, x1=1, yref="y", y0=i0_ - 0.5, y1=i0_ - 0.5, line=dict(color="#10335c", width=1.4))
            fig.add_annotation(xref="paper", x=1.0, xanchor="left", xshift=8, yref="y", y=(i0_ + i1_) / 2, text=f"<b>{rg}</b>", showarrow=False, font=dict(size=10.5, color="#10335c"))
        if pref_sel and pref_sel in set(hm.prefecture):
            k_ = int(hm.index[hm.prefecture == pref_sel][0])
            fig.add_shape(type="rect", xref="x", x0=-0.5, x1=len(HM) - 0.5, yref="y", y0=k_ - 0.5, y1=k_ + 0.5, line=dict(color="#f20e36", width=2.5))
        charts.show(fig, "carte_heatmap_ch")

# ---- Rangée 4 : répartition des auto-écoles par région et préfecture (agréées / non agréées, agrégée ou non) ---------------
page_title("fa-building-columns", "Répartition des auto-écoles", "Combien d'auto-écoles par région et par préfecture, agréées et non agréées, en effectifs ou rapportées à la population ?", section=True)
split, per100k = f["ae_vue"].startswith("Agréées"), f["ae_mode"].startswith("Pour")
ar, ap = L.ae_repartition("Région"), L.ae_repartition("Préfecture")
C_AGR, C_NON, C_TOT = charts.C_AE["Agréée"], charts.C_AE["Non agréée"], "#0a5ec0"
U_AE = "pour 100 000 hab." if per100k else "auto-écoles"
fv = (lambda v: d1(v, 2)) if per100k else (lambda v: i0(v))


def _vals(d):
    return (d.agr_100k, d.non_agr_100k, d.ae_100k) if per100k else (d.agreees, d.non_agr, d.total)


def _hov_ae(r) -> str:
    nom = getattr(r, "prefecture", None)
    ent = f"<b>{nom}</b> · {r.region}" if nom else f"<b>{r.region}</b> (région)"
    return (f"{ent}<br>Agréées : {i0(r.agreees)} (dont {i0(r.antenne)} antennes)<br>Non agréées : {i0(r.non_agr)}<br>Total : {i0(r.total)}"
            f" · {p1(r.part_agreees, 0) if np.isfinite(r.part_agreees) else 'aucune'} agréées<br>Population : {i0(r.population)} · {d1(r.ae_100k, 2)} auto-écoles / 100 000 hab.")


ap_v = (ap if not region else ap[ap.region == region])
pa = ap_v[ap_v.total > 0].assign(_r=lambda d: d.region.map({r: i for i, r in enumerate(L.ORDRE_REGIONS)})).sort_values(["_r", "total", "prefecture"], ascending=[True, False, True]).reset_index(drop=True)
sans = sorted(ap_v.loc[ap_v.total == 0, "prefecture"])
h_ae = max(440, 17 * len(pa) + 60)
H_R = h_ae + 59 + 44                      # panneau préfectures ; les deux panneaux de gauche s'empilent à la même hauteur totale
H_1 = 262; H_2 = H_R - 14 - H_1
c7, c8 = st.columns([1, 1.25], gap="small")
with c7:
    with panel("ae_region", f"Auto-écoles par région — {'agréées et non agréées' if split else 'total'}", "fa-building-columns", "ae_region", height=H_1):
        va, vn, vt = _vals(ar)
        op = [1.0 if (not region or r == region) else 0.4 for r in ar.region]
        hov = [_hov_ae(r) for r in ar.itertuples()]
        fig = go.Figure()
        if split:
            fig.add_trace(go.Bar(x=ar.region, y=va, name="Agréées", marker=dict(color=C_AGR, opacity=op), hovertext=hov, hoverinfo="text"))
            fig.add_trace(go.Bar(x=ar.region, y=vn, name="Non agréées", marker=dict(color=C_NON, opacity=op), hovertext=hov, hoverinfo="text"))
        else:
            fig.add_trace(go.Bar(x=ar.region, y=vt, name="Total", marker=dict(color=C_TOT, opacity=op), hovertext=hov, hoverinfo="text"))
        fig.add_trace(go.Scatter(x=ar.region, y=vt, mode="text", text=[fv(v) for v in vt], textposition="top center", showlegend=False, hoverinfo="skip", cliponaxis=False))
        charts.layout(fig, H_1 - 59, legend=split, t=34, barmode="stack"); fig.update_layout(legend_traceorder="normal")
        fig.update_yaxes(title_text=("Auto-écoles / 100 000 hab." if per100k else "Auto-écoles"), title_font=dict(size=11), range=[0, float(vt.max()) * 1.18])
        charts.show(fig, "ae_region_ch")
    with panel("ae_part", "Statut national et poids des régions" if split else "Poids des régions : auto-écoles et population", "fa-chart-pie", "ae_part", height=H_2):
        CR = {"Grand Lomé": "#10335c", "Maritime": "#1488ee", "Plateaux": "#0d8a7a", "Centrale": "#7b61c9", "Kara": "#c9a227", "Savanes": "#b08968"}
        ar_ = ar.assign(sh_ae=100 * ar.total / ar.total.sum(), sh_pop=100 * ar.population / ar.population.sum())
        pull = [0.07 if r == region else 0 for r in ar_.region]
        hov_r = [f"<b>{r.region}</b><br>{i0(r.total)} auto-écoles ({p1(r.sh_ae, 0)} du pays)<br>dont {i0(r.agreees)} agréées · {i0(r.non_agr)} non agréées<br>Population : {i0(r.population)} ({p1(r.sh_pop, 0)} du pays)" for r in ar_.itertuples()]

        def _pie(x0, x1, labels, values, colors, hover, legend, pull=None, centre=""):
            return go.Pie(title=dict(text=centre, position="middle center", font=dict(size=10.5, color="#10335c")), labels=labels, values=values, hole=0.55, sort=False, direction="clockwise", domain=dict(x=[x0, x1], y=[0, 1]), pull=pull, marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
                          texttemplate="%{percent:.0%}", textposition="inside", insidetextorientation="horizontal", textfont=dict(size=11, color="#ffffff"), hovertext=hover, hoverinfo="text", showlegend=legend)

        fig = go.Figure()
        if split:
            agr_n, non_n = int(ar.agreees.sum()), int(ar.non_agr.sum())
            fig.add_trace(_pie(0.0, 0.47, ["Agréées", "Non agréées"], [agr_n, non_n], [C_AGR, C_NON], [f"<b>Agréées</b><br>{i0(agr_n)} auto-écoles ({p1(100 * agr_n / (agr_n + non_n), 0)})", f"<b>Non agréées</b><br>{i0(non_n)} auto-écoles ({p1(100 * non_n / (agr_n + non_n), 0)})"], True,
                              centre=f"<b>{p1(100 * agr_n / (agr_n + non_n), 0)}</b><br>agréées"))
            fig.add_trace(_pie(0.53, 1.0, list(ar_.region), list(ar_.total), [CR[r] for r in ar_.region], hov_r, True, pull, centre=f"<b>{i0(ar.total.sum())}</b><br>auto-écoles"))
        else:
            fig.add_trace(_pie(0.0, 0.47, list(ar_.region), list(ar_.total), [CR[r] for r in ar_.region], hov_r, True, pull, centre=f"<b>{i0(ar.total.sum())}</b><br>auto-écoles"))
            fig.add_trace(_pie(0.53, 1.0, list(ar_.region), list(ar_.population), [CR[r] for r in ar_.region], hov_r, False, pull, centre=f"<b>{i0(ar.population.sum())}</b><br>habitants"))
        charts.layout(fig, H_2 - 59 - 6, t=48, b=2, l=2, r=2, uniformtext=dict(minsize=9, mode="hide"))
        charts.show(fig, "ae_part_ch")
with c8:
    with panel("ae_prefecture", f"Auto-écoles par préfecture — {region or 'toutes les régions'}", "fa-map", "ae_prefecture", height=H_R):
        fig = go.Figure()
        vpa, vpn, vpt = _vals(pa)
        hp = [_hov_ae(r) for r in pa.itertuples()]
        op = [1.0 if (not pref_sel or p == pref_sel) else 0.45 for p in pa.prefecture]
        if split:
            fig.add_trace(go.Bar(y=pa.prefecture, x=vpa, orientation="h", name="Agréées", customdata=pa.prefecture, marker=dict(color=C_AGR, opacity=op), hovertext=hp, hoverinfo="text"))
            fig.add_trace(go.Bar(y=pa.prefecture, x=vpn, orientation="h", name="Non agréées", customdata=pa.prefecture, marker=dict(color=C_NON, opacity=op), hovertext=hp, hoverinfo="text"))
        else:
            fig.add_trace(go.Bar(y=pa.prefecture, x=vpt, orientation="h", name="Total", customdata=pa.prefecture, marker=dict(color=C_TOT, opacity=op), hovertext=hp, hoverinfo="text"))
        for p_, v_ in zip(pa.prefecture, vpt):
            fig.add_annotation(y=p_, x=float(v_), text=f" {fv(v_)}", showarrow=False, xanchor="left", font=dict(size=10.5, color="#4a6572"))
        charts.layout(fig, h_ae, legend=split, t=30, barmode="stack", r=92); fig.update_layout(legend_traceorder="normal")
        fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(size=10.5), dtick=1, categoryorder="array", categoryarray=list(pa.prefecture))
        fig.update_xaxes(title_text=("Auto-écoles / 100 000 hab." if per100k else "Auto-écoles"), title_font=dict(size=10.5), range=[0, float(max(vpt.max(), 1e-9)) * 1.12])
        for rg, blk in pa.groupby("region", sort=False):
            i0_, i1_ = blk.index.min(), blk.index.max()
            if i0_ > 0:
                fig.add_shape(type="line", xref="paper", x0=0, x1=1, yref="y", y0=i0_ - 0.5, y1=i0_ - 0.5, line=dict(color="#10335c", width=1.2))
            fig.add_annotation(xref="paper", x=1.0, xanchor="left", xshift=8, yref="y", y=(i0_ + i1_) / 2, text=f"<b>{rg}</b>", showarrow=False, font=dict(size=10.5, color="#10335c"))
        sel3 = charts.show(fig, "ae_pref_ch", select=True)
        v3 = charts.clicked_value(sel3)
        if v3 and v3 != pref_sel and v3 in set(df.prefecture):
            set_territory(v3); st.rerun()
        st.markdown(f'<div class="note"><b>Sans auto-école recensée ({len(sans)}) :</b> {", ".join(sans) if sans else "aucune"}.</div>', unsafe_allow_html=True)

# Tableau : version agrégée (régions) et version détaillée (préfectures), avec export
TAB = {"region": "Région", "prefecture": "Préfecture", "population": "Population", "agreees": "Agréées", "antenne": "dont antennes", "non_agr": "Non agréées", "total": "Total",
       "part_agreees": "Part agréées (%)", "hab_par_ae": "Hab. / auto-école", "ae_100k": "Auto-écoles / 100 000 hab."}
nat = pd.DataFrame([{"region": "Total national", "population": ar.population.sum(), "agreees": ar.agreees.sum(), "antenne": ar.antenne.sum(), "non_agr": ar.non_agr.sum(), "total": ar.total.sum(),
                     "part_agreees": 100 * ar.agreees.sum() / ar.total.sum(), "hab_par_ae": ar.population.sum() / ar.total.sum(), "ae_100k": 1e5 * ar.total.sum() / ar.population.sum()}])
t_reg = pd.concat([ar, nat], ignore_index=True)[[c for c in TAB if c != "prefecture"]].rename(columns=TAB)
t_pref = ap_v.assign(_r=ap_v.region.map({r: i for i, r in enumerate(L.ORDRE_REGIONS)})).sort_values(["_r", "total", "prefecture"], ascending=[True, False, True])[list(TAB)].rename(columns=TAB)
CC = {"Population": st.column_config.NumberColumn(format="localized"), "Agréées": st.column_config.NumberColumn(format="%d"), "dont antennes": st.column_config.NumberColumn(format="%d"),
      "Non agréées": st.column_config.NumberColumn(format="%d"), "Total": st.column_config.NumberColumn(format="%d"), "Part agréées (%)": st.column_config.NumberColumn(format="%.1f"),
      "Hab. / auto-école": st.column_config.NumberColumn(format="localized"), "Auto-écoles / 100 000 hab.": st.column_config.NumberColumn(format="%.2f")}
with panel("ae_tableau", "Répartition détaillée — agrégée par région, non agrégée par préfecture", "fa-database", "ae_tableau"):
    tab_r, tab_p = st.tabs(["Par région (agrégé)", f"Par préfecture (non agrégé){' — ' + region if region else ''}"])
    with tab_r:
        st.dataframe(t_reg, hide_index=True, width="stretch", height=285, column_config=CC)
        st.download_button("Exporter en CSV", t_reg.to_csv(index=False).encode("utf-8"), "auto_ecoles_par_region.csv", "text/csv", key="dl_ae_region")
    with tab_p:
        st.dataframe(t_pref, hide_index=True, width="stretch", height=285, column_config=CC)
        st.download_button("Exporter en CSV", t_pref.to_csv(index=False).encode("utf-8"), "auto_ecoles_par_prefecture.csv", "text/csv", key="dl_ae_pref")

# ---- Tableau de données et export (conservés sous les graphiques) ---------------------------------
with st.expander("Tableau région → préfecture (indicateurs et export)"):
    show = df.sort_values(["region", "prefecture"])[["region", "prefecture", "population", "km", "km_10k", "part_non_revetue", "ae_toutes", "ae_agreees", "hab_par_ae", "score", "rang"]]
    show = show if not region else show[show.region == region]
    st.dataframe(show.rename(columns={"region": "Région", "prefecture": "Préfecture", "population": "Population", "km": "Routes (km)", "km_10k": "km / 10 000 hab.", "part_non_revetue": "Part non revêtue",
                                      "ae_toutes": "Auto-écoles", "ae_agreees": "Agréées", "hab_par_ae": "Hab. / auto-école", "score": "Score", "rang": "Rang"}),
                 hide_index=True, width="stretch", height=300)
    st.download_button("Exporter en CSV", show.to_csv(index=False).encode("utf-8"), "territoires_carte.csv", "text/csv", key="dl_carte")
flush_panel_css()
