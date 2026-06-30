"""Génère data/france/prefectures.json : { code: { pref, region } } par dépt.

  - préfecture (chef-lieu) : Wikidata (P31 = département Q6465, P2586 = code,
    P36 = capitale administrative).
  - région : calculée géométriquement (le centroïde du département tombe dans le
    polygone de la région), à partir des geojson déjà présents.

On ne garde que les 96 départements métropolitains de departements.geojson.

Lancer :  python scripts/build_prefectures.py
"""

import json
import os
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
FR = os.path.normpath(os.path.join(HERE, "..", "data", "france"))
OUT = os.path.join(FR, "prefectures.json")
UA = "quiz-trainer/1.0 (projet perso ; https://github.com/floSa/quiz-trainer)"

QUERY = """
SELECT ?code ?prefLabel WHERE {
  ?dep wdt:P31 wd:Q6465 ; wdt:P2586 ?code ; wdt:P36 ?pref .
  ?pref rdfs:label ?prefLabel . FILTER(lang(?prefLabel) = "fr")
}
"""


def sparql(q, tries=4):
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"})
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read())["results"]["bindings"]
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(4)


# --- géométrie : région d'un département (point-dans-polygone) -------------- //
def coords_avg(geom):
    """Point représentatif : moyenne des sommets du plus grand anneau."""
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    ring = max((poly[0] for poly in polys), key=len)
    return (sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring))

def in_ring(pt, ring):
    x, y = pt
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside

def in_geom(pt, geom):
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    for poly in polys:
        if in_ring(pt, poly[0]) and not any(in_ring(pt, h) for h in poly[1:]):
            return True
    return False


def main():
    deps = json.load(open(os.path.join(FR, "departements.geojson"), encoding="utf-8"))["features"]
    regs = json.load(open(os.path.join(FR, "regions.geojson"), encoding="utf-8"))["features"]
    dep_ids = {f["id"] for f in deps}

    prefs = {}
    for b in sparql(QUERY):
        code = b["code"]["value"]
        if code in dep_ids:
            prefs[code] = b["prefLabel"]["value"]
    missing = sorted(dep_ids - set(prefs))
    if missing:
        print("préfectures manquantes :", missing)

    reg_cent = [(r["properties"]["nom"], r["geometry"], coords_avg(r["geometry"])) for r in regs]
    def region_of(geom):
        pt = coords_avg(geom)
        for nom, rgeom, _ in reg_cent:
            if in_geom(pt, rgeom):
                return nom
        return min(reg_cent, key=lambda r: (r[2][0] - pt[0]) ** 2 + (r[2][1] - pt[1]) ** 2)[0]

    out = {}
    for f in sorted(deps, key=lambda f: f["id"]):
        code = f["id"]
        out[code] = {"pref": prefs.get(code, ""), "region": region_of(f["geometry"])}

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    nb_reg = len(set(v["region"] for v in out.values()))
    print(f"{len(out)} départements -> {OUT} ; {nb_reg} régions")


if __name__ == "__main__":
    main()
