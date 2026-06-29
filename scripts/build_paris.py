"""Génère data/france/paris.geojson : les 20 arrondissements de Paris.

  id           = numéro d'arrondissement (1..20, en chaîne)
  properties.nom = ordinal + quartier officiel : « 1er (Louvre) », « 19e (Buttes-Chaumont) »

Source : opendata.paris.fr (jeu « arrondissements »), licence ODbL.

Lancer :  python scripts/build_paris.py
"""

import json
import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "data", "france", "paris.geojson"))
SOURCE = (
    "https://opendata.paris.fr/explore/dataset/arrondissements/download/"
    "?format=geojson&timezone=Europe/Berlin"
)
NDIGITS = 4  # ~11 m : Paris est petit, on garde de la précision


def round_coords(x):
    if isinstance(x, (int, float)):
        return round(x, NDIGITS)
    return [round_coords(c) for c in x]


def ordinal(n):
    return "1er" if n == 1 else f"{n}e"


def main():
    with urllib.request.urlopen(SOURCE, timeout=90) as r:
        g = json.loads(r.read())

    feats = []
    for f in g["features"]:
        n = int(f["properties"]["c_ar"])
        quartier = (f["properties"].get("l_aroff") or "").strip()
        label = f"{ordinal(n)} ({quartier})" if quartier else ordinal(n)
        feats.append({
            "type": "Feature",
            "id": str(n),
            "properties": {"nom": label},
            "geometry": {
                "type": f["geometry"]["type"],
                "coordinates": round_coords(f["geometry"]["coordinates"]),
            },
        })
    feats.sort(key=lambda f: int(f["id"]))
    assert len(feats) == 20, f"attendu 20 arrondissements, obtenu {len(feats)}"

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"type": "FeatureCollection", "features": feats}, fh,
                  ensure_ascii=False, separators=(",", ":"))
    print(f"{len(feats)} arrondissements -> {OUT} ({os.path.getsize(OUT)//1024} Ko)")


if __name__ == "__main__":
    main()
