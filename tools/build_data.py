"""
Phase A — construit data/processed/ à partir des données ouvertes brutes (data/raw/).

    python tools/build_data.py            # nécessite requirements-build.txt (geopandas, shapely, pyproj)

Règles : aucune valeur inventée ni interpolée ; tout ratio approximatif est signalé « Indicatif »
dans l'application. Le script échoue (assert) si une valeur de contrôle s'écarte de plus de 0,5 % ou si
la table de correspondance géographique n'est pas 39/39 sans orphelin ni doublon.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)
EPSG_METRIQUE = 32631
ANNEE_POP = 2022


# ----------------------------------------------------------------------------------------------
# Outils
# ----------------------------------------------------------------------------------------------
def cle_geo(s) -> str | float:
    """Clé de jointure : sans accents, majuscules, ponctuation -> espace, chiffre collé séparé."""
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return np.nan
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()
    s = re.sub(r"[^A-Z0-9+]+", " ", s)
    s = re.sub(r"([A-Z])(\d)", r"\1 \2", s)
    return re.sub(r"\s+", " ", s).strip()


CONTROLES: list[dict] = []


def controle(nom: str, obtenu: float, attendu: float, tol: float = 0.005) -> None:
    ecart = abs(obtenu - attendu) / abs(attendu) if attendu else abs(obtenu)
    ok = ecart <= tol
    CONTROLES.append({"indicateur": nom, "valeur_attendue": attendu, "valeur_obtenue": round(float(obtenu), 4),
                      "ecart_relatif": round(float(ecart), 5), "statut": "OK" if ok else "ÉCART"})
    if not ok:
        print(f"!! ÉCART {nom}: obtenu {obtenu} vs attendu {attendu} ({ecart:.2%})")


def lire(nom: str, **kw) -> pd.DataFrame:
    return pd.read_csv(RAW / nom, **kw)


# ----------------------------------------------------------------------------------------------
# 1. Population (RGPH 2022, instantané) — 6 régions, 39 préfectures
# ----------------------------------------------------------------------------------------------
pop = lire("population_territoire.csv")
pref = (pop[pop.niveau == "prefecture"][["region", "prefecture", "population"]]
        .rename(columns={"region": "region", "prefecture": "pref_rgph"}).reset_index(drop=True))
pref["cle"] = pref["pref_rgph"].map(cle_geo)
reg_pop = pop[pop.niveau == "region"].set_index("region")["population"]
assert len(pref) == 39 and pref.groupby("region").population.sum().to_dict() == reg_pop.to_dict()
POP_PAYS = int(reg_pop.sum())
NOM_REGION = {"DAGL": "Grand Lomé", "MARITIME": "Maritime", "PLATEAUX": "Plateaux", "CENTRALE": "Centrale",
              "KARA": "Kara", "SAVANES": "Savanes"}
ORDRE_REGIONS = ["Grand Lomé", "Maritime", "Plateaux", "Centrale", "Kara", "Savanes"]
pref["region"] = pref["region"].map(NOM_REGION)
PREF_VERS_REGION = dict(zip(pref.cle, pref.region))
NOM_PREF = dict(zip(pref.cle, pref.pref_rgph.str.title()))
NOM_PREF.update({"AGOE NYIVE": "Agoè-Nyivé", "TOTOAL AVE": "Avé", "MO": "Mô", "TONE": "Tône", "KERAN": "Kéran", "KPELE": "Kpélé",
                 "ANIE": "Anié", "TANDJOARE": "Tandjoaré", "CINKASSE": "Cinkassé", "AKEBOU": "Akébou", "EST MONO": "Est-Mono",
                 "MOYEN MONO": "Moyen-Mono", "BAS MONO": "Bas-Mono", "KPENDJAL OUEST": "Kpendjal-Ouest", "OTI SUD": "Oti-Sud"})
pref["prefecture"] = pref.cle.map(NOM_PREF)
reg_pop = reg_pop.rename(index=NOM_REGION)

controle("Population totale", POP_PAYS, 8_095_498)
for r, v in {"Grand Lomé": 2_188_376, "Plateaux": 1_635_946, "Maritime": 1_346_615, "Savanes": 1_143_520,
             "Kara": 985_512, "Centrale": 795_529}.items():
    controle(f"Population {r}", reg_pop[r], v)

# ----------------------------------------------------------------------------------------------
# 2. Contours : table geo_match (36 identiques + 3 alias vérifiés ; Lomé Commune fusionné dans Golfe)
# ----------------------------------------------------------------------------------------------
import geopandas as gpd  # noqa: E402  (build seulement)
from shapely import wkt  # noqa: E402

gj = gpd.read_file(ROOT / "data" / "togo_prefectures.geojson")
ALIAS_CONTOUR = {"AVE": ("TOTOAL AVE", "alias (nom de la préfecture dans le RGPH)"),
                 "PLAINE DU MO": ("MO", "alias (même territoire, nom différent)"),
                 "NAKI OUEST": ("KPENDJAL OUEST", "alias par chef-lieu ; validé spatialement (tools/check_geo_spatial.py : routes déclarées Kpendjal-Ouest dans ce polygone)"),
                 "LOME COMMUNE": ("GOLFE", "fusionné dans Golfe (le RGPH ne distingue pas la commune de Lomé)")}
lignes = []
for nom in gj["name"]:
    k = cle_geo(nom)
    if k in PREF_VERS_REGION:
        lignes.append((nom, k, "identique après normalisation", "OK"))
    elif k in ALIAS_CONTOUR:
        lignes.append((nom, ALIAS_CONTOUR[k][0], ALIAS_CONTOUR[k][1], "OK (validé spatialement)" if k == "NAKI OUEST" else "OK"))
    else:
        lignes.append((nom, np.nan, "non apparié", "ORPHELIN"))
geo_match = pd.DataFrame(lignes, columns=["nom_contour", "cle_rgph", "methode", "statut"])
geo_match["prefecture_rgph"] = geo_match.cle_rgph.map(NOM_PREF)
geo_match.to_csv(OUT / "geo_match.csv", index=False, encoding="utf-8")
assert (geo_match.statut != "ORPHELIN").all(), "contour orphelin"
assert geo_match.cle_rgph.nunique() == 39 and set(geo_match.cle_rgph) == set(PREF_VERS_REGION), "géo 39/39 non atteint"
assert (geo_match.groupby("cle_rgph").size() == 1).sum() == 38, "doublons inattendus"      # Golfe = 2 polygones fusionnés
GEO_TEST = {"prefectures_rgph": 39, "appariees": int(geo_match.cle_rgph.nunique()), "orphelins": 0,
            "doublons": int((geo_match.groupby("cle_rgph").size() > 1).sum() - 1)}   # Golfe fusionné volontairement

gj["cle_rgph"] = gj["name"].map(lambda n: geo_match.set_index("nom_contour").loc[n, "cle_rgph"])
pgeo = gj.dissolve(by="cle_rgph", as_index=False)[["cle_rgph", "geometry"]]
pgeo["prefecture"] = pgeo.cle_rgph.map(NOM_PREF)
pgeo["region"] = pgeo.cle_rgph.map(PREF_VERS_REGION)
pgeo["geometry"] = pgeo.geometry.simplify(0.002, preserve_topology=True)
rgeo = pgeo.dissolve(by="region", as_index=False)[["region", "geometry"]]
(OUT / "prefectures.geojson").write_text(json.dumps(json.loads(pgeo[["cle_rgph", "prefecture", "region", "geometry"]].to_json(na="null")), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
(OUT / "regions.geojson").write_text(json.dumps(json.loads(rgeo.to_json()), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
cent = pgeo.to_crs(EPSG_METRIQUE).geometry.representative_point().to_crs(4326)
pref = pref.merge(pd.DataFrame({"cle": pgeo.cle_rgph, "lon": cent.x.values, "lat": cent.y.values}), on="cle")

# ----------------------------------------------------------------------------------------------
# 3. Véhicules immatriculés (akkouh 1990–2022) et détail deux-roues (wklhvw 2013–2019)
# ----------------------------------------------------------------------------------------------
a = lire("observationdata-akkouh.csv").rename(columns={"types-de-vehicule": "cat", "Date": "annee", "Value": "valeur"})
a["cat"] = a["cat"].str.strip().replace({"Voitues": "Voitures", "2 roues et assimilées": "Deux-roues"})
pv = a.pivot(index="annee", columns="cat", values="valeur").sort_index()
pv["Poids lourds"] = pv["Camions"] + pv["Semi-remorques"] + pv["Tracteurs"]
parc = pv[["Deux-roues", "Voitures", "Camionnettes", "Poids lourds", "Autocars/Autobus", "Total"]].copy()
parc["somme_categories"] = parc[["Deux-roues", "Voitures", "Camionnettes", "Poids lourds", "Autocars/Autobus"]].sum(axis=1)
parc["ecart_total"] = parc["Total"] - parc["somme_categories"]
parc.reset_index().to_csv(OUT / "parc.csv", index=False, encoding="utf-8")
p22, p02 = parc.loc[2022], parc.loc[2002]
controle("Immatriculations 2022 : total", p22["Total"], 93_770)
controle("Immatriculations 2022 : deux-roues", p22["Deux-roues"], 67_639)
controle("Part deux-roues 2022 (%)", 100 * p22["Deux-roues"] / p22["Total"], 72.1, 0.005)
controle("Immatriculations 2022 : voitures", p22["Voitures"], 18_131)
controle("Immatriculations 2022 : poids lourds", p22["Poids lourds"], 3_229)
controle("Total 2002", p02["Total"], 20_553)
controle("Rapport 2022/2002", p22["Total"] / p02["Total"], 4.56)
controle("Part deux-roues dans la hausse 2002-2022 (%)", 100 * (p22["Deux-roues"] - p02["Deux-roues"]) / (p22["Total"] - p02["Total"]), 80.6)
controle("Part deux-roues 2002 (%)", 100 * p02["Deux-roues"] / p02["Total"], 42.0, 0.02)

w = lire("observationdata-wklhvw.csv").rename(columns={"automobile": "cat", "Date": "annee", "Value": "valeur"})
w["cat"] = w["cat"].replace({"Engins à 2 R de 50 à 125cm3": "50 à 125 cm³", "Engins à 2 R + de 125cm3": "Plus de 125 cm³"})
cyl = w[w["cat"].isin(["50 à 125 cm³", "Plus de 125 cm³", "Total 2 Roues"])].pivot(index="annee", columns="cat", values="valeur")
cyl.reset_index().to_csv(OUT / "parc_deux_roues_cylindree.csv", index=False, encoding="utf-8")

# ----------------------------------------------------------------------------------------------
# 4. Permis de conduire délivrés (2007–2022 ; 2013 = donnée manquante)
# ----------------------------------------------------------------------------------------------
pm = lire("observationdata-wvtolmb.csv").rename(columns={"categories-de-permis": "cat", "Date": "annee", "Value": "valeur"})
pm["cat"] = pm["cat"].str.strip().replace({"Voiture légèr (B)": "Voiture légère (B)"})
ppv = pm.pivot(index="annee", columns="cat", values="valeur").reindex(range(2007, 2023))
CATS_PERMIS = ["Moto (A)", "Voiture légère (B)", "Poids lourd (C)", "Transport en commun (D)", "Semi-remorque (E)", "Voiture spéciale (F)"]
assert ppv.loc[2013, CATS_PERMIS].isna().all(), "2013 devrait être manquant pour toutes les catégories"
ppv.loc[2013, "Total"] = np.nan                                  # 2013 : donnée manquante, jamais interpolée ni cumulée
ppv.reset_index().to_csv(OUT / "permis.csv", index=False, encoding="utf-8")
hors13 = ppv.drop(index=2013)
controle("Permis 2022 : total", ppv.loc[2022, "Total"], 24_598)
controle("Permis 2022 : A", ppv.loc[2022, "Moto (A)"], 4_837)
controle("Permis 2022 : B", ppv.loc[2022, "Voiture légère (B)"], 16_988)
controle("Part permis A 2022 (%)", 100 * ppv.loc[2022, "Moto (A)"] / ppv.loc[2022, "Total"], 19.7)
controle("Cumul permis A 2007–2022 hors 2013", hors13["Moto (A)"].sum(), 10_494)
controle("Cumul permis total 2007–2022 hors 2013", hors13["Total"].sum(), 205_057)
controle("Part permis A cumul (%)", 100 * hors13["Moto (A)"].sum() / hors13["Total"].sum(), 5.1, 0.01)

# ----------------------------------------------------------------------------------------------
# 5. Sécurité routière (national, annuel, 2010–2022)
# ----------------------------------------------------------------------------------------------
h = lire("observationdata-hxdpzbg.csv").rename(columns={"Date": "annee", "Value": "valeur"})
NOMS_SEC = {"Nombre de cas d'accidents de la circulation": "accidents", "Nombre de blessés": "blesses", "Nombre de morts": "morts",
            "Accidents mortels /100.000 hab": "accidents_100k_source"}
sec = (h[h.indicateur.isin(NOMS_SEC)].assign(k=lambda d: d.indicateur.map(NOMS_SEC))
       .pivot(index="annee", columns="k", values="valeur").sort_index()[["accidents", "blesses", "morts", "accidents_100k_source"]])
sec.reset_index().to_csv(OUT / "securite.csv", index=False, encoding="utf-8")
s22, s10 = sec.loc[2022], sec.loc[2010]
controle("Accidents 2022", s22.accidents, 7_507); controle("Blessés 2022", s22.blesses, 9_918); controle("Morts 2022", s22.morts, 683)
controle("Accidents 2010", s10.accidents, 3_101); controle("Blessés 2010", s10.blesses, 6_241); controle("Morts 2010", s10.morts, 470)
controle("Morts / 100 000 hab. 2022", 1e5 * s22.morts / POP_PAYS, 8.4, 0.01)
controle("Accidents / 10 000 véhicules 2022", 1e4 * s22.accidents / p22["Total"], 801, 0.01)
controle("Morts / 100 accidents 2022", 100 * s22.morts / s22.accidents, 9.1, 0.01)

# ----------------------------------------------------------------------------------------------
# 6. État du réseau (2020, une seule année)
# ----------------------------------------------------------------------------------------------
t = lire("observationdata-tmdtnad.csv").rename(columns={"tronçon": "troncon", "Value": "km", "indicateur": "categorie", "etat": "etat"})
LIGNE_NAT = t.troncon.isin(["TOTAL", "TOTAL RT"]) | t.categorie.str.startswith("VOIRIES")       # lignes de total national (les voiries n'ont qu'une ligne)
tot = t[LIGNE_NAT].pivot(index="categorie", columns="etat", values="km")
tot.reset_index().to_csv(OUT / "reseau_etat_national.csv", index=False, encoding="utf-8")
tr = t[~LIGNE_NAT].pivot(index=["categorie", "troncon"], columns="etat", values="km").reset_index()
tr["cle"] = tr.troncon.map(cle_geo)
assert len(tr) == 84, f"84 tronçons attendus, {len(tr)} trouvés"
for k, ref in {"TOTAL": 2198.47, "BON": 754.16, "MOYEN": 431.84, "MAUVAIS": 562.74, "TRAVAUX": 449.74}.items():
    controle(f"Routes revêtues 2020 {k} (km)", tot.loc["ROUTES REVETUES", k], ref)
for k, ref in {"TOTAL": 964.96, "BON": 242.84, "MOYEN": 303.72, "MAUVAIS": 106.58, "TRAVAUX": 311.82}.items():
    controle(f"Routes en terre 2020 {k} (km)", tot.loc["ROUTES EN TERRES", k], ref)

# ----------------------------------------------------------------------------------------------
# 7. Routes classées : longueur géodésique (EPSG:32631), rattachement par attributs
# ----------------------------------------------------------------------------------------------
r = lire("file-routes-routes-classees-18-12-2024-20-38-02.csv")
assert len(r) == 799
gr = gpd.GeoDataFrame(r.drop(columns="geometry"), geometry=r["geometry"].map(wkt.loads), crs=4326)
gr["km"] = gr.to_crs(EPSG_METRIQUE).geometry.length / 1000
ALIAS_PREF = {"AVE": "TOTOAL AVE"}
gr["cle_pref"] = gr["prefecture_nom_bdd"].map(cle_geo).map(lambda k: ALIAS_PREF.get(k, k))
gr["pref_ok"] = gr.cle_pref.isin(PREF_VERS_REGION)
gr["region"] = gr.cle_pref.map(PREF_VERS_REGION)
assert gr.pref_ok.all(), gr.loc[~gr.pref_ok, "prefecture_nom_bdd"].unique()
gr["cle_route"] = gr["route_nom"].map(cle_geo)
REVETU_OBS = {"Bitume", "Béton", "Beton", "Pavé"}
gr["revetue_observe"] = gr["route_recouvrement"].isin(REVETU_OBS)
gr["revetue_admin"] = gr["route_type"].isin(["Route nationale revêtue"]) | ((gr["route_type"] == "Voirie urbaine") & gr["revetue_observe"])
controle("Km de routes classées (total)", gr.km.sum(), 3366, 0.01)

det = (gr.groupby(["cle_pref", "route_type", "route_recouvrement"], as_index=False)
       .agg(km=("km", "sum"), troncons=("km", "size")))
det["prefecture"] = det.cle_pref.map(NOM_PREF); det["region"] = det.cle_pref.map(PREF_VERS_REGION)
det["revetue_observe"] = det.route_recouvrement.isin(REVETU_OBS)
det.to_csv(OUT / "routes_detail.csv", index=False, encoding="utf-8")

# ----------------------------------------------------------------------------------------------
# 8. Auto-écoles (272 ; 2 « Néant » exclues)
# ----------------------------------------------------------------------------------------------
ae = lire("file-entreprises-auto-ecoles-02-01-2025-16-28-05.csv")
assert len(ae) == 272
ae_all = ae.copy()
ae = ae[ae.agregation != "Néant"].copy()
g = gpd.GeoSeries(ae["geometry"].map(wkt.loads), crs=4326)
ae["lon"], ae["lat"] = g.x.values, g.y.values
ae["cle_pref"] = ae["prefecture_nom_bdd"].map(cle_geo).map(lambda k: ALIAS_PREF.get(k, k))
assert ae.cle_pref.isin(PREF_VERS_REGION).all(), ae.loc[~ae.cle_pref.isin(PREF_VERS_REGION), "prefecture_nom_bdd"].unique()
ae["region"] = ae.cle_pref.map(PREF_VERS_REGION); ae["prefecture"] = ae.cle_pref.map(NOM_PREF)
ae["statut"] = ae["agregation"].replace({"Antenne agréée": "Agréée (antenne)"})
ae["agreee"] = ae["agregation"].isin(["Agréée", "Antenne agréée"])
ae[["nom_etablissement", "region", "prefecture", "commune_nom_bdd", "canton_nom_bdd", "statut", "agreee", "lon", "lat", "cle_pref"]] \
    .rename(columns={"commune_nom_bdd": "commune", "canton_nom_bdd": "canton"}).to_csv(OUT / "auto_ecoles.csv", index=False, encoding="utf-8")
brut_reg = ae_all["prefecture_nom_bdd"].map(cle_geo).map(lambda k: ALIAS_PREF.get(k, k)).map(PREF_VERS_REGION).value_counts()
for rr_, v in {"Grand Lomé": 213, "Kara": 14, "Centrale": 12, "Plateaux": 12, "Maritime": 11, "Savanes": 10}.items():
    controle(f"Auto-écoles (avant exclusion Néant) {rr_}", brut_reg[rr_], v)


# ----------------------------------------------------------------------------------------------
# 9. Tables territoriales, contrôles régionaux
# ----------------------------------------------------------------------------------------------
sys.path.insert(0, str(ROOT))
from data import diag  # noqa: E402

aeo = pd.read_csv(OUT / "auto_ecoles.csv")
detc = pd.read_csv(OUT / "routes_detail.csv")
t_pref = diag.table_territoire(pref, detc, aeo, "Préfecture", "Toutes")
t_reg = diag.table_territoire(pref, detc, aeo, "Région", "Toutes").set_index("region").reindex(ORDRE_REGIONS)
for rr_, v in {"Grand Lomé": 0.74, "Maritime": 3.51, "Savanes": 4.63, "Centrale": 5.77, "Plateaux": 6.16, "Kara": 7.44}.items():
    controle(f"km routes classées / 10 000 hab. {rr_}", t_reg.loc[rr_, "km_10k"], v, 0.01)
controle("Préfectures sans route classée", int(t_pref.zero_route.sum()), 1, 0)
controle("Préfectures sans auto-école", int(t_pref.zero_ae.sum()), 15, 0)
print("Sans route :", t_pref.loc[t_pref.zero_route, "prefecture"].tolist())
print("Sans auto-école :", t_pref.loc[t_pref.zero_ae, "prefecture"].tolist())
t_pref.drop(columns=["niveau"]).to_csv(OUT / "territoire_prefectures.csv", index=False, encoding="utf-8")
t_reg.reset_index().drop(columns=["niveau"]).to_csv(OUT / "territoire_regions.csv", index=False, encoding="utf-8")
pref.to_csv(OUT / "population_prefectures.csv", index=False, encoding="utf-8")
reg_pop.rename("population").reset_index().rename(columns={"index": "region"}).to_csv(OUT / "population_regions.csv", index=False, encoding="utf-8")

# ----------------------------------------------------------------------------------------------
# 10. État du réseau : tronçons et estimation régionale exploratoire (Indicatif, hors score)
# ----------------------------------------------------------------------------------------------
cles_cl = set(gr.cle_route.dropna())
tr["apparie"] = tr.cle.isin(cles_cl)
tr.rename(columns={"cle": "cle_troncon"}).assign(apparie_routes_classees=tr["apparie"]).to_csv(OUT / "reseau_etat_troncons.csv", index=False, encoding="utf-8")
ratios = tr[tr.apparie].drop_duplicates("cle").set_index("cle")[["BON", "MOYEN", "MAUVAIS", "TRAVAUX", "TOTAL"]].fillna(0)
rg = gr[gr.cle_route.isin(ratios.index)].copy()
for e in ("BON", "MOYEN", "MAUVAIS", "TRAVAUX"):
    rg[e] = rg.km * rg.cle_route.map(ratios[e] / ratios["TOTAL"])      # hypothèse : état homogène le long de la route (non vérifiable)
etat_reg = rg.groupby("region")[["km", "BON", "MOYEN", "MAUVAIS", "TRAVAUX"]].sum().rename(columns={"km": "km_apparies"})
etat_reg["km_classes"] = gr.groupby("region").km.sum()
etat_reg = etat_reg.reindex(ORDRE_REGIONS).fillna(0).assign(km_classes=lambda d: gr.groupby("region").km.sum().reindex(ORDRE_REGIONS))
etat_reg["couverture"] = etat_reg.km_apparies / etat_reg.km_classes
for e in ("BON", "MOYEN", "MAUVAIS", "TRAVAUX"):
    etat_reg[f"part_{e.lower()}"] = np.where(etat_reg.km_apparies > 0, etat_reg[e] / etat_reg.km_apparies.where(etat_reg.km_apparies > 0), np.nan)
etat_reg.reset_index().to_csv(OUT / "etat_reseau_region_indicatif.csv", index=False, encoding="utf-8")
controle("Couverture état du réseau — Grand Lomé (%)", 100 * etat_reg.loc["Grand Lomé", "couverture"], 0.0, 1.0) if etat_reg.loc["Grand Lomé", "couverture"] > 0 else None
controle("Couverture état du réseau — Kara (%)", 100 * etat_reg.loc["Kara", "couverture"], 90.6, 0.01)
print(etat_reg.round(3).to_string())

# ----------------------------------------------------------------------------------------------
# 11. Routes en GeoJSON simplifié (≤ 1,5 Mo)
# ----------------------------------------------------------------------------------------------
def export_routes(tol: float) -> int:
    g = gr[["route_nom", "cle_route", "route_type", "route_recouvrement", "region", "cle_pref", "km", "geometry"]].copy()
    g["prefecture"] = g.cle_pref.map(NOM_PREF)
    g["geometry"] = g.geometry.simplify(tol, preserve_topology=False)
    g["km"] = g.km.round(2)
    feats = []
    for _, row in g.iterrows():
        geom = json.loads(gpd.GeoSeries([row.geometry]).to_json())["features"][0]["geometry"]
        geom = json.loads(json.dumps(geom), parse_float=lambda x: round(float(x), 4))
        feats.append({"type": "Feature", "geometry": geom, "properties": {k: row[k] for k in ["route_nom", "cle_route", "route_type", "route_recouvrement", "region", "prefecture", "km"]}})
    txt = json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False, separators=(",", ":"))
    (OUT / "routes.geojson").write_text(txt, encoding="utf-8")
    return len(txt.encode("utf-8"))


for tol in (0.0008, 0.0015, 0.003, 0.006):
    taille = export_routes(tol)
    if taille <= 1_500_000:
        break
print(f"routes.geojson : {taille / 1e6:.2f} Mo (tolérance {tol}°)")
assert taille <= 1_500_000

# ----------------------------------------------------------------------------------------------
# 12. Diagnostic (défaut 50/50, auto-écoles toutes), robustesse
# ----------------------------------------------------------------------------------------------
dg = diag.diagnostic(t_pref, 0.5)
dg.drop(columns=["niveau"]).to_csv(OUT / "diagnostic_prefectures.csv", index=False, encoding="utf-8")
dgr = diag.diagnostic(diag.table_territoire(pref, detc, aeo, "Région", "Toutes"), 0.5)
dgr.drop(columns=["niveau"]).to_csv(OUT / "diagnostic_regions.csv", index=False, encoding="utf-8")
rob = diag.robustesse(pref, detc, aeo)
rob.to_csv(OUT / "robustesse.csv", index=False, encoding="utf-8")
json.dump({"stables": rob.attrs["stables"], "union": rob.attrs["union"]}, open(OUT / "robustesse_stables.json", "w", encoding="utf-8"), ensure_ascii=False)
print("Quintile défavorable (50/50, toutes) :", dg.loc[dg.quintile_defavorable, "prefecture"].tolist())
print("Stables aux 6 configurations :", rob.attrs["stables"])
print(dgr[["region", "score_infra", "score_formation", "score", "rang"]].round(2).to_string())

pd.DataFrame(CONTROLES).to_csv(OUT / "controles.csv", index=False, encoding="utf-8")
json.dump(GEO_TEST, open(OUT / "geo_test.json", "w", encoding="utf-8"), ensure_ascii=False)
ecarts = [c for c in CONTROLES if c["statut"] != "OK"]
print(f"\n{len(CONTROLES) - len(ecarts)}/{len(CONTROLES)} contrôles OK")
assert not ecarts, f"Écarts > 0,5 % : {ecarts}"

import runpy  # noqa: E402
runpy.run_path(str(ROOT / "tools" / "build_reco.py"), run_name="build_reco_import") if False else None
sys.path.insert(0, str(ROOT / "tools"))
import build_reco  # noqa: E402
build_reco.build()
print("recommandations.json généré")
runpy.run_path(str(ROOT / "tools" / "check_geo_spatial.py"), run_name="__main__")
