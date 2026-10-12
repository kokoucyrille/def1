"""Helpers Plotly communs : palette, mise en page, affichage (avec ou sans sélection par clic)."""
from __future__ import annotations

import math
from numbers import Real

import plotly.graph_objects as go
import streamlit as st

from components.styles import FONT, THEME

GRID = "#e3edf0"
AXIS_TXT = "#0a4a9a"
TICK = "#3a5566"          # graduations et titres d'axes : contraste ≥ 7:1 sur blanc
C_VEH = {"Deux-roues": "#e8590c", "Voitures": "#1488ee", "Camionnettes": "#7b61c9", "Poids lourds": "#0d8a7a", "Autocars/Autobus": "#8a99a8"}
C_PERMIS = {"Moto (A)": "#e8590c", "Voiture légère (B)": "#1488ee", "Poids lourd (C)": "#0d8a7a", "Transport en commun (D)": "#8a99a8",
            "Semi-remorque (E)": "#5b21b6", "Voiture spéciale (F)": "#b08968"}
C_SEC = {"accidents": "#1488ee", "blesses": "#e8590c", "morts": "#b3122d"}
C_TYPE = {"Route nationale revêtue": "#10335c", "Route nationale non revêtue": "#a0522d", "Voirie urbaine": "#7b61c9", "Piste rurale": "#0d8a7a"}
C_AE = {"Agréée": "#e8590c", "Agréée (antenne)": "#f59f00", "Non agréée": "#868e96"}


def _safe_customdata(value):
    if value is None:
        return "n.d."
    if hasattr(value, "tolist"):
        return _safe_customdata(value.tolist())
    if isinstance(value, (list, tuple)):
        return [_safe_customdata(item) for item in value]
    if isinstance(value, Real) and not math.isfinite(float(value)):
        return "n.d."
    return value


def prepare_figure(fig: go.Figure) -> go.Figure:
    """Keep existing hover details, supply a concise fallback, and make missing custom data explicit."""
    for trace in fig.data:
        if trace.customdata is not None:
            trace.customdata = _safe_customdata(trace.customdata)
        if trace.hovertemplate:
            continue
        if trace.hovertext is not None:
            if trace.text is None:
                trace.text = trace.hovertext
            trace.hovertemplate = "%{text}<extra></extra>"
        elif trace.type == "pie":
            trace.hovertemplate = "%{label}<br>Valeur : %{value}<extra></extra>"
        elif trace.type == "heatmap":
            trace.hovertemplate = "%{y}<br>%{x} : %{z}<extra></extra>"
        elif trace.type in {"choroplethmap", "scattermap"}:
            trace.hovertemplate = "%{text}<extra></extra>" if trace.text is not None else "%{location}<extra></extra>"
        else:
            trace.hovertemplate = "%{x}<br>Valeur : %{y}<extra></extra>"
    return fig


def show(fig: go.Figure, key: str, select: bool = False):
    """Affiche une figure sans barre d'outils, à la largeur du conteneur ; avec select=True, renvoie la sélection (clic)."""
    prepare_figure(fig)
    cfg = {"displayModeBar": False, "responsive": True}
    if select:
        return st.plotly_chart(fig, width="stretch", key=key, config=cfg, on_select="rerun", selection_mode="points")
    st.plotly_chart(fig, width="stretch", key=key, config=cfg)
    return None


def layout(fig: go.Figure, height: int, legend: bool = True, t: int = 6, b: int = 4, l: int = 4, r: int = 8, **kw) -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=l, r=r, t=t, b=b), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family=FONT, size=12.5, color=AXIS_TXT), showlegend=legend,
                      legend=dict(orientation="h", x=0, y=1.0, yanchor="bottom", font=dict(size=11.5), itemclick="toggle", itemdoubleclick="toggleothers"),
                      hoverlabel=dict(font=dict(family=FONT, size=12.5)), **kw)
    fig.update_xaxes(showgrid=False, tickfont=dict(size=11.5, color=TICK), title_font=dict(color=TICK), zeroline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, tickfont=dict(size=11.5, color=TICK), title_font=dict(color=TICK), separatethousands=True)
    return fig


def empty_fig(height: int, msg: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=msg, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False, font=dict(size=14, color="#4a6572"))
    fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
    return layout(fig, height, legend=False)


def clicked_value(sel, field: str = "customdata"):
    """Première valeur cliquée (customdata) d'une sélection Plotly, ou None."""
    try:
        pts = sel["selection"]["points"] if sel is not None else []
    except (KeyError, TypeError):
        return None
    for p in pts or []:
        v = p.get(field)
        if v is None:
            continue
        return v[0] if isinstance(v, (list, tuple)) else v
    return None
