"""Page « Données & méthode » — sources, vérifications du cadrage, limites et décisions, exports."""
from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from components.ui import page_title
from data import loader as L
from data.loader import fmt_dec as d1, fmt_int as i0, fmt_pct as p1

F = L.facts()
with st.sidebar:
    st.markdown('<div class="f-title"><i class="fa-solid fa-database"></i><span>DONNÉES</span></div><div class="side-sub">Cette page n\'a pas de filtre : elle documente les sources, les contrôles et les décisions de méthode.</div>', unsafe_allow_html=True)
    st.checkbox("Afficher les lectures", value=True, key="show_readings")
control_count = int((L.table("controles").statut == "OK").sum())
page_title(
    "fa-database",
    "Données & méthode",
    "Sources, vérifications, limites, décisions et exports.",
    takeaway=f"{control_count} contrôles de données conformes ; cette page documente les sources plutôt qu'une tendance.",
)
t1, t2, t3, t5, t4 = st.tabs(["Sources", "Vérifications du cadrage", "Limites et décisions", "Fiches des graphiques", "Exports"])

with t1:
    src = pd.DataFrame([
        ["DEPAITV-TG", "observationdata-akkouh.csv", "1990–2022", "National, annuel", "Véhicules immatriculés par type", "Stock/flux ambigu ; baisse certaines années"],
        ["DEPAITV-TG", "observationdata-wklhvw.csv", "2013–2019", "National, annuel", "Deux-roues par cylindrée", "Sept années seulement"],
        ["DNPCDC-TG", "observationdata-wvtolmb.csv", "2007–2022", "National, annuel", "Permis délivrés par catégorie", "2013 manquant ; flux ≠ conducteurs"],
        ["DSCTT-TG", "observationdata-hxdpzbg.csv", "2010–2022", "National, annuel", "Accidents, blessés, morts", "Aucun découpage territorial ; n = 13"],
        ["DERR-TG", "observationdata-tmdtnad.csv", "2020", "Tronçons nommés", "État du réseau (bon, moyen, mauvais, travaux)", "Une année ; pas de région"],
        ["DORRC-TG", "routes-routes-classees (CSV/WKT)", "Non daté (extrait fin 2024)", "799 tronçons géolocalisés", "Linéaire par préfecture (EPSG:32631)", "Tronçon rattaché entier à une préfecture"],
        ["DEA-TG", "entreprises-auto-ecoles (CSV)", "Non daté (extrait 2025)", "272 points (2 « Néant » exclues)", "Auto-écoles par préfecture et statut", "Recensement possiblement incomplet hors Grand Lomé"],
        ["DRGPH-TG", "observationdata-kwwolwb.csv", "2022", "6 régions, 39 préfectures", "Population (RGPH)", "Instantané ; aucune population annuelle ni superficie"],
    ], columns=["Code", "Fichier", "Période", "Granularité", "Usage", "Limite principale"])
    st.dataframe(src, hide_index=True, width="stretch")
    st.caption("Contours : togo_prefectures.geojson (40 polygones, « contours indicatifs »), réduits à 39 préfectures RGPH par la table geo_match.")
with t2:
    ctl = L.table("controles")
    ok = int((ctl.statut == "OK").sum())
    st.markdown(f"**{ok} / {len(ctl)} valeurs de contrôle retrouvées** (écart maximal toléré : 0,5 %, 1 % pour les ratios arrondis).")
    st.dataframe(ctl.rename(columns={"indicateur": "Indicateur", "valeur_attendue": "Attendu", "valeur_obtenue": "Obtenu", "ecart_relatif": "Écart relatif", "statut": "Statut"}), hide_index=True, width="stretch", height=300)
    gt = json.loads((L.PROC / "geo_test.json").read_text(encoding="utf-8"))
    sp = json.loads((L.PROC / "controle_spatial.json").read_text(encoding="utf-8"))
    st.markdown(f"**Contrôle spatial indépendant des noms** (`tools/check_geo_spatial.py`) : {sp['routes_part_km_dans_polygone_decl'] * 100:.1f} % de la longueur des routes classées tombe dans le polygone de la préfecture déclarée "
                f"({sp['troncons_majoritairement_hors_polygone']} tronçons sur 799 sont majoritairement hors du polygone déclaré) ; {sp['ae_dans_polygone_decl_tolerance_1km']} / {sp['ae_total']} auto-écoles tombent dans leur polygone (tolérance 1 km). "
                f"**Alias Naki-Ouest ↔ Kpendjal-Ouest : validé** ({sp['alias_naki_ouest_kpendjal_ouest_part_km'] * 100:.1f} % des km déclarés Kpendjal-Ouest dans ce polygone). "
                "Écarts connus, non corrigés (le rattachement par attributs administratifs est conservé, les contours étant indicatifs) : les 3 tronçons déclarés Akébou (10,8 km) tombent dans le polygone de Wawa ; "
                "29 des 70 auto-écoles d'Agoè-Nyivé tombent dans le polygone de Golfe (sans effet au niveau région : les deux sont dans Grand Lomé). Ces écarts rendent la lecture par préfecture du Grand Lomé et d'Akébou à vérifier sur le terrain.")
    sp_t = L.table("controle_spatial").merge(L.prefs()[["cle", "prefecture"]], left_on="cle_rgph", right_on="cle")
    sp_t = sp_t[(sp_t.routes_part_km_dans_polygone_decl < 0.8) | (sp_t.ae_n > sp_t.ae_dans_polygone_decl)]
    st.dataframe(sp_t[["prefecture", "routes_km", "routes_part_km_dans_polygone_decl", "ae_n", "ae_dans_polygone_decl"]].rename(columns={"prefecture": "Préfecture", "routes_km": "Routes (km)", "routes_part_km_dans_polygone_decl": "Part des km dans le polygone déclaré", "ae_n": "Auto-écoles", "ae_dans_polygone_decl": "Dont dans le polygone déclaré"}), hide_index=True, width="stretch")
    se = json.loads((L.PROC / "sensibilite_rattachement.json").read_text(encoding="utf-8"))
    st.markdown("**Sensibilité du diagnostic au mode de rattachement** (attributs administratifs, retenus par défaut, vs position géographique dans les contours indicatifs ; "
                f"{se['tronçons_rattaches_differemment']} tronçons et {se['auto_ecoles_rattachees_differemment']} auto-écoles rattachés différemment) :")
    st.dataframe(pd.DataFrame([
        ["Unités stables aux 6 configurations (zéros au rang le plus défavorable)", ", ".join(se["stables_attributs"]) or "aucune", ", ".join(se["stables_geographique"]) or "aucune"],
        ["Quintile défavorable à 50/50", ", ".join(se["quintile_50_50_attributs"]), ", ".join(se["quintile_50_50_geographique"])],
        ["Unités stables aux 6 configurations (zéros structurels classés à part)", ", ".join(se["stables_hors_zeros_attributs"]) or "aucune", ", ".join(se["stables_hors_zeros_geographique"]) or "aucune"],
        ["Quintile défavorable à 50/50 (zéros classés à part)", ", ".join(se["quintile_hors_zeros_attributs"]) or "aucune", ", ".join(se["quintile_hors_zeros_geographique"]) or "aucune"]],
        columns=["Résultat", "Rattachement par attributs (défaut)", "Rattachement géographique"]), hide_index=True, width="stretch")
    st.caption("Lecture : Mô et Akébou ressortent quel que soit le rattachement (conclusion robuste). Les unités du quintile hors zéros structurels changent selon le rattachement : ce sont des pistes à confirmer, pas des conclusions.")
    st.markdown(f"**Test géographique :** {gt['appariees']} / {gt['prefectures_rgph']} préfectures appariées, {gt['orphelins']} orphelin, {gt['doublons']} doublon (Lomé Commune fusionné dans Golfe). "
                "L'alias « Naki-Ouest ↔ Kpendjal-Ouest » est fait par chef-lieu et **validé spatialement** (voir ci-dessus).")
    st.dataframe(L.table("geo_match").rename(columns={"nom_contour": "Contour", "cle_rgph": "Clé RGPH", "methode": "Méthode", "statut": "Statut", "prefecture_rgph": "Préfecture RGPH"}), hide_index=True, width="stretch", height=240)
with t3:
    st.markdown(f"""
**Décisions de méthode**
- **Régions** : 6 régions RGPH (Grand Lomé = Golfe + Agoè-Nyivé) ; la région déclarée dans les routes et les auto-écoles est ignorée.
- **Poids lourds** = camions + semi-remorques + tracteurs ; « Deux-roues » = « 2 roues et assimilées » (≠ motos strictes).
- **Permis 2013** : donnée manquante, jamais interpolée, exclue des cumuls ; on compare des tendances (base 100) ou des parts, jamais des niveaux de flux.
- **Revêtue** : revêtement observé ∈ {{Bitume, Béton, Pavé}} par défaut ; définition administrative (type de route) disponible dans le filtre.
- **Auto-écoles** : « Agréée » + « Antenne agréée » = agréées ; 2 « Néant » exclues.
- **Diagnostic** : rangs percentiles ; zéro route ou zéro auto-école = rang le plus défavorable (« zéro structurel »), jamais NaN ; seuils fixes 0,80 et 2/3 ; sécurité et état du réseau exclus.

**Limites**
- Immatriculations : série annuelle fournie (stock/flux ambigu, baisse en 2020 de {d1(abs(F['chute2020']), 0)} %) : tout ratio par véhicule est **Indicatif**.
- Accidents : national et annuel, 13 années ; 2010 et 2015 atypiquement bas ; la série « Accidents mortels / 100 000 hab. » du fichier source compte en réalité tous les accidents et n'est pas utilisée telle quelle.
- État du réseau : 2020 seulement ; estimation régionale par jointure d'identifiants (couverture 0 à 90,6 %), état supposé homogène le long d'une route : **Indicatif**, hors score.
- Population : RGPH 2022 appliqué à toutes les années pour les ratios « pour 100 000 hab. » (Indicatif).
- Contours reconstitués : indicatifs ; communes inférées ; routes non datées.
""")
with t5:
    from data.docs import fiches
    fi = pd.DataFrame(fiches())
    st.markdown("Pour chaque graphique : ce qu'il montre, le chiffre à retenir, les détails de lecture, le calcul, la source et la limite.")
    sel = st.selectbox("Page", ["Toutes"] + list(dict.fromkeys(g.split(" — ")[0] for g in fi["Graphique"])), key="fiches_page", help="Filtrer les fiches par menu (dans l'ordre de la barre de navigation).")
    if sel != "Toutes":
        fi = fi[fi["Graphique"].str.startswith(sel + " — ")]
    for _, r in fi.iterrows():
        with st.expander(r["Graphique"]):
            st.markdown("".join(f"**{k}** : {r[k]}  \n" for k in ("Question", "Lecture", "Détails", "Calcul", "Source", "Limite") if r[k]))
    st.download_button("Fiches des graphiques (CSV)", pd.DataFrame(fiches()).to_csv(index=False).encode("utf-8"), "fiches_graphiques.csv", "text/csv", key="dl_fiches")
with t4:
    cles = pd.DataFrame([
        ["Immatriculations 2022", i0(F["immat22"])], ["Part des deux-roues 2022 (%)", d1(F["part2r_22"])], ["Part des deux-roues 2002 (%)", d1(F["part2r_02"])],
        ["Part des deux-roues dans la hausse 2002–2022 (%)", d1(F["part_hausse_2r"])], ["Part du permis A, cumul 2007–2022 hors 2013 (%)", d1(F["part_A_cumul"])],
        ["Accidents 2022", i0(F["acc22"])], ["Morts 2022", i0(F["morts22"])], ["Morts pour 100 000 hab. 2022", d1(F["morts100k22"])],
        ["Routes revêtues en mauvais état 2020 (%)", d1(F["pct_mauvais_rev"])], ["Part de la population de Grand Lomé (%)", d1(F["gl_part_pop"])],
        ["Part du linéaire classé de Grand Lomé (%)", d1(F["gl_part_km"])], ["Part des auto-écoles de Grand Lomé (%)", d1(F["gl_part_ae"])],
        ["Préfectures sans auto-école", str(F["n_sans_ae"])]], columns=["Chiffre clé", "Valeur"])
    st.dataframe(cles, hide_index=True, width="stretch")
    st.download_button("Chiffres clés (CSV)", cles.to_csv(index=False).encode("utf-8"), "chiffres_cles.csv", "text/csv", key="dl_cles")
    dico = []
    for p in sorted(L.PROC.glob("*.csv")):
        d = pd.read_csv(p)
        for c in d.columns:
            ex = d[c].dropna().iloc[0] if d[c].notna().any() else ""
            dico.append([p.name, c, str(d[c].dtype), int(d[c].notna().sum()), str(ex)[:40]])
    dico = pd.DataFrame(dico, columns=["Fichier", "Colonne", "Type", "Valeurs renseignées", "Exemple"])
    st.download_button("Dictionnaire de données (CSV)", dico.to_csv(index=False).encode("utf-8"), "dictionnaire_donnees.csv", "text/csv", key="dl_dico")
    st.markdown("**Tables pré-calculées**")
    cols = st.columns(3)
    for i, name in enumerate(["parc", "permis", "securite", "territoire_prefectures", "territoire_regions", "diagnostic_prefectures", "reseau_etat_troncons", "etat_reseau_region_indicatif", "auto_ecoles"]):
        cols[i % 3].download_button(f"{name}.csv", (L.PROC / f"{name}.csv").read_bytes(), f"{name}.csv", "text/csv", key=f"dl_{name}")
