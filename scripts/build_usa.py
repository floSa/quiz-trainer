"""Génère data/usa/states.geojson (états américains contigus, ~48).

On exclut Alaska et Hawaï (cadrage de carte : leurs coordonnées rendraient la
carte des 48 états minuscule), ainsi que Washington D.C. et Porto Rico (pas des
états). Noms en français.

Source : PublicaMundi/MappingAPI (us-states.json, domaine public).
Lancer :  python scripts/build_usa.py
"""

import json
import os
import urllib.request

SRC = "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "data", "usa", "states.geojson"))

EXCLUDE = {"Alaska", "Hawaii", "District of Columbia", "Puerto Rico"}

# Noms français des états qui diffèrent de l'anglais (les autres sont inchangés).
NOM_FR = {
    "California": "Californie",
    "Florida": "Floride",
    "Georgia": "Géorgie",
    "Louisiana": "Louisiane",
    "New Mexico": "Nouveau-Mexique",
    "North Carolina": "Caroline du Nord",
    "North Dakota": "Dakota du Nord",
    "South Carolina": "Caroline du Sud",
    "South Dakota": "Dakota du Sud",
    "Pennsylvania": "Pennsylvanie",
    "Virginia": "Virginie",
    "West Virginia": "Virginie-Occidentale",
    "New Hampshire": "Nouveau-Hampshire",
}


def round_coords(x, n=2):
    if isinstance(x, (int, float)):
        return round(x, n)
    return [round_coords(c, n) for c in x]


def main():
    with urllib.request.urlopen(SRC, timeout=60) as r:
        g = json.loads(r.read())
    feats = []
    for f in g["features"]:
        name = f["properties"]["name"]
        if name in EXCLUDE:
            continue
        feats.append({
            "type": "Feature",
            "id": name,  # identifiant interne = nom anglais (unique)
            "properties": {"nom": NOM_FR.get(name, name)},
            "geometry": {
                "type": f["geometry"]["type"],
                "coordinates": round_coords(f["geometry"]["coordinates"]),
            },
        })
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"type": "FeatureCollection", "features": feats}, fh,
                  ensure_ascii=False, separators=(",", ":"))
    print(f"{len(feats)} états → {OUT} ({os.path.getsize(OUT)//1024} Ko)")


if __name__ == "__main__":
    main()
