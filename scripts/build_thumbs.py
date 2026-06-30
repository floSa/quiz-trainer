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

# --- rendu SVG --------------------------------------------------------------
def viewbox(window):
    lon0, lon1, lat0, lat1 = window
    x0, _ = project(lon0, lat1)
    x1, _ = project(lon1, lat1)
    _, ytop = project(lon0, lat1)
    _, ybot = project(lon0, lat0)
    w, h = x1 - x0, ybot - ytop
    return (x0, ytop, w, h)

def svg(window, grey_paths, red_path, red_dot=None):
    x, y, w, h = viewbox(window)
    sw = max(w, h) / 400
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x:.3f} {y:.3f} {w:.3f} {h:.3f}" preserveAspectRatio="xMidYMid meet">',
        f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" fill="{OCEAN}"/>',
        f'<g stroke="{COAST}" stroke-width="{sw:.4f}" stroke-linejoin="round">',
    ]
    for d in grey_paths:
        parts.append(f'<path d="{d}" fill="{LAND}"/>')
    if red_path:
        parts.append(f'<path d="{red_path}" fill="{RED}"/>')
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
    "Asie": (25, 150, -11, 80),
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

# --- point d'entrée (groupes sélectionnables en argument) -------------------
BUILDERS = {
    "countries": build_countries,
    "dept": build_departments,
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
