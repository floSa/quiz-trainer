"""Génère data/cities_world.json : les grandes villes du monde à placer.

Pour chaque pays (parmi nos 194), on garde de 1 à 10 villes connues — plus le
pays est peuplé/grand, plus il a droit à de villes — en prenant les plus
peuplées (gage de notoriété).

Sources (GeoNames, CC-BY) :
  - villes      : cities15000.zip  (villes >= 15 000 hab.)
  - population  : countryInfo.txt

Lancer :  python scripts/build_cities_world.py
"""

import io
import json
import os
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
COUNTRIES = os.path.normpath(os.path.join(HERE, "..", "data", "countries.json"))
OUT = os.path.normpath(os.path.join(HERE, "..", "data", "cities_world.json"))

CITIES = "https://download.geonames.org/export/dump/cities15000.zip"
COUNTRYINFO = "https://download.geonames.org/export/dump/countryInfo.txt"

# Exonymes français des villes les plus connues (GeoNames donne la forme
# internationale). On n'en couvre que quelques-unes, les plus emblématiques.
CITY_FR = {
    "Beijing": "Pékin", "Moscow": "Moscou", "London": "Londres",
    "Lisbon": "Lisbonne", "Athens": "Athènes", "Cairo": "Le Caire",
    "Warsaw": "Varsovie", "Vienna": "Vienne", "Geneva": "Genève",
    "Brussels": "Bruxelles", "Antwerp": "Anvers", "Venice": "Venise",
    "Seville": "Séville", "Edinburgh": "Édimbourg", "Copenhagen": "Copenhague",
    "The Hague": "La Haye", "Bucharest": "Bucarest", "Tehran": "Téhéran",
    "Damascus": "Damas", "Algiers": "Alger", "Beirut": "Beyrouth",
    "Munich": "Munich", "Cologne": "Cologne", "Florence": "Florence",
    "Naples": "Naples", "Genoa": "Gênes", "Turin": "Turin",
    "Saint Petersburg": "Saint-Pétersbourg", "Kolkata": "Calcutta",
    "Hô Chi Minh City": "Hô-Chi-Minh-Ville", "Ho Chi Minh City": "Hô-Chi-Minh-Ville",
}


def fetch(url):
    with urllib.request.urlopen(url, timeout=120) as r:
        return r.read()


def n_cities(pop, area):
    """1..10 villes selon population (principal) et superficie (bonus)."""
    for thr, n in [(3e6, 1), (8e6, 2), (20e6, 3), (40e6, 4),
                   (70e6, 5), (100e6, 6), (200e6, 8)]:
        if pop < thr:
            base = n
            break
    else:
        base = 10
    if area > 2_000_000:
        base += 2
    elif area > 700_000:
        base += 1
    return max(1, min(10, base))


def main():
    countries = json.load(open(COUNTRIES, encoding="utf-8"))
    iso2_to_iso3 = {c["iso2"]: c["iso3"] for c in countries}
    name_fr = {c["iso3"]: c["name"] for c in countries}
    area_by = {c["iso3"]: c.get("area", 0) for c in countries}

    # population par iso3 (countryInfo.txt : col0=iso2, col7=population)
    pop_by = {}
    for line in fetch(COUNTRYINFO).decode("utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        f = line.split("\t")
        if len(f) > 7 and f[0] in iso2_to_iso3 and f[7].isdigit():
            pop_by[iso2_to_iso3[f[0]]] = int(f[7])

    # villes par iso3 (on écarte les sections PPLX et les noms à chiffre)
    z = zipfile.ZipFile(io.BytesIO(fetch(CITIES)))
    by_country = {}
    for line in z.read("cities15000.txt").decode("utf-8").splitlines():
        c = line.split("\t")
        iso3 = iso2_to_iso3.get(c[8])
        if not iso3 or c[7] == "PPLX" or not c[14].isdigit():
            continue
        name = CITY_FR.get(c[1], c[1])
        if any(ch.isdigit() for ch in name):
            continue
        by_country.setdefault(iso3, {})
        cur = by_country[iso3].get(name)
        pop = int(c[14])
        if cur is None or pop > cur["pop"]:
            by_country[iso3][name] = {
                "name": name,
                "iso3": iso3,
                "country": name_fr.get(iso3, iso3),
                "lat": round(float(c[4]), 4),
                "lng": round(float(c[5]), 4),
                "pop": pop,
            }

    out = []
    for iso3, cities in by_country.items():
        n = n_cities(pop_by.get(iso3, 0), area_by.get(iso3, 0))
        top = sorted(cities.values(), key=lambda x: -x["pop"])[:n]
        out.extend(top)
    out.sort(key=lambda x: -x["pop"])

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(out)} villes ({len(by_country)} pays) -> {OUT} "
          f"({os.path.getsize(OUT)//1024} Ko)")


if __name__ == "__main__":
    main()
