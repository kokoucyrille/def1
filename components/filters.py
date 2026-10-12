"""
Filtres de la sidebar, propres à chaque page, appliqués immédiatement (aucun bouton « Appliquer »).
Région / préfecture sont PARTAGÉES entre toutes les pages sauf Données & méthode (État du réseau : région seule) (`shared_region`, `shared_pref`).
« Réinitialiser » remet les valeurs par défaut de la page. Un filtre sans effet est grisé avec son explication.
"""
from __future__ import annotations

import html

import streamlit as st

from components.ui import flag_data_uri
from data import loader as L
from data import territoire as T

ss = st.session_state
ALL_R, ALL_P = L.ALL_REGIONS, L.ALL_PREFS
VEH = ["Deux-roues", "Voitures", "Camionnettes", "Poids lourds", "Autocars/Autobus"]
PERMIS = ["Moto (A)", "Voiture légère (B)", "Poids lourd (C)", "Transport en commun (D)", "Semi-remorque (E)", "Voiture spéciale (F)"]
TYPES = ["Route nationale revêtue", "Route nationale non revêtue", "Voirie urbaine", "Piste rurale"]
CAT_VOIE = ["Toutes les catégories", "Routes revêtues", "Routes en terre", "Voiries revêtues", "Voiries en terre"]
INDIC_CARTE = ["Km de routes classées / 10 000 hab.", "Part de routes non revêtues", "Habitants par auto-école",
               "Auto-écoles agréées / 100 000 hab.", "Score du diagnostic (50/50)", "Population (RGPH 2022)"]
AE_VUES = ["Agréées et non agréées", "Total agrégé"]
AE_MODES = ["Effectifs", "Pour 100 000 hab."]
THEMES = ["Tous les thèmes", "Sécurité & deux-roues", "Formation des conducteurs", "Entretien du réseau"]
DEFAULTS = {
    "vue_ensemble": {"annee": 2022},
    "immat": {"periode": (2002, 2022), "veh": VEH, "mode": "Volumes", "base": 2002, "couche": None},
    "permis": {"periode": (2007, 2022), "permis": PERMIS, "mode": "Volumes", "base": 2007, "couche": None},
    "securite": {"periode": (2010, 2022), "indic": "Morts", "base": "Pour 10 000 véhicules", "couche": None},
    "etat_reseau": {"cat": CAT_VOIE[0], "etats": ["BON", "MOYEN", "MAUVAIS", "TRAVAUX"], "q": ""},
    "routes_ae": {"indic": INDIC_CARTE[0], "couches": ["Réseau routier", "Auto-écoles"], "types": TYPES, "defn": "Revêtement observé", "statut": "Toutes", "osm": False, "ae_vue": AE_VUES[0], "ae_mode": AE_MODES[0]},
    "diagnostic": {"niveau": "Préfecture", "score_mode": "Pondéré (curseur)", "zeros": "Au rang le plus défavorable", "poids": 50, "seuil": "Quintile défavorable (≥ 0,80)", "ae": "Toutes", "theme": THEMES[0]},
}
SHARED_PAGES = {"vue_ensemble", "immat", "permis", "securite", "etat_reseau", "routes_ae", "diagnostic"}


def K(page: str, name: str) -> str:
    return f"w_{page}_{name}"


def _label(text: str, icon: str, help_: str = "") -> None:
    """Titre de filtre sans infobulle."""
    st.markdown(f'<div class="f-label"><i class="fa-solid {icon}"></i><span>{text}</span></div>', unsafe_allow_html=True)


def _reset(page: str) -> None:
    for n, v in DEFAULTS[page].items():
        ss[K(page, n)] = v
    if page in SHARED_PAGES:
        ss["shared_region"], ss["shared_pref"] = ALL_R, ALL_P
    if page in ("immat", "permis"):
        ss[K(page, "base")] = DEFAULTS[page]["periode"][0]


def _on_region(page: str) -> None:
    ss["shared_region"], ss["shared_pref"] = ss[K(page, "region")], ALL_P


def _on_pref(page: str) -> None:
    ss["shared_pref"] = ss[K(page, "pref")]


def set_territory(pref: str | None) -> None:
    """Sélectionne une préfecture ou une région pour toutes les pages."""
    if pref and pref != ss.get("shared_pref"):
        p = L.prefs()
        row = p[p.prefecture == pref]
        if len(row):
            ss["shared_region"], ss["shared_pref"] = row.region.iloc[0], pref
    elif pref is None and ss.get("shared_pref") != ALL_P:
        ss["shared_pref"] = ALL_P


def set_region(region: str) -> None:
    """Sélectionne une région sans préfecture pour toutes les pages."""
    if region in L.ORDRE_REGIONS:
        ss["shared_region"], ss["shared_pref"] = region, ALL_P


def _init(page: str) -> None:
    for n, v in DEFAULTS[page].items():
        ss.setdefault(K(page, n), v)


def _territory(page: str, region_disabled: bool = False, region_help: str = "", with_pref: bool = True, pref_disabled: bool | None = None) -> tuple[str | None, str | None]:
    """Région → Préfecture en cascade, partagés entre pages (`with_pref=False` : région seule, ex. État du réseau).
    `pref_disabled` (par défaut = `region_disabled`) permet de griser la préfecture sans griser la région."""
    pref_disabled = region_disabled if pref_disabled is None else pref_disabled
    ss.setdefault("shared_region", ALL_R); ss.setdefault("shared_pref", ALL_P)
    if ss["shared_pref"] != ALL_P and ss["shared_pref"] not in L.prefectures_of(ss["shared_region"]):
        ss["shared_pref"] = ALL_P
    ss[K(page, "region")], ss[K(page, "pref")] = ss["shared_region"], ss["shared_pref"]
    _label("Région", "fa-location-dot", region_help or "Sélection partagée par toutes les pages (sauf Données & méthode). Restreint les préfectures proposées.")
    st.selectbox("Région", [ALL_R] + L.ORDRE_REGIONS, key=K(page, "region"), label_visibility="collapsed",
                 on_change=_on_region, args=(page,), disabled=region_disabled)
    if with_pref:
        _label("Préfecture", "fa-building", "Préfecture RGPH 2022 (39). Un clic sur la carte ou sur un classement sélectionne aussi la préfecture.")
        st.selectbox("Préfecture", [ALL_P] + L.prefectures_of(ss["shared_region"]), key=K(page, "pref"), label_visibility="collapsed",
                     on_change=_on_pref, args=(page,), disabled=pref_disabled)
    return (None if ss["shared_region"] == ALL_R else ss["shared_region"], None if ss["shared_pref"] == ALL_P else ss["shared_pref"])


def _couche(page: str, f: dict) -> None:
    """Choix de la couche affichée sur la carte « Données par territoire » (séries thématiques si le fichier territorial existe, sinon contexte)."""
    opts = T.couches(page)
    if ss.get(K(page, "couche")) not in opts:
        ss[K(page, "couche")] = opts[0]
    _label("Couche de la carte", "fa-layer-group", "Donnée colorée sur la carte et dans le classement de la section « Données par territoire ». Les séries thématiques (immatriculations, permis, accidents) n'apparaissent que si le fichier data/processed/donnees_territoire.csv est fourni ; sinon, contexte territorial (population, auto-écoles, routes).")
    f["couche"] = st.selectbox("Couche", opts, key=K(page, "couche"), label_visibility="collapsed")


def sidebar(page: str) -> dict:
    """Dessine la sidebar de la page et renvoie le dictionnaire des filtres appliqués."""
    _init(page)
    f: dict = {}
    with st.sidebar:
        st.markdown('<div class="f-title"><i class="fa-solid fa-filter"></i><span>FILTRES</span></div>', unsafe_allow_html=True)
        st.checkbox("Afficher les lectures", value=True, key="show_readings")
        if page == "vue_ensemble":
            _label("Année de référence", "fa-calendar-days", "Année affichée dans les KPI, le donut et la carte (2010 à 2022 : période commune aux accidents et aux immatriculations).")
            f["annee"] = st.selectbox("Année", list(range(2022, 2009, -1)), key=K(page, "annee"), label_visibility="collapsed")
            f["region"], f["pref"] = _territory(page, region_help="Zoome la carte sur la région et met en évidence la région dans le classement ; les séries nationales (immatriculations, permis, accidents) n'existent pas par territoire.")
        elif page == "immat":
            _label("Période", "fa-calendar-days", "Années affichées dans tous les panneaux (1990–2022).")
            f["periode"] = st.slider("Période", 1990, 2022, key=K(page, "periode"), label_visibility="collapsed")
            f["region"], f["pref"] = _territory(page, region_help="Zoome la carte « Données par territoire » et filtre ses chiffres. Les séries d'immatriculations nationales ne sont pas découpées par territoire : voir la note de la section.")
            st.caption("La région et la préfecture agissent sur le contexte territorial uniquement ; les immatriculations restent nationales.")
            _couche(page, f)
            _label("Catégories de véhicules", "fa-layer-group", "Poids lourds = camions + semi-remorques + tracteurs ; Deux-roues = « 2 roues et assimilées ».")
            f["veh"] = st.multiselect("Véhicules", VEH, key=K(page, "veh"), label_visibility="collapsed")
            _label("Affichage", "fa-chart-simple", "Volumes (valeurs annuelles), Base 100 (indice à l'année de base) ou Parts (répartition en % de l'année).")
            f["mode"] = st.radio("Affichage", ["Volumes", "Base 100", "Parts"], key=K(page, "mode"), label_visibility="collapsed", horizontal=True)
            a0, a1 = f["periode"]
            if ss.get(K(page, "base")) not in range(a0, a1 + 1):
                ss[K(page, "base")] = a0
            _label("Année de base (indice 100)", "fa-calendar-days", "Année prise comme 100 dans le panneau Base 100 & TCAM ; elle doit appartenir à la période.")
            f["base"] = st.selectbox("Année de base", list(range(a0, a1 + 1)), key=K(page, "base"), label_visibility="collapsed")
        elif page == "permis":
            _label("Période", "fa-calendar-days", "Permis délivrés : 2007–2022 (2013 manquant, jamais interpolé).")
            f["periode"] = st.slider("Période", 2007, 2022, key=K(page, "periode"), label_visibility="collapsed")
            f["region"], f["pref"] = _territory(page, region_help="Zoome la carte « Données par territoire » et filtre ses chiffres. Les séries d'permis nationales ne sont pas découpées par territoire : voir la note de la section.")
            st.caption("La région et la préfecture agissent sur le contexte territorial uniquement ; les permis restent nationaux.")
            _couche(page, f)
            _label("Catégories de permis", "fa-suitcase-medical", "A = moto ; B = voiture légère ; C = poids lourd ; D = transport en commun ; E = semi-remorque ; F = voiture spéciale.")
            f["permis"] = st.multiselect("Permis", PERMIS, key=K(page, "permis"), label_visibility="collapsed")
            _label("Affichage", "fa-chart-simple", "Volumes (valeurs annuelles), Base 100 (indice à l'année de base) ou Parts (répartition en % de l'année). Comparer des tendances ou des parts, jamais des niveaux.")
            f["mode"] = st.radio("Affichage", ["Volumes", "Base 100", "Parts"], key=K(page, "mode"), label_visibility="collapsed", horizontal=True)
            a0, a1 = f["periode"]
            if ss.get(K(page, "base")) not in range(a0, a1 + 1):
                ss[K(page, "base")] = a0
            _label("Année de base (indice 100)", "fa-calendar-days", "Année prise comme 100 en mode Base 100 ; elle doit appartenir à la période.")
            f["base"] = st.selectbox("Année de base", list(range(a0, a1 + 1)), key=K(page, "base"), label_visibility="collapsed")
        elif page == "securite":
            _label("Période", "fa-calendar-days", "Accidents, blessés et morts n'existent que de 2010 à 2022 (national, annuel).")
            f["periode"] = st.slider("Période", 2010, 2022, key=K(page, "periode"), label_visibility="collapsed")
            f["region"], f["pref"] = _territory(page, region_help="Zoome la carte « Données par territoire » et filtre ses chiffres. Les séries d'accidents nationales ne sont pas découpées par territoire : voir la note de la section.")
            st.caption("La région et la préfecture agissent sur le contexte territorial uniquement ; les séries de sécurité restent nationales.")
            _couche(page, f)
            _label("Indicateur", "fa-gauge-high", "Indicateur suivi dans le panneau de ratio et dans la corrélation avec les deux-roues.")
            f["indic"] = st.selectbox("Indicateur", ["Accidents", "Blessés", "Morts"], key=K(page, "indic"), label_visibility="collapsed")
            _label("Base du ratio", "fa-layer-group", "10 000 véhicules : indicateur / immatriculations de l'année (Indicatif). 100 000 hab. : population 2022 seule (Indicatif). Brut : valeurs absolues.")
            f["base"] = st.selectbox("Base", ["Pour 10 000 véhicules", "Pour 100 000 hab. (pop. 2022)", "Brut"], key=K(page, "base"), label_visibility="collapsed")
        elif page == "etat_reseau":
            _label("Période", "fa-calendar-days", "L'état du réseau n'existe que pour 2020 : aucune période n'est applicable.")
            st.selectbox("Période", ["Non daté (état : 2020)"], disabled=True, key=K(page, "periode_nd"), label_visibility="collapsed")
            _label("Catégorie de voie", "fa-layer-group", "Filtre l'état du réseau (national, 2020) : KPI, panneau État par catégorie et Explorateur de tronçons.")
            f["cat"] = st.selectbox("Catégorie", CAT_VOIE, key=K(page, "cat"), label_visibility="collapsed")
            _label("État", "fa-gauge-high", "États affichés (BON, MOYEN, MAUVAIS, TRAVAUX). Travaux est inclus dans le total et n'est pas assimilé au mauvais état.")
            f["etats"] = st.multiselect("État", ["BON", "MOYEN", "MAUVAIS", "TRAVAUX"], key=K(page, "etats"), format_func=lambda e: L.ETAT_LIBELLES[e], label_visibility="collapsed")
            f["region"], f["pref"] = _territory(page, with_pref=False, region_help="Met en évidence une région dans le panneau État estimé par région (l'état n'est connu par région que par estimation indicative). Sélection partagée avec Routes & auto-écoles et Diagnostic & recommandations.")
            _label("Recherche de tronçon", "fa-filter", "Texte recherché dans le nom des tronçons de l'explorateur.")
            f["q"] = st.text_input("Recherche", key=K(page, "q"), label_visibility="collapsed", placeholder="ex. RN1, KARA…")
        elif page == "routes_ae":
            _label("Période", "fa-calendar-days", "Routes classées et auto-écoles ne sont pas datées ; population RGPH 2022 : aucune période n'est applicable.")
            st.selectbox("Période", ["Non daté (pop. 2022)"], disabled=True, key=K(page, "periode_nd"), label_visibility="collapsed")
            f["region"], f["pref"] = _territory(page)
            _label("Indicateur coloré", "fa-chart-pie", "Indicateur qui colore les préfectures de la carte et du treemap, et trie le classement.")
            f["indic"] = st.selectbox("Indicateur", INDIC_CARTE, key=K(page, "indic"), label_visibility="collapsed")
            with st.expander("Options avancées"):
                _label("Couches de la carte", "fa-layer-group", "Réseau routier (une couleur par type) et points d'auto-écoles (par statut).")
                f["couches"] = st.multiselect("Couches", ["Réseau routier", "Auto-écoles"], key=K(page, "couches"), label_visibility="collapsed")
                _label("Type de route", "fa-map", "Types de route tracés sur la carte et retenus dans les panneaux Réseau classé par territoire et Types de routes et revêtements.")
                f["types"] = st.multiselect("Types", TYPES, key=K(page, "types"), label_visibility="collapsed")
                _label("Revêtement : définition", "fa-gear", "Observé : revêtement ∈ {Bitume, Béton, Pavé}. Administratif : type « Route nationale revêtue » ; voiries et pistes selon le revêtement observé. Concerne le panneau Réseau classé par territoire.")
                f["defn"] = st.radio("Définition", ["Revêtement observé", "Type administratif"], key=K(page, "defn"), label_visibility="collapsed")
                _label("Statut des auto-écoles", "fa-building-columns", "Agréée = Agréée + Antenne agréée. Sans effet si la couche Auto-écoles est masquée.")
                f["statut"] = st.selectbox("Statut", ["Toutes", "Agréées", "Non agréées"], key=K(page, "statut"), label_visibility="collapsed", disabled="Auto-écoles" not in f["couches"])
                _label("Répartition des auto-écoles", "fa-building-columns", "Section « Répartition des auto-écoles » : agréées et non agréées côte à côte (empilées), ou total agrégé. Indépendant du filtre « Statut des auto-écoles » (qui ne concerne que les points de la carte).")
                f["ae_vue"] = st.radio("Répartition", AE_VUES, key=K(page, "ae_vue"), label_visibility="collapsed")
                f["ae_mode"] = st.radio("Unité", AE_MODES, key=K(page, "ae_mode"), label_visibility="collapsed", horizontal=True)
                _label("Fond OpenStreetMap", "fa-map", "Remplace la carte autonome par une carte Folium avec fond OpenStreetMap. Nécessite une connexion Internet : hors connexion, seuls les polygones et le réseau restent visibles.")
                f["osm"] = st.checkbox("Fond OpenStreetMap (Internet requis)", key=K(page, "osm"))
        elif page == "diagnostic":
            _label("Niveau", "fa-layer-group", "Préfecture (39 unités) ou Région (6 unités). Les rangs sont calculés au niveau choisi.")
            f["niveau"] = st.radio("Niveau", ["Préfecture", "Région"], key=K(page, "niveau"), label_visibility="collapsed", horizontal=True)
            f["region"], f["pref"] = _territory(page, pref_disabled=f["niveau"] == "Région",
                                                 region_help="Diagnostic : restreint l'affichage à une région (niveau Préfecture ; au niveau Région, les 6 régions sont toujours comparées entre elles). "
                                                             "Recommandations : recompose les constats et les territoires cités pour la région choisie, quel que soit le niveau.")
            with st.expander("Options avancées"):
                _label("Score affiché", "fa-star", "Le consensus est la moyenne des 6 configurations (20/80, 50/50, 80/20 × auto-écoles toutes/agréées).")
                f["score_mode"] = st.radio("Score", ["Pondéré (curseur)", "Consensus (6 configurations)"], key=K(page, "score_mode"), label_visibility="collapsed")
                cons = f["score_mode"].startswith("Consensus")
                _label("Zéros structurels", "fa-circle-info", "Au rang le plus défavorable ou classés à part, hors score.")
                f["zeros"] = st.radio("Zéros", ["Au rang le plus défavorable", "Classés à part (hors score)"], key=K(page, "zeros"), label_visibility="collapsed")
                _label("Poids infrastructure (%)", "fa-gear", "50 = poids égaux entre infrastructure et formation.")
                f["poids"] = st.slider("Poids", 0, 100, step=10, key=K(page, "poids"), label_visibility="collapsed", disabled=cons)
                _label("Seuil de mise en évidence", "fa-filter", "Quintile défavorable = score ≥ 0,80 ; tercile défavorable = score ≥ 2/3.")
                f["seuil"] = st.radio("Seuil", ["Quintile défavorable (≥ 0,80)", "Tercile défavorable (≥ 2/3)"], key=K(page, "seuil"), label_visibility="collapsed")
                _label("Auto-écoles", "fa-building-columns", "Toutes les auto-écoles ou seulement les agréées (Agréée + Antenne agréée).")
                f["ae"] = st.radio("Auto-écoles", ["Toutes", "Agréées"], key=K(page, "ae"), label_visibility="collapsed", horizontal=True, disabled=cons)
                _label("Thème des recommandations", "fa-lightbulb", "Affiche une seule des trois priorités ou toutes.")
                f["theme"] = st.selectbox("Thème", THEMES, key=K(page, "theme"), label_visibility="collapsed")
        st.button("Réinitialiser", key=f"reset_{page}", type="secondary", width="stretch", on_click=_reset, args=(page,))
        st.markdown(f'<div class="side-foot"><img src="{flag_data_uri()}" alt=""><div><b>Défi 1 · Mobilité</b>'
                    f'<span>Données ouvertes du Togo</span></div></div>', unsafe_allow_html=True)
    return f
