"""Option « Fond OpenStreetMap » (Folium). Hors connexion, les tuiles ne se chargent pas mais polygones, réseau et points restent affichés."""
from __future__ import annotations

import folium
import numpy as np
import streamlit as st
import streamlit.components.v1 as components

from components.charts import C_AE, C_TYPE
from data import loader as L
from data.loader import fmt_dec as d1


def _color(t: float) -> str:
    a, b = (255, 255, 204), (12, 44, 132)           # jaune clair → bleu foncé
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def render(df, col, unit, fmt, f, region, pref, height: int) -> None:
    z = df[col].replace([np.inf, -np.inf], np.nan)
    lo, hi = float(z.min()), float(z.max())
    vals = {c: (None if not np.isfinite(v) else v) for c, v in zip(df["cle"], z)}
    names = dict(zip(df["cle"], df["prefecture"]))
    m = folium.Map(location=[8.6, 0.98], zoom_start=7, tiles="OpenStreetMap", control_scale=True)

    def style(feat):
        v = vals.get(feat["properties"]["cle_rgph"])
        return {"fillColor": "#e9eff1" if v is None else _color((v - lo) / (hi - lo or 1)), "color": "#ffffff", "weight": 1, "fillOpacity": 0.7}

    folium.GeoJson(L.geojson("prefectures"), name="Préfectures", style_function=style,
                   tooltip=folium.GeoJsonTooltip(fields=["prefecture", "region"], aliases=["Préfecture", "Région"])).add_to(m)
    for feat in L.geojson("prefectures")["features"]:
        c = feat["properties"]["cle_rgph"]
        v = vals.get(c)
        folium.GeoJson(feat, style_function=lambda _: {"fillOpacity": 0, "weight": 0},
                       tooltip=f"{names[c]} · {feat['properties']['region']} — {unit} : {fmt(v) if v is not None else 'n.d.'}").add_to(m)
    if "Réseau routier" in f["couches"]:
        for feat in L.geojson("routes")["features"]:
            pr = feat["properties"]
            if pr["route_type"] in f["types"] and (not region or pr["region"] == region) and (not pref or pr["prefecture"] == pref):
                folium.GeoJson(feat, style_function=lambda _, t=pr["route_type"]: {"color": C_TYPE[t], "weight": 2},
                               tooltip=f'{pr["route_nom"]} · {pr["prefecture"]}, {pr["region"]} · {d1(pr["km"], 1)} km').add_to(m)
    if "Auto-écoles" in f["couches"]:
        ae = L.table("auto_ecoles")
        ae = ae if f["statut"] == "Toutes" else ae[ae["agreee"] == (f["statut"] == "Agréées")]
        ae = ae if not region else ae[ae.region == region]
        ae = ae if not pref else ae[ae.prefecture == pref]
        for r in ae.itertuples():
            folium.CircleMarker([r.lat, r.lon], radius=4, color="#fff", weight=1, fill=True, fill_color=C_AE.get(r.statut, "#868e96"), fill_opacity=0.95,
                                tooltip=f"{r.nom_etablissement} · {r.prefecture}, {r.region} · {r.statut}").add_to(m)
    m.get_root().html.add_child(folium.Element(
        '<div id="osm-offline" style="display:none;font:14px sans-serif;color:#6b4700;background:#fff4cc;border:1px solid #f0cf6b;border-radius:8px;padding:12px;margin:12px">'
        "Carte OpenStreetMap indisponible hors connexion (la bibliothèque Leaflet et les tuiles se chargent depuis Internet). "
        "Décochez « Fond OpenStreetMap » dans les filtres pour revenir à la carte autonome, qui fonctionne sans réseau.</div>"
        "<script>window.addEventListener('load', function () { if (typeof L === 'undefined') { document.getElementById('osm-offline').style.display = 'block'; } });</script>"))
    page = m.get_root().render()                     # HTML produit localement à partir de données de confiance
    if hasattr(st, "iframe"):
        st.iframe(page, height=height)
    else:                                            # Streamlit plus ancien
        components.html(page, height=height)
    st.caption("Fond OpenStreetMap : nécessite Internet ; hors connexion, décochez l'option pour revenir à la carte autonome. Cartes OSM : sélection par clic non disponible.")
