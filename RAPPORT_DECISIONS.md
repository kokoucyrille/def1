# RAPPORT_DECISIONS — Dashboard « Mobilité et sécurité routière au Togo » (Défi 1)

## 1. Ce qui a été construit
Dashboard Streamlit à 8 menus, un par analyse attendue du défi (Vue d'ensemble · Immatriculations · Permis · Sécurité routière · État du réseau · Routes & auto-écoles · Diagnostic & recommandations · Données & méthode),
construit à partir du template `dashboard_togo` (charte, polices embarquées, header/navbar/sidebar, grille de panneaux, dossier `views/`).
Aucune valeur inventée ni interpolée : tout vient de `data/raw/` via `tools/build_data.py`, qui échoue si une valeur de contrôle s'écarte de plus de 0,5 %.
Résultat : **58/58 valeurs de contrôle retrouvées**, test géographique **39/39** (0 orphelin, 0 doublon ; Lomé Commune fusionné dans Golfe).

> **Réorganisation des menus (v5.1)** : sur demande, chaque menu répond à une analyse attendue du défi ; « Accueil » devient « Vue d'ensemble » (un chiffre clé par analyse) ; « Parc & permis » est scindé en **Immatriculations** et **Permis** ; « Réseau routier » est scindé entre **État du réseau** (état par région, par catégorie, par tronçon) et **Routes & auto-écoles** (ex-« Carte » + linéaire par territoire + types de routes) ; le tableau région → préfecture a une **version graphique** (treemap et heatmap), le tableau et l'export CSV restant disponibles.
>
> **Version 5** : sur demande, (1) l'**explorateur de tronçons est cartographié** : carte des tracés colorés par état dominant (couleurs d'état fixes) et classement graphique des 14 tronçons les plus dégradés ; 61 des 84 tronçons ont un tracé (jointure par identifiant avec les routes classées), les 23 autres figurent seulement dans le classement ; (2) les infobulles des titres de sections et de filtres sont supprimées (les KPI gardent la leur) ; (3) le bloc « Données des graphiques » en bas de page est supprimé : les fiches complètes des graphiques sont dans Données & méthode, onglet « Fiches des graphiques ».
> **Version 4 (infobulles allégées)** : sur demande, les infobulles sont réduites à Question, Lecture et Limite ; détails, calcul et source passent dans le bloc « Données des graphiques ». **Version 3** : sur demande, le bandeau « Messages clés », le badge « Objectifs … du défi » sous les titres et la ligne « Lecture » sous chaque graphique ont été retirés des pages ; la lecture et les repères chiffrés restent dans les infobulles ⓘ, et les hauteurs de panneaux ont été resserrées en conséquence.

## 2. Décisions de méthode (défauts appliqués, aucune question posée)
| Sujet | Décision |
|---|---|
| Régions | 6 régions RGPH 2022 (Grand Lomé = Golfe + Agoè-Nyivé) ; région déclarée dans routes/auto-écoles ignorée |
| Contours | `togo_prefectures.geojson` (« contours indicatifs ») ; alias vérifiés : Avé↔Totoal Ave, Plaine du Mô↔Mô, **Naki-Ouest↔Kpendjal-Ouest (par chef-lieu), validé spatialement : 97,6 % des km des routes déclarées Kpendjal-Ouest tombent dans ce polygone** (`tools/check_geo_spatial.py`) |
| Véhicules | « Voitues » corrigé ; deux-roues = « 2 roues et assimilées » ; poids lourds = camions + semi-remorques + tracteurs ; série nommée « Véhicules immatriculés (série annuelle fournie) » (baisse de 13 % en 2020 : stock/flux ambigu) ; ratios par véhicule « Indicatif » |
| Permis | 2013 = donnée manquante (rupture annotée, barre vide, exclu des cumuls) ; on compare tendances (base 100) ou parts, jamais des niveaux |
| Accidents | national et annuel seulement, jamais territorialisés ; série « Accidents mortels /100 000 hab » du fichier source = en réalité tous les accidents : non utilisée telle quelle ; 2010 et 2015 annotés |
| État du réseau | 2020 seul ; lignes de total séparées des tronçons (**la ligne de total des routes en terre s'appelle « TOTAL RT »**, d'où 84 tronçons = 52 + 32) ; travaux inclus dans le total ; estimation régionale exploratoire : « Indicatif », couverture affichée (0 % Grand Lomé → 90,6 % Kara), hors score |
| Routes classées | longueur calculée en EPSG:32631 (3 366 km) ; « revêtue » = Bitume/Béton/Pavé par défaut, définition administrative en filtre ; fichier non daté → filtre « Non daté » grisé |
| Auto-écoles | 2 « Néant » exclues (270 retenues dont 132 agréées) ; bascule toutes/agréées |
| Diagnostic | rangs percentiles ; zéro route ou zéro auto-école = rang le plus défavorable (« zéro structurel », jamais NaN) ; seuils fixes 0,80 et 2/3 ; sécurité et état du réseau exclus |
| Contrôle spatial | Indépendant des noms : 84,8 % des km de routes classées et 243/270 auto-écoles (tolérance 1 km) tombent dans le polygone de la préfecture déclarée. Écarts connus, **non corrigés** (rattachement par attributs conservé, contours indicatifs) : 3 tronçons déclarés Akébou (10,8 km) tombent dans Wawa ; 29/70 auto-écoles d'Agoè-Nyivé tombent dans Golfe (sans effet au niveau région) |
| Score | Au choix : pondéré (curseur) ou **consensus** (moyenne des 6 configurations) ; fréquence d'appartenance au quintile affichée (x/6) |
| Cartes | **Plotly `Choroplethmap`/`Scattermap` en style `white-bg`** : aucune requête externe. (`Choropleth`/`Scattergeo` ont été écartés : ils téléchargent un fond topojson sur cdn.plot.ly.) Option « Fond OpenStreetMap » via Folium avec repli hors connexion |

### Infobulles et fiches
Seuls les **KPI** portent une infobulle courte (survol et clavier) : Question, Lecture (le chiffre à retenir, calculé) et Limite. Les titres de sections et de filtres n'en ont plus. La documentation complète de chaque graphique (question, lecture, détails, calcul, source, limite) est dans l'onglet « Fiches des graphiques » de la page Données & méthode, exportable en CSV.

## 3. Ce que disent les données (chiffres calculés)
- Immatriculations 20 553 (2002) → 93 770 (2022), ×4,56 ; deux-roues 42,0 % → 72,1 %, ≈ 80,6 % de la hausse.
- Permis A = 5,1 % des permis cumulés 2007–2022 (hors 2013) ; 19,7 % en 2022 : la formation ne suit pas l'usage.
- Accidents ×2,4 et morts +45 % depuis 2010 (à nuancer : 2010 bas) ; morts pour 100 accidents 15,2 → 9,1 (gravité apparente en baisse : hypothèse de meilleure déclaration, non vérifiable).
- Corrélation de rang deux-roues/morts : ρ = 0,15 (n = 13) : faible, non causale.
- Routes revêtues 2020 : 34 % bon, 26 % mauvais, 20 % en travaux.
- Grand Lomé : 27 % de la population, ≈ 5 % du linéaire classé, ≈ 79 % des auto-écoles ; 15 préfectures sans auto-école, 1 sans route classée (Mô).
- Diagnostic : région la plus défavorable = Maritime (50/50). Préfectures stables dans le quintile défavorable aux 6 configurations : Akébou, Mô. À 20/80, 15 préfectures entrent dans le quintile (les zéros auto-école pèsent lourd) : seules les unités stables sont des conclusions robustes.

- **Conclusions robustes du diagnostic** : seuls **Mô** (aucune route classée ni auto-école) et **Akébou** (aucune auto-école, 10,8 km de routes déclarées) restent dans le quintile défavorable aux 6 configurations de pondération/auto-écoles **et** quel que soit le rattachement (administratif ou géographique). Une fois les 15 zéros structurels classés à part, **Anié** est la seule unité mesurée stable aux 6 configurations, mais elle ne l'est plus avec un rattachement géographique (aucune unité stable) : Anié, Zio, Yoto et Bas-Mono sont des **pistes à confirmer**, pas des conclusions.

## 4. Dix chiffres clés pour le PowerPoint
1. 93 770 véhicules immatriculés en 2022 (×4,56 vs 2002)
2. 72,1 % de deux-roues (contre 42,0 % en 2002)
3. ≈ 80,6 % de la hausse 2002–2022 portée par les deux-roues
4. 5,1 % de permis A dans les permis cumulés 2007–2022
5. 7 507 accidents et 683 morts en 2022
6. 8,4 morts pour 100 000 habitants (Indicatif)
7. 26 % des routes revêtues en mauvais état en 2020 (20 % en travaux)
8. 4,16 km de routes classées pour 10 000 habitants (Grand Lomé : 0,74)
9. Grand Lomé : 27 % de la population, ≈ 79 % des auto-écoles
10. 15 préfectures sans auto-école recensée

## 5. Limites
Immatriculations (stock/flux) · permis (2013 manquant, flux ≠ conducteurs) · accidents (national, n = 13) · état du réseau (2020, sans région, jointure partielle) · population d'une seule année ·
contours reconstitués · routes et auto-écoles non datées · recensement des auto-écoles possiblement incomplet hors Grand Lomé.

## 6. Auto-évaluation sévère (version finale)
| Critère | Note | Preuves |
|---|---|---|
| C1 Ergonomie | **3,5/4** | 8 pages, ⓘ sur les KPI, fiches complètes des graphiques dans Données & méthode, 0 débordement, **audit de contraste WCAG AA : 0 combinaison sous le seuil (graphiques inclus)**, **audit axe-core : 0 violation WCAG A/AA** (hors un attribut `aria-expanded` posé par Streamlit sur sa propre sidebar, non modifiable), infobulles au clavier, tableaux alternatifs des graphiques, cartes non rognées à 1670×942 et 1366×768. |
| C2 Pertinence, données, conclusions | **7,5/8** | 58 contrôles OK, pièges traités, contrôle spatial, **test de sensibilité au rattachement** (conclusions robustes séparées des pistes), trois lectures du diagnostic, limites écrites. |
| C3 Interactions et filtres | **4/4** | 36 combinaisons de filtres sans exception ; clic réel carte et classement (pixels de polygone) ; repli OSM hors connexion testé ; filtres sans effet grisés ; réponse < 1 s. |

**Recette finale (copie neuve du ZIP)** : reconstruction de `data/processed` depuis `data/raw` reproductible (58/58 contrôles, 0 fichier différent) ; 13 tests OK ; contraste AA : 0 écart ; axe-core : 0 violation ; 0 débordement ; **environnement Python vierge (`requirements.txt` seul) : 8 pages sans exception** (`tools/check_clean_env.py`). Cette recette a révélé une dépendance cachée à `scipy` (corrélation de Spearman calculée par pandas) : corrigée en calculant la corrélation sur les rangs (résultat identique, ρ = 0,149).
**Performance mesurée** (Chromium, `tools/check_perf.py`) : tous les graphiques sont dessinés en 2,0 à 3,3 s selon la page à chaud (ancienne page Parc & permis 2,7–3,2 s, mesurée avant la réorganisation des menus ; Diagnostic 3,1–3,3 s) ; réponse à un filtre ≈ 0,6 s ; premier chargement à froid ≈ 4,5 s (hors objectif). Une mesure qui inclut l'attente de réseau inactif donne 0,5 s de plus.

**Corrigé au dernier tour** : audit axe-core (légendes à opacité réduite corrigées) ; consensus et robustesse étendus au mode « zéros classés à part » ; **test de sensibilité au rattachement** (146 tronçons et 35 auto-écoles rattachés différemment) qui a montré que le quintile hors zéros structurels n'est pas robuste, d'où une réserve affichée dans la page Diagnostic et dans Données & méthode.

**Défauts restants (5)**
1. Le premier chargement à froid prend ≈ 4,5 s (objectif < 3 s tenu à ≈ 0,3 s près seulement à chaud : 2,0–3,3 s).
2. Les contours restent indicatifs : pour Akébou, Agoè-Nyivé et quelques préfectures, attributs et géométrie ne concordent pas (voir `controle_spatial.csv`) ; seul un fond cartographique officiel permettrait de trancher.
3. Aucun test avec un vrai lecteur d'écran (seulement axe-core) ; les graphiques n'ont plus de tableau alternatif en bas de page (supprimé à la demande) : les valeurs sont dans les exports de la page Données & méthode et dans le tableau région → préfecture de la page Carte.
4. L'option « Fond OpenStreetMap » (Folium) n'a pas pu être testée en ligne (environnement sans Internet) : seul le repli hors connexion est vérifié.
5. Le recensement des auto-écoles hors Grand Lomé est possiblement incomplet ; un zéro peut être une absence d'enregistrement, ce qui conditionne les « zéros structurels ».
