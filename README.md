# Dashboard « Mobilité et sécurité routière au Togo » — Défi 1 (Streamlit)

Tableau de bord du Data Challenge **Administration territoriale et mobilité (Défi 1)**, construit sur les données ouvertes
fournies (immatriculations, permis, accidents, état et tracé du réseau, auto-écoles, population RGPH 2022).

## Lancer l'application

```bash
pip install -r requirements.txt
streamlit run app.py
```

Les données pré-calculées sont déjà dans `data/processed/`. Polices et icônes sont embarquées (`assets/embedded_fonts.css`) :
l'application fonctionne **sans Internet**, cartes comprises (Plotly/maplibre sans tuiles). Seule l'option
« Fond OpenStreetMap » (menu Routes & auto-écoles, Folium) demande une connexion ; hors connexion, polygones et réseau restent visibles.
Résolutions de référence : 1670 × 942 et 1366 × 768 (`docs/captures/`).

## v6 — lectures et diagnostic

Chaque page présente sous son titre une phrase « À retenir » fondée sur ses données et la sélection active ; la case « Afficher les lectures » permet de la masquer. Les pages d'analyse rappellent aussi le territoire sélectionné. Les tendances non calculables faute de série sont indiquées comme telles.

Le diagnostic affiche en premier un classement 50/50 des cinq priorités et associe une action au territoire le plus prioritaire. Les analyses de consensus, seuils et zéros structurels sont repliées dans « Options avancées ». Les cartes de recommandations conservent les cinq éléments de décision et proposent des boutons de sélection pour les territoires cités.

Sur la page État du réseau, la part en mauvais état par région est calculée uniquement sur les tronçons joints ; la couverture de la jointure est affichée. Une couverture nulle est laissée non renseignée, jamais imputée. L'état reste une mesure par tronçon en 2020, pas une observation régionale.

Les filtres territoriaux des pages Immatriculations, Permis et Sécurité n'agissent que sur le contexte territorial : les séries nationales ne sont pas ventilées par région ou préfecture. Les hauteurs des panneaux s'adaptent au contenu pour éviter la troncature sur les écrans plus étroits.

Les pages proposent un export CSV de la sélection et des filtres actifs. Sur Vue d'ensemble, les KPI non territorialisés portent explicitement le libellé « national ». Les calculs et agrégations territoriales coûteux sont mis en cache avec Streamlit.

Les survols indiquent les valeurs avec les formats français, l'année ou le territoire et, selon le graphique, les variations, parts et formules. Les valeurs manquantes restent explicites (« n.d. », « non renseigné » ou « aucune auto-école ») ; les chiffres utiles sont aussi visibles hors survol pour les écrans tactiles. Le test transversal collecte les figures des huit pages via AppTest et vérifie leurs templates et `customdata` ; il est ignoré explicitement si la politique de contrôle Windows bloque l'extension native NumPy requise.

## Menus : un menu = une analyse attendue du défi

| Menu | Analyse attendue du défi |
|---|---|
| Vue d'ensemble | Résumé : un chiffre clé par analyse, courbes base 100, déficits par région |
| Immatriculations | Évolution des immatriculations (voitures, deux-roues, poids lourds) |
| Permis | Évolution des permis de conduire délivrés |
| Sécurité routière | Accidents, blessés et décès rapportés à la population |
| État du réseau | État du réseau routier par région (et par catégorie de voie, par tronçon) |
| Routes & auto-écoles | Répartition des routes classées et des auto-écoles : carte, treemap et heatmap région → préfecture, répartition des auto-écoles agréées / non agréées par région (agrégé) et par préfecture (détail), tableaux et exports CSV |
| Diagnostic & recommandations | Où les déficits d'infrastructure et de formation se cumulent, puis recommandations pour une sécurité routière renforcée (mêmes filtres de région pour les deux sections) |
| Données & méthode | Sources, vérifications, limites, fiches des graphiques, exports |

Aucune infobulle ⓘ n'est affichée (ni sur les KPI, ni sur les titres de sections ou de filtres) ; la fiche complète de chaque graphique (question, lecture, détails, calcul, source, limite) est dans l'onglet « Fiches des graphiques » de la page Données & méthode alimentée par
`data/docs.py`. Les filtres s'appliquent immédiatement ; région/préfecture sont partagées entre État du réseau (région), Routes & auto-écoles et Diagnostic &
recommandations ; sur Vue d'ensemble, État du réseau et Diagnostic & recommandations, choisir une région recadre (zoom) la carte sur cette région ; un clic sur la carte ou sur un classement sélectionne une préfecture. Les mesures approximatives sont signalées dans la limite de chaque fiche.

## Contexte territorial (immatriculations, permis, accidents)

Les séries ouvertes d'immatriculations, de permis et d'accidents sont **nationales** : elles n'existent ni par région ni par préfecture. les pages Immatriculations, Permis et Sécurité routière ont une section « Contexte territorial » qui affiche, par défaut, le contexte territorial disponible (population, auto-écoles, routes classées). Pour y voir aussi les séries elles-mêmes (KPI du menu et couches de la carte), déposer `data/processed/donnees_territoire.csv` :

```
theme,annee,region,prefecture,valeur
permis,2022,,Kozah,120          # valeur d'une préfecture
morts,2022,Kara,,35             # prefecture vide = valeur de la région
```

Thèmes : `immatriculations`, `permis`, `accidents`, `blesses`, `morts`. Noms de régions et de préfectures : ceux du RGPH 2022 (voir `data/processed/population_prefectures.csv`). Pour un thème donné, des lignes au niveau préfecture l'emportent sur des lignes au niveau région. Le fichier est relu dès qu'il change (actualiser la page).

## Reconstruire les données (facultatif)

```bash
pip install -r requirements-build.txt
python tools/build_data.py     # lit data/raw/, vérifie 58 valeurs de contrôle + test géographique 39/39, écrit data/processed/
```

Le script échoue si une valeur de contrôle s'écarte de plus de 0,5 % ou si la table `geo_match` n'est pas 39/39.

## Tests et contrôles qualité

```bash
python tests/                  smoke_test.py (AppTest), browser_test.py (Playwright), _server.py          # AppTest : 8 pages, 47 combinaisons de filtres, fiches des graphiques, explorateur de tronçons graphique, géo 39/39, contrôle spatial, consensus, zéros à part, infobulles, valeurs de contrôle
                                    #   + lance tests/browser_test.py (clic réel sur la carte et le classement, clavier, cadrage des cartes, repli OSM hors connexion)
python tests/browser_test.py        # seulement les tests navigateur (Playwright + Chromium : `pip install playwright pillow && playwright install chromium`)
python tools/check_contrast.py      # audit de contraste WCAG AA dans le navigateur, textes des graphiques inclus (0 combinaison sous le seuil)
python tools/check_clean_env.py     # recette en environnement vierge (venv + requirements.txt seul, 8 pages)
python tools/check_perf.py          # temps de dessin des graphiques et réponse à un filtre
python -m pytest tests/test_v6.py   # tests ciblés des nouveautés v6 (AppTest nécessite NumPy fonctionnel)
python tools/check_a11y.py          # audit axe-core WCAG A/AA (pip install axe-playwright-python)
python tools/check_geo_spatial.py   # routes et auto-écoles vs polygones de la préfecture déclarée (écrit data/processed/controle_spatial.* et sensibilite_rattachement.json)
python tools/capture.py 8501        # captures d'écran (serveur Streamlit lancé sur ce port)
python tools/check_overflow.py 8501 # détecte les textes qui dépassent des panneaux
```

## Structure

```
app.py                  pages, en-tête, navigation, CSS
views/                  une page par menu
components/             styles, header, navbar, filters (sidebar), ui (panneaux, KPI, messages), charts, maps, map_osm, recommendation_cards
data/loader.py          lecture des tables, formats français, chiffres clés (facts)
data/diag.py            agrégation territoriale, diagnostic, robustesse (pandas seul)
data/docs.py            dictionnaire des infobulles KPI et fiches des graphiques
data/processed/         tables pré-calculées, GeoJSON, controles.csv, recommandations.json
data/raw/               données brutes minimales
tools/                  build_data.py, build_reco.py, check_geo_spatial.py, check_a11y.py, check_contrast.py, check_overflow.py, capture.py, build_embedded_fonts.py
tests/                  smoke_test.py (AppTest), browser_test.py (Playwright), _server.py
```

Pour régénérer les polices/icônes embarquées (nouvelle icône Font Awesome) : `tools/build_embedded_fonts.py`.
