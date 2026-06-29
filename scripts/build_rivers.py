"""Génère data/rivers.json : les grands fleuves du monde (nom FR + géométrie).

Natural Earth ne fournit que des noms anglais, souvent découpés en segments
(« Victoria Nile », « Chang Jiang », « Jinsha »…). On part d'une liste curatée
de fleuves connus (nom français + alias NE) et on agrège tous les segments
correspondants en une seule MultiLineString par fleuve.

Source : Natural Earth 50m rivers (nvkelso/natural-earth-vector).

Lancer :  python scripts/build_rivers.py
"""

import json
import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "data", "rivers.json"))
SOURCE = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    "master/geojson/ne_50m_rivers_lake_centerlines.geojson"
)
NDIGITS = 2  # ~1 km

# nom FR -> alias (sous-chaînes cherchées dans name / name_en / name_alt de NE)
RIVERS = {
    "Nil": ["Nile", "Bahr el Jebel", "El Bahr el Abyad", "Damietta", "Rosetta"],
    "Amazone": ["Amazonas", "Amazon", "Ucayali", "Solimões", "Solimoes"],
    "Mississippi": ["Mississippi"],
    "Missouri": ["Missouri"],
    "Yangtsé": ["Yangtze", "Chang Jiang", "Jinsha", "Tongtian", "Tuotuo"],
    "Mékong": ["Mekong", "Lancang"],
    "Danube": ["Danube", "Donau"],
    "Volga": ["Volga"],
    "Congo": ["Congo", "Lualaba"],
    "Niger": ["Niger"],
    "Gange": ["Ganges", "Ganga"],
    "Indus": ["Indus"],
    "Brahmapoutre": ["Brahmaputra", "Yarlung", "Dihang"],
    "Ob": ["Ob ", "Irtysh", "Irtych", "Ertis", "Ertix"],
    "Ienisseï": ["Yenisey", "Yenisei", "Selenge", "Selenga", "Angara"],
    "Léna": ["Lena"],
    "Amour": ["Amur"],
    "Paraná": ["Paraná", "Parana"],
    "Saint-Laurent": ["St. Lawrence", "Saint Lawrence"],
    "Mackenzie": ["Mackenzie", "Slave", "Peace"],
    "Colorado": ["Colorado"],
    "Zambèze": ["Zambezi"],
    "Murray": ["Murray", "Darling"],
    "Rhin": ["Rhine", "Rhein"],
    "Rhône": ["Rhone", "Rhône"],
    "Loire": ["Loire"],
    "Seine": ["Seine"],
    "Garonne": ["Garonne"],
    "Tage": ["Tagus", "Tejo"],
    "Euphrate": ["Euphrates"],
    "Tigre": ["Tigris"],
    "Pô": ["Po "],
    "Elbe": ["Elbe"],
}


def round_coords(x):
    if isinstance(x, (int, float)):
        return round(x, NDIGITS)
    return [round_coords(c) for c in x]


def lines_of(geom):
    """Renvoie la liste des polylignes (chacune = liste de [lng,lat])."""
    if geom["type"] == "LineString":
        return [geom["coordinates"]]
    if geom["type"] == "MultiLineString":
        return list(geom["coordinates"])
    return []


def main():
    with urllib.request.urlopen(SOURCE, timeout=90) as r:
        feats = json.loads(r.read())["features"]

    # pour chaque fleuve, on accumule les segments dont un nom NE matche un alias
    out = []
    for fr_name, aliases in RIVERS.items():
        al = [a.lower() for a in aliases]
        coords = []
        for f in feats:
            p = f["properties"]
            hay = " ".join(str(p.get(k) or "") for k in ("name", "name_en", "name_alt")).lower()
            if any(a in hay for a in al):
                coords.extend(lines_of(f["geometry"]))
        if not coords:
            print(f"  ⚠ aucun segment pour {fr_name}")
            continue
        out.append({
            "name": fr_name,
            "geometry": {"type": "MultiLineString", "coordinates": round_coords(coords)},
        })

    out.sort(key=lambda r: r["name"])
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(out)} fleuves -> {OUT} ({os.path.getsize(OUT)//1024} Ko)")


if __name__ == "__main__":
    main()
