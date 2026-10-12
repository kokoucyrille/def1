"""Éléments d'interface partagés : titres de page, messages clés, panneaux et KPI avec infobulle ⓘ."""
from __future__ import annotations

import base64
import html
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

import streamlit as st

ASSETS = Path(__file__).resolve().parent.parent / "assets"
_PANEL_HEIGHTS: dict[str, int] = {}


@lru_cache(maxsize=1)
def flag_data_uri() -> str:
    raw = (ASSETS / "logo_togo.png").read_bytes()
    return "data:image/png;base64," + base64.b64encode(raw).decode()


def page_title(
    icon: str,
    title: str,
    subtitle: str,
    objectif: str | None = None,
    section: bool = False,
    takeaway: str | None = None,
) -> None:
    """Titre de page (h1) ; `section=True` : titre d'une seconde partie de la page (h2, avec un espace au-dessus)."""
    obj = f'<span class="obj">{html.escape(objectif)}</span>' if objectif else ""
    tag, cls = ("h2", "page-title sec") if section else ("h1", "page-title")
    reading = ""
    territory_reminder = ""
    if not section:
        selected_pref = st.session_state.get("shared_pref")
        selected_region = st.session_state.get("shared_region")
        territory = selected_pref or selected_region or "toutes les régions"
        territory_reminder = f'<div class="territory-reminder">Territoire sélectionné : {html.escape(territory)}</div>'
        if takeaway and st.session_state.get("show_readings", True):
            reading = f'<div class="takeaway"><b>À retenir</b> · {html.escape(takeaway)}</div>'
    st.markdown(f'<div class="{cls}"><div class="pi"><i class="fa-solid {icon}"></i></div>'
                f'<div><{tag}>{title}</{tag}><p>{subtitle}</p>{obj}{territory_reminder}{reading}</div></div>', unsafe_allow_html=True)


def banner(text: str, kind: str = "warn") -> None:
    st.markdown(f'<div class="banner {"info" if kind == "info" else ""}"><i class="fa-solid fa-circle-info"></i><span>{text}</span></div>',
                unsafe_allow_html=True)


@contextmanager
def panel(key: str, title: str, icon: str, doc: str, height: int | None = None):
    """Panneau à titre (sans badge ni infobulle) ; `height` aligne les panneaux d'une rangée."""
    if height:
        _PANEL_HEIGHTS[key] = height
    with st.container(key=f"panel_{key}"):
        st.markdown(f'<div class="panel-title"><i class="fa-solid {icon}"></i><span>{title}</span></div>',
                    unsafe_allow_html=True)
        yield


def flush_panel_css() -> None:
    """Hauteurs minimales alignées par rangée ; réserve +24 px sous 1500 px."""
    if _PANEL_HEIGHTS:
        base = "".join(f".st-key-panel_{k}{{min-height:{h}px !important;height:auto !important;flex:0 0 auto !important;}}" for k, h in _PANEL_HEIGHTS.items())
        narrow = "".join(f".st-key-panel_{k}{{min-height:{h + 24}px !important;}}" for k, h in _PANEL_HEIGHTS.items())
        st.markdown(f"<style>{base}@media (max-width:1500px){{{narrow}}}</style>", unsafe_allow_html=True)
        _PANEL_HEIGHTS.clear()
