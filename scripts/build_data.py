"""Génère data/countries.json à partir du dataset mledoze/countries.

Source : https://github.com/mledoze/countries (licence ODbL).
On ne garde que les États membres de l'ONU (~194), avec leur nom et leur
capitale en français quand c'est pertinent.

Lancer :  python scripts/build_data.py
"""

import json
import os
import urllib.request

SOURCE = "https://raw.githubusercontent.com/mledoze/countries/master/countries.json"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "data", "countries.json"))

REGION_FR = {
    "Africa": "Afrique",
    "Americas": "Amériques",
    "Asia": "Asie",
    "Europe": "Europe",
    "Oceania": "Océanie",
    "Antarctic": "Antarctique",
}

# Capitales dont le nom français diffère sensiblement de la forme internationale
# fournie par la source. Les autres capitales sont conservées telles quelles
# (elles sont le plus souvent identiques en français).
CAPITAL_FR = {
    "London": "Londres",
    "Moscow": "Moscou",
    "Beijing": "Pékin",
    "Cairo": "Le Caire",
    "Lisbon": "Lisbonne",
    "Athens": "Athènes",
    "Warsaw": "Varsovie",
    "Vienna": "Vienne",
    "Brussels": "Bruxelles",
    "Bucharest": "Bucarest",
    "Copenhagen": "Copenhague",
    "Bern": "Berne",
    "Algiers": "Alger",
    "Damascus": "Damas",
    "Baghdad": "Bagdad",
    "Tehran": "Téhéran",
    "Riyadh": "Riyad",
    "Beirut": "Beyrouth",
    "Kuwait City": "Koweït",
    "Seoul": "Séoul",
    "Hanoi": "Hanoï",
    "Mexico City": "Mexico",
    "Havana": "La Havane",
    "Washington, D.C.": "Washington",
    "Edinburgh": "Édimbourg",
    "Kyiv": "Kiev",
    "Kiev": "Kiev",
    "Chisinau": "Chișinău",
    "Tbilisi": "Tbilissi",
    "Yerevan": "Erevan",
    "Baku": "Bakou",
    "Nicosia": "Nicosie",
    "Valletta": "La Valette",
    "Addis Ababa": "Addis-Abeba",
    "Cape Town": "Le Cap",
    "Khartoum": "Khartoum",
    "Tripoli": "Tripoli",
    "Singapore": "Singapour",
}


def main():
    with urllib.request.urlopen(SOURCE, timeout=30) as resp:
        raw = json.loads(resp.read())

    out = []
    for c in raw:
        if not c.get("unMember"):
            continue
        caps = c.get("capital") or []
        capital = caps[0] if caps else ""
        capital = CAPITAL_FR.get(capital, capital)
        name = c["translations"].get("fra", {}).get("common") or c["name"]["common"]
        out.append(
            {
                "iso2": c["cca2"],
                "iso3": c["cca3"],
                "name": name,
                "capital": capital,
                "region": REGION_FR.get(c.get("region", ""), c.get("region", "")),
                "subregion": c.get("subregion", ""),
                "borders": c.get("borders", []),
                "area": c.get("area"),
            }
        )

    # On ne garde dans les frontières que les pays présents dans notre jeu.
    kept = {c["iso3"] for c in out}
    for c in out:
        c["borders"] = [b for b in c["borders"] if b in kept]

    # Invariant : les QCM de capitales affichent la capitale comme libellé et
    # corrigent sur le pays → deux pays de même capitale donneraient deux choix
    # identiques. On le garantit dès la génération des données.
    caps = [c["capital"] for c in out if c["capital"]]
    dups = sorted({c for c in caps if caps.count(c) > 1})
    assert not dups, f"Capitales en double (QCM ambigu) : {dups}"

    out.sort(key=lambda x: x["name"])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"{len(out)} pays écrits dans {OUT}")


if __name__ == "__main__":
    main()
