"""Génère data/france/monuments.json (~100 monuments français célèbres) ET
télécharge une vignette photo par monument dans data/thumbs/monument-photo/.

Source : Wikidata (SPARQL pour la liste + l'image P18 ; repli via l'API de
recherche pour les incontournables ajoutés à la main). Photos = Wikimedia
Commons (Special:FilePath, redimensionnées à 320 px). Tri par notoriété.

Lancer :  python scripts/build_monuments.py
"""

import json
import os
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "data", "france", "monuments.json"))
PHOTOS = os.path.normpath(os.path.join(HERE, "..", "data", "thumbs", "monument-photo"))

UA = "quiz-trainer/1.0 (projet perso ; https://github.com/floSa/quiz-trainer)"
KEEP = 100
LAT_MIN, LAT_MAX = 41.0, 51.6
LON_MIN, LON_MAX = -5.6, 9.8

QUERY = """
SELECT ?item ?itemLabel (SAMPLE(?lat) AS ?la) (SAMPLE(?lon) AS ?lo)
       (SAMPLE(?img) AS ?image) (MAX(?sl) AS ?s) WHERE {
  ?item wdt:P17 wd:Q142 ; wikibase:sitelinks ?sl ; wdt:P31 ?type .
  VALUES ?type {
    wd:Q4989906 wd:Q751876 wd:Q23413 wd:Q2977 wd:Q163687 wd:Q160742
    wd:Q12518 wd:Q12280 wd:Q16560 wd:Q33506 wd:Q39715 wd:Q570116
    wd:Q34627 wd:Q207694 wd:Q1107656
  }
  FILTER(?sl > 14)
  ?item p:P625/psv:P625 ?cv .
  ?cv wikibase:geoLatitude ?lat ; wikibase:geoLongitude ?lon .
  OPTIONAL { ?item wdt:P18 ?img }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". }
}
GROUP BY ?item ?itemLabel
ORDER BY DESC(?s)
LIMIT 600
"""

EXCLUDE = {"Shakespeare and Company", "La Défense", "Cœur Défense"}
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


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return "".join(c if c.isalnum() else "-" for c in s).strip("-").lower()


def get(url, tries=5):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < tries - 1:
                time.sleep(5 * (i + 1))  # rate-limit Wikimedia → on attend
                continue
            raise


def sparql(q):
    return json.loads(get("https://query.wikidata.org/sparql?" +
                          urllib.parse.urlencode({"query": q, "format": "json"})))["results"]["bindings"]


def api(params):
    return json.loads(get("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(params)))


def img_from_filepath(url):
    return urllib.parse.unquote(url.split("Special:FilePath/")[-1])


def search_image(name):
    """Repli : recherche l'entité par nom puis lit sa P18."""
    try:
        s = api({"action": "wbsearchentities", "search": name, "language": "fr",
                 "format": "json", "limit": 1, "type": "item"}).get("search") or []
        if not s:
            return None
        ent = api({"action": "wbgetentities", "ids": s[0]["id"], "props": "claims", "format": "json"})
        p18 = ent["entities"][s[0]["id"]]["claims"].get("P18")
        return p18[0]["mainsnak"]["datavalue"]["value"] if p18 else None
    except Exception:
        return None


def download_photo(filename, dest):
    url = "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(filename) + "?width=320"
    data = get(url)  # récupéré AVANT d'ouvrir le fichier (sinon fichier vide si échec)
    with open(dest, "wb") as f:
        f.write(data)


def main():
    rows = sparql(QUERY)
    seen, seen_pos, out = set(), set(), []

    def add(name, lat, lng, imgfile):
        pos = (round(lat, 3), round(lng, 3))
        if name in seen or pos in seen_pos or name in EXCLUDE:
            return
        seen.add(name)
        seen_pos.add(pos)
        out.append({"name": name, "lat": lat, "lng": lng, "imgfile": imgfile})

    for name, lat, lng in ESSENTIALS:
        add(name, lat, lng, None)

    for b in rows:
        if len(out) >= KEEP:
            break
        name = b["itemLabel"]["value"]
        if name.startswith("Q") and name[1:].isdigit():
            continue
        lat, lng = round(float(b["la"]["value"]), 4), round(float(b["lo"]["value"]), 4)
        if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lng <= LON_MAX):
            continue
        imgfile = img_from_filepath(b["image"]["value"]) if "image" in b else None
        add(cap(name), lat, lng, imgfile)

    # images manquantes (surtout les incontournables) → repli par recherche
    for m in out:
        if not m["imgfile"]:
            m["imgfile"] = search_image(m["name"])
            time.sleep(0.1)

    # téléchargement des vignettes + écriture du JSON
    os.makedirs(PHOTOS, exist_ok=True)
    ok = 0
    final = []
    for m in out:
        s = slug(m["name"])
        rec = {"name": m["name"], "lat": m["lat"], "lng": m["lng"], "slug": s}
        if m["imgfile"]:
            try:
                download_photo(m["imgfile"], os.path.join(PHOTOS, s + ".jpg"))
                rec["img"] = s + ".jpg"
                ok += 1
                time.sleep(0.4)  # poli avec Wikimedia
            except Exception as e:
                print(f"  photo KO : {m['name']} ({e})")
        final.append(rec)

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(final, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(final)} monuments -> {OUT} ; {ok} photos téléchargées")


if __name__ == "__main__":
    main()
