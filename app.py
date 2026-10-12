"""
Dashboard « Mobilité et sécurité routière au Togo » (Défi 1 — Data Challenge Administration territoriale et mobilité).

Point d'entrée : `streamlit run app.py` — chaque page vit dans views/ ; en-tête, navigation et CSS sont partagés ici.
"""
import streamlit as st

st.set_page_config(page_title="Mobilité et sécurité routière – Togo", page_icon="assets/favicon.png", layout="wide",
                   initial_sidebar_state="expanded")

from components.header import create_header   # noqa: E402  (après set_page_config)
from components.navbar import create_navbar   # noqa: E402
from components.styles import inject_css      # noqa: E402

PAGES = {  # un menu = une analyse attendue du défi (voir README) ; « Vue d'ensemble » résume l'ensemble
    "vue_ensemble": st.Page("views/vue_ensemble.py", title="Vue d'ensemble", url_path="vue-ensemble", default=True),
    "immat": st.Page("views/immatriculations.py", title="Immatriculations", url_path="immatriculations"),
    "permis": st.Page("views/permis.py", title="Permis", url_path="permis"),
    "securite": st.Page("views/securite.py", title="Sécurité routière", url_path="securite-routiere"),
    "etat_reseau": st.Page("views/etat_reseau.py", title="État du réseau", url_path="etat-reseau"),
    "routes_ae": st.Page("views/routes_auto_ecoles.py", title="Routes & auto-écoles", url_path="routes-auto-ecoles"),
    "diagnostic": st.Page("views/diagnostic.py", title="Diagnostic & recommandations", url_path="diagnostic-recommandations"),
    "donnees": st.Page("views/donnees.py", title="Données & méthode", url_path="donnees-methode"),
}
current = st.navigation(list(PAGES.values()), position="hidden")
current_key = next(k for k, p in PAGES.items() if p.url_path == current.url_path or (k == "vue_ensemble" and current.url_path == ""))

inject_css()

with st.container(key="topbar"):                    # bandeau fixe : header (68 px) + navbar (61 px)
    create_header()
    create_navbar(PAGES, current_key)
current.run()
