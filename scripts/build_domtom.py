"""Génère data/france/domtom.json : les territoires français d'outre-mer.

Liste curatée (les plus connus : 5 DROM + principales collectivités), avec un
point représentatif (lat, lng). Le jeu « place le DOM-TOM » sert à situer le
territoire sur le globe (quel océan / quelle région), d'où une tolérance large.

Lancer :  python scripts/build_domtom.py
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "data", "france", "domtom.json"))

# name, lat, lng — point représentatif du territoire
TERRITOIRES = [
    ("Guadeloupe", 16.25, -61.58),
    ("Martinique", 14.64, -61.02),
    ("Guyane", 4.00, -53.00),
    ("La Réunion", -21.11, 55.53),
    ("Mayotte", -12.83, 45.16),
    ("Nouvelle-Calédonie", -21.30, 165.50),
    ("Polynésie française", -17.68, -149.41),
    ("Saint-Pierre-et-Miquelon", 46.88, -56.32),
    ("Wallis-et-Futuna", -13.30, -176.20),
    ("Saint-Martin", 18.08, -63.05),
]


def main():
    data = [{"name": n, "lat": lat, "lng": lng} for n, lat, lng in TERRITOIRES]
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(data)} territoires -> {OUT}")


if __name__ == "__main__":
    main()
