"""Génère des miniatures SVG de localisation dans data/thumbs/.

Pur stdlib. Projection Web Mercator (x = lng en radians, y = -ln(tan(...))).
Chaque miniature = entités d'un groupe en gris, la cible en rouge, cadrée
(viewBox) sur une fenêtre lon/lat. Servies en <img> dans la page « Apprendre »
(aucune carte Leaflet → pas de rechargement par ligne).

Lancer :  python scripts/build_thumbs.py
"""

import json
import math
import os
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data"))
THUMBS = os.path.join(DATA, "thumbs")

OCEAN = "#a9d2ea"
LAND = "#e8efe2"
COAST = "#7e96a9"
RED = "#e8453c"

# --- projection -------------------------------------------------------------
def merc(lat):
    lat = max(-85.0, min(85.0, lat))
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))

def project(lng, lat):
    return (math.radians(lng), -merc(lat))

# --- simplification Douglas-Peucker (en degrés, planaire) -------------------
EPS = 0.25       # tolérance ~25 km : contours reconnaissables, fichiers légers
MIN_ISLAND = 0.6  # on jette les anneaux de contexte plus petits que ça (degrés)

def _seg_dist(p, a, b):
    px, py = p; ax, ay = a; bx, by = b
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

def douglas_peucker(points, eps):
    n = len(points)
    if n < 3:
        return points
    keep = [False] * n
    keep[0] = keep[n - 1] = True
    stack = [(0, n - 1)]
    while stack:
        i, j = stack.pop()
        dmax, idx = 0.0, -1
        for k in range(i + 1, j):
            d = _seg_dist(points[k], points[i], points[j])
            if d > dmax:
                dmax, idx = d, k
        if dmax > eps and idx > 0:
            keep[idx] = True
            stack.append((i, idx))
            stack.append((idx, j))
    return [points[k] for k in range(n) if keep[k]]

def ring_path(ring, skip_small, eps, min_island):
    if len(ring) < 4:
        return ""
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    if skip_small and (max(xs) - min(xs)) < min_island and (max(ys) - min(ys)) < min_island:
        return ""  # îlot de contexte → ignoré
    simp = douglas_peucker([(p[0], p[1]) for p in ring], eps)
    if len(simp) < 3:
        return ""
    pts, last = [], None
    for lng, lat in simp:
        x, y = project(lng, lat)
        p = (round(x, 4), round(y, 4))
        if p != last:
            pts.append(p)
            last = p
    if len(pts) < 3:
        return ""
    return "M" + " ".join(f"{x},{y}" for x, y in pts) + "Z"

def geom_path(geom, skip_small=True, eps=EPS, min_island=MIN_ISLAND):
    t = geom["type"]
    polys = [geom["coordinates"]] if t == "Polygon" else geom["coordinates"] if t == "MultiPolygon" else []
    out = [ring_path(ring, skip_small, eps, min_island) for poly in polys for ring in poly]
    return " ".join(d for d in out if d)

def line_path(geom, eps=0.1):
    t = geom["type"]
    lines = [geom["coordinates"]] if t == "LineString" else geom["coordinates"] if t == "MultiLineString" else []
    out = []
    for line in lines:
        simp = douglas_peucker([(p[0], p[1]) for p in line], eps)
        pts, last = [], None
        for lng, lat in simp:
            x, y = project(lng, lat)
            p = (round(x, 4), round(y, 4))
            if p != last:
                pts.append(p)
                last = p
        if len(pts) >= 2:
            out.append("M" + " ".join(f"{x},{y}" for x, y in pts))
    return " ".join(out)

def centroid(geom):
    pts = []
    def walk(x):
        if x and isinstance(x[0], (int, float)):
            pts.append(x)
        else:
            for y in x:
                walk(y)
    walk(geom["coordinates"])
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)

def bbox(geom):
    pts = []
    def walk(x):
        if x and isinstance(x[0], (int, float)):
            pts.append(x)
        else:
            for y in x:
                walk(y)
    walk(geom["coordinates"])
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), max(xs), min(ys), max(ys))

# --- rendu SVG --------------------------------------------------------------
def viewbox(window):
    lon0, lon1, lat0, lat1 = window
    x0, _ = project(lon0, lat1)
    x1, _ = project(lon1, lat1)
    _, ytop = project(lon0, lat1)
    _, ybot = project(lon0, lat0)
    w, h = x1 - x0, ybot - ytop
    return (x0, ytop, w, h)

def svg(window, grey_paths, red_path=None, red_dot=None, red_line=None, red_zone=None):
    x, y, w, h = viewbox(window)
    sw = max(w, h) / 400
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x:.3f} {y:.3f} {w:.3f} {h:.3f}" preserveAspectRatio="xMidYMid meet">',
        f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" fill="{OCEAN}"/>',
        f'<g stroke="{COAST}" stroke-width="{sw:.4f}" stroke-linejoin="round">',
    ]
    for d in grey_paths:
        parts.append(f'<path d="{d}" fill="{LAND}"/>')
    if red_path:  # pays / entité administrative : rempli plein
        parts.append(f'<path d="{red_path}" fill="{RED}"/>')
    if red_zone:  # zone (mer, désert, chaîne) : polygone rouge translucide
        parts.append(f'<path d="{red_zone}" fill="{RED}" fill-opacity="0.5" stroke="{RED}" stroke-width="{sw:.4f}"/>')
    if red_line:  # fleuve : trait rouge épais
        parts.append(f'<path d="{red_line}" fill="none" stroke="{RED}" stroke-width="{sw * 3.5:.4f}" stroke-linecap="round"/>')
    if red_dot:  # cible minuscule (micro-État) ou point (sommet) : pastille rouge
        cx, cy = project(red_dot[0], red_dot[1])
        parts.append(f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{max(w, h) / 55:.3f}" fill="{RED}" stroke="#fff" stroke-width="{sw:.4f}"/>')
    parts.append("</g></svg>")
    return "".join(parts)

def write_svg(group, name, content):
    d = os.path.join(THUMBS, group)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name + ".svg"), "w", encoding="utf-8") as f:
        f.write(content)

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return "".join(c if c.isalnum() else "-" for c in s).strip("-").lower()

# --- pays (groupés par bloc continental) ------------------------------------
BLOCKS = {
    "Europe": {"Western Europe", "Eastern Europe", "Northern Europe",
               "Southern Europe", "Central Europe", "Southeast Europe"},
    "Afrique": {"Northern Africa", "Western Africa", "Eastern Africa",
                "Middle Africa", "Southern Africa"},
    "Asie": {"Central Asia", "Eastern Asia", "Western Asia",
             "Southern Asia", "South-Eastern Asia"},
    "Amérique du Nord": {"North America", "Central America", "Caribbean"},
    "Amérique du Sud": {"South America"},
    "Océanie": {"Australia and New Zealand", "Melanesia", "Micronesia", "Polynesia"},
}
WINDOWS = {
    "Europe": (-25, 45, 33, 72),
    "Afrique": (-19, 52, -37, 38),
    "Asie": (25, 147, -11, 58),  # lat plafonnée : sinon l'Arctique (Mercator) tasse le continent
    "Amérique du Nord": (-170, -52, 7, 74),
    "Amérique du Sud": (-82, -34, -56, 13),
    "Océanie": (110, 179, -48, 0),
}

def block_of(subregion):
    for name, subs in BLOCKS.items():
        if subregion in subs:
            return name
    return None

def build_countries():
    geo = json.load(open(os.path.join(DATA, "world.geojson"), encoding="utf-8"))
    countries = json.load(open(os.path.join(DATA, "countries.json"), encoding="utf-8"))
    sub = {c["iso3"]: c["subregion"] for c in countries}
    feat = {f["id"]: f for f in geo["features"]}

    n = 0
    for block, window in WINDOWS.items():
        members = [iso for iso, s in sub.items() if block_of(s) == block and iso in feat]
        grey_all = {iso: geom_path(feat[iso]["geometry"], skip_small=True) for iso in members}
        red_all = {iso: geom_path(feat[iso]["geometry"], skip_small=False) for iso in members}
        for target in members:
            grey = [grey_all[iso] for iso in members if iso != target and grey_all[iso]]
            dot = None if red_all[target] else centroid(feat[target]["geometry"])
            content = svg(window, grey, red_all[target], dot)
            write_svg("countries", target, content)
            n += 1
    print(f"countries : {n} miniatures")

# --- générique : groupe de polygones (départements, arr., états US) ---------
# eps_grey > eps_red : le contexte (gris, répété partout) est plus grossier que
# la cible (détaillée) → fichiers nettement plus légers.
def build_polys(group, features, window, eps_grey, eps_red, min_island):
    grey = {f["id"]: geom_path(f["geometry"], True, eps_grey, min_island) for f in features}
    red = {f["id"]: geom_path(f["geometry"], False, eps_red, min_island / 3) for f in features}
    n = 0
    for f in features:
        tid = f["id"]
        greys = [grey[i] for i in grey if i != tid and grey[i]]
        dot = None if red[tid] else centroid(f["geometry"])
        write_svg(group, str(tid), svg(window, greys, red[tid], dot))
        n += 1
    print(f"{group} : {n} miniatures")

FR_WINDOW = (-5.2, 9.7, 41.3, 51.1)

def build_departments():
    dep = json.load(open(os.path.join(DATA, "france", "departements.geojson"), encoding="utf-8"))
    build_polys("dept", dep["features"], FR_WINDOW, eps_grey=0.1, eps_red=0.03, min_island=0.08)

def france_base():
    dep = json.load(open(os.path.join(DATA, "france", "departements.geojson"), encoding="utf-8"))
    return [d for d in (geom_path(f["geometry"], True, 0.1, 0.08) for f in dep["features"]) if d]

def build_monuments():
    base = france_base()
    mons = json.load(open(os.path.join(DATA, "france", "monuments.json"), encoding="utf-8"))
    for m in mons:
        write_svg("monument", m["slug"], svg(FR_WINDOW, base, "", (m["lng"], m["lat"])))
    print(f"monument : {len(mons)} miniatures")

PARIS_WINDOW = (2.21, 2.48, 48.80, 48.91)
US_WINDOW = (-125, -66.5, 24, 49.5)

def build_arr():
    paris = json.load(open(os.path.join(DATA, "france", "paris.geojson"), encoding="utf-8"))
    # Paris est minuscule → simplification très fine (sinon contours en escalier).
    build_polys("arr", paris["features"], PARIS_WINDOW, eps_grey=0.0012, eps_red=0.0005, min_island=0.001)

def build_usa():
    usa = json.load(open(os.path.join(DATA, "usa", "states.geojson"), encoding="utf-8"))
    build_polys("usa", usa["features"], US_WINDOW, eps_grey=0.2, eps_red=0.07, min_island=0.25)

# Entités sur fond mondial (DOM-TOM, sommets, fleuves, mers, déserts, chaînes) :
# fenêtre régionale + pays voisins en gris (filtrés par bbox pour rester légers).
def _world_grey():
    geo = json.load(open(os.path.join(DATA, "world.geojson"), encoding="utf-8"))
    paths, boxes = {}, {}
    for f in geo["features"]:
        d = geom_path(f["geometry"], skip_small=True, eps=0.3, min_island=1.0)
        if d:
            paths[f["id"]] = d
            boxes[f["id"]] = bbox(f["geometry"])
    return paths, boxes

def _hits(b, w):
    return not (b[1] < w[0] or b[0] > w[1] or b[3] < w[2] or b[2] > w[3])

def _window_around(b, pad_frac=0.2, pad_min=2.0):
    plng = max((b[1] - b[0]) * pad_frac, pad_min)
    plat = max((b[3] - b[2]) * pad_frac, pad_min)
    return (b[0] - plng, b[1] + plng, max(-84, b[2] - plat), min(84, b[3] + plat))

def build_world_points(group, items, half_lng, half_lat):
    paths, boxes = _world_grey()
    for it in items:
        lng, lat = it["lng"], it["lat"]
        w = (lng - half_lng, lng + half_lng, max(-84, lat - half_lat), min(84, lat + half_lat))
        greys = [paths[i] for i in paths if _hits(boxes[i], w)]
        write_svg(group, slug(it["name"]), svg(w, greys, red_dot=(lng, lat)))
    print(f"{group} : {len(items)} miniatures")

def build_world_features(group, items, kind):  # kind : "zone" (polygone) | "river" (ligne)
    paths, boxes = _world_grey()
    for it in items:
        # zones (mers/déserts/chaînes) un peu plus larges → un poil dézoomées
        w = _window_around(bbox(it["geometry"]),
                           pad_frac=0.2 if kind == "river" else 0.35,
                           pad_min=2.0 if kind == "river" else 4.0)
        greys = [paths[i] for i in paths if _hits(boxes[i], w)]
        if kind == "river":
            content = svg(w, greys, red_line=line_path(it["geometry"], eps=0.1))
        else:
            content = svg(w, greys, red_zone=geom_path(it["geometry"], skip_small=False, eps=0.15, min_island=0.0))
        write_svg(group, slug(it["name"]), content)
    print(f"{group} : {len(items)} miniatures")

def _load(name):
    return json.load(open(os.path.join(DATA, name), encoding="utf-8"))

def build_domtom():
    build_world_points("domtom", _load("france/domtom.json"), half_lng=20, half_lat=14)

def build_peaks():
    build_world_points("peak", _load("peaks.json"), half_lng=15, half_lat=11)

def build_rivers():
    build_world_features("river", _load("rivers.json"), "river")

def build_seas():
    build_world_features("sea", _load("seas.json"), "zone")

def build_deserts():
    build_world_features("desert", _load("deserts.json"), "zone")

def build_ranges():
    build_world_features("range", _load("ranges.json"), "zone")

# --- point d'entrée (groupes sélectionnables en argument) -------------------
BUILDERS = {
    "countries": build_countries,
    "dept": build_departments,
    "monument": build_monuments,
    "arr": build_arr,
    "usa": build_usa,
    "domtom": build_domtom,
    "peak": build_peaks,
    "river": build_rivers,
    "sea": build_seas,
    "desert": build_deserts,
    "range": build_ranges,
}

def main():
    groups = sys.argv[1:] or list(BUILDERS)
    for g in groups:
        if g in BUILDERS:
            BUILDERS[g]()
        else:
            print(f"groupe inconnu : {g}")

if __name__ == "__main__":
    main()
