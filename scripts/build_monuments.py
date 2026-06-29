"""Génère data/france/monuments.json : ~100 monuments français célèbres.

Source : Wikidata (requête SPARQL). On prend les lieux situés en France d'un
type « monument » (château, cathédrale, tour, pont, abbaye, musée…), triés par
notoriété (nombre de liens interwikis = wikibase:sitelinks), avec coordonnées,
restreints à la France métropolitaine (pour les placer sur la carte FR).

Lancer :  python scripts/build_monuments.py
"""

import json
import os
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "data", "france", "monuments.json"))

ENDPOINT = "https://query.wikidata.org/sparql"
UA = "quiz-trainer/1.0 (projet perso ; https://github.com/floSa/quiz-trainer)"
KEEP = 100

# bbox France métropolitaine (Corse incluse)
LAT_MIN, LAT_MAX = 41.0, 51.6
LON_MIN, LON_MAX = -5.6, 9.8

QUERY = """
SELECT ?item ?itemLabel (SAMPLE(?lat) AS ?la) (SAMPLE(?lon) AS ?lo) (MAX(?sl) AS ?s) WHERE {
  ?item wdt:P17 wd:Q142 ;
        wikibase:sitelinks ?sl ;
        wdt:P31 ?type .
  VALUES ?type {
    wd:Q4989906 wd:Q751876 wd:Q23413 wd:Q2977 wd:Q163687 wd:Q160742
    wd:Q12518 wd:Q12280 wd:Q16560 wd:Q33506 wd:Q39715 wd:Q570116
    wd:Q34627 wd:Q207694 wd:Q1107656
  }
  FILTER(?sl > 14)
  ?item p:P625/psv:P625 ?cv .
  ?cv wikibase:geoLatitude ?lat ; wikibase:geoLongitude ?lon .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". }
}
GROUP BY ?item ?itemLabel
ORDER BY DESC(?s)
LIMIT 600
"""

# Quelques entrées remontées par le type mais qui ne sont pas des monuments.
EXCLUDE = {"Shakespeare and Company", "La Défense", "Cœur Défense"}

# Incontournables que la requête peut manquer (classés autrement sur Wikidata) :
# on les garantit en tête. (name, lat, lng)
ESSENTIALS = [
    ("Mont-Saint-Michel", 48.6361, -1.5115),
    ("Arc de triomphe de l'Étoile", 48.8738, 2.2950),
    ("Cité de Carcassonne", 43.2061, 2.3645),
    ("Arènes de Nîmes", 43.8345, 4.3590),
    ("Cathédrale Notre-Dame de Reims", 49.2537, 4.0344),
    ("Cathédrale Notre-Dame de Chartres", 48.4475, 1.4875),
    ("Cathédrale Notre-Dame de Strasbourg", 48.5817, 7.7510),
    ("Cathédrale Sainte-Cécile d'Albi", 43.9283, 2.1430),
    ("Opéra Garnier", 48.8719, 2.3316),
    ("Panthéon", 48.8462, 2.3464),
    ("Sainte-Chapelle", 48.8554, 2.3450),
    ("Pont Saint-Bénézet", 43.9520, 4.8050),
]


def cap(s):
    return s[0].upper() + s[1:] if s else s


def main():
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": QUERY, "format": "json"})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        rows = json.loads(r.read())["results"]["bindings"]

    seen, seen_pos = set(), set()
    out = []

    def add(name, lat, lng):
        pos = (round(lat, 3), round(lng, 3))  # ~110 m : tue les doublons co-localisés
        if name in seen or pos in seen_pos or name in EXCLUDE:
            return
        seen.add(name)
        seen_pos.add(pos)
        out.append({"name": name, "lat": lat, "lng": lng})

    # 1) incontournables garantis
    for name, lat, lng in ESSENTIALS:
        add(name, lat, lng)

    # 2) complétés par Wikidata (par notoriété décroissante)
    for b in rows:
        if len(out) >= KEEP:
            break
        name = b["itemLabel"]["value"]
        if name.startswith("Q") and name[1:].isdigit():
            continue  # pas de libellé français
        lat = round(float(b["la"]["value"]), 4)
        lng = round(float(b["lo"]["value"]), 4)
        if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lng <= LON_MAX):
            continue  # hors France métropolitaine
        add(cap(name), lat, lng)

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(out)} monuments -> {OUT} ({os.path.getsize(OUT)//1024} Ko)")


if __name__ == "__main__":
    main()
