"""Cartes KPI : icône ronde + titre + valeur (rien dessous), sans infobulle."""
from __future__ import annotations

import streamlit as st

from components.styles import THEME

VARIANTS = {
    "green": (THEME["kpi_green"], THEME["green"], THEME["green_dark"]),
    "yellow": (THEME["kpi_yellow"], THEME["gold"], "#a36f00"),
    "gray": (THEME["kpi_gray"], "#3d3d3d", "#3d3d3d"),
    "red": (THEME["kpi_pink"], THEME["red"], THEME["red"]),
    "blue": (THEME["kpi_blue"], "#1488ee", "#0b5cc7"),
    "purple": (THEME["kpi_purple"], "#8b3fe0", "#5b21b6"),
}


def create_kpi_card(title: str, value: str, icon: str, variant: str, doc: str | None = None) -> str:
    bg, icon_bg, val_color = VARIANTS[variant]
    return (f'<div class="kpi" style="background:{bg}">'
            f'<div class="kpi__icon" style="background:{icon_bg};color:#fff"><i class="fa-solid {icon}"></i></div>'
            f'<div class="kpi__body"><div class="kpi__title">{title}</div>'
            f'<div class="kpi__value" style="color:{val_color}">{value}</div></div></div>')


def create_kpi_row(cards: list[dict]) -> None:
    """cards : {title, value, icon, variant} (la clé « doc » éventuelle est ignorée)."""
    with st.container(key="kpi_row"):
        for col, c in zip(st.columns(len(cards), gap="small"), cards):
            col.markdown(create_kpi_card(c["title"], c["value"], c["icon"], c.get("variant", "green")), unsafe_allow_html=True)
