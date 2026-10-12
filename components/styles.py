"""
Charte graphique et CSS global du dashboard.

Dimensions relevées sur les maquettes (résolution de référence 1670 x 942 px) :
  * header 68 px, barre de navigation 61 px -> bandeau supérieur fixe de 129 px
  * sidebar 290 px, marges du contenu 20 px
  * cartes KPI : ~122 px de haut, icône ronde 64 px, valeur 32 px
  * panneaux : rayon 10 px, bordure 1 px #ddedef, ombre très légère
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import streamlit as st

# --------------------------------------------------------------------------------------
# Palette (valeurs échantillonnées sur les maquettes)
# --------------------------------------------------------------------------------------
THEME = {
    "green": "#016b4b",        # vert institutionnel (navbar, boutons, séries principales)
    "green_dark": "#004f31",
    "green_mid": "#59b78d",
    "green_light": "#a9dcc1",
    "gold": "#fdcf00",         # accent : menu actif, boutons d'action
    "gold_dark": "#df9401",
    "blue": "#003f8c",         # titres
    "blue_link": "#0a5ec0",    # libellés, valeurs de sélecteurs
    "red": "#f20e36",
    "gray": "#a2b8cc",
    "text": "#1e3a4c",
    "bg": "#f7fcfe",
    "sidebar_bg": "#f5fbfb",
    "border": "#ddedef",
    "kpi_green": "#eaf7f4", "kpi_yellow": "#fef9e6", "kpi_gray": "#f2f3f5", "kpi_pink": "#fdebef",
    "kpi_blue": "#edf7fe", "kpi_purple": "#f2eefd",
}
OP_COLORS = {"Togocom": "#016b4b", "Moov": "#fec902", "Yas": "#f20e36", "Autres": "#a2b8cc"}
FONT = "'Nunito Sans', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"

TOPBAR_H = 129     # header (68) + navbar (61)
SIDEBAR_W = 290

_CSS = """

:root { --green:%green%; --gold:%gold%; --blue:%blue%; --blue-link:%blue_link%; --border:%border%; --topbar:%TOPBAR%px; --sidebar:%SIDEBAR%px; }

/* ---------- Base ---------- */
html, body, .stApp, [class*="st-"] , button, input, select, textarea { font-family: %FONT%; }
.stApp { background: %bg%; color: %text%; }
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], footer,
[data-testid="stSidebarCollapseButton"], [data-testid="stSidebarCollapsedControl"], [data-testid="stSidebarHeader"] { display: none !important; }
[data-testid="stMain"] { margin-left: var(--sidebar); width: calc(100% - var(--sidebar)) !important; min-width: 0; }
[data-testid="stMainBlockContainer"], .stMainBlockContainer {
    max-width: 100% !important; padding: calc(var(--topbar) - 14px) 20px 24px 20px !important; }
[data-testid="stMainBlockContainer"] > div > [data-testid="stVerticalBlock"] { gap: 14px; }
h1, h2, h3 { font-family: %FONT%; }
.i-fa { font-style: normal; }

/* ---------- Bandeau supérieur fixe (header + navbar) ---------- */
.st-key-topbar { position: fixed; top: 0; left: 0; right: 0; z-index: 1000; background: %bg%; padding: 0 !important; gap: 0 !important; height: var(--topbar); box-sizing: border-box; }
.st-key-topbar > div { gap: 0 !important; }
.st-key-header { height: 68px !important; min-height: 68px; padding: 0 20px !important; box-sizing: border-box; display:flex; align-items: center; }
.st-key-header [data-testid="stHorizontalBlock"] { align-items: center; height: 68px; gap: 10px; width: 100%; }
.st-key-header .stButton, .st-key-header [data-testid="stButton"], .st-key-header .stElementContainer { width: 100% !important; }
.hdr { display: flex; align-items: center; gap: 16px; height: 68px; }
.hdr img { height: 48px; width: auto; border-radius: 3px; box-shadow: 0 1px 3px rgba(0,0,0,.18); }
.hdr .t1 { color: %green%; font-weight: 800; font-size: 23px; line-height: 26px; letter-spacing: .1px; }
.hdr .t2 { color: %green%; font-weight: 600; font-size: 12.5px; line-height: 16px; letter-spacing: .3px; }

/* titre du challenge (à la place de l'ancien sélecteur de période) */
.hdr-challenge { color: %green%; font-weight: 800; font-size: 15px; line-height: 20px; text-align: right; letter-spacing: .2px; }

/* boutons FR / EN */
.st-key-header [data-testid="stDateInput"] { width: 100%; }
.st-key-header [data-testid="stDateInput"] > div > div { background: #fff; border: 1.5px solid #c9e2ea; border-radius: 10px; min-height: 44px; }
.st-key-header [data-testid="stDateInput"] input { color: %blue_link%; font-weight: 600; font-size: 14px; text-align: center; }
.st-key-header .stButton button { height: 44px; min-height: 44px; border-radius: 10px; font-weight: 700; font-size: 15px; width: 100%; padding: 0; }
.st-key-header .stButton button[kind="secondary"] { background: #fff; border: 1.5px solid #d6e8ee; color: %green%; }
.st-key-header .stButton button[kind="primary"] { background: %green%; border: 1.5px solid %green%; color: #fff; }

/* navbar */
.st-key-navbar { background: %green%; height: 61px !important; min-height: 61px; padding: 8px 12px 0 12px !important; box-sizing: border-box; display: flex; align-items: flex-start; }
.st-key-navbar [data-testid="stHorizontalBlock"] { gap: 6px; width: 100%; align-items: flex-start; flex-wrap: nowrap; }
.st-key-navbar [data-testid="stColumn"] { min-width: 0; }
.st-key-navbar .stButton button { height: 44px; min-height: 44px; width: 100%; border-radius: 8px; border: none; font-weight: 700; font-size: 15px;
    background: transparent; color: #fff; padding: 0 6px; box-shadow: none; justify-content: center; white-space: nowrap; }
.st-key-navbar .stButton button p { font-size: 15px; font-weight: 700; margin: 0; }
.st-key-navbar .stButton button:hover { background: rgba(255,255,255,.12); color: #fff; }
.st-key-navbar .stButton button[kind="primary"] { background: %gold%; color: %green_dark%; }
.st-key-navbar .stButton button[kind="primary"]:hover { background: %gold%; color: %green_dark%; }
.st-key-navbar .stButton button[kind="primary"] p { color: %blue%; }


/* icônes de la navbar et des boutons (Font Awesome, chargé en local) */
.st-key-nav_0 button p::before { --fa: "\\e473"; }
.st-key-nav_1 button p::before { --fa: "\\f201"; }
.st-key-nav_2 button p::before { --fa: "\\f09d"; }
.st-key-nav_3 button p::before { --fa: "\\f0fa"; }
.st-key-nav_4 button p::before { --fa: "\\f625"; }
.st-key-nav_5 button p::before { --fa: "\\f279"; }
.st-key-nav_6 button p::before { --fa: "\\f601"; }
.st-key-nav_7 button p::before { --fa: "\\f1c0"; }
.st-key-navbar button p::before, section[data-testid="stSidebar"] .stButton button p::before {
    content: none; --unused: 1; font-family: "Font Awesome 7 Free"; font-weight: 900; margin-right: 10px; font-size: 18px; display: inline-block; vertical-align: -1px; }

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] { position: fixed !important; top: var(--topbar); bottom: 0; left: 0; width: var(--sidebar) !important; min-width: var(--sidebar) !important;
    max-width: var(--sidebar) !important; transform: none !important; background: %sidebar_bg%; border-right: 1px solid %border%; z-index: 900; }
section[data-testid="stSidebar"] > div { width: var(--sidebar) !important; }
[data-testid="stSidebarContent"] { overflow-y: auto; padding: 0 !important; }
[data-testid="stSidebarUserContent"] { padding: 14px 18px 90px 18px !important; }
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 4px; }
.f-title { display:flex; align-items:center; gap:10px; color:%blue%; font-weight:800; font-size:19px; margin: 2px 0 6px 0; }
.f-title i { color:%green%; font-size: 24px; width: 28px; text-align:center; }
.f-label { display:flex; align-items:center; gap:10px; color:%green_dark%; font-weight:800; font-size:15px; height: 20px; line-height: 20px; margin: 8px 0 16px 0; }   /* 16px compense la marge -1rem de Streamlit */
.f-label i { color:%green%; font-size:16px; width:28px; text-align:center; line-height: 20px; }
section[data-testid="stSidebar"] [data-baseweb="select"] > div, section[data-testid="stSidebar"] [data-testid="stDateInput"] > div > div {
    background: #fff; border: 1.5px solid #d3e8ee; border-radius: 10px; min-height: 40px; }
section[data-testid="stSidebar"] [data-baseweb="select"] div, section[data-testid="stSidebar"] [data-testid="stDateInput"] input { color: %blue_link%; font-weight: 600; font-size: 13.5px; }
section[data-testid="stSidebar"] span[data-baseweb="tag"] { background: %green%; border-radius: 6px; color: #fff; }
section[data-testid="stSidebar"] span[data-baseweb="tag"] span { color: #fff !important; }
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] { display: none; }
section[data-testid="stSidebar"] .stButton button { width: 100%; height: 44px; border-radius: 10px; font-weight: 800; font-size: 15px; }
section[data-testid="stSidebar"] .stButton button[kind="primary"] { background: %gold%; border: 1px solid %gold%; color: %blue%; }
section[data-testid="stSidebar"] .stButton button[kind="primary"] p { color: %blue%; font-weight: 800; }
section[data-testid="stSidebar"] .stButton button[kind="secondary"] { background: #fff; border: 1.5px solid #cfe5ea; color: %green%; }
section[data-testid="stSidebar"] .stButton button[kind="secondary"] p { color: %green%; }
.side-foot { position: fixed; bottom: 16px; left: 18px; width: calc(var(--sidebar) - 36px); border-top: 1px solid %border%; padding-top: 14px; display:flex; gap:12px; align-items:center; background: %sidebar_bg%; z-index: 5; }
.side-foot img { height: 30px; border-radius: 2px; box-shadow: 0 1px 2px rgba(0,0,0,.2); }
.side-foot b { color: %blue%; font-size: 14px; display:block; line-height:17px; }
.side-foot span { color: %blue_link%; font-size: 13px; }


/* ---------- Widgets de formulaire (Streamlit récent : react-aria ; anciennes versions : baseweb) ---------- */
section[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="group"],
section[data-testid="stSidebar"] [data-testid="stMultiSelect"] [role="group"],
section[data-testid="stSidebar"] [data-testid="stDateInputField"],
.st-key-header [data-testid="stDateInputField"] {
    background: #fff !important; border: 1.5px solid #d3e8ee !important; border-radius: 10px !important; min-height: 40px; box-shadow: none; }
.st-key-header [data-testid="stDateInputField"] { min-height: 44px; border-color: #c9e2ea !important; justify-content: center; }
section[data-testid="stSidebar"] [data-testid="stSelectbox"] input,
div[class*="st-key-ctl_"] [data-testid="stSelectbox"] input { color: %blue_link% !important; font-weight: 600; font-size: 13.5px; -webkit-text-fill-color: %blue_link%; }
section[data-testid="stSidebar"] [data-testid="stDateInputField"] *, .st-key-header [data-testid="stDateInputField"] * { color: %blue_link%; font-weight: 600; font-size: 13.5px; }
section[data-testid="stSidebar"] [data-testid="stSelectbox"] svg, section[data-testid="stSidebar"] [data-testid="stMultiSelect"] svg { color: %blue_link%; }
div[class*="st-key-ctl_"] [data-testid="stSelectbox"] [role="group"] { background:#fff !important; border: 1.5px solid #d3e8ee !important; border-radius: 8px !important; min-height: 38px; }
section[data-testid="stSidebar"] [data-testid="stMultiSelectTagsContainer"] > div[role="row"], section[data-testid="stSidebar"] [data-testid="stMultiSelectTagsContainer"] [data-testid="stTag"] { background: %green% !important; color:#fff !important; border-radius: 6px; }
section[data-testid="stSidebar"] [data-testid="stMultiSelectTagsContainer"] [data-testid="stTag"] * { color:#fff !important; }
[role="listbox"] [role="option"] { font-size: 13.5px; }


/* ---------- Ergonomie : focus clavier visible, états interactifs ---------- */
.stButton button:focus-visible, [data-testid="stDownloadButton"] button:focus-visible, [role="radiogroup"] button:focus-visible {
    outline: 3px solid %blue_link% !important; outline-offset: 2px; }
.st-key-navbar .stButton button:focus-visible { outline: 3px solid #ffffff !important; outline-offset: -4px; }
.st-key-navbar .stButton button[kind="primary"]:focus-visible { outline-color: %green_dark% !important; }
.st-key-navbar .stButton button, .st-key-header .stButton button { cursor: pointer; transition: background-color .15s ease; }
.st-key-navbar .stButton button[kind="secondary"]:hover { background: rgba(255,255,255,.16); }
section[data-testid="stSidebar"] .stButton button[kind="primary"]:hover { filter: brightness(.96); }

/* ---------- Titres de page ---------- */
.page-title { display:flex; align-items:center; gap:16px; margin: 0 0 18px 0; }
.page-title .pi { color:%green%; font-size: 38px; width: 52px; text-align:center; }
.page-title.sec { margin-top: 22px; }
.page-title h1, .page-title h2 { color:%blue%; font-size: 27px; font-weight: 800; margin:0; padding:0; line-height: 31px; }
.page-title p { color:%blue_link%; font-size: 14.5px; margin: 2px 0 0 0; }
.territory-reminder { color:#4a6572; font-size:12px; margin-top:3px; }
.takeaway { color:#4a6572; font-size:13px; line-height:18px; margin-top:4px; }
.takeaway b { color:%green_dark%; font-weight:800; }

/* ---------- Cartes KPI ---------- */
.st-key-kpi_row { margin-bottom: 12px; }   /* petit espace entre les KPI et les sections suivantes */
.kpi { display:flex; align-items:center; gap: 11px; height: 122px; border-radius: 10px; padding: 0 12px; border: 1px solid rgba(0,0,0,.05); }
.kpi__icon { flex: 0 0 56px; width:56px; height:56px; border-radius: 50%; display:flex; align-items:center; justify-content:center; color:#fff; font-size: 24px; }
.kpi__body { min-width: 0; flex: 1; }
.kpi__title { font-weight: 800; font-size: 12.5px; line-height: 16px; color:%green_dark%; }
.kpi__value { font-weight: 800; font-size: 27px; line-height: 36px; white-space: nowrap; }

/* ---------- Panneaux (cartes de graphiques) ---------- */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"] > .stElementContainer .panel-title),
.st-key-panelwrap { }
div[class*="st-key-panel_"] { background:#fff; border: 1px solid %border%; border-radius: 10px; box-shadow: 0 1px 3px rgba(11,70,90,.05); padding: 14px 16px 10px 16px; overflow: visible; }
div[class*="st-key-ctl_"] { background:#fff; border: 1px solid %border%; border-radius: 10px; padding: 8px 16px; min-height: 64px; justify-content: center; }
.panel-title { display:flex; align-items:center; gap: 10px; color:%blue%; font-weight: 800; font-size: 15px; line-height: 19px; margin-bottom: 4px; }
.panel-title i { color:%green%; font-size: 20px; width: 26px; text-align:center; }
.panel-title .dots { margin-left:auto; color:%blue_link%; letter-spacing: 1px; font-weight: 800; }
.legend-dot { display:inline-block; width:12px; height:12px; border-radius:50%; margin-right: 9px; vertical-align: middle; }
.leg-row { display:flex; align-items:center; justify-content:space-between; font-size: 16px; color:%blue_link%; margin: 12px 0; }
.leg-row b { font-weight: 600; color:%blue_link%; }
.leg-center { text-align:center; color:%blue_link%; font-size:13px; margin-top: -6px; }

/* ---------- Tableaux ---------- */
table.tbl { width:100%; border-collapse: collapse; font-size: 13.5px; color:%text%; }
table.tbl th { background: #e6f5f1; color:%green_dark%; font-weight: 700; padding: 8px 6px; font-size: 13px; border: 1px solid #cfe6e1; text-align:center; }
table.tbl th:first-child, table.tbl td:first-child { text-align: left; }
table.tbl td { padding: 6px 6px; font-size: 13px; border: 1px solid #d9ecee; text-align:center; color:%blue%; font-weight: 500; }
table.tbl td.up { color: #12a150; font-weight: 700; }
table.tbl tr:nth-child(even) td { background: #fbfefe; }

/* ---------- Top 5 (barres horizontales) ---------- */
.top5 { display:flex; flex-direction:column; gap: 8px; margin-top: 6px; }
.top5 .row { display:grid; grid-template-columns: 74px 1fr 76px; align-items:center; gap: 12px; font-size: 14.5px; color:%blue%; font-weight: 600; }
.top5 .track { background:#e9eff1; border-radius: 6px; height: 22px; overflow:hidden; }
.top5 .fill { height: 100%; border-radius: 6px; }
.top5 .val { text-align:right; font-weight: 600; color:%blue%; }

/* ---------- Indicateurs clés / qualité ---------- */
.ind-row { display:flex; align-items:center; gap: 14px; margin: 9px 0; }
.ind-ico { flex: 0 0 46px; width:46px; height:46px; border-radius:50%; background:#e3f3ee; color:%green%; display:flex; align-items:center; justify-content:center; font-size:22px; }
.ind-lab { font-size: 13px; color:%green_dark%; font-weight: 600; }
.ind-val { font-size: 23px; color:%green%; font-weight: 800; line-height: 28px; }
.ind-delta { margin-left:auto; color:#12a150; font-size: 13px; font-weight: 700; }
.q-grid { display:grid; grid-template-columns: repeat(4, 1fr); gap: 6px; text-align:center; }
.q-item { border-right: 1px solid #e3eef0; padding: 0 4px; }
.q-item:last-child { border-right: none; }
.q-ico { width:42px; height:42px; border-radius:50%; margin: 0 auto 6px auto; display:flex; align-items:center; justify-content:center; color:#fff; font-size:20px; }
.q-lab { font-size: 12px; color:%blue%; min-height: 32px; line-height: 15px; }
.ring { width: 74px; height: 74px; border-radius: 50%; margin: 4px auto 0 auto; display:flex; align-items:center; justify-content:center; font-weight: 800; font-size: 17px; }
.ring > span { width: 58px; height: 58px; background:#fff; border-radius:50%; display:flex; align-items:center; justify-content:center; }

/* ---------- Segmented / selects de contrôle ---------- */
div[class*="st-key-ctl_"] [data-baseweb="select"] > div { background:#fff; border: 1.5px solid #d3e8ee; border-radius: 8px; min-height: 38px; }
div[class*="st-key-ctl_"] [data-baseweb="select"] div { color: %blue_link%; font-weight: 600; font-size: 14px; }
div[class*="st-key-ctl_"] [data-testid="stWidgetLabel"] { display:none; }
div[class*="st-key-ctl_"] [role="radiogroup"] { gap: 6px; }
div[class*="st-key-ctl_"] [role="radiogroup"] button { border-radius: 8px !important; font-weight: 700; min-height: 34px; padding: 0 16px; background:#eaf7f4; border: 1px solid #cfe6e1; color: %green%; }
div[class*="st-key-ctl_"] [role="radiogroup"] button p { color: inherit; font-weight: 700; font-size: 14px; }
div[class*="st-key-ctl_"] [role="radiogroup"] button[aria-checked="true"] { background: %green% !important; border-color: %green% !important; color: #fff !important; }
.ctl-label { color:%blue%; font-weight: 800; font-size: 14px; line-height: 17px; white-space: nowrap; }

.st-key-dl_btn button { height: 40px; border-radius: 8px; background:#fff; border:1.5px solid #cfe5ea; color:%green%; width: 100%; }
.st-key-dl_btn button p::before { content: "\\f019"; font-family: "Font Awesome 7 Free"; font-weight: 900; font-size: 17px; }
.st-key-dl_btn button p { font-size: 0; }
.list-scroll { max-height: 410px; overflow-y: auto; }


/* ---------- Page « Recommandations » : cartes de priorité ---------- */
.reco-card { background:#fff; border:1px solid %border%; border-radius:10px; padding: 10px 16px 16px 16px; margin-bottom: 14px;   /* compense la marge -1rem de Streamlit */
    box-shadow: 0 1px 3px rgba(11,70,90,.05); }
.reco-head { display:flex; align-items:center; gap: 20px; min-height: 44px; }
.reco-ico { flex: 0 0 56px; width:56px; display:flex; align-items:center; justify-content:center; font-size: 38px; color:%green%; }
.reco-ico .box { width:44px; height:44px; border-radius:10px; background:#1488ee; color:#fff; font-size:23px; display:flex; align-items:center; justify-content:center; }
.reco-title { font-size: 18.5px; line-height: 24px; font-weight: 800; }
.reco-badge { margin-left:auto; flex: 0 0 auto; background:#fdecec; color:#d3202f; border:1px solid #f1a9ae; border-radius:6px; padding: 5px 12px; font-size: 12px; font-weight: 800; letter-spacing: .2px; }
.reco-rows { margin: 9px 0 0 0; display:flex; flex-direction:column; gap: 11px; }
.reco-row { box-sizing: border-box; display:flex; align-items:flex-start; gap: 14px; min-height: 42px; padding: 5px 16px 5px 14px; background:#f6fbfb; border:1px solid #dcebee; border-radius: 8px; }
.reco-row:hover { background:#eef8f6; border-color:#c5e1da; }
.reco-tag { flex: 0 0 32px; height: 30px; margin-top: 2px; border-radius: 8px; background:%green_dark%; color:#fff; font-size: 13px; font-weight: 800; display:flex; align-items:center; justify-content:center; }
.reco-text { flex: 1; min-width: 0; font-size: 13.5px; line-height: 19px; color:#2a4b57; }
.reco-text b { color:#0a5a45; font-weight: 800; font-size: 14px; }
.reco-chev { flex: 0 0 auto; color:#3c5968; font-size: 14px; }
@media (max-width: 1100px) {
  .reco-head { gap: 12px; } .reco-ico { flex-basis: 44px; width:44px; font-size: 30px; } .reco-ico .box { width:40px; height:40px; font-size:20px; }
  .reco-rows { margin-left: 0; } .reco-title { font-size: 16px; }
}


/* ---------- Infobulles ⓘ, badges, messages clés, lecture ---------- */
.tip { position: relative; display:inline-flex; align-items:center; justify-content:center; margin-left:auto; flex: 0 0 auto; cursor: help; outline: none; width: 26px; height: 26px; border-radius: 50%; }
.panel-title .tip i, .tip i { color: %blue_link%; font-size: 15px; width: auto; }
.tip:hover, .tip:focus-visible { background: #e3f0fb; }
.tip:focus-visible { outline: 2px solid %blue_link%; }
.tip::after { content: attr(data-tip); position: absolute; top: calc(100% + 6px); right: -4px; width: max-content; max-width: 340px; white-space: pre-line; text-align: left;
    background: #10335c; color: #fff; font-size: 12px; line-height: 15.5px; font-weight: 500; padding: 8px 11px; border-radius: 8px; box-shadow: 0 8px 24px rgba(0,0,0,.28);
    opacity: 0; visibility: hidden; transition: opacity .12s; z-index: 2147483000; pointer-events: none; }
.tip.up::after { top: auto; bottom: calc(100% + 6px); }
.tip:hover::after, .tip:focus::after, .tip:focus-visible::after { opacity: 1; visibility: visible; }
.kpi { position: relative; }
.panel-title .badge-ind, .badge-ind { display:inline-block; background:#fff4cc; color:#8a5a00; border:1px solid #f0cf6b; border-radius: 6px; padding: 1px 7px; font-size: 11px; font-weight: 800; letter-spacing:.2px; line-height: 16px; white-space: nowrap; }
.panel-title .badge-ind { margin-left: 4px; }
.page-title .obj { display:inline-block; margin-top: 4px; background:#eaf7f4; color:%green_dark%; border:1px solid #cfe6e1; border-radius: 6px; padding: 1px 8px; font-size: 12px; font-weight: 800; }
.msgbar { background:#fff; border:1px solid %border%; border-left: 5px solid %gold%; border-radius: 10px; padding: 10px 16px 8px 16px; margin: 0 0 14px 0; }
.msgbar .mh { color:%blue%; font-weight: 800; font-size: 13.5px; margin-bottom: 3px; }
.msgbar .mh i { color:%green%; margin-right: 8px; }
.msgbar p { margin: 0 0 4px 0; font-size: 13.5px; line-height: 19px; color:%text%; }
.lecture { font-size: 12px; line-height: 16px; color:#4a6572; margin-top: -2px; }
.lecture b { color:%green_dark%; }
.banner { display:flex; gap:10px; align-items:center; background:#fff4cc; border:1px solid #f0cf6b; color:#6b4700; border-radius: 10px; padding: 8px 14px; font-size: 13px; font-weight: 700; margin-bottom: 12px; }
.banner.info { background:#edf7fe; border-color:#bcdcf5; color:#0b4b86; }
.fiche { margin-bottom: 8px; display:grid; grid-template-columns: 1fr auto; gap: 4px 12px; font-size: 13px; color:%text%; }
.fiche div:nth-child(odd) { color:#4a6572; } .fiche div:nth-child(even) { font-weight: 800; color:%blue%; text-align:right; }
.fiche-h { color:%green_dark%; font-weight: 800; font-size: 15px; margin-bottom: 6px; }
.chip { display:inline-block; background:#f2f3f5; border:1px solid #dde3e8; border-radius: 12px; padding: 1px 9px; font-size: 12px; margin: 2px 4px 2px 0; }
.chip.z { background:#fdebef; border-color:#f1a9ae; color:#a3182c; font-weight: 700; }
.reco-line { display:grid; grid-template-columns: 112px 1fr; gap: 0 10px; font-size: 13px; line-height: 18px; padding: 1px 0; }
.reco-line .k { color:%green_dark%; font-weight: 800; }
.reco-text .rt { font-weight: 800; color:#0a5a45; font-size: 14.5px; display:block; margin-bottom: 3px; }
.note { font-size: 12px; color:#4a6572; margin-top: 4px; }
.st-key-dl_row button, [data-testid="stDownloadButton"] button { border-radius: 8px; border: 1.5px solid #cfe5ea; color: %green%; font-weight: 700; }
[data-testid="stExpander"] { background:#fff; border: 1px solid %border%; border-radius: 10px; }
[data-testid="stDataFrame"] { border: 1px solid %border%; border-radius: 8px; }
.stTabs [data-baseweb="tab"] { font-weight: 800; color: %blue%; }
[data-testid^="stSliderTickBar"], [data-testid^="stSliderTickBar"] * { color: #1e3a4c !important; opacity: 1 !important; }
.f-label .tip { width: 22px; height: 22px; }
.f-label .tip::after { max-width: 232px; }
[data-testid="stIconMaterial"], span[data-testid="stIconMaterial"] { font-family: "Material Symbols Rounded", "Material Symbols Outlined" !important; }
section[data-testid="stSidebar"] [data-testid="stRadio"], section[data-testid="stSidebar"] [data-testid="stSlider"], section[data-testid="stSidebar"] [data-testid="stTextInput"] { margin-top: 10px; }
section[data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="select"] > div, section[data-testid="stSidebar"] [data-testid="stMultiSelect"] [role="group"] { max-height: none !important; height: auto !important; overflow: visible !important; }
section[data-testid="stSidebar"] [data-testid="stCheckbox"] [data-testid="stWidgetLabel"] { display: flex !important; }
section[data-testid="stSidebar"] [data-testid="stCheckbox"] p { color: #1e3a4c; font-size: 13px; font-weight: 600; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * { color: #3a5566 !important; opacity: 1 !important; }
.f-label { height: auto !important; min-height: 20px; }
.side-sub { color:#4a6572; font-size: 12px; margin: -8px 0 8px 0; }

/* ---------- Placeholder ---------- */
.placeholder { margin: 60px auto; max-width: 560px; text-align:center; background:#fff; border:1px solid %border%; border-radius: 14px; padding: 48px 32px; }
.placeholder i { font-size: 46px; color:%green%; }
.placeholder h2 { color:%blue%; margin: 18px 0 6px 0; font-weight: 800; }
.placeholder p { color:%blue_link%; margin: 0; }

/* ---------- Plotly / iframes ---------- */
[data-testid="stPlotlyChart"] { margin: 0; }
iframe[title*="folium"] { border-radius: 8px; border: 1px solid %border%; }

/* ---------- Responsive ---------- */
@media (max-height: 900px) {
  .side-foot { position: static; width: auto; margin-top: 18px; }
}
@media (max-width: 1500px) {
  /* écrans plus étroits que la maquette : les panneaux s'adaptent à leur contenu au lieu d'être tronqués */
  .q-lab { min-height: 48px; font-size: 11.5px; }
  .q-ico { width: 34px; height: 34px; font-size: 16px; }
  .ring { width: 58px; height: 58px; font-size: 13px; } .ring > span { width: 44px; height: 44px; }
  .top5, .q-grid { padding-bottom: 18px; }   /* compense la marge -1rem de Streamlit sous le dernier bloc Markdown */
}
@media (max-width: 1600px) {
  /* 8 menus : icônes masquées et police réduite pour que tous les libellés tiennent sur une ligne */
  .st-key-navbar .stButton button p { font-size: 14px; } .st-key-navbar button p::before { display:none; }
}
@media (max-width: 1280px) {
  :root { --sidebar: 250px; }
  .hdr .t1 { font-size: 17px; } .kpi__value { font-size: 22px; } .kpi__icon { flex-basis: 44px; width:44px; height:44px; font-size: 19px; }
  .st-key-navbar .stButton button p { font-size: 13px; } .st-key-navbar button p::before { display:none; }
}
@media (max-width: 900px) {
  :root { --sidebar: 0px; }
  section[data-testid="stSidebar"] { display: none !important; }
  [data-testid="stMain"] { margin-left: 0; }
  .st-key-navbar { overflow-x: auto; }
  .st-key-navbar [data-testid="stHorizontalBlock"] { min-width: 900px; }
  .hdr .t1 { font-size: 15px; } .hdr .t2 { font-size: 10px; }
}
"""


@lru_cache(maxsize=1)
def _embedded_fonts() -> str:
    """Polices (Nunito Sans) et icônes (Font Awesome) encodées en base64 : aucune requête externe ni fichier statique."""
    return (Path(__file__).resolve().parent.parent / "assets" / "embedded_fonts.css").read_text(encoding="utf-8")


def inject_css() -> None:
    """Injecte le CSS global (appelé à chaque exécution depuis app.py)."""
    css = _CSS
    tokens = {**{f"%{k}%": v for k, v in THEME.items()}, "%FONT%": FONT, "%TOPBAR%": str(TOPBAR_H),
              "%SIDEBAR%": str(SIDEBAR_W)}
    for token, value in tokens.items():
        css = css.replace(token, value)
    st.markdown(f"<style>{_embedded_fonts()}\n{css}</style>", unsafe_allow_html=True)
