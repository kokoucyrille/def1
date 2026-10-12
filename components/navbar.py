"""Barre de navigation (vert foncé) : 8 entrées (une par analyse attendue, plus la vue d'ensemble et les données) ; l'entrée active est jaune. Icônes par index dans styles.py."""
from __future__ import annotations

import streamlit as st

# (libellé, clé de page, poids de colonne ≈ (8,4 px × nb de caractères + 44 px) / 100)
NAV_ITEMS = [
    ("Vue d'ensemble", "vue_ensemble", 1.62),
    ("Immatriculations", "immat", 1.78),
    ("Permis", "permis", 0.94),
    ("Sécurité routière", "securite", 1.87),
    ("État du réseau", "etat_reseau", 1.62),
    ("Routes & auto-écoles", "routes_ae", 2.12),
    ("Diagnostic & recommandations", "diagnostic", 2.79),
    ("Données & méthode", "donnees", 1.87),
]


def create_navbar(pages: dict, current: str) -> None:
    with st.container(key="navbar"):
        cols = st.columns([w for *_, w in NAV_ITEMS], gap="small")
        for i, (col, (label, key, _)) in enumerate(zip(cols, NAV_ITEMS)):
            is_active = key == current
            with col:
                if st.button(label, key=f"nav_{i}", type="primary" if is_active else "secondary", width="stretch"):
                    st.switch_page(pages[key])
