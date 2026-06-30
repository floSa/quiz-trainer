"""Génère data/france/prefectures.json : chef-lieu (préfecture) par département.

Source : Wikidata (P31 = département français Q6465, P2586 = code INSEE,
P36 = capitale administrative). On ne garde que les 96 départements
métropolitains présents dans departements.geojson.

Lancer :  python scripts/build_prefectures.py
"""

import json
import os
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
FR = os.path.normpath(os.path.join(HERE, "..", "data", "france"))
OUT = os.path.join(FR, "prefectures.json")
UA = "quiz-trainer/1.0 (projet perso ; https://github.com/floSa/quiz-trainer)"

QUERY = """
SELECT ?code ?prefLabel WHERE {
  ?dep wdt:P31 wd:Q6465 ; wdt:P2586 ?code ; wdt:P36 ?pref .
  ?pref rdfs:label ?prefLabel . FILTER(lang(?prefLabel) = "fr")
}
"""


def sparql(q, tries=4):
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"})
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read())["results"]["bindings"]
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(4)


def main():
    dep_ids = {f["id"] for f in json.load(open(os.path.join(FR, "departements.geojson"), encoding="utf-8"))["features"]}
    prefs = {}
    for b in sparql(QUERY):
        code = b["code"]["value"]
        if code in dep_ids:
            prefs[code] = b["prefLabel"]["value"]
    missing = sorted(dep_ids - set(prefs))
    if missing:
        print("préfectures manquantes :", missing)
    out = {k: prefs[k] for k in sorted(prefs)}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(out)} préfectures -> {OUT}")


if __name__ == "__main__":
    main()
