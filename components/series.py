"""Séries annuelles partagées par les pages Immatriculations et Permis : volumes / parts (empilés) ou base 100 (courbes)."""
from __future__ import annotations

import math

import pandas as pd
import plotly.graph_objects as go

from components import charts
from data.loader import fmt_dec as d1, fmt_int as i0, fmt_pct as p1, fmt_signed_pct as sp


def stacked_series(df: pd.DataFrame, cols: list[str], colors: dict, key: str, unit: str, height: int, mode: str, base: int, bars: bool = False) -> None:
    """Volumes / Parts (empilés) ou Base 100 (courbes) ; `bars=True` : barres (une année manquante reste vide, jamais interpolée)."""
    fig = go.Figure()
    d = df[cols]
    totals = d.sum(axis=1, min_count=1)

    def fmt_variation(value):
        return sp(value, 1) if pd.notna(value) and math.isfinite(float(value)) else "n.d."

    for c in cols:
        y = d[c]
        variation = y.pct_change(fill_method=None) * 100
        if mode == "Base 100":
            b = d[c].loc[base] if base in d.index else d[c].dropna().iloc[0]
            indexed = 100 * y / b
            custom = [
                (d1(v, 0), i0(raw), fmt_variation(delta))
                for v, raw, delta in zip(indexed, y, variation)
            ]
            fig.add_trace(go.Scatter(x=d.index, y=indexed, name=c, mode="lines+markers", connectgaps=False, line=dict(color=colors[c], width=2.4), marker=dict(size=4),
                                     customdata=custom, hovertemplate=f"{c} · %{{x}} : indice <b>%{{customdata[0]}}</b> (base {base} = 100)<br>Valeur : %{{customdata[1]}} {unit}<br>Variation annuelle : %{{customdata[2]}}<br>Formule : valeur / valeur de base × 100<extra></extra>"))
        elif bars:
            custom = [
                (i0(v), p1(100 * v / totals.loc[year]) if pd.notna(v) and totals.loc[year] else "n.d.",
                 fmt_variation(variation.loc[year]))
                for year, v in y.items()
            ]
            detail = (
                "Part du total sélectionné : %{customdata[1]}<br>Variation annuelle : %{customdata[2]}<br>Formule : catégorie / total des catégories sélectionnées × 100"
                if mode == "Parts" else "Variation vs période précédente : %{customdata[2]}"
            )
            fig.add_trace(go.Bar(x=d.index, y=y, name=c, marker_color=colors[c], customdata=custom,
                                 hovertemplate=f"{c} · %{{x}} : <b>%{{customdata[0]}}</b> {unit}<br>{detail}<extra></extra>"))
        else:
            custom = [
                (i0(v), p1(100 * v / totals.loc[year]) if pd.notna(v) and totals.loc[year] else "n.d.",
                 fmt_variation(variation.loc[year]))
                for year, v in y.items()
            ]
            detail = (
                "Part du total sélectionné : %{customdata[1]}<br>Variation annuelle : %{customdata[2]}<br>Formule : catégorie / total des catégories sélectionnées × 100"
                if mode == "Parts" else "Variation vs période précédente : %{customdata[2]}"
            )
            fig.add_trace(go.Scatter(x=d.index, y=y, name=c, mode="lines", stackgroup="s", groupnorm="percent" if mode == "Parts" else None, line=dict(width=0.6, color=colors[c]), fillcolor=colors[c],
                                     customdata=custom, hovertemplate=f"{c} · %{{x}} : <b>%{{customdata[0]}}</b> {unit}<br>{detail}<extra></extra>"))
    charts.layout(fig, height, t=34)
    if bars and mode != "Base 100":
        fig.update_layout(barmode="stack", barnorm="percent" if mode == "Parts" else None)
        if 2013 in d.index:
            fig.add_annotation(x=2013, y=0, yref="paper", text="2013 manquant", showarrow=False, yanchor="bottom", font=dict(size=10.5, color="#4a6572"), textangle=-90, xshift=0)
    fig.update_yaxes(title_text={"Volumes": unit, "Parts": "% du total", "Base 100": f"Indice ({base} = 100)"}[mode], title_font=dict(size=11))
    charts.show(fig, key)
