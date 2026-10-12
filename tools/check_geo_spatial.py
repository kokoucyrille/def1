"""
Contrôle spatial indépendant des noms : chaque tronçon de route (géométrie) et chaque auto-école (point) tombe-t-il dans le polygone
de la préfecture que ses attributs déclarent ? Écrit data/processed/controle_spatial.csv et .json.

    python tools/check_geo_spatial.py        # nécessite requirements-build.txt
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely import wkt

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "processed"
EPSG = 32631

pg = gpd.read_file(OUT / "prefectures.geojson").set_crs(4326)          # 39 polygones (contours indicatifs, simplifiés)
pg_m = pg.to_crs(EPSG)

# ---- auto-écoles : point dans le polygone déclaré ?
ae = pd.read_csv(OUT / "auto_ecoles.csv")
pts = gpd.GeoDataFrame(ae, geometry=gpd.points_from_xy(ae.lon, ae.lat), crs=4326).to_crs(EPSG)
j = gpd.sjoin(pts, pg_m[["cle_rgph", "geometry"]], how="left", predicate="within")
j = j[~j.index.duplicated()]
ae_ok = (j["cle_rgph"] == j["cle_pref"])
# tolérance : point à moins de 1 km du polygone déclaré (contours simplifiés)
poly = pg_m.set_index("cle_rgph").geometry
dist = [poly[c].distance(p) if c in poly.index else 1e9 for c, p in zip(pts.cle_pref, pts.geometry)]
ae_ok_tol = pd.Series([d <= 1000 for d in dist], index=pts.index)

# ---- routes : part de la longueur dans le polygone déclaré
r = pd.read_csv(ROOT / "data" / "raw" / "file-routes-routes-classees-18-12-2024-20-38-02.csv")
sys.path.insert(0, str(ROOT))
from tools.build_data_keys import cle_geo  # noqa: E402
ALIAS = {"AVE": "TOTOAL AVE"}
g = gpd.GeoDataFrame(r.drop(columns="geometry"), geometry=r["geometry"].map(wkt.loads), crs=4326).to_crs(EPSG)
g["cle_pref"] = g["prefecture_nom_bdd"].map(cle_geo).map(lambda k: ALIAS.get(k, k))
part = []
for cle, geom in zip(g.cle_pref, g.geometry):
    p = poly.get(cle)
    part.append(geom.intersection(p.buffer(1000)).length / geom.length if p is not None and geom.length else 0.0)
g["part_dans_pref"] = part

rows = []
for cle in sorted(poly.index):
    a = ae_ok_tol[pts.cle_pref == cle]; rt = g[g.cle_pref == cle]
    rows.append({"cle_rgph": cle, "ae_n": int(len(a)), "ae_dans_polygone_decl": int(a.sum()),
                 "routes_n": int(len(rt)), "routes_km": round(float((rt.geometry.length / 1000).sum()), 1),
                 "routes_part_km_dans_polygone_decl": round(float((rt.part_dans_pref * rt.geometry.length).sum() / rt.geometry.length.sum()), 3) if len(rt) else None})
t = pd.DataFrame(rows)
t.to_csv(OUT / "controle_spatial.csv", index=False, encoding="utf-8")
tot = {"ae_total": int(len(pts)), "ae_dans_polygone_decl_strict": int(ae_ok.sum()), "ae_dans_polygone_decl_tolerance_1km": int(ae_ok_tol.sum()),
       "routes_km_total": round(float((g.geometry.length / 1000).sum()), 1),
       "routes_part_km_dans_polygone_decl": round(float((g.part_dans_pref * g.geometry.length).sum() / g.geometry.length.sum()), 3),
       "troncons_majoritairement_hors_polygone": int((g.part_dans_pref < 0.5).sum())}
(OUT / "controle_spatial.json").write_text(json.dumps(tot, ensure_ascii=False, indent=1), encoding="utf-8")
kp = t.set_index("cle_rgph").loc["KPENDJAL OUEST", "routes_part_km_dans_polygone_decl"]
tot["alias_naki_ouest_kpendjal_ouest_part_km"] = float(kp)
assert kp >= 0.9, f"alias Naki-Ouest ↔ Kpendjal-Ouest non validé spatialement ({kp:.1%})"
(OUT / "controle_spatial.json").write_text(json.dumps(tot, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(tot, ensure_ascii=False, indent=1))
print(t[t.cle_rgph.isin(["KPENDJAL OUEST", "KPENDJAL", "GOLFE", "TOTOAL AVE", "MO"])].to_string())
print("Préfectures avec < 80 % des km dans le polygone déclaré :")
print(t[(t.routes_part_km_dans_polygone_decl < 0.8)].to_string())
print("Préfectures avec auto-écoles hors polygone :")
print(t[t.ae_n > t.ae_dans_polygone_decl][["cle_rgph", "ae_n", "ae_dans_polygone_decl"]].to_string())


# ======================================================================================================
# Sensibilité du diagnostic au mode de rattachement : attributs administratifs (défaut) vs position géographique
# (contours indicatifs). Écrit data/processed/sensibilite_rattachement.json
# ======================================================================================================
from data import diag  # noqa: E402

geo_cle = []
for geom in g.geometry:
    best, best_len = None, -1.0
    for cle in pg_m.index[pg_m.intersects(geom)]:
        ln = geom.intersection(pg_m.loc[cle, "geometry"]).length
        if ln > best_len:
            best, best_len = pg_m.loc[cle, "cle_rgph"], ln
    geo_cle.append(best if best is not None else pg_m.geometry.distance(geom).idxmin())
g["cle_pref_geo"] = geo_cle
if any(isinstance(c, int) for c in g["cle_pref_geo"]):                       # repli : plus proche polygone
    g["cle_pref_geo"] = [pg_m.loc[c, "cle_rgph"] if isinstance(c, int) else c for c in g["cle_pref_geo"]]
REV = {"Bitume", "Béton", "Beton", "Pavé"}
det_geo = (g.assign(km=g.geometry.length / 1000, cle_pref=g["cle_pref_geo"], revetue_observe=g["route_recouvrement"].isin(REV))
           .groupby(["cle_pref", "route_type", "route_recouvrement", "revetue_observe"], as_index=False).km.sum())
nj = gpd.sjoin_nearest(pts, pg_m[["cle_rgph", "geometry"]], how="left")
nj = nj[~nj.index.duplicated()]
ae_geo = ae.copy(); ae_geo["cle_pref"] = nj["cle_rgph"].values

pref = pd.read_csv(OUT / "population_prefectures.csv")
det_attr = pd.read_csv(OUT / "routes_detail.csv")


def stables_et_quintile(det_, ae_):
    rob = diag.robustesse(pref, det_, ae_, "Préfecture")
    q = rob[(rob.label == "50/50") & (rob.auto_ecoles == "Toutes")].unites.iloc[0]
    return sorted(rob.attrs["stables"]), sorted(q.split(", ")) if q else []


s_a, q_a = stables_et_quintile(det_attr, ae)
s_g, q_g = stables_et_quintile(det_geo, ae_geo)
d_apart_a = diag.diagnostic(diag.table_territoire(pref, det_attr, ae, "Préfecture", "Toutes"), 0.5, True)
d_apart_g = diag.diagnostic(diag.table_territoire(pref, det_geo, ae_geo, "Préfecture", "Toutes"), 0.5, True)
qa_part = sorted(d_apart_a.loc[d_apart_a.quintile_defavorable, "prefecture"]); qg_part = sorted(d_apart_g.loc[d_apart_g.quintile_defavorable, "prefecture"])
sens = {"stables_attributs": s_a, "stables_geographique": s_g, "quintile_50_50_attributs": q_a, "quintile_50_50_geographique": q_g,
        "quintile_hors_zeros_attributs": qa_part, "quintile_hors_zeros_geographique": qg_part,
        "stables_hors_zeros_attributs": sorted(diag.robustesse(pref, det_attr, ae, "Préfecture", "observe", True).attrs["stables"]),
        "stables_hors_zeros_geographique": sorted(diag.robustesse(pref, det_geo, ae_geo, "Préfecture", "observe", True).attrs["stables"]),
        "tronçons_rattaches_differemment": int((g["cle_pref"] != g["cle_pref_geo"]).sum()),
        "auto_ecoles_rattachees_differemment": int((ae["cle_pref"].values != ae_geo["cle_pref"].values).sum())}
(OUT / "sensibilite_rattachement.json").write_text(json.dumps(sens, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(sens, ensure_ascii=False, indent=1))
