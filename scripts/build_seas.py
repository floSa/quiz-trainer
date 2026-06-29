"""Génère data/seas.json : grandes mers et océans (nom FR + géométrie).

Liste curatée (les plus connus), avec alias anglais pour matcher Natural Earth
et FUSIONNER les morceaux (ex. North/South Atlantic Ocean → océan Atlantique).

Source : Natural Earth 50m marine polys (nvkelso/natural-earth-vector).

Lancer :  python scripts/build_seas.py
"""

import json
import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "data", "seas.json"))
SOURCE = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    "master/geojson/ne_50m_geography_marine_polys.geojson"
)
NDIGITS = 1  # mers très étendues : ~11 km suffit largement

# nom FR -> alias cherchés dans le champ `name` (anglais) de Natural Earth
SEAS = {
    "Océan Atlantique": ["Atlantic Ocean"],
    "Océan Pacifique": ["Pacific Ocean"],
    "Océan Indien": ["INDIAN OCEAN", "Indian Ocean"],
    "Océan Arctique": ["Arctic Ocean"],
    "Océan Austral": ["SOUTHERN OCEAN", "Southern Ocean"],
    "Mer Méditerranée": ["Mediterranean Sea"],
    "Mer des Caraïbes": ["Caribbean Sea"],
    "Golfe du Mexique": ["Gulf of Mexico"],
    "Mer du Nord": ["North Sea"],
    "Mer Baltique": ["Baltic Sea"],
    "Mer Noire": ["Black Sea"],
    "Mer Rouge": ["Red Sea"],
    "Mer d'Arabie": ["Arabian Sea"],
    "Golfe du Bengale": ["Bay of Bengal"],
    "Mer de Chine méridionale": ["South China Sea"],
    "Mer de Chine orientale": ["East China Sea"],
    "Mer du Japon": ["Sea of Japan"],
    "Mer Caspienne": ["Caspian Sea"],
    "Golfe Persique": ["Persian Gulf"],
    "La Manche": ["English Channel"],
    "Golfe de Gascogne": ["Bay of Biscay"],
    "Mer de Norvège": ["Norwegian Sea"],
    "Mer de Béring": ["Bering Sea"],
    "Mer d'Okhotsk": ["Sea of Okhotsk"],
    "Mer de Tasman": ["Tasman Sea"],
    "Mer des Philippines": ["Philippine Sea"],
    "Mer Adriatique": ["Adriatic Sea"],
    "Mer Égée": ["Aegean Sea"],
    "Mer de Corail": ["Coral Sea"],
    "Baie d'Hudson": ["Hudson Bay"],
}


def round_coords(x):
    if isinstance(x, (int, float)):
        return round(x, NDIGITS)
    return [round_coords(c) for c in x]


def polys_of(geom):
    if geom["type"] == "Polygon":
        return [geom["coordinates"]]
    if geom["type"] == "MultiPolygon":
        return list(geom["coordinates"])
    return []


def main():
    with urllib.request.urlopen(SOURCE, timeout=90) as r:
        feats = json.loads(r.read())["features"]

    out = []
    for fr_name, aliases in SEAS.items():
        polys = []
        for f in feats:
            name = str(f["properties"].get("name") or "")
            if any(a in name for a in aliases):
                polys.extend(polys_of(f["geometry"]))
        if not polys:
            print(f"  ⚠ rien pour {fr_name}")
            continue
        out.append({
            "name": fr_name,
            "geometry": {"type": "MultiPolygon", "coordinates": round_coords(polys)},
        })

    out.sort(key=lambda r: r["name"])
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(out)} mers/océans -> {OUT} ({os.path.getsize(OUT)//1024} Ko)")


if __name__ == "__main__":
    main()
