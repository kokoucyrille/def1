# Journal des versions

## v6
- **Passe 1 — C2** : ajout d'une lecture « À retenir » chiffrée sur chaque page, masquable depuis la case cochée par défaut « Afficher les lectures » ; rappel du territoire sélectionné sous les titres. Les tendances non calculables (état du réseau et documentation) sont annoncées comme indisponibles, sans extrapolation.
- État du réseau : comparaison régionale de la part en mauvais état limitée aux tronçons joints, couverture indiquée, couverture nulle en gris « non renseigné » ; la carte des tronçons est conservée. L'état est explicitement décrit comme connu par tronçon, pas par région.
- Diagnostic : classement des cinq scores simples 50/50 en tête, priorité n° 1 et action associée, contrôles et analyses de robustesse repliés dans « Options avancées ».
- Recommandations : format constat / où / action / indicateur / horizon conservé ; boutons sous les cartes pour sélectionner les préfectures et régions citées. Les recommandations nationales ne ciblent pas de territoire non cité.
- **Passe 2 — C1** : les panneaux utilisent des hauteurs minimales plutôt que des hauteurs fixes ; contexte territorial renommé et accompagné d'une introduction ; les filtres région/préfecture des pages Immatriculations, Permis et Sécurité précisent qu'ils ne modifient que ce contexte. Les filtres secondaires de Routes & auto-écoles sont repliés ; les filtres avancés du Diagnostic restent repliés.
- Les contrôles visuels à 1670 et 1366 px n'ont pas pu être exécutés : le binaire Chromium de Playwright n'est pas installé dans l'environnement. Le test AppTest reste limité par le blocage système du module NumPy natif.
- **Passe 3 — C3** : mise en cache des tables et agrégations territoriales réutilisées, ajout d'un export CSV des données de la sélection sur les huit pages, et libellés « national » sur les KPI de la Vue d'ensemble qui ne suivent pas le filtre territorial. Les données manquantes des tronçons restent vides dans l'export.
- La comparaison de deux préfectures et la persistance des filtres dans l'URL ne sont pas incluses : l'option était conditionnée à une validation interactive fiable, indisponible ici. Les mesures numériques de `check_perf.py` n'ont pas pu être relevées avant/après, faute du Chromium requis par le script.
- **Passe 4 — survol enrichi** : les figures ajoutent ou précisent, selon le graphique, les valeurs exactes formatées en français, l'année ou le territoire, les variations, les parts et les formules des indicateurs calculés. Les templates informatifs existants sont conservés ; les données manquantes de `customdata` sont affichées « n.d. » plutôt que NaN/inf. Les lectures importantes restent aussi dans les titres et « À retenir » pour les écrans tactiles.
- Test transversal ajouté : collecte des figures en remplaçant `components.charts.show`, exécution des huit pages AppTest, vérification des templates et de l'absence de NaN/inf dans `customdata`. Le test est ignoré avec une raison explicite si le chargement de l'extension NumPy `_bounded_integers` est bloqué par la politique Windows ; il reste actif dans un environnement fonctionnel.
- Validation locale : `pytest tests/test_v6.py` — 3 réussis, 4 ignorés (AppTest bloqué sur NumPy) ; compilation Python et `git diff --check` réussis. `tests/smoke_test.py` a aussi été lancé en dernier avec un délai maximal de 4 minutes, puis s'est arrêté sur le même blocage NumPy.
- **Éléments non validés ici** : les vues AppTest, l'overflow/captures aux résolutions demandées et les temps `check_perf.py`. AppTest bute sur l'extension NumPy bloquée ; Playwright ne dispose pas de Chromium. Aucun temps de performance ni succès de vérification visuelle n'est revendiqué.

## v5.5
- Routes & auto-écoles : deux représentations passent en cercles (donuts). « Types de routes et revêtements » : un cercle par type de route et un par revêtement observé (km classés au centre, légende commune). « Statut des auto-écoles et poids des régions » (ex « Part d'agréées par région ») : statut national agréées / non agréées et poids des régions dans les auto-écoles ; en vue « Total agrégé », poids des régions dans les auto-écoles et dans la population, mêmes couleurs. Région filtrée légèrement détachée. Fiches de « Données & méthode » mises à jour.

## v5.4
- Sécurité routière : la section « Accidents par type de véhicule » est supprimée (page, fiches, modèle de fichier et tests).
- Données par territoire (Immatriculations, Permis, Sécurité routière) : section réduite à la carte par préfecture et aux KPI propres au menu (Immatriculations : population, routes classées ; Permis : auto-écoles agréées / non agréées, habitants par auto-école ; Sécurité : routes non revêtues, part non revêtue, population). Le KPI « … · par territoire n.d. » est supprimé : le KPI de la série du menu (immatriculations, permis, accidents…) n'apparaît que si un fichier territorial le fournit. Textes explicatifs, classement et tableau supprimés.

## v5.3
- Filtres Région et Préfecture (partagés d'une page à l'autre) ajoutés à Vue d'ensemble, Immatriculations, Permis et Sécurité routière, en plus de Routes & auto-écoles, Diagnostic et État du réseau (région seule : l'état du réseau n'existe pas par préfecture). Données & méthode, page documentaire, reste sans filtre.
- Immatriculations, Permis, Sécurité routière : nouvelle section « Données par territoire » — carte par préfecture (zoom sur la région filtrée, clic = sélection), cinq chiffres du territoire choisi, classement, tableau par région (agrégé) et par préfecture (détail) avec export CSV, et un filtre « Couche de la carte ».
- **Limite des données** : les immatriculations, permis et accidents ouverts sont nationaux, sans découpage territorial. Sans fichier territorial, la carte affiche le contexte disponible (population, auto-écoles agréées / non agréées, routes classées) et la section l'indique ; rien n'est réparti au prorata de la population. Avec un fichier `data/processed/donnees_territoire.csv` (theme, annee, region, prefecture, valeur), les couches thématiques (nombre et pour 100 000 hab.) apparaissent, au niveau préfecture ou région (valeur régionale reportée sur les préfectures, jamais additionnée).
- Vue d'ensemble : la préfecture filtrée est mise en évidence sur la carte et dans le chiffre « Routes classées ».
- Tests : filtres partout, section territoire sans/avec fichier (fichier factice dans `tests/fixtures/`, réservé aux tests), fichier invalide.

## v5.2
- Diagnostic & recommandations : choisir une région dans les filtres recadre (zoom) la carte du score sur cette région, aux niveaux Préfecture et Région (contour bleu conservé) ; « Toutes les régions » rétablit la vue nationale.
- Routes & auto-écoles : nouvelle section « Répartition des auto-écoles » — auto-écoles par région (agrégé) et par préfecture (détail), agréées et non agréées (agréée = agréée + antenne agréée), part d'agréées par région, liste des préfectures sans auto-école, tableau à deux onglets (région / préfecture) avec export CSV. Deux nouveaux filtres : « Agréées et non agréées » ou « Total agrégé » ; « Effectifs » ou « Pour 100 000 hab. ».
- Sécurité routière : nouvelle section « Accidents par type de véhicule » (accidents, blessés et morts par type, évolution annuelle, gravité, tableau et export). **Les données ouvertes fournies ne contiennent pas ce découpage** (accidents, blessés et morts n'existent qu'en total national annuel) : la section lit un fichier facultatif `data/processed/accidents_vehicule.csv` (annee, type_vehicule, accidents, blesses, morts) ; sans lui, elle l'indique et propose un modèle de fichier (`data/modeles/`). Aucune valeur n'est estimée.
- Données & méthode : 8 nouvelles fiches de graphiques (4 auto-écoles, 4 type de véhicule).
- Tests : zoom du diagnostic, répartition des auto-écoles (270 / 132 / 138), section type de véhicule avec et sans fichier (fichier factice dans `tests/fixtures/`, réservé aux tests), fichier mal formé.

## v5.1
- Vue d'ensemble et État du réseau : choisir une région dans les filtres recadre (zoom) la carte sur cette région ; « Toutes les régions » rétablit la vue nationale. Sur État du réseau, la région est aussi cerclée de bleu (les tracés de tronçons restent nationaux : l'état n'est pas connu par région).
- Menus Diagnostic et Recommandations fusionnés en « Diagnostic & recommandations » (8 menus) : diagnostic en haut, recommandations en dessous, filtres uniques (le filtre Thème rejoint la sidebar ; la région reste active au niveau Région car elle pilote les recommandations ; seule la préfecture est grisée). Nouvelle adresse : /diagnostic-recommandations.
- Infobulles ⓘ supprimées sur les cartes KPI (il n'en reste plus aucune dans le tableau de bord) ; test navigateur adapté.
- Sécurité routière : bandeau « Données nationales uniquement… » supprimé ; Diagnostic : bandeau « Exclus du score… » supprimé.
- Badge « Indicatif » supprimé des titres de sections (toutes les pages).
- Menus réorganisés, un menu = une analyse attendue : Vue d'ensemble (ex-Accueil) · Immatriculations · Permis · Sécurité routière · État du réseau · Routes & auto-écoles (ex-Carte) · Diagnostic & recommandations · Données & méthode.
- Permis : nouveaux panneaux « Répartition cumulée par catégorie » et « Croissance annuelle moyenne par catégorie ».
- Routes & auto-écoles : « Tableau région → préfecture » complété par une version graphique (treemap population × indicateur, heatmap des rangs par indicateur) ; tableau et export CSV conservés.
- Correctif Windows : page Données & méthode — `KeyError: 'tronçons_rattaches_differemment'` (fichiers JSON lus sans `encoding="utf-8"`, donc en cp1252) ; lectures forcées en UTF-8 et test de non-régression ajouté.

## v5
- Réseau routier : l'explorateur de tronçons est **cartographié** (carte des tracés colorés par état dominant + classement graphique des 14 tronçons les plus dégradés) ; 61 tronçons sur 84 ont un tracé ; filtres catégorie, état et recherche appliqués ; le tableau est supprimé.
- Infobulles supprimées sur les titres de sections et de filtres (conservées sur les KPI) ; bloc « Données des graphiques » supprimé en bas de page.
- Page Données & méthode : nouvel onglet « Fiches des graphiques » (question, lecture, détails, calcul, source, limite de chaque graphique, export CSV).
- Données : `routes.geojson` et `reseau_etat_troncons.csv` portent la clé de jointure des tronçons.

## v4
- Infobulles ⓘ allégées : Question, Lecture (chiffre à retenir, calculé) et Limite seulement (≈ 300 caractères au lieu de ≈ 900) ; les « Lecture » descriptives sont remplacées par la conclusion chiffrée de chaque graphique.
- Détails du graphique, calcul et source déplacés dans le bloc « Données des graphiques de cette page » (avec tableau et export CSV).

## v3
- Retrait du bandeau « Messages clés », du badge « Objectifs … du défi » sous les titres de page et de la ligne « Lecture » sous chaque graphique (la lecture reste dans l'infobulle ⓘ).
- Hauteurs de panneaux recalculées par rangée (mesure du contenu à 1670 et 1366 px) ; 0 débordement.

## v2 (version finale)
- Infobulles ⓘ : ligne « Détails » sur chaque graphique (séries, couleurs, pics et creux, effectifs, calculés sur les données) ; ouverture vers le haut, 106 positions testées.
- Diagnostic : trois lectures (pondéré, consensus des 6 configurations, zéros structurels classés à part) ; fréquence d'appartenance au quintile ; réserve affichée sur la sensibilité au rattachement.
- Contrôle spatial indépendant des noms (routes et auto-écoles vs polygones) ; alias Naki-Ouest ↔ Kpendjal-Ouest validé ; test de sensibilité au rattachement.
- Accessibilité : audit axe-core (0 violation), contraste AA (0 écart, graphiques compris), tableaux alternatifs et export CSV des graphiques, accès clavier aux infobulles.
- Cartes : clics réels testés (carte et classement), cadrage vérifié, repli OSM hors connexion, aucune requête réseau.
- Dépendance cachée à scipy supprimée (Spearman calculé sur les rangs) ; recette en environnement vierge (`tools/check_clean_env.py`).
- Outils de contrôle : check_overflow, check_contrast, check_a11y, check_geo_spatial, check_clean_env, check_perf ; tests AppTest et navigateur.

## v1
- 8 pages, données réelles (58 contrôles), diagnostic territorial, recommandations calculées, infobulles à 5 lignes.
