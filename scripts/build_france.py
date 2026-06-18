"""Génère les données France métropolitaine dans data/france/ :
  regions.geojson       (13, id = code INSEE, properties.nom)
  departements.geojson  (96, id = code, properties.nom)
  cities.json           (villes >= 50 000 hab. : nom, lat, lng, pop)

Sources :
  - régions/départements : gregoiredavid/france-geojson (version simplifiée)
  - villes : GeoNames cities15000 (CC-BY)

Lancer :  python scripts/build_france.py
"""

import json
import os
import urllib.request
import zipfile
import io

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "data", "france"))

GEO = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/"
REGIONS = GEO + "regions-version-simplifiee.geojson"
DEPS = GEO + "departements-version-simplifiee.geojson"
CITIES = "https://download.geonames.org/export/dump/cities15000.zip"
MIN_POP = 50000


def round_coords(x, n):
    if isinstance(x, (int, float)):
        return round(x, n)
    return [round_coords(c, n) for c in x]


def fetch(url):
    with urllib.request.urlopen(url, timeout=90) as r:
        return r.read()


def build_admin(url, out_name):
    g = json.loads(fetch(url))
    feats = []
    for f in g["features"]:
        code = f["properties"]["code"]
        feats.append({
            "type": "Feature",
            "id": code,
            "properties": {"nom": f["properties"]["nom"]},
            "geometry": {
                "type": f["geometry"]["type"],
                "coordinates": round_coords(f["geometry"]["coordinates"], 3),
            },
        })
    path = os.path.join(OUT, out_name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"type": "FeatureCollection", "features": feats}, fh, separators=(",", ":"))
    print(f"{len(feats)} → {out_name} ({os.path.getsize(path)//1024} Ko)")


def build_cities():
    z = zipfile.ZipFile(io.BytesIO(fetch(CITIES)))
    rows = z.read("cities15000.txt").decode("utf-8").splitlines()
    cities = []
    for line in rows:
        c = line.split("\t")
        if c[8] == "FR" and c[14].isdigit() and int(c[14]) >= MIN_POP:
            cities.append({
                "name": c[1],
                "lat": round(float(c[4]), 4),
                "lng": round(float(c[5]), 4),
                "pop": int(c[14]),
            })
    cities.sort(key=lambda x: -x["pop"])
    path = os.path.join(OUT, "cities.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(cities, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(cities)} villes → cities.json")


def main():
    os.makedirs(OUT, exist_ok=True)
    build_admin(REGIONS, "regions.geojson")
    build_admin(DEPS, "departements.geojson")
    build_cities()


if __name__ == "__main__":
    main()
