"""Génère data/processed/recommandations.json : 3 priorités × 3 actions, pour le national et chacune des 6 régions.
Tous les chiffres sont calculés à partir des tables de data/processed (aucune valeur saisie)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from data.loader import fmt_dec as d1, fmt_int as i0, fmt_pct as p1, facts  # noqa: E402

OUT = ROOT / "data" / "processed"


def liste(xs, n=6):
    xs = list(xs)
    return ", ".join(xs[:n]) + (f" (+{len(xs) - n})" if len(xs) > n else "")


def build() -> dict:
    F = facts()
    tp = pd.read_csv(OUT / "diagnostic_prefectures.csv")
    tr = pd.read_csv(OUT / "territoire_regions.csv").set_index("region")
    er = pd.read_csv(OUT / "etat_reseau_region_indicatif.csv").set_index("region")
    tron = pd.read_csv(OUT / "reseau_etat_troncons.csv")
    top = tron[tron.categorie == "ROUTES REVETUES"].sort_values("MAUVAIS", ascending=False).head(3)
    top_txt = "; ".join(f"{r.troncon} ({d1(r.MAUVAIS)} km)" for r in top.itertuples())
    res = {}
    for R in [None] + list(tr.index):
        d = tp if R is None else tp[tp.region == R]
        zae = d[d.zero_ae].sort_values("population", ascending=False)
        nat = R is None
        ou_loc = "National" if nat else R
        # --- priorité 1
        a1 = {"tag": "A1", "label": "Programme national deux-roues",
              "constat": f"Deux-roues = {p1(F['part2r_22'])} des immatriculations 2022 ({p1(F['part2r_02'])} en 2002), ≈ {p1(F['part_hausse_2r'])} de la hausse ; {i0(F['morts22'])} morts en 2022 ({'+' if F['morts_var'] >= 0 else '−'}{d1(abs(F['morts_var']), 0)} % vs 2010).",
              "ou": "National (accidents non territorialisés)" + ("" if nat else f" ; {R} : {p1(100 * tr.loc[R, 'population'] / F['pop'])} de la population, à cibler après production des données par préfecture"),
              "action": "Casque et équipement obligatoires contrôlés, contrôles routiers ciblés sur les deux-roues, campagnes de prévention.",
              "indicateur": f"Morts pour 100 000 hab. ({d1(F['morts100k22'])} en 2022)", "horizon": "12 à 24 mois"}
        a2 = {"tag": "A2", "label": "Accidents par préfecture",
              "constat": f"{i0(F['acc22'])} accidents et {i0(F['morts22'])} morts en 2022, publiés uniquement au niveau national : aucun ciblage territorial n'est possible.",
              "ou": f"{len(d)} préfecture(s) : {liste(d.prefecture)}", "action": "Géolocaliser chaque accident et publier chaque année accidents, blessés et morts par préfecture.",
              "indicateur": "Part des accidents géolocalisés (objectif 100 %)", "horizon": "12 mois"}
        a3 = {"tag": "A3", "label": "Fiabiliser la gravité",
              "constat": f"Accidents ×{d1(F['acc_x'])} depuis 2010 mais morts pour 100 accidents de {d1(F['morts100acc10'])} à {d1(F['morts100acc22'])} : amélioration réelle ou meilleure déclaration, non démontrable.",
              "ou": "National", "action": "Harmoniser la déclaration (police, santé) et réviser la série 2010–2022.", "indicateur": "Morts pour 100 accidents, série révisée", "horizon": "12 à 18 mois"}
        # --- priorité 2
        nA = int(tr.ae_toutes.sum()) if nat else int(tr.loc[R, "ae_toutes"]); nAg = int(tr.ae_agreees.sum()) if nat else int(tr.loc[R, "ae_agreees"])
        b1 = {"tag": "B1", "label": "Combler l'écart permis A / deux-roues",
              "constat": f"Permis A = {p1(F['part_A_cumul'])} des permis délivrés 2007–2022 (hors 2013) contre {p1(F['part2r_22'])} des immatriculations de deux-roues en 2022.",
              "ou": f"{ou_loc} : {nA} auto-école(s) recensée(s), dont {nAg} agréée(s)", "action": "Ouvrir des sessions d'examen et de formation au permis A, diffuser une offre accessible (coût, délais).",
              "indicateur": f"Part du permis A dans les permis délivrés ({p1(F['part_A22'])} en 2022)", "horizon": "24 mois"}
        b2 = {"tag": "B2", "label": "Couvrir les préfectures sans auto-école",
              "constat": f"{len(zae)} préfecture(s) sans auto-école recensée{'' if nat else f' dans {R}'}" + (f" sur {F['n_sans_ae']} au niveau national" if not nat else "") + ".",
              "ou": liste(zae.prefecture) if len(zae) else "Aucune préfecture sans auto-école dans cette région", "action": "Créer des antennes agréées ou des auto-écoles mobiles et un centre d'examen par préfecture non couverte.",
              "indicateur": f"Préfectures sans auto-école ({len(zae)} → 0)", "horizon": "24 à 36 mois"}
        w = d.sort_values("score_formation", ascending=False).head(4)
        b3 = {"tag": "B3", "label": "Rééquilibrer l'offre de formation",
              "constat": f"Grand Lomé : {p1(F['gl_part_pop'], 0)} de la population et {p1(F['gl_part_ae'], 0)} des auto-écoles ; {i0(F['hab_par_ae_nat'])} hab. par auto-école au niveau national (Indicatif : sous-recensement possible hors Lomé).",
              "ou": "Plus forts déficits de formation : " + liste(w.prefecture), "action": "Incitations à l'agrément hors Grand Lomé et vérification terrain du recensement.",
              "indicateur": "Habitants par auto-école, par région", "horizon": "36 mois"}
        # --- priorité 3
        c1 = {"tag": "C1", "label": "Prioriser les tronçons dégradés",
              "constat": f"Routes revêtues 2020 : {p1(F['pct_bon_rev'], 0)} bon, {p1(F['pct_mauvais_rev'], 0)} mauvais, {p1(F['pct_travaux_rev'], 0)} en travaux. Tronçons les plus dégradés : {top_txt}."
                         + ("" if nat else (f" {R} (Indicatif, couverture {d1(100 * er.loc[R, 'couverture'], 0)} %) : {p1(100 * er.loc[R, 'part_mauvais'], 0)} de mauvais état." if er.loc[R, "couverture"] > 0 else f" {R} : état non renseigné (0 % de couverture).")),
              "ou": "Tronçons nommés (état national 2020, sans région)", "action": "Programme d'entretien périodique ciblé sur les tronçons en mauvais état avant leur dégradation complète.",
              "indicateur": f"Part de routes revêtues en mauvais état ({p1(F['pct_mauvais_rev'])} en 2020)", "horizon": "12 à 36 mois"}
        low = d.sort_values("km_10k").head(4)
        c2 = {"tag": "C2", "label": "Compléter le linéaire classé",
              "constat": f"{d1(F['km_10k_nat'], 2)} km classés pour 10 000 hab. au niveau national ; Grand Lomé {d1(tr.loc['Grand Lomé', 'km_10k'], 2)} ; {F['n_sans_route']} préfecture sans route classée ({', '.join(F['sans_route'])}).",
              "ou": "Plus faibles km / 10 000 hab. : " + liste(f"{r.prefecture} ({d1(r.km_10k, 2)})" for r in low.itertuples()),
              "action": "Inventorier et programmer les routes et voiries à classer dans ces préfectures (peu de voirie urbaine dans le fichier).",
              "indicateur": "km de routes classées pour 10 000 hab., par préfecture", "horizon": "24 à 48 mois"}
        c3 = {"tag": "C3", "label": "Étendre le suivi de l'état du réseau",
              "constat": f"L'état du réseau n'existe que pour 2020 et sans région ; jointure aux routes classées : couverture de {d1(100 * er.couverture.min(), 0)} % ({er.couverture.idxmin()}) à {d1(100 * er.couverture.max(), 1)} % ({er.couverture.idxmax()}).",
              "ou": ou_loc, "action": "Relever l'état annuellement avec les identifiants des routes classées, en couvrant d'abord les régions non renseignées.",
              "indicateur": "Couverture du linéaire classé par un état daté (objectif ≥ 80 % par région)", "horizon": "12 mois"}
        res["Toutes les régions" if nat else R] = {"themes": [
            {"id": "Sécurité & deux-roues", "title": "Priorité 1 — Sécurité & deux-roues", "icon": "fa-suitcase-medical", "actions": [a1, a2, a3]},
            {"id": "Formation des conducteurs", "title": "Priorité 2 — Formation des conducteurs", "icon": "fa-users", "actions": [b1, b2, b3]},
            {"id": "Entretien du réseau", "title": "Priorité 3 — Entretien du réseau", "icon": "fa-layer-group", "actions": [c1, c2, c3]}]}
    (OUT / "recommandations.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res


if __name__ == "__main__":
    r = build()
    print(len(r), "jeux de recommandations")
    for a in r["Toutes les régions"]["themes"][2]["actions"]:
        print(a["tag"], a["constat"])
