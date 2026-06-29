"""Génère data/ranges.json : grandes chaînes de montagnes (nom FR + géométrie).

Source : Natural Earth 50m geography regions (FEATURECLA = Range/mtn), qui
fournit déjà NAME_FR. On ne garde que les chaînes célèbres (filtre par mot-clé).

Lancer :  python scripts/build_ranges.py
"""

import json
import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "data", "ranges.json"))
SOURCE = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    "master/geojson/ne_50m_geography_regions_polys.geojson"
)
NDIGITS = 1

# Liste blanche EXACTE des chaînes canoniques (NAME_FR de Natural Earth) : on
# évite ainsi les sous-massifs (« Alpes du Sud »…) et les homonymes ambigus
# (deux « Sierra Nevada » US/Espagne) qui pollueraient le QCM.
KEEP = {
    "Alpes", "Himalaya", "cordillère des Andes", "montagnes Rocheuses",
    "Caucase", "Oural", "Atlas", "Pyrénées", "Carpates", "Tian Shan",
    "Altaï", "Zagros", "Hindou Kouch", "Karakoram", "Pamir", "Appalaches",
    "Drakensberg", "Alpes scandinaves", "Cordillère du Kunlun", "Grand Khingan",
    "Monts Stanovoï", "Chaîne Annamitique", "Cordillère australienne",
    "Grand Balkan", "massif du Tibesti", "Monts de Verkhoïansk",
}


def round_coords(x):
    if isinstance(x, (int, float)):
        return round(x, NDIGITS)
    return [round_coords(c) for c in x]


def main():
    with urllib.request.urlopen(SOURCE, timeout=90) as r:
        feats = json.loads(r.read())["features"]

    seen, out = set(), []
    for f in feats:
        p = f["properties"]
        if p.get("FEATURECLA") != "Range/mtn":
            continue
        name = p.get("NAME_FR") or p.get("NAME")
        if not name or name in seen or name not in KEEP:
            continue
        seen.add(name)
        out.append({
            "name": name,
            "geometry": {"type": f["geometry"]["type"], "coordinates": round_coords(f["geometry"]["coordinates"])},
        })

    out.sort(key=lambda r: r["name"])
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(out)} chaînes -> {OUT} ({os.path.getsize(OUT)//1024} Ko)")
    print("noms:", [r["name"] for r in out])


if __name__ == "__main__":
    main()
