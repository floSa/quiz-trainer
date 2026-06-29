"""Génère data/deserts.json : grands déserts du monde (nom FR + géométrie).

Source : Natural Earth 50m geography regions (FEATURECLA = Desert), qui fournit
déjà NAME_FR. On ne garde que les déserts célèbres (filtre par mot-clé).

Lancer :  python scripts/build_deserts.py
"""

import json
import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "data", "deserts.json"))
SOURCE = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    "master/geojson/ne_50m_geography_regions_polys.geojson"
)
NDIGITS = 1

# on ne garde que les déserts dont le NAME_FR contient un de ces mots-clés
KEEP = [
    "Sahara", "Gobi", "Kalahari", "Namib", "Rub al", "Thar", "Atacama",
    "Victoria", "Karakoum", "Kyzylkoum", "Ténéré", "Nubie", "Libyque",
    "Taklamakan", "Mojave", "Sonora", "Patagon", "sable", "Syrie", "Arabique",
]


def round_coords(x):
    if isinstance(x, (int, float)):
        return round(x, NDIGITS)
    return [round_coords(c) for c in x]


def main():
    with urllib.request.urlopen(SOURCE, timeout=90) as r:
        feats = json.loads(r.read())["features"]

    out = []
    for f in feats:
        p = f["properties"]
        if p.get("FEATURECLA") != "Desert":
            continue
        name = p.get("NAME_FR") or p.get("NAME")
        if not name or not any(k.lower() in name.lower() for k in KEEP):
            continue
        out.append({
            "name": name,
            "geometry": {"type": f["geometry"]["type"], "coordinates": round_coords(f["geometry"]["coordinates"])},
        })

    out.sort(key=lambda r: r["name"])
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(out)} déserts -> {OUT} ({os.path.getsize(OUT)//1024} Ko)")
    print("noms:", [r["name"] for r in out])


if __name__ == "__main__":
    main()
