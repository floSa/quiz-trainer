"""Génère data/world.geojson : les géométries des 194 pays, clé = ISO3.

Source : Natural Earth 50m (via le dépôt nvkelso/natural-earth-vector).
On ne garde que les pays de data/countries.json, on met `id = iso3`, on retire
les propriétés inutiles et on arrondit les coordonnées (~1 km) pour alléger le
fichier servi au navigateur.

Lancer :  python scripts/build_geo.py
"""

import json
import os
import urllib.request
from collections import defaultdict

SOURCE = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    "master/geojson/ne_50m_admin_0_countries.geojson"
)
HERE = os.path.dirname(os.path.abspath(__file__))
COUNTRIES = os.path.normpath(os.path.join(HERE, "..", "data", "countries.json"))
OUT = os.path.normpath(os.path.join(HERE, "..", "data", "world.geojson"))

NDIGITS = 2  # ~1 km : suffisant pour cliquer un pays


def round_coords(x):
    if isinstance(x, (int, float)):
        return round(x, NDIGITS)
    return [round_coords(c) for c in x]


def feature_iso3(props):
    k = props.get("ISO_A3_EH")
    if not k or k in ("-99", -99):
        k = props.get("ADM0_A3")
    return k


def main():
    with urllib.request.urlopen(SOURCE, timeout=90) as resp:
        src = json.loads(resp.read())
    wanted = {c["iso3"] for c in json.load(open(COUNTRIES, encoding="utf-8"))}

    # Natural Earth peut avoir PLUSIEURS entités pour un même pays (territoires,
    # îles externes…). On FUSIONNE leurs polygones au lieu d'écraser : sinon une
    # entité minuscule arrivée en dernier remplace le continent (ex. l'Australie
    # écrasée par l'îlot Ashmore & Cartier à 123,6°E / -12,4°).
    polys = defaultdict(list)  # iso3 -> liste de polygones [ [ring, …], … ]
    for f in src["features"]:
        iso = feature_iso3(f["properties"])
        if iso not in wanted:
            continue
        g = f["geometry"]
        if g["type"] == "Polygon":
            polys[iso].append(g["coordinates"])
        elif g["type"] == "MultiPolygon":
            polys[iso].extend(g["coordinates"])

    missing = sorted(wanted - set(polys))
    assert not missing, f"Pays sans géométrie : {missing}"

    by_iso = {
        iso: {
            "type": "Feature",
            "id": iso,
            "properties": {},
            "geometry": {"type": "MultiPolygon", "coordinates": round_coords(plist)},
        }
        for iso, plist in polys.items()
    }

    out = {"type": "FeatureCollection", "features": list(by_iso.values())}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"))
    kb = os.path.getsize(OUT) // 1024
    print(f"{len(by_iso)} géométries écrites dans {OUT} ({kb} Ko)")


if __name__ == "__main__":
    main()
