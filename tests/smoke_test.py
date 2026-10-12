"""
Test de fumée (Streamlit AppTest) : python tests/smoke_test.py   (ou pytest)

Vérifie : chaque page s'exécute avec les filtres par défaut puis avec ≥ 10 combinaisons de filtres, sans exception ;
géo 39/39 ; chaque panneau et chaque KPI a son infobulle (une entrée manquante dans data/docs.py lève une exception) ;
valeurs de contrôle affichées dans l'interface ; aucun reste du sujet précédent dans le code.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from streamlit.testing.v1 import AppTest  # noqa: E402

PAGES = ["vue_ensemble", "immat", "permis", "securite", "etat_reseau", "routes_ae", "diagnostic", "donnees"]   # un menu = une analyse attendue
FICHIER = {"immat": "immatriculations", "routes_ae": "routes_auto_ecoles"}   # clé de page -> fichier de views/ quand ils diffèrent
COMBOS = {  # (page, widget, valeur) appliqués successivement : au moins 10 combinaisons
    "vue_ensemble": [{"annee": 2015}, {"region": "Kara"}, {"annee": 2013, "region": "Savanes"}],
    "immat": [{"periode": (1990, 2022)}, {"mode": "Base 100"}, {"mode": "Parts", "veh": ["Deux-roues", "Voitures"]}, {"periode": (2012, 2014), "mode": "Volumes"}, {"veh": ["Poids lourds"]}],
    "permis": [{"periode": (2007, 2022)}, {"mode": "Base 100"}, {"mode": "Parts", "permis": ["Moto (A)", "Voiture légère (B)"]}, {"periode": (2012, 2014), "mode": "Volumes"}, {"periode": (2013, 2013)}, {"permis": ["Moto (A)"]}],
    "securite": [{"indic": "Accidents"}, {"base": "Pour 100 000 hab. (pop. 2022)"}, {"base": "Brut", "indic": "Blessés"}, {"periode": (2014, 2018)}],
    "etat_reseau": [{"cat": "Routes revêtues"}, {"cat": "Voiries en terre"}, {"etats": ["MAUVAIS"]}, {"q": "KARA"}, {"q": "zzzz"}, {"region": "Kara"}],
    "routes_ae": [{"ae_vue": "Total agrégé"}, {"ae_mode": "Pour 100 000 hab."}, {"region": "Savanes", "ae_vue": "Total agrégé", "ae_mode": "Pour 100 000 hab."}, {"indic": "Part de routes non revêtues"}, {"indic": "Habitants par auto-école"}, {"statut": "Agréées"}, {"couches": ["Auto-écoles"]}, {"couches": ["Réseau routier"], "types": ["Piste rurale"]}, {"defn": "Type administratif"}, {"types": ["Voirie urbaine"]}, {"indic": "Score du diagnostic (50/50)"}, {"indic": "Population (RGPH 2022)"}, {"region": "Kara"}, {"osm": True}],
    "diagnostic": [{"niveau": "Région"}, {"poids": 20}, {"poids": 80, "ae": "Agréées"}, {"seuil": "Tercile défavorable (≥ 2/3)"}, {"score_mode": "Consensus (6 configurations)"}, {"niveau": "Région", "score_mode": "Consensus (6 configurations)"}, {"zeros": "Classés à part (hors score)"}, {"zeros": "Classés à part (hors score)", "poids": 80, "ae": "Agréées"},
                   {"theme": "Formation des conducteurs"}, {"theme": "Entretien du réseau"}, {"region": "Kara", "theme": "Sécurité & deux-roues"}, {"niveau": "Région", "region": "Maritime"}],
    "donnees": [],
}
SHARED = {"etat_reseau", "routes_ae", "diagnostic"}
CONTROLES = {"vue_ensemble": ["93\u00a0770", "24\u00a0598", "7\u00a0507", "683"], "immat": ["93\u00a0770", "72,1"], "permis": ["24\u00a0598"]}
FORBIDDEN = re.compile("|".join(["mobile" + " money", "opé" + "rateur", "zones" + " blanches", "Togo" + " Numérique", "syn" + "th"]), re.I)


def run_page(page: str, **filters):
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120)
    at.run()
    at.switch_page(f"views/{FICHIER.get(page, page)}.py")
    at.run()
    for k, v in filters.items():
        key = f"w_{page}_{k}"
        w = next((x for x in list(at.sidebar.selectbox) + list(at.sidebar.multiselect) + list(at.sidebar.radio) + list(at.sidebar.slider) + list(at.sidebar.text_input) + list(at.sidebar.checkbox) if x.key == key), None)
        assert w is not None, f"filtre introuvable : {key}"
        w.set_value(v)
        at.run()
    return at


def texte(at) -> str:
    return " ".join([m.value for m in at.markdown] + [str(e.value) for e in at.get("text")])


def test_defaults():
    for p in PAGES:
        at = run_page(p)
        assert not at.exception, (p, [e.value[:300] for e in at.exception])
        html = texte(at)
        assert not re.search(r'class="panel-title">(?:(?!</div>).)*class="tip', html, flags=re.S), f"infobulle sur un titre de panneau : {p}"
        assert not any('f-label' in m.value and 'class="tip' in m.value for m in at.sidebar.markdown), f"infobulle sur un titre de filtre : {p}"
        assert "Données des graphiques" not in " ".join(e.label for e in at.expander), f"bloc de données des graphiques encore présent : {p}"
        assert "Messages clés" not in html and "Objectifs" not in html and 'class="lecture"' not in html, f"éléments supprimés encore présents : {p}"


def test_fiches_graphiques():
    """La documentation de chaque graphique (Question, Lecture, Détails, Calcul, Source, Limite) est dans Données & méthode."""
    from data.docs import TITRES, fiches
    fi = fiches()
    assert len(fi) == len(TITRES) >= 30 and all(r["Question"] and r["Lecture"] and r["Calcul"] and r["Source"] and r["Limite"] for r in fi)
    at = run_page("donnees")
    assert not at.exception and any(e.label.startswith("État du réseau — Explorateur de tronçons") for e in at.expander)


def test_explorateur_troncons_graphique():
    """L'explorateur de tronçons est une carte + un classement (plus de tableau) ; 61 tronçons sur 84 ont un tracé."""
    import pandas as pd
    at = run_page("etat_reseau")
    assert not at.exception and len(at.dataframe) == 0, "tableau encore présent dans l'explorateur"
    t = pd.read_csv(ROOT / "data/processed/reseau_etat_troncons.csv")
    assert len(t) == 84 and t.apparie_routes_classees.sum() == 61


def test_combinations():
    n = 0
    for p, combos in COMBOS.items():
        for c in combos:
            at = run_page(p, **c)
            assert not at.exception, (p, c, [e.value[:300] for e in at.exception])
            n += 1
    assert n >= 10, n
    print(f"{n} combinaisons de filtres sans exception")


def test_valeurs_de_controle():
    for page, valeurs in CONTROLES.items():
        html = texte(run_page(page)).replace("\xa0", "\u00a0")
        for v in valeurs:
            assert v in html, f"valeur de contrôle absente de la page {page} : {v}"


def _carte(at, key: str) -> dict:
    """Disposition (center, zoom) de la carte Plotly `key` rendue par la page."""
    import json as _j
    for el in at.get("plotly_chart"):
        if el.proto.id and key in str(el.key):
            return _j.loads(el.proto.spec)["layout"]["map"]
    raise AssertionError(f"carte introuvable : {key}")


def test_cartes_zoom_region():
    """Vue d'ensemble et État du réseau : choisir une région recadre la carte sur cette région (zoom plus fort, centre déplacé)."""
    for page, key in (("vue_ensemble", "acc_map"), ("etat_reseau", "res_troncons_map"), ("diagnostic", "diag_map")):
        nat = _carte(run_page(page), key)
        for region in ("Kara", "Savanes"):
            reg = _carte(run_page(page, region=region), key)
            assert reg["zoom"] > nat["zoom"] + 0.4, (page, region, nat["zoom"], reg["zoom"])
            assert (reg["center"]["lat"], reg["center"]["lon"]) != (nat["center"]["lat"], nat["center"]["lon"]), (page, region)
        # retour à « Toutes les régions » : cadrage national retrouvé
        at = run_page(page, region="Kara")
        at.sidebar.selectbox(key=f"w_{page}_region").set_value("Toutes les régions").run()
        back = _carte(at, key)
        assert abs(back["zoom"] - nat["zoom"]) < 1e-6, (page, back["zoom"], nat["zoom"])


def test_un_menu_par_analyse_attendue():
    """8 menus : vue d'ensemble, les 6 analyses attendues du défi (diagnostic et recommandations réunis), données ; chaque fiche de graphique est rattachée à un menu."""
    import re as _re
    from data.docs import TITRES
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert len(_re.findall(r"st\.Page\(", app)) == len(PAGES) == 8
    menus = [t.split(" — ")[0] for t in TITRES.values()]
    assert list(dict.fromkeys(menus)) == ["Vue d'ensemble", "Immatriculations", "Permis", "Sécurité routière", "État du réseau", "Routes & auto-écoles", "Diagnostic & recommandations"]
    nav = (ROOT / "components" / "navbar.py").read_text(encoding="utf-8")
    for m in ("Vue d'ensemble", "Immatriculations", "Permis", "Sécurité routière", "État du réseau", "Routes & auto-écoles", "Diagnostic & recommandations", "Données & méthode"):
        assert f'("{m}"' in nav, m


def test_routes_ae_vue_graphique():
    """Le tableau région → préfecture a une version graphique (treemap + heatmap) ; le tableau et l'export CSV restent disponibles."""
    at = run_page("routes_ae")
    assert not at.exception, [e.value[:300] for e in at.exception]
    html = texte(at)
    assert "Région → préfecture" in html and "Profil des préfectures" in html
    assert any("Tableau région → préfecture" in e.label for e in at.expander)
    at = run_page("routes_ae", region="Kara")
    assert not at.exception and "Profil des préfectures" in texte(at)


def test_geo_39():
    import json
    g = json.loads((ROOT / "data/processed/geo_test.json").read_text(encoding="utf-8"))
    assert (g["appariees"], g["orphelins"]) == (39, 0)
    import pandas as pd
    m = pd.read_csv(ROOT / "data/processed/geo_match.csv")
    assert m.cle_rgph.nunique() == 39 and (m.statut != "ORPHELIN").all()


def test_controle_spatial():
    import json
    sp = json.loads((ROOT / "data/processed/controle_spatial.json").read_text(encoding="utf-8"))
    assert sp["alias_naki_ouest_kpendjal_ouest_part_km"] >= 0.9, "alias Naki-Ouest ↔ Kpendjal-Ouest non validé spatialement"
    assert sp["routes_part_km_dans_polygone_decl"] >= 0.8 and sp["ae_dans_polygone_decl_tolerance_1km"] / sp["ae_total"] >= 0.85


def test_sensibilite_rattachement():
    import json
    se = json.loads((ROOT / "data/processed/sensibilite_rattachement.json").read_text(encoding="utf-8"))
    assert set(se["stables_attributs"]) == set(se["stables_geographique"]) == {"Akébou", "Mô"}, se   # conclusion robuste au rattachement


def test_consensus_et_robustesse():
    import json
    import pandas as pd
    from data import diag
    pref = pd.read_csv(ROOT / "data/processed/population_prefectures.csv")
    det = pd.read_csv(ROOT / "data/processed/routes_detail.csv"); ae = pd.read_csv(ROOT / "data/processed/auto_ecoles.csv")
    cons = diag.consensus(pref, det, ae, "Préfecture")
    st = json.loads((ROOT / "data/processed/robustesse_stables.json").read_text(encoding="utf-8"))["stables"]
    assert len(cons) == 39 and cons.n_quintile.between(0, 6).all()
    assert set(st) == set(cons.loc[cons.n_quintile == 6, "prefecture"]), (st, cons[cons.n_quintile == 6].prefecture.tolist())


def test_zeros_a_part():
    import pandas as pd
    from data import diag
    pref = pd.read_csv(ROOT / "data/processed/population_prefectures.csv")
    det = pd.read_csv(ROOT / "data/processed/routes_detail.csv"); ae = pd.read_csv(ROOT / "data/processed/auto_ecoles.csv")
    t = diag.table_territoire(pref, det, ae, "Préfecture", "Toutes")
    d = diag.diagnostic(t, 0.5, zeros_a_part=True)
    z = d[d.zero_structurel]
    assert len(z) == 15 and z.score.isna().all() and not z.quintile_defavorable.any()
    assert d.loc[~d.zero_structurel, "score"].notna().all() and d.score.max() <= 1


def test_controles_build():
    import pandas as pd
    c = pd.read_csv(ROOT / "data/processed/controles.csv")
    assert (c.statut == "OK").all(), c[c.statut != "OK"]


def test_pas_de_reste_du_sujet_precedent():
    bad = []
    for p in list(ROOT.glob("*.py")) + list((ROOT / "components").glob("*.py")) + list((ROOT / "views").glob("*.py")) + list((ROOT / "data").glob("*.py")):
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if FORBIDDEN.search(line):
                bad.append(f"{p.relative_to(ROOT)}:{i}")
    assert not bad, bad


def test_docs_completes():
    from data.docs import DOCS
    from data.loader import facts
    for k, e in DOCS().items():
        assert all(e[x] for x in ("q", "calc", "src", "lim")), k
        assert callable(e["lec"]) or e["lec"], k
        if not k.startswith("kpi_"):
            assert callable(e.get("det")) and len(e["det"](facts())) > 60, f"détails manquants pour le graphique {k}"


def test_navigateur():
    """Clic carte/classement, clavier, cadrage : tests/browser_test.py (nécessite Playwright + Chromium)."""
    import subprocess
    r = subprocess.run([sys.executable, str(ROOT / "tests" / "browser_test.py")], capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-1500:]


def test_diagnostic_zoom_niveau_region():
    """Diagnostic : la carte zoome aussi quand on choisit une région au niveau « Région » (et revient au cadrage national)."""
    nat = _carte(run_page("diagnostic"), "diag_map")
    reg = _carte(run_page("diagnostic", niveau="Région", region="Kara"), "diag_map")
    assert reg["zoom"] > nat["zoom"] + 0.4 and reg["center"] != nat["center"]


def test_repartition_auto_ecoles():
    """Routes & auto-écoles : section « Répartition des auto-écoles » (région agrégée + préfecture détaillée, agréées / non agréées) cohérente avec les 270 auto-écoles."""
    from data import loader as L
    ar, ap = L.ae_repartition("Région"), L.ae_repartition("Préfecture")
    for t in (ar, ap):
        assert (t.total, t.agreees, t.non_agr) and t.total.sum() == 270 and t.agreees.sum() == 132 and t.non_agr.sum() == 138 and (t.agreees + t.non_agr == t.total).all()
        assert (t.agr_princ + t.antenne == t.agreees).all()
    assert len(ar) == 6 and len(ap) == 39 and (ap.total == 0).sum() == 15
    for kw in ({}, {"ae_vue": "Total agrégé"}, {"ae_mode": "Pour 100 000 hab."}, {"region": "Kara"}):
        at = run_page("routes_ae", **kw)
        assert not at.exception, (kw, [e.value[:300] for e in at.exception])
        html = texte(at)
        assert "Répartition des auto-écoles" in html and "Sans auto-école recensée" in html
        assert [t.label for t in at.tabs][:2] == ["Par région (agrégé)", [t.label for t in at.tabs][1]] and at.tabs[1].label.startswith("Par préfecture (non agrégé)")


def test_filtres_region_prefecture_partout():
    """Région et Préfecture sont proposées dans tous les menus d'analyse (sauf Données & méthode, et État du réseau : région seule, l'état n'a pas de préfecture)."""
    for page in ("vue_ensemble", "immat", "permis", "securite", "routes_ae", "diagnostic"):
        labels = [w.label for w in run_page(page).sidebar.selectbox]
        assert "Région" in labels and "Préfecture" in labels, (page, labels)
    assert "Région" in [w.label for w in run_page("etat_reseau").sidebar.selectbox]


def test_territoire_sans_fichier():
    """Immatriculations / Permis / Sécurité : section « Données par territoire » réduite à la carte et aux KPI du menu ; aucun KPI « n.d. », aucun graphique ni tableau en dessous."""
    from data import territoire as TT
    ancien = TT.TERR_PATH
    try:
        TT.TERR_PATH = ROOT / "tests" / "fixtures" / "inexistant.csv"
        attendu = {"immat": "Population (RGPH 2022)", "permis": "Auto-écoles agréées / non agréées", "securite": "Part de routes non revêtues"}
        for page, kw in (("immat", {}), ("permis", {"couche": "Auto-écoles pour 100 000 hab."}), ("securite", {"region": "Kara"}), ("securite", {"region": "Kara", "pref": "Kozah"})):
            at = run_page(page, **kw)
            assert not at.exception, (page, [e.value[:300] for e in at.exception])
            html = texte(at)
            assert "Données par territoire" in html and attendu[page] in html, page
            sec = html.split("Données par territoire")[-1]                                   # texte de la section seule (les aides des filtres sont hors section)
            assert "par territoire" not in sec and "niveau national" not in sec and "n.d." not in sec, (page, sec[:300])
            assert not [t for t in at.tabs if t.label.startswith("Par région")] and "Classement —" not in html
    finally:
        TT.TERR_PATH = ancien
    b = TT.base()
    assert len(b) == 39 and b.population.sum() == 8095498 and b.total.sum() == 270 and b.agreees.sum() == 132


def test_territoire_avec_fichier():
    """Avec un fichier territorial valide : couches thématiques, niveau préfecture et niveau région (jamais de double compte), pages sans erreur."""
    from data import territoire as TT
    ancien = TT.TERR_PATH
    try:
        TT.TERR_PATH = ROOT / "tests" / "fixtures" / "donnees_territoire_FACTICE.csv"        # valeurs factices, réservées à ce test
        d, err = TT.donnees()
        assert err is None and set(d.theme) == {"permis", "immatriculations", "accidents", "blesses", "morts"}
        assert TT.couches("permis")[0] == "Permis délivrés (période)" and "Morts pour 100 000 hab." in TT.couches("securite")
        sp = TT.serie_theme("permis", 2018, 2022)
        assert sp["niveau"] == "préfecture" and len(sp["valeurs"]) == 39 and sp["valeurs"].sum() == d[(d.theme == "permis")].valeur.sum()
        sm = TT.serie_theme("morts", 2018, 2022)
        assert sm["niveau"] == "région" and len(sm["valeurs"]) == 6 and sm["valeurs"].sum() == d[d.theme == "morts"].valeur.sum()
        assert TT.serie_theme("morts", 2010, 2012) is None
        c = TT.couche("securite", "Morts (période)", 2018, 2022)["df"]
        assert (c.groupby("region").val.nunique() == 1).all()                              # valeur régionale reportée à l'identique sur chaque préfecture
        for page, kw in (("permis", {"couche": "Permis délivrés pour 100 000 hab.", "region": "Kara"}), ("immat", {"couche": "Immatriculations (période)"}),
                         ("securite", {"couche": "Morts (période)", "region": "Savanes", "pref": "Tône"}), ("securite", {"couche": "Accidents pour 100 000 hab.", "periode": (2010, 2014)})):
            at = run_page(page, **kw)
            assert not at.exception, (page, kw, [e.value[:300] for e in at.exception])
            assert "Données par territoire" in texte(at)
        assert "Permis délivrés 2007–2022" in texte(run_page("permis"))                       # KPI thématique présent seulement quand le fichier le fournit
    finally:
        TT.TERR_PATH = ancien


def test_territoire_fichier_invalide(tmp_path):
    """Fichier territorial mal formé : message lisible (colonnes, thèmes, préfectures, régions inconnus), pas d'exception."""
    from data import territoire as TT
    cas = {"colonnes": ("theme,annee\npermis,2020\n", "Colonnes manquantes"),
           "theme": ("theme,annee,region,prefecture,valeur\nvelos,2020,Kara,,5\n", "Thèmes inconnus"),
           "pref": ("theme,annee,region,prefecture,valeur\npermis,2020,,Nulle-part,5\n", "Préfectures inconnues"),
           "region": ("theme,annee,region,prefecture,valeur\npermis,2020,Atlantide,,5\n", "Régions inconnues")}
    for nom, (txt, attendu) in cas.items():
        f = tmp_path / f"{nom}.csv"; f.write_text(txt, encoding="utf-8")
        d, err = TT._lire(str(f), 1.0)
        assert d is None and attendu in err, (nom, err)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); print("OK", name)


def test_lectures_texte_en_utf8():
    """Régression Windows : `read_text()` sans encoding lit en cp1252 et casse les clés accentuées (ex. « tronçons_… » -> KeyError)."""
    import re
    bad = []
    for p in ROOT.rglob("*.py"):
        if "tests" in p.parts and p.name == "smoke_test.py":
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"\.read_text\(\s*\)", line) or re.search(r"open\([^)]*[\"'][wra]\+?[\"']\s*\)", line):
                bad.append(f"{p.relative_to(ROOT)}:{i}")
    assert not bad, f"lecture/écriture de fichier texte sans encoding='utf-8' : {bad}"
