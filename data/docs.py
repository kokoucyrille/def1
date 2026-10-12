"""
Dictionnaire unique des infobulles : chaque panneau et chaque KPI y a une entrée de 5 lignes
(Question · Lecture · Calcul · Source · Limite). Les « Lectures » sont calculées (jamais saisies à la main).
Un test (tests/smoke_test.py) échoue si un panneau n'a pas d'entrée ici.
"""
from __future__ import annotations

import html

from data.loader import fmt_dec as d1, fmt_int as i0, fmt_pct as p1, fmt_signed_pct as sp, facts

NAT = "Source : données ouvertes du Togo (DNPCDC-TG, DEPAITV-TG, DSCTT-TG, DERR-TG, DORRC-TG, DEA-TG, DRGPH-TG)."


def _e(q, lec, calc, src, lim, ind=False):
    return {"q": q, "lec": lec, "calc": calc, "src": src, "lim": lim, "ind": ind}


def _build() -> dict:
    return {
        # ------------------------------------------------------------------ KPI
        "kpi_immat": _e("Combien de véhicules sont immatriculés l'année choisie ?", lambda F: f"En 2022 : {i0(F['immat22'])} véhicules, soit ×{d1(F['ratio_22_02'], 2)} par rapport à 2002.", "Total annuel de la série fournie (nombre de véhicules).", "DEPAITV-TG (akkouh), 1990–2022.", "Série annuelle fournie : stock ou flux ambigu (elle baisse certaines années, ex. 2020).", True),
        "kpi_part2r": _e("Quel poids pèsent les deux-roues ?", lambda F: f"En 2022 : {p1(F['part2r_22'])} des immatriculations (contre {p1(F['part2r_02'])} en 2002).", "Deux-roues / total × 100.", "DEPAITV-TG, 1990–2022.", "« 2 roues et assimilées » ≠ motos strictes.", True),
        "kpi_permis": _e("Combien de permis sont délivrés l'année choisie ?", lambda F: f"En 2022 : {i0(F['permis22'])} permis, dont {i0(F['permisA22'])} permis A.", "Somme des catégories de permis délivrées aux examens.", "DNPCDC-TG, 2007–2022.", "2013 = donnée manquante (jamais interpolée) ; un flux de permis n'est pas un nombre de conducteurs.", False),
        "kpi_acc": _e("Combien d'accidents corporels de la circulation ?", lambda F: f"En 2022 : {i0(F['acc22'])} accidents, ×{d1(F['acc_x'])} depuis 2010 ({i0(F['acc10'])}).", "Valeur annuelle nationale.", "DSCTT-TG, 2010–2022.", "National seul, non territorialisable ; 2010 et 2015 atypiquement bas.", False),
        "kpi_blesses": _e("Combien de blessés ?", lambda F: f"En 2022 : {i0(F['bl22'])} blessés (contre {i0(F['bl10'])} en 2010).", "Valeur annuelle nationale.", "DSCTT-TG, 2010–2022.", "National seul ; sensible à la sous-déclaration.", False),
        "kpi_morts": _e("Combien de morts sur les routes ?", lambda F: f"En 2022 : {i0(F['morts22'])} morts, {sp(F['morts_var'])} depuis 2010 ({i0(F['morts10'])}).", "Valeur annuelle nationale.", "DSCTT-TG, 2010–2022.", "National seul ; 2010 est une année basse, la hausse est à nuancer.", False),
        "kpi_morts100k": _e("Quel poids démographique des décès ?", lambda F: f"{i0(F['morts22'])} morts / {i0(F['pop'])} hab. = {d1(F['morts100k22'])} pour 100 000 hab.", "Morts / population RGPH 2022 × 100 000.", "DSCTT-TG + DRGPH-TG (2022).", "Population d'une seule année (2022) appliquée à toute la période.", True),
        "kpi_morts100acc": _e("Les accidents sont-ils plus meurtriers ?", lambda F: f"2022 : {d1(F['morts100acc22'])} morts pour 100 accidents (2010 : {d1(F['morts100acc10'])}).", "Morts / accidents × 100.", "DSCTT-TG.", "Sensible à la sous-déclaration des accidents légers.", False),
        "kpi_km": _e("Quel linéaire de routes classées ?", lambda F: f"National : {i0(F['km_total'])} km pour {d1(F['km_10k_nat'], 2)} km / 10 000 hab.", "Somme des longueurs géométriques (EPSG:32631) des 799 tronçons.", "DORRC-TG (fichier non daté, extrait fin 2024).", "Tronçon rattaché entier à une préfecture ; peu de voirie urbaine.", False),
        "kpi_pct_bon": _e("Quelle part du réseau est en bon état ?", lambda F: f"Routes revêtues 2020 : {p1(F['pct_bon_rev'])} en bon état.", "km bon / km total de la catégorie (travaux inclus au total).", "DERR-TG, 2020.", "Une seule année, pas de région.", False),
        "kpi_pct_mauvais": _e("Quelle part du réseau est en mauvais état ?", lambda F: f"Routes revêtues 2020 : {p1(F['pct_mauvais_rev'])} en mauvais état.", "km mauvais / km total de la catégorie.", "DERR-TG, 2020.", "Une seule année ; « travaux » n'est pas assimilé au mauvais état.", False),
        "kpi_km10k": _e("Quel linéaire par habitant ?", lambda F: f"National : {d1(F['km_10k_nat'], 2)} km de routes classées pour 10 000 hab.", "km classés / population RGPH 2022 × 10 000.", "DORRC-TG + DRGPH-TG.", "Les routes non classées sont hors champ.", False),
        "kpi_double": _e("Combien d'unités cumulent les deux déficits ?", lambda F: f"Préfectures dont infrastructure ET formation sont dans le tercile défavorable (≥ 2/3).", "Score d'infrastructure ≥ 2/3 et score de formation ≥ 2/3.", "Diagnostic (section 7).", "Sécurité exclue (accidents nationaux) ; auto-écoles possiblement sous-recensées.", False),
        "kpi_zeros": _e("Où n'y a-t-il aucune route ou aucune auto-école ?", lambda F: f"{F['n_sans_ae']} préfectures sans auto-école, {F['n_sans_route']} sans route classée (Mô).", "Comptage des unités à effectif nul.", "DEA-TG, DORRC-TG.", "Absence d'enregistrement ≠ absence réelle (sous-couverture possible).", False),
        "kpi_region_def": _e("Quelle région est la plus défavorable ?", lambda F: "Région au score pondéré le plus élevé (1 = le plus défavorable).", "Score = pondération × infrastructure + (1 − pondération) × formation.", "Diagnostic (section 7).", "Rangs entre 6 régions seulement ; égalités possibles.", False),
        "kpi_quintile": _e("Combien d'unités dans le quintile le plus défavorable ?", lambda F: "Unités dont le score est ≥ 0,80 (seuil fixe).", "Comptage des scores ≥ 0,80.", "Diagnostic (section 7).", "Sensible à la pondération : voir le panneau Robustesse.", False),
        # ------------------------------------------------------------------ Vue d'ensemble
        "acc_carte": _e("Où sont les routes classées par rapport à la population ?", lambda F: f"Plus la teinte est foncée, plus le linéaire par habitant est élevé ; Grand Lomé : {d1(F['gl_part_km'])} % du linéaire pour {d1(F['gl_part_pop'])} % de la population.", "km classés / population × 10 000, par préfecture.", "DORRC-TG + DRGPH-TG 2022 ; contours indicatifs.", "Contours reconstitués (indicatifs) ; population d'une seule année.", True),
        "acc_courbes": _e("Les accidents suivent-ils les immatriculations ?", lambda F: f"Depuis 2010 : immatriculations ×{d1(F['immat_x10'])}, accidents ×{d1(F['acc_x'])}, morts {sp(F['morts_var'])}.", "Valeur de l'année / valeur de l'année de base × 100.", "DEPAITV-TG, DNPCDC-TG, DSCTT-TG.", "On compare des tendances, jamais des niveaux ; 2013 manquant pour les permis.", False),
        "acc_classement": _e("Quelles régions cumulent les déficits ?", lambda F: "Scores 0 à 1 (1 = le plus défavorable) pour l'infrastructure et la formation.", "Moyenne de rangs percentiles (voir page Diagnostic & recommandations).", "DORRC-TG, DEA-TG, DRGPH-TG.", "Rangs entre 6 régions ; sécurité exclue.", True),
        "acc_donut": _e("De quoi se compose le parc immatriculé ?", lambda F: f"En 2022, les deux-roues représentent {p1(F['part2r_22'])} des immatriculations.", "Part de chaque catégorie dans le total de l'année.", "DEPAITV-TG.", "Série annuelle fournie : stock ou flux ambigu.", True),
        # ------------------------------------------------------------------ Immatriculations et Permis
        "parc_aires": _e("Qui porte la hausse ?", lambda F: f"Deux-roues : {p1(F['part2r_22'])} du total en 2022 contre {p1(F['part2r_02'])} en 2002.", "Véhicules par an ; poids lourds = camions + semi-remorques + tracteurs.", "DEPAITV-TG (akkouh), 1990–2022.", "Série annuelle fournie : stock/flux ambigu.", True),
        "parc_base100": _e("Quelle catégorie croît le plus vite ?", lambda F: f"Immatriculations totales ×{d1(F['ratio_22_02'], 2)} entre 2002 et 2022.", "TCAM = (V_fin / V_début)^(1/n) − 1 ; indice = V / V_base × 100.", "DEPAITV-TG.", "Très sensible à l'année de départ choisie.", True),
        "parc_contrib": _e("Quelle part de la hausse revient à chaque catégorie ?", lambda F: f"Les deux-roues expliquent {p1(F['part_hausse_2r'])} de la hausse 2002–2022.", "ΔV_catégorie / ΔV_total sur la période.", "DEPAITV-TG.", "« 2 roues et assimilées » ≠ motos strictes.", True),
        "permis_cat": _e("Combien de permis, de quel type ?", lambda F: f"En 2022 : {i0(F['permis22'])} permis dont {i0(F['permisA22'])} permis A ({p1(F['part_A22'])}).", "Permis délivrés par an et par catégorie.", "DNPCDC-TG, 2007–2022.", "2013 manquant (rupture annotée, exclu des cumuls) ; flux ≠ conducteurs actifs.", False),
        "permis_part": _e("Quelle catégorie de permis domine ?", lambda F: f"Permis A : {p1(F['part_A_cumul'])} des permis cumulés 2007–2022 (hors 2013).", "Somme des permis de la catégorie / somme du total, années exploitables (2013 exclu).", "DNPCDC-TG, 2007–2022.", "Flux de permis délivrés, pas un nombre de conducteurs ; 2013 manquant.", False),
        "permis_tcam": _e("Quelle catégorie de permis croît le plus vite ?", lambda F: "Taux de croissance annuel moyen entre la première et la dernière année exploitable de la période (2013 exclu).", "TCAM = (V_fin / V_début)^(1/n) − 1, n = nombre d'années entre les deux extrémités.", "DNPCDC-TG, 2007–2022.", "Sensible aux années extrêmes ; les catégories à petits effectifs (D, E, F) sont très volatiles.", False),
        "part_immat_permis": _e("La formation suit-elle l'usage ?", lambda F: f"Deux-roues : {p1(F['part2r_22'])} des immatriculations 2022 ; permis A : {p1(F['part_A_cumul'])} des permis cumulés 2007–2022 (hors 2013).", "Part des deux-roues dans les immatriculations vs part du permis A dans les permis délivrés.", "DEPAITV-TG, DNPCDC-TG.", "Permis non captés ou conduite sans permis : à investiguer ; on compare des parts, pas des conducteurs.", True),
        "parc_cylindree": _e("Quelles cylindrées dominent chez les deux-roues ?", lambda F: "Répartition 2013–2019 entre 50–125 cm³ et plus de 125 cm³.", "Immatriculations par tranche de cylindrée.", "DEPAITV-TG (wklhvw), 2013–2019.", "Sept années seulement ; ne couvre pas 2020–2022.", False),
        # ------------------------------------------------------------------ Sécurité
        "sec_serie": _e("Le bilan s'aggrave-t-il ?", lambda F: f"Accidents ×{d1(F['acc_x'])} et morts {sp(F['morts_var'])} entre 2010 et 2022.", "Valeurs annuelles.", "DSCTT-TG, 2010–2022 (n = 13).", "National seul ; 2010 et 2015 atypiquement bas.", False),
        "sec_gravite": _e("Les accidents sont-ils plus graves ?", lambda F: f"Morts pour 100 accidents : {d1(F['morts100acc10'])} en 2010, {d1(F['morts100acc22'])} en 2022.", "Morts / accidents × 100 ; blessés / accident.", "DSCTT-TG.", "Sensible à la sous-déclaration des accidents.", False),
        "sec_ratio_veh": _e("Le risque suit-il l'exposition ?", lambda F: f"2022 : {i0(F['acc10kveh22'])} accidents pour 10 000 véhicules immatriculés.", "Indicateur / immatriculations de l'année × 10 000.", "DSCTT-TG + DEPAITV-TG.", "Immatriculations ≠ parc en circulation.", True),
        "sec_hab": _e("Quel poids démographique ?", lambda F: f"2022 : {i0(F['morts22'])} / {i0(F['pop'])} × 100 000 = {d1(F['morts100k22'])} morts pour 100 000 hab.", "Indicateur / population 2022 × 100 000.", "DSCTT-TG + DRGPH-TG 2022.", "Population 2022 seule, appliquée à toutes les années.", True),
        "terr_carte_immat": _e("Où se situent les valeurs, préfecture par préfecture ?", lambda F: "Les immatriculations ouverts sont nationaux : sans fichier territorial, la carte montre le contexte (population, auto-écoles, routes classées).", "Valeur de la couche choisie par préfecture ; zoom sur la région filtrée ; clic = sélection de la préfecture. Séries thématiques : somme de la période du filtre ; valeurs régionales reportées sur les préfectures de la région.", "DRGPH-TG 2022 (population) ; DORRC-TG (routes classées) ; DEA-TG (auto-écoles) ; fichier data/processed/donnees_territoire.csv pour les séries thématiques, s'il est fourni.", "Aucune série nationale n'est répartie au prorata de la population ; une préfecture sans valeur reste blanche.", False),
        "terr_carte_permis": _e("Où se situent les valeurs, préfecture par préfecture ?", lambda F: "Les permis délivrés ouverts sont nationaux : sans fichier territorial, la carte montre le contexte (population, auto-écoles, routes classées).", "Valeur de la couche choisie par préfecture ; zoom sur la région filtrée ; clic = sélection de la préfecture. Séries thématiques : somme de la période du filtre ; valeurs régionales reportées sur les préfectures de la région.", "DRGPH-TG 2022 (population) ; DORRC-TG (routes classées) ; DEA-TG (auto-écoles) ; fichier data/processed/donnees_territoire.csv pour les séries thématiques, s'il est fourni.", "Aucune série nationale n'est répartie au prorata de la population ; une préfecture sans valeur reste blanche.", False),
        "terr_carte_securite": _e("Où se situent les valeurs, préfecture par préfecture ?", lambda F: "Les accidents, blessés et morts ouverts sont nationaux : sans fichier territorial, la carte montre le contexte (population, auto-écoles, routes classées).", "Valeur de la couche choisie par préfecture ; zoom sur la région filtrée ; clic = sélection de la préfecture. Séries thématiques : somme de la période du filtre ; valeurs régionales reportées sur les préfectures de la région.", "DRGPH-TG 2022 (population) ; DORRC-TG (routes classées) ; DEA-TG (auto-écoles) ; fichier data/processed/donnees_territoire.csv pour les séries thématiques, s'il est fourni.", "Aucune série nationale n'est répartie au prorata de la population ; une préfecture sans valeur reste blanche.", False),
        "sec_corr": _e("Deux-roues et morts évoluent-ils ensemble ?", lambda F: f"Spearman ρ = {d1(F['spearman'], 2)} (n = {F['spearman_n']}) entre immatriculations de deux-roues et morts, 2010–2022.", "Corrélation de rang de Spearman, une observation par année.", "DEPAITV-TG + DSCTT-TG.", "n petit ; corrélation ≠ causalité.", False),
        # ------------------------------------------------------------------ Réseau
        "res_etat_cat": _e("Quelle part du réseau est dégradée ?", lambda F: f"Routes revêtues 2020 : {p1(F['pct_bon_rev'])} bon, {p1(F['pct_mauvais_rev'])} mauvais, {p1(F['pct_travaux_rev'])} en travaux.", "km par état / km total de la catégorie.", "DERR-TG, 2020.", "Une seule année (2020), pas de région ; travaux inclus dans le total.", False),
        "res_explorateur": _e("Quels tronçons sont les plus dégradés, et où sont-ils ?", lambda F: "Classement des tronçons par km en mauvais état et carte des tracés.", "km par état et par tronçon ; couleur de la carte = état dominant (le plus grand nombre de km).", "DERR-TG (2020) ⨝ DORRC-TG (tracés, fin 2024).", "Seuls les tronçons dont l'identifiant figure dans les routes classées ont un tracé (61 sur 84) ; les autres ne sont que dans le classement ; une année, pas de région.", False),
        "res_territoire": _e("Quel linéaire par habitant ?", lambda F: f"National : {d1(F['km_10k_nat'], 2)} km pour 10 000 hab. ; {F['n_sans_route']} préfecture sans route classée.", "km (géométrie, EPSG:32631) / population × 10 000.", "DORRC-TG + DRGPH-TG.", "Tronçon rattaché entier à une préfecture ; peu de voirie urbaine.", False),
        "res_etat_region": _e("L'entretien est-il inégal selon les régions ?", lambda F: "Part de mauvais état sur les seules routes appariées (couverture affichée).", "Part du mauvais état des routes appariées par identifiant, pondérée par la longueur classée.", "DERR-TG (2020) ⨝ DORRC-TG (fin 2024).", "Couverture de 0 % (Grand Lomé) à 90,6 % (Kara) ; état supposé homogène le long d'une route ; hors score.", True),
        "res_types": _e("Quels types de routes et quels revêtements ?", lambda F: "Répartition du linéaire classé par type et par revêtement observé.", "km par route_type et route_recouvrement.", "DORRC-TG.", "Contradictions possibles entre type administratif et revêtement observé.", False),
        # ------------------------------------------------------------------ Carte
        "carte_main": _e("Où sont routes et auto-écoles par rapport à la population ?", lambda F: "Choroplèthe par préfecture, réseau par type de route et points d'auto-écoles par statut.", "Indicateur choisi par préfecture ; km en EPSG:32631.", "DORRC-TG, DEA-TG, DRGPH-TG 2022.", "Contours indicatifs ; communes inférées ; fichier des routes non daté.", True),
        "carte_fiche": _e("Quel est le profil du territoire sélectionné ?", lambda F: "Population, linéaire, km / 10 000 hab., part non revêtue, auto-écoles, habitants par auto-école, rang.", "Voir page Diagnostic & recommandations pour les formules.", "DORRC-TG, DEA-TG, DRGPH-TG.", "Rang calculé sur le score du diagnostic (50/50).", True),
        "carte_classement": _e("Quelles préfectures sont les plus défavorisées pour l'indicateur ?", lambda F: "Classement des 39 préfectures selon l'indicateur coloré.", "Valeur de l'indicateur, tri décroissant ou croissant selon le sens défavorable.", "DORRC-TG, DEA-TG, DRGPH-TG.", "Zéro auto-école = valeur la plus défavorable (« zéro structurel »).", True),
        "carte_treemap": _e("Comment la population et l'indicateur choisi se répartissent-ils de la région à la préfecture ?", lambda F: f"Grand Lomé : {p1(F['gl_part_pop'], 0)} de la population ; {F['n_sans_ae']} préfectures sans auto-école, {F['n_sans_route']} sans route classée.", "Surface = population RGPH 2022 ; couleur = indicateur choisi (échelle bornée aux 5ᵉ–95ᵉ percentiles) ; une région est colorée par sa valeur calculée sur la région entière.", "DORRC-TG, DEA-TG, DRGPH-TG.", "Un zéro (aucune route, aucune auto-école) prend la couleur la plus défavorable ; rattachement des routes et auto-écoles aux préfectures par attributs (voir Données & méthode).", True),
        "carte_heatmap": _e("Quelles préfectures cumulent les déficits, indicateur par indicateur ?", lambda F: "Teinte = rang du déficit parmi les 39 préfectures (0 = favorable, 1 = le plus défavorable) pour cinq indicateurs.", "Rang percentile de chaque indicateur sur les 39 préfectures (les ex æquo prennent le rang le plus défavorable), inversé quand une valeur haute est favorable ; zéro auto-école = rang 1 ; aucune route classée = case blanche.", "DORRC-TG, DEA-TG, DRGPH-TG.", "Rangs relatifs, pas des valeurs ; les préfectures sans auto-école sont au rang le plus défavorable sur l'indicateur « habitants par auto-école ».", True),
        "ae_region": _e("Combien d'auto-écoles par région, agréées et non agréées ?", lambda F: f"{i0(F['ae_total'])} auto-écoles recensées dont {i0(F['ae_agreees'])} agréées ({p1(F['ae_part_agr'], 0)}) ; Grand Lomé en concentre {p1(F['gl_part_ae'], 0)}.", "Comptage des auto-écoles par région selon le statut (agréée = agréée + antenne agréée) ; en mode « Pour 100 000 hab. » : effectif / population RGPH 2022 × 100 000.", "DEA-TG (recensement des auto-écoles) + DRGPH-TG 2022 (population).", "Le recensement est possiblement incomplet hors Grand Lomé : un faible effectif peut être un défaut d'enregistrement.", False),
        "ae_part": _e("La part d'agréées diffère-t-elle selon les régions ? Les auto-écoles suivent-elles la population ?", lambda F: f"Part d'agréées : {p1(F['ae_gl_part_agr'], 0)} à Grand Lomé, {p1(F['ae_hors_gl_part_agr'], 0)} hors Grand Lomé ({F['ae_hors_gl_total']} auto-écoles).", "Statut : agréées / total × 100 au niveau national ; poids d'une région = ses auto-écoles / auto-écoles du pays × 100 (comparé à sa part de la population en vue « Total agrégé »).", "DEA-TG (recensement des auto-écoles) + DRGPH-TG 2022 (population).", "Effectifs faibles hors Grand Lomé : un point de pourcentage = peu d'unités.", False),
        "ae_prefecture": _e("Dans quelles préfectures sont les auto-écoles, et lesquelles n'en ont aucune ?", lambda F: f"{F['ae_n_pref_avec']} préfectures sur 39 ont au moins une auto-école ; {F['ae_top_pref']} en compte {F['ae_top_pref_n']}.", "Comptage par préfecture selon le statut, regroupé par région ; clic sur une barre = sélection de la préfecture.", "DEA-TG (recensement des auto-écoles) + DRGPH-TG 2022 (population).", "Le rattachement à la préfecture suit l'adresse déclarée ; une préfecture sans auto-école peut être un défaut de recensement.", False),
        "ae_tableau": _e("Quels sont les chiffres exacts, par région (agrégé) et par préfecture (détail) ?", lambda F: f"National : {i0(F['ae_total'])} auto-écoles ({i0(F['ae_agreees'])} agréées, {i0(F['ae_non_agreees'])} non agréées), soit {i0(F['hab_par_ae_nat'])} habitants par auto-école.", "Somme des préfectures pour la version régionale ; habitants par auto-école = population / total.", "DEA-TG (recensement des auto-écoles) + DRGPH-TG 2022 (population).", "Voir les limites de chaque graphique de la section.", False),
        # ------------------------------------------------------------------ Diagnostic
        "diag_score": _e("Où cumule-t-on les déficits ?", lambda F: "Teinte = score pondéré (1 = le plus défavorable) ; contour marqué pour le quintile défavorable.", "Moyenne de rangs percentiles : infrastructure (km/10 000 hab., part non revêtue) et formation (hab./auto-école, agréées/100 000 hab.).", "DORRC-TG, DEA-TG, DRGPH-TG.", "Sécurité exclue (accidents nationaux) ; état du réseau exclu (couverture insuffisante).", True),
        "diag_classement": _e("Quelles unités sont les plus défavorisées ?", lambda F: "Barres empilées : part infrastructure et part formation du score.", "Score = pondération × infrastructure + (1 − pondération) × formation.", "Diagnostic (section 7).", "Zéros structurels placés au rang le plus défavorable.", True),
        "diag_nuage": _e("Où croisent faible linéaire et faible offre de formation ?", lambda F: "Chaque point est une unité ; en haut à gauche = faible linéaire et peu d'auto-écoles par habitant.", "km / 10 000 hab. (abscisse) × habitants par auto-école (ordonnée).", "DORRC-TG, DEA-TG, DRGPH-TG.", "Zéro auto-école tracé en bordure (« zéro structurel ») ; auto-écoles possiblement sous-recensées hors Grand Lomé.", True),
        "diag_robustesse": _e("Le classement résiste-t-il aux choix de pondération ?", lambda F: "Nombre d'unités dans le quintile défavorable selon 20/80, 50/50, 80/20 et auto-écoles toutes ou agréées.", "Recalcul du diagnostic pour 6 configurations.", "Diagnostic (section 7).", "Les unités stables sont les seules conclusions robustes.", True),
        # ------------------------------------------------------------------ Recommandations
        "reco_p1": _e("Que faire pour la sécurité des deux-roues ?", lambda F: f"Deux-roues = {p1(F['part2r_22'])} des immatriculations 2022.", "Constats issus des tableaux calculés (data/processed).", "Voir les pages Immatriculations, Permis et Sécurité routière.", "Accidents non territorialisés : les actions territoriales sont à confirmer par de nouvelles données.", False),
        "reco_p2": _e("Que faire pour la formation des conducteurs ?", lambda F: f"{F['n_sans_ae']} préfectures sans auto-école ; permis A = {p1(F['part_A_cumul'])} des permis cumulés.", "Constats issus des tableaux calculés.", "DEA-TG, DNPCDC-TG, DRGPH-TG.", "Auto-écoles possiblement sous-recensées hors Grand Lomé.", True),
        "reco_p3": _e("Que faire pour l'entretien du réseau ?", lambda F: f"Routes revêtues 2020 : {p1(F['pct_mauvais_rev'])} en mauvais état, {p1(F['pct_travaux_rev'])} en travaux.", "Constats issus des tableaux calculés.", "DERR-TG (2020), DORRC-TG.", "État du réseau : une année, sans région ; estimation régionale indicative.", True),
        "reco_limites": _e("Que ne peut-on pas décider avec ces données ?", lambda F: "Aucune action par préfecture sur les accidents : ils n'existent qu'au niveau national.", "—", "Voir Données & méthode.", "Limite structurelle des données ouvertes disponibles.", False),
    }


def _details() -> dict:
    """Ligne « Détails » de chaque graphique : séries et couleurs, repères (pics, creux, effectifs) calculés sur l'ensemble des données (hors filtres)."""
    return {
        "acc_carte": lambda F: f"39 préfectures teintées de 0 (Mô, aucune route classée) à {d1(F['km10k_pref_max_v'], 1)} km / 10 000 hab. ({F['km10k_pref_max']}). Régions : {F['km10k_max_reg']} {d1(F['km10k_max'], 2)} (la mieux dotée), {F['km10k_min_reg']} {d1(F['km10k_min'], 2)} (la moins dotée). Trait bleu épais = région filtrée.",
        "acc_courbes": lambda F: f"4 séries en indice 100 (2010) : immatriculations (bleu), permis (vert), accidents (orange), morts (rouge). Pics : accidents {F['acc_pic_an']} ({i0(F['acc_pic'])}), morts {F['morts_pic_an']} ({i0(F['morts_pic'])}), permis {F['permis_pic_an']} ({i0(F['permis_pic'])}). Pointillé vertical = année de référence ; permis 2013 manquant.",
        "acc_classement": lambda F: f"6 régions, 2 barres : infrastructure (bleu) et formation (orange), de 0 à 1 (1 = le plus défavorable). À 50/50 : {F['reg_def']} la plus défavorable ({d1(F['reg_def_score'], 2)}), {F['reg_fav']} la plus favorable ({d1(F['reg_fav_score'], 2)}). La région filtrée est mise en avant.",
        "acc_donut": lambda F: f"5 catégories (mêmes couleurs que les autres pages : orange = deux-roues). Étiquettes = part du total de l'année ; centre = total. 2022 : {i0(F['deuxr22'])} deux-roues, {i0(F['voitures22'])} voitures, {i0(F['pl22'])} poids lourds.",
        "parc_aires": lambda F: f"Pile des 5 catégories, 1990–2022 (période filtrée) ; mode Volumes, Parts (100 %) ou Base 100. Total : {i0(F['immat90'])} en 1990, pic {i0(F['immat_pic'])} en {F['immat_pic_an']}, {i0(F['immat22'])} en 2022. Poids lourds = camions + semi-remorques + tracteurs.",
        "parc_base100": lambda F: "Une courbe par catégorie, indice 100 à l'année de base ; échelle logarithmique si l'écart dépasse ×12. TCAM 2002–2022 : " + ", ".join(f"{c.lower()} {d1(v, 1)} %/an" for c, v in sorted(F["tcam"].items(), key=lambda x: -x[1])) + ".",
        "parc_contrib": lambda F: "Part de la hausse 2002–2022 (somme = 100 %) : " + ", ".join(f"{c.lower()} {d1(v, 1)} %" for c, v in sorted(F["contrib"].items(), key=lambda x: -x[1])) + ".",
        "permis_cat": lambda F: f"Barres empilées : A moto, B voiture légère, C poids lourd, D transport en commun, E semi-remorque, F spéciale. Pic {F['permis_pic_an']} ({i0(F['permis_pic'])}), creux {F['permis_creux_an']} ({i0(F['permis_creux'])}) ; B = {p1(F['permisB_part_cumul'], 0)} du cumul. 2013 : barre vide (manquant).",
        "permis_part": lambda F: f"Une barre par catégorie sélectionnée (mêmes couleurs que les permis par catégorie) ; part de chaque catégorie dans les permis délivrés sur la période choisie, 2013 exclu. Permis A : {p1(F['part_A_cumul'])} du cumul 2007–2022.",
        "permis_tcam": lambda F: "Une barre par catégorie sélectionnée : taux de croissance annuel moyen entre la première et la dernière année exploitable de la période (2013 exclu comme extrémité). Les catégories D, E et F ont de petits effectifs : leur taux est volatil.",
        "part_immat_permis": lambda F: f"Orange : part des deux-roues dans les immatriculations ; bleu pointillé : part du permis A dans les permis (2013 exclu). Permis A : {p1(F['part_A_cumul'])} du cumul, maximum {p1(F['part_A_pic'])} en {F['part_A_pic_an']} ; deux-roues : {p1(F['part2r_22'])} en 2022.",
        "parc_cylindree": lambda F: f"Barres 2013–2019 : 50 à 125 cm³ (orange) et plus de 125 cm³ (brun). Maximum {i0(F['cyl_pic'])} deux-roues en {F['cyl_pic_an']} ; en 2019, {p1(F['cyl_part125_19'])} sont de 50 à 125 cm³.",
        "sec_serie": lambda F: f"Accidents (bleu) et blessés (orange) sur l'axe gauche, morts (rouge pointillé) sur l'axe droit. Accidents : pic {F['acc_pic_an']} ({i0(F['acc_pic'])}), creux {F['acc_min_an']} ({i0(F['acc_min'])}). Morts : pic {F['morts_pic_an']} ({i0(F['morts_pic'])}), creux {F['morts_min_an']} ({i0(F['morts_min'])}).",
        "sec_gravite": lambda F: f"Morts pour 100 accidents (rouge, axe gauche) : maximum {d1(F['grav_max'])} en {F['grav_max_an']}, minimum {d1(F['grav_min'])} en {F['grav_min_an']}. Blessés par accident (orange pointillé, axe droit) : {d1(F['bl_par_acc22'], 2)} en 2022.",
        "sec_ratio_veh": lambda F: f"Une barre par année. Accidents pour 10 000 véhicules : maximum {i0(F['r10k_max'])} en {F['r10k_max_an']}, minimum {i0(F['r10k_min'])} en {F['r10k_min_an']}, {i0(F['acc10kveh22'])} en 2022. Le filtre « Base du ratio » bascule vers 100 000 hab. ou valeurs brutes.",
        "sec_hab": lambda F: f"Population 2022 fixe : la forme des barres est identique à la série brute, seule l'échelle change. Morts : {d1(1e5 * F['morts_min'] / F['pop'], 1)} (2010, minimum) à {d1(1e5 * F['morts_pic'] / F['pop'], 1)} ({F['morts_pic_an']}, pic) pour 100 000 hab. ; {d1(F['morts100k22'], 1)} en 2022.",
        "terr_carte_immat": lambda F: "Carte des 39 préfectures colorées selon la couche choisie dans les filtres (échelle de couleur à gauche) ; la région filtrée est cadrée et entourée en bleu, la préfecture sélectionnée en rouge. Les préfectures sans valeur restent blanches.",
        "terr_carte_permis": lambda F: "Carte des 39 préfectures colorées selon la couche choisie dans les filtres (échelle de couleur à gauche) ; la région filtrée est cadrée et entourée en bleu, la préfecture sélectionnée en rouge. Les préfectures sans valeur restent blanches.",
        "terr_carte_securite": lambda F: "Carte des 39 préfectures colorées selon la couche choisie dans les filtres (échelle de couleur à gauche) ; la région filtrée est cadrée et entourée en bleu, la préfecture sélectionnée en rouge. Les préfectures sans valeur restent blanches.",
        "sec_corr": lambda F: f"1 point = 1 année (étiquette = année), 2010–2022 : abscisse = deux-roues immatriculés, ordonnée = indicateur choisi. ρ de Spearman = {d1(F['spearman'], 2)} sur n = {F['spearman_n']} (0 = aucun lien de rang, 1 = lien parfait) : lien faible.",
        "res_etat_cat": lambda F: f"4 catégories : routes revêtues ({i0(F['km_rev_total'])} km), routes en terre ({i0(F['km_terre'])} km), voiries revêtues et en terre. Couleurs fixes : vert bon, jaune moyen, rouge mauvais, gris travaux. Routes en terre : {p1(F['pct_mauvais_terre'], 0)} mauvais, {p1(F['pct_travaux_terre'], 0)} en travaux.",
        "res_explorateur": lambda F: f"{F['n_tron_rev'] + F['n_tron_terre']} tronçons nommés ({F['n_tron_rev']} revêtus, {F['n_tron_terre']} en terre), dont {F['tron_apparies']} tracés sur la carte (couleurs d'état fixes : vert bon, jaune moyen, rouge mauvais, gris travaux). Classement : les 14 plus forts km en mauvais état ; survol = détail par état.",
        "res_territoire": lambda F: f"Barres empilées revêtu (bleu marine) / non revêtu (ocre) et losanges orange = km / 10 000 hab. (axe droit). {p1(F['non_rev_nat'], 0)} du linéaire classé est non revêtu (définition observée). Mieux dotée : {F['km10k_max_reg']} ({d1(F['km10k_max'], 2)}) ; moins dotée : {F['km10k_min_reg']} ({d1(F['km10k_min'], 2)}).",
        "res_etat_region": lambda F: f"Part de chaque état parmi les km appariés ; la couverture figure au-dessus de chaque barre ({F['cov_min_reg']} : {d1(F['cov_min'], 0)} % → non renseigné ; {F['cov_max_reg']} : {d1(F['cov_max'], 1)} %). Part de mauvais état la plus élevée : {F['mauvais_est_max_reg']} ({p1(F['mauvais_est_max'], 0)}). Hors score.",
        "res_types": lambda F: f"Deux cercles : à gauche la répartition des kilomètres par type de route ({', '.join(f'{t_.lower()} {i0(v)} km' for t_, v in F['types_ordre'].items())}), à droite par revêtement observé ; le total classé est au centre du premier, les pourcentages sur les parts, le détail au survol. {d1(F['km_contra'])} km classés « non revêtue » portent un revêtement en dur.",
        "carte_main": lambda F: f"Fond = indicateur choisi sur 39 préfectures ; traits = {F['n_routes']} tronçons par type de route ; points = {F['ae_total']} auto-écoles ({F['ae_agreees']} agréées). Un clic sur une préfecture, un tronçon ou un point sélectionne la préfecture ; la carte zoome sur la région ou la préfecture choisie.",
        "carte_fiche": lambda F: "7 repères : population, km classés, km / 10 000 hab., part non revêtue, auto-écoles (dont agréées), habitants par auto-école, rang du score (1 = le plus défavorable, sur 39 préfectures ou 6 régions). Une puce rouge signale un zéro structurel (aucune route ou aucune auto-école).",
        "carte_classement": lambda F: f"Les 10 unités les plus défavorables dans le sens de l'indicateur ; barre rouge = préfecture sélectionnée ; un clic sur une barre la sélectionne. Au niveau national : {F['n_sans_ae']} préfectures sans auto-école, {F['n_sans_route']} sans route classée.",
        "carte_treemap": lambda F: f"Une case par préfecture (surface = population), regroupées par région ; couleur = indicateur choisi dans les filtres ; contour rouge = préfecture sélectionnée. Les {F['n_sans_ae']} préfectures sans auto-école et les {F['n_sans_route']} sans route classée prennent la couleur la plus défavorable.",
        "carte_heatmap": lambda F: f"Une ligne par préfecture, regroupées par région (séparateurs et noms à droite) et triées du score le plus défavorable au moins défavorable ; 5 colonnes : km / 10 000 hab., part non revêtue, habitants par auto-école, agréées / 100 000 hab., score du diagnostic. Contour rouge = préfecture sélectionnée. {F['n_sans_ae']} préfectures sans auto-école sont au rang 1 sur la colonne auto-école.",
        "ae_region": lambda F: f"Une barre par région (6), empilée agréées (orange) et non agréées (gris) ou unique en vue « Total agrégé » ; chiffre au-dessus = total. Région filtrée mise en évidence (les autres s'estompent). Hors Grand Lomé : {F['ae_hors_gl_total']} auto-écoles pour {i0(F['pop'] * (1 - F['gl_part_pop'] / 100))} habitants.",
        "ae_part": lambda F: "Deux donuts. Vue « Agréées et non agréées » : à gauche le statut national (agréées en orange, non agréées en gris, part d'agréées au centre), à droite le poids de chaque région dans les auto-écoles du pays. Vue « Total agrégé » : poids des régions dans les auto-écoles (gauche) et dans la population (droite), mêmes couleurs, à comparer. Région filtrée légèrement détachée ; détail au survol.",
        "ae_prefecture": lambda F: f"Une ligne par préfecture ayant au moins une auto-école ({F['ae_n_pref_avec']} sur 39), regroupées par région (noms à droite) puis triées par effectif ; préfecture sélectionnée en couleur pleine. La liste des préfectures sans auto-école est écrite sous le graphique.",
        "ae_tableau": lambda F: "Deux onglets : « Par région (agrégé) » (6 régions + total national) et « Par préfecture (non agrégé) » (39 préfectures, restreintes à la région filtrée) ; colonnes : population, agréées, dont antennes, non agréées, total, part agréée, habitants par auto-école, auto-écoles pour 100 000 hab. Export CSV de chaque onglet.",
        "diag_score": lambda F: f"Teinte de 0 à 1 ; contour sombre = score ≥ seuil (quintile 0,80 ou tercile 2/3). À 50/50 : {F['n_quintile']} unités dans le quintile, {F['n_double']} en double déficit ({', '.join(F['double_noms'])}). Région la plus défavorable : {F['reg_def']} ({d1(F['reg_def_score'], 2)}).",
        "diag_classement": lambda F: f"12 premières préfectures (6 régions). Barre bleue = infrastructure × poids ; orange = formation × (1 − poids) ; annotation = score total. Les {F['n_sans_ae']} zéros structurels sont au rang le plus défavorable, sauf si l'option « Classés à part » est choisie.",
        "diag_nuage": lambda F: f"1 point = 1 unité, taille proportionnelle à la population ; ✕ = zéro auto-école (ligne du haut). Axe vertical logarithmique ; km / 10 000 hab. de 0 (Mô) à {d1(F['km10k_pref_max_v'], 1)} ({F['km10k_pref_max']}). En haut à gauche : double déficit.",
        "diag_robustesse": lambda F: f"6 configurations : 20/80, 50/50, 80/20 × auto-écoles toutes ou agréées ; barres = nombre d'unités dans le quintile. Stables aux 6 : {', '.join(F['stables'])} (aussi stables avec un rattachement géographique). Puces = fréquence x/6.",
        "reco_p1": lambda F: f"3 actions : A1 programme deux-roues, A2 accidents par préfecture, A3 fiabilisation de la gravité. Repères : {p1(F['part2r_22'])} de deux-roues, {i0(F['morts22'])} morts, accidents ×{d1(F['acc_x'])} depuis 2010.",
        "reco_p2": lambda F: f"3 actions : B1 écart permis A / deux-roues, B2 préfectures sans auto-école, B3 rééquilibrage de l'offre. Repères : permis A {p1(F['part_A_cumul'])} du cumul, {F['n_sans_ae']} préfectures sans auto-école, Grand Lomé {p1(F['gl_part_ae'], 0)} des auto-écoles pour {p1(F['gl_part_pop'], 0)} de la population.",
        "reco_p3": lambda F: f"3 actions : C1 tronçons dégradés, C2 linéaire classé, C3 suivi de l'état. Repères : {p1(F['pct_mauvais_rev'], 0)} de mauvais état et {p1(F['pct_travaux_rev'], 0)} de travaux sur les routes revêtues ; tronçon le plus dégradé : {F['tron_top']}.",
        "reco_limites": lambda F: "5 limites : sécurité seulement nationale, état du réseau limité à 2020 sans région, permis = flux et non conducteurs, auto-écoles possiblement sous-recensées, corrélations non causales (ρ faible sur 13 années).",
    }


def _lectures() -> dict:
    """« Lecture » = le chiffre à retenir de chaque graphique (calculé). Remplace les descriptions génériques."""
    return {
        "acc_classement": lambda F: f"{F['reg_def']} cumule le plus fort déficit ({d1(F['reg_def_score'], 2)}), {F['reg_fav']} le plus faible ({d1(F['reg_fav_score'], 2)}) à 50/50.",
        "parc_base100": lambda F: "Croissance annuelle 2002–2022 : " + ", ".join(f"{c.lower()} {d1(v, 1)} %" for c, v in sorted(F["tcam"].items(), key=lambda x: -x[1])[:3]) + ".",
        "parc_cylindree": lambda F: f"En 2019, {p1(F['cyl_part125_19'])} des deux-roues sont de 50 à 125 cm³.",
        "res_explorateur": lambda F: f"Tronçon le plus dégradé : {F['tron_top']} ({d1(F['tron_top_km'])} km en mauvais état).",
        "res_etat_region": lambda F: f"Part de mauvais état la plus élevée : {F['mauvais_est_max_reg']} ({p1(F['mauvais_est_max'], 0)} des routes appariées).",
        "res_types": lambda F: f"{d1(F['km_contra'])} km classés « non revêtue » portent pourtant un revêtement en dur.",
        "carte_main": lambda F: f"Grand Lomé : {p1(F['gl_part_pop'], 0)} de la population, {p1(F['gl_part_km'], 0)} du linéaire, {p1(F['gl_part_ae'], 0)} des auto-écoles.",
        "carte_fiche": lambda F: f"National : {i0(F['pop'])} hab., {i0(F['km_total'])} km classés, {d1(F['km_10k_nat'], 2)} km / 10 000 hab.",
        "carte_classement": lambda F: f"{F['n_sans_ae']} préfectures sans auto-école, {F['n_sans_route']} sans route classée (Mô).",
        "diag_score": lambda F: f"À 50/50 : {F['n_quintile']} unités dans le quintile défavorable, {F['n_double']} en double déficit ({', '.join(F['double_noms'])}).",
        "diag_classement": lambda F: f"{F['n_sans_ae']} préfectures sont des zéros structurels : elles occupent le haut du classement.",
        "diag_nuage": lambda F: "En haut à gauche : peu de routes et peu d'auto-écoles par habitant (double déficit).",
        "diag_robustesse": lambda F: f"Seules {' et '.join(F['stables'])} restent dans le quintile aux 6 configurations.",
        "acc_carte": lambda F: f"Grand Lomé : {p1(F['gl_part_km'], 1)} du linéaire pour {p1(F['gl_part_pop'], 0)} de la population.",
        "res_territoire": lambda F: f"{F['km10k_min_reg']} : {d1(F['km10k_min'], 2)} km pour 10 000 hab. ; {F['km10k_max_reg']} : {d1(F['km10k_max'], 2)}.",
    }


@__import__("functools").lru_cache(maxsize=1)
def DOCS() -> dict:
    d, det_ = _build(), _details()
    for k, f in det_.items():
        d[k]["det"] = f
    for k, f in _lectures().items():
        d[k]["lec"] = f
    return d


def tip_html(key: str, up: bool = True) -> str:
    """Icône ⓘ avec infobulle CSS (survol et focus clavier) : Question, Lecture, Limite.
    up=True : s'ouvre vers le haut (évite de sortir de l'écran en bas) ; up=False pour les icônes proches de la barre fixe."""
    e = DOCS()[key]
    F = facts()
    lec = e["lec"](F) if callable(e["lec"]) else e["lec"]
    # infobulle volontairement courte : ce que montre le graphique, le chiffre à retenir, la limite à connaître.
    # Détails, calcul et source sont dans le bloc « Données des graphiques » en bas de page (data_expander).
    lignes = [("Question", e["q"]), ("Lecture", lec), ("Limite", e["lim"] + (" [Indicatif]" if e["ind"] else ""))]
    txt = "&#10;".join(f"{k} : {html.escape(v, quote=True)}" for k, v in lignes)
    return (f'<span class="tip{" up" if up else ""}" tabindex="0" role="note" aria-label="{html.escape(" ".join(f"{k} : {v}." for k, v in lignes), quote=True)}" '
            f'data-tip="{txt}"><i class="fa-solid fa-circle-info"></i></span>')


def is_indicatif(key: str) -> bool:
    return DOCS()[key]["ind"]


def detail_lines(key: str) -> list[tuple[str, str]]:
    """Informations complémentaires d'un graphique (bloc « Données des graphiques ») : Détails, Calcul, Source."""
    e, F = DOCS()[key], facts()
    out = []
    if e.get("det"):
        out.append(("Détails", e["det"](F)))
    out += [("Calcul", e["calc"]), ("Source", e["src"])]
    return out


TITRES = {  # clé -> « Menu — Panneau », dans l'ordre des menus
    "acc_carte": "Vue d'ensemble — Routes classées par habitant (carte)",
    "acc_courbes": "Vue d'ensemble — Indice base 100 (2010)",
    "acc_classement": "Vue d'ensemble — Déficit par région",
    "acc_donut": "Vue d'ensemble — Structure des immatriculations",
    "parc_aires": "Immatriculations — Véhicules immatriculés",
    "parc_base100": "Immatriculations — Base 100 et TCAM",
    "parc_contrib": "Immatriculations — Contribution à la hausse",
    "parc_cylindree": "Immatriculations — Deux-roues par cylindrée",
    "terr_carte_immat": "Immatriculations — Carte par territoire",
    "permis_cat": "Permis — Permis par catégorie",
    "permis_part": "Permis — Répartition cumulée par catégorie",
    "part_immat_permis": "Permis — Part immatriculations vs part permis",
    "permis_tcam": "Permis — Croissance annuelle moyenne par catégorie",
    "terr_carte_permis": "Permis — Carte par territoire",
    "sec_serie": "Sécurité routière — Accidents, blessés et morts",
    "sec_gravite": "Sécurité routière — Gravité des accidents",
    "sec_ratio_veh": "Sécurité routière — Pour 10 000 véhicules",
    "sec_hab": "Sécurité routière — Pour 100 000 habitants",
    "sec_corr": "Sécurité routière — Deux-roues et morts (corrélation)",
    "terr_carte_securite": "Sécurité routière — Carte par territoire",
    "res_etat_region": "État du réseau — État estimé par région",
    "res_etat_cat": "État du réseau — État par catégorie de voie",
    "res_explorateur": "État du réseau — Explorateur de tronçons (carte et classement)",
    "carte_main": "Routes & auto-écoles — Carte interactive",
    "carte_fiche": "Routes & auto-écoles — Fiche territoire",
    "carte_classement": "Routes & auto-écoles — Classement des préfectures",
    "res_territoire": "Routes & auto-écoles — Réseau classé par territoire",
    "res_types": "Routes & auto-écoles — Types de routes et revêtements",
    "carte_treemap": "Routes & auto-écoles — Région → préfecture (treemap)",
    "carte_heatmap": "Routes & auto-écoles — Profil des préfectures (heatmap)",
    "ae_region": "Routes & auto-écoles — Auto-écoles par région (agréées / non agréées)",
    "ae_part": "Routes & auto-écoles — Statut des auto-écoles et poids des régions",
    "ae_prefecture": "Routes & auto-écoles — Auto-écoles par préfecture",
    "ae_tableau": "Routes & auto-écoles — Répartition détaillée (agrégée / non agrégée)",
    "diag_score": "Diagnostic & recommandations — Carte du score",
    "diag_classement": "Diagnostic & recommandations — Classement et composantes",
    "diag_nuage": "Diagnostic & recommandations — Routes par habitant × habitants par auto-école",
    "diag_robustesse": "Diagnostic & recommandations — Robustesse du classement",
    "reco_p1": "Diagnostic & recommandations — Priorité 1 · Sécurité & deux-roues",
    "reco_p2": "Diagnostic & recommandations — Priorité 2 · Formation des conducteurs",
    "reco_p3": "Diagnostic & recommandations — Priorité 3 · Entretien du réseau",
    "reco_limites": "Diagnostic & recommandations — Limites des recommandations",
}


def fiches() -> list[dict]:
    """Fiches de tous les graphiques et panneaux (page Données & méthode) : Question, Lecture, Détails, Calcul, Source, Limite."""
    F, rows = facts(), []
    for k, titre in TITRES.items():
        e = DOCS()[k]
        rows.append({"Graphique": titre, "Question": e["q"], "Lecture": e["lec"](F) if callable(e["lec"]) else e["lec"], "Détails": e["det"](F) if e.get("det") else "",
                     "Calcul": e["calc"], "Source": e["src"], "Limite": e["lim"] + (" [Indicatif]" if e["ind"] else "")})
    return rows
