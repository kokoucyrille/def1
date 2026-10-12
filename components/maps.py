"""Cartes Plotly SANS dépendance réseau (maplibre, style « white-bg » : aucune tuile, aucune requête externe) :
choroplèthe de préfectures, réseau routier (une trace par type), auto-écoles (une trace par statut)."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.charts import C_AE, C_TYPE, layout
from data import loader as L
from data.loader import fmt_dec as d1

TRANSPARENT = [[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]]


def _coords(geom):
    if geom["type"] == "Polygon":
        return [pt for ring in geom["coordinates"] for pt in ring]
    return [pt for poly in geom["coordinates"] for ring in poly for pt in ring]


@st.cache_data(show_spinner=False)
def bounds(region: str | None = None, pref: str | None = None) -> tuple[float, float, float, float]:
    pts = [pt for f in L.geojson("prefectures")["features"]
           if (not region or f["properties"]["region"] == region) and (not pref or f["properties"]["prefecture"] == pref) for pt in _coords(f["geometry"])]
    a = np.array(pts)
    return a[:, 0].min(), a[:, 0].max(), a[:, 1].min(), a[:, 1].max()


def view(region: str | None, pref: str | None, height: int, width: int = 640) -> dict:
    x0, x1, y0, y1 = bounds(region, pref)
    dx, dy = max(x1 - x0, 0.05) * 1.18, max(y1 - y0, 0.05) * 1.12
    zoom = min(math.log2(360 * width / (512 * dx)), math.log2(360 * height / (512 * dy)))
    return dict(style="white-bg", center=dict(lon=(x0 + x1) / 2, lat=(y0 + y1) / 2), zoom=zoom - 0.2)


def outline_region(fig: go.Figure, region: str | None) -> go.Figure:
    """Contour bleu épais de la région sélectionnée (sans effet si aucune région)."""
    if region:
        fig.add_trace(go.Choroplethmap(geojson=L.geojson("regions"), locations=[region], featureidkey="properties.region", z=[1], showscale=False,
                                       colorscale=TRANSPARENT, marker=dict(line=dict(color="#003f8c", width=3)), hoverinfo="skip"))
    return fig


def choropleth(df: pd.DataFrame, col: str, label: str, fmt, height: int, colorscale="YlGnBu", reverse: bool = False,
               selected: str | None = None, region: str | None = None, hover_extra: str = "", zmin=None, zmax=None,
               contour_cles: set | None = None, show_scale: bool = True, zoom_region: str | None = None, width: int = 640) -> go.Figure:
    """df : une ligne par préfecture (colonnes cle, prefecture, region + `col`). Les valeurs NaN restent sans teinte."""
    gj = L.geojson("prefectures")
    z = df[col].replace([np.inf, -np.inf], np.nan)
    suffix = f"<br>{hover_extra}" if hover_extra else ""
    text = [f"<b>{n}</b> · {r}<br>{label} : {fmt(v)}{suffix}" for n, r, v in zip(df["prefecture"], df["region"], df[col])]
    fig = go.Figure(go.Choroplethmap(geojson=gj, locations=df["cle"], featureidkey="properties.cle_rgph", z=z, customdata=df["prefecture"], text=text,
                                     hovertemplate="%{text}<extra></extra>", colorscale=colorscale, reversescale=reverse, zmin=zmin, zmax=zmax,
                                     marker=dict(line=dict(color="#ffffff", width=0.8), opacity=0.92), showscale=show_scale,
                                     colorbar=dict(thickness=10, len=0.5, x=0.01, xanchor="left", y=0.3, title=dict(text=label, font=dict(size=10.5)), tickfont=dict(size=10.5))))

    def outline(cles, color, width_):
        fig.add_trace(go.Choroplethmap(geojson=gj, locations=list(cles), featureidkey="properties.cle_rgph", z=[1] * len(cles), showscale=False,
                                       colorscale=TRANSPARENT, marker=dict(line=dict(color=color, width=width_)), hoverinfo="skip"))
    if contour_cles:
        outline(contour_cles, "#10335c", 2.4)
    if selected:
        outline(df.loc[df["prefecture"] == selected, "cle"], "#f20e36", 3.2)
    outline_region(fig, region)
    layout(fig, height, legend=False, t=0, b=0, l=0, r=0, dragmode="pan", hoverdistance=4)
    fig.update_layout(map=view(zoom_region, selected if zoom_region or selected else None, height, width) if (zoom_region or selected) else view(None, None, height, width))
    return fig


@st.cache_data(show_spinner=False)
def _route_lines(types: tuple, region: str | None, pref: str | None) -> dict:
    out: dict = {}
    for f in L.geojson("routes")["features"]:
        pr = f["properties"]
        if pr["route_type"] not in types or (region and pr["region"] != region) or (pref and pr["prefecture"] != pref):
            continue
        g = f["geometry"]
        lines = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
        d = out.setdefault(pr["route_type"], ([], [], [], []))
        for ln in lines:
            d[0].extend([c[0] for c in ln] + [None]); d[1].extend([c[1] for c in ln] + [None])
            d[2].extend([f'<b>{pr["route_nom"]}</b> · {pr["prefecture"]}, {pr["region"]}<br>Linéaire : {d1(pr["km"], 1)} km'] * len(ln) + [None])
        d[3].extend([pr["prefecture"]] * len(ln) + [None])
    return out


def add_roads(fig: go.Figure, types: list[str], region: str | None, pref: str | None) -> go.Figure:
    for t, (lon, lat, txt, pf) in _route_lines(tuple(types), region, pref).items():
        fig.add_trace(go.Scattermap(lon=lon, lat=lat, mode="lines+markers", name=t, marker=dict(size=9, opacity=0), line=dict(width=2.2 if "nationale" in t else 1.4, color=C_TYPE[t]),
                                    text=txt, customdata=pf, hovertemplate="%{text}<br>" + t + "<extra></extra>"))
    return fig


def add_ae(fig: go.Figure, ae: pd.DataFrame) -> go.Figure:
    for stt, d in ae.groupby("statut"):
        fig.add_trace(go.Scattermap(lon=d["lon"], lat=d["lat"], mode="markers", name=f"Auto-école · {stt}", marker=dict(size=9, color=C_AE.get(stt, "#868e96")),
                                    text=[f"<b>{r.nom_etablissement}</b> · {r.prefecture}, {r.region}<br>Statut : {r.statut} · auto-école recensée" for r in d.itertuples()],
                                    customdata=d["prefecture"], hovertemplate="%{text}<extra></extra>"))
    return fig


def fond_prefectures(fig: go.Figure) -> go.Figure:
    """Fond neutre : contours des 39 préfectures (aucune requête réseau)."""
    gj = L.geojson("prefectures")
    cles = [f["properties"]["cle_rgph"] for f in gj["features"]]
    fig.add_trace(go.Choroplethmap(geojson=gj, locations=cles, featureidkey="properties.cle_rgph", z=[0] * len(cles), showscale=False,
                                   colorscale=[[0, "#eef3f5"], [1, "#eef3f5"]], marker=dict(line=dict(color="#c4d2d9", width=0.7), opacity=1), hoverinfo="skip"))
    return fig


def add_troncons(fig: go.Figure, tr: pd.DataFrame) -> int:
    """Trace les tronçons de l'état du réseau 2020 qui ont un tracé dans les routes classées, colorés par état dominant (couleurs d'état fixes).
    `tr` : colonnes cle_troncon, troncon, TOTAL, BON, MOYEN, MAUVAIS, TRAVAUX, dominant. Renvoie le nombre de tronçons tracés."""
    info = {r.cle_troncon: r for r in tr.itertuples()}
    out: dict = {}
    drawn = set()
    for f in L.geojson("routes")["features"]:
        r = info.get(f["properties"].get("cle_route"))
        if r is None:
            continue
        drawn.add(r.cle_troncon)
        g = f["geometry"]
        lines = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
        d = out.setdefault(r.dominant, ([], [], []))
        pref = f["properties"].get("prefecture", "territoire n.d.")
        region = f["properties"].get("region", "région n.d.")
        txt = (f"<b>{r.troncon}</b> · {pref}, {region}<br>État du réseau (2020) : total {d1(r.TOTAL, 1)} km<br>"
               f"Bon {d1(r.BON, 1)} km · moyen {d1(r.MOYEN, 1)} km<br>Mauvais {d1(r.MAUVAIS, 1)} km · travaux {d1(r.TRAVAUX, 1)} km")
        for ln in lines:
            d[0].extend([c[0] for c in ln] + [None]); d[1].extend([c[1] for c in ln] + [None]); d[2].extend([txt] * len(ln) + [None])
    for etat in ("MAUVAIS", "TRAVAUX", "MOYEN", "BON"):          # le mauvais état au-dessus
        if etat in out:
            lon, lat, txt = out[etat]
            fig.add_trace(go.Scattermap(lon=lon, lat=lat, mode="lines+markers", name=f"{L.ETAT_LIBELLES[etat]} (dominant)", text=txt, hovertemplate="%{text}<extra></extra>",
                                        line=dict(width=4, color=L.ETAT_COULEURS[etat]), marker=dict(size=9, opacity=0)))
    return len(drawn)
