"""Génère data/peaks.json : sommets célèbres du monde (à placer sur la carte).

Liste curatée (name, lat, lng). On choisit des sommets emblématiques et
suffisamment espacés pour rester distinguables au clic (tolérance du jeu).

Lancer :  python scripts/build_peaks.py
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "data", "peaks.json"))

PEAKS = [
    ("Everest", 27.9881, 86.9250),
    ("K2", 35.8808, 76.5133),
    ("Mont Blanc", 45.8326, 6.8652),
    ("Kilimandjaro", -3.0758, 37.3533),
    ("Denali", 63.0692, -151.0070),
    ("Aconcagua", -32.6533, -70.0109),
    ("Mont Fuji", 35.3606, 138.7274),
    ("Mont Elbrouz", 43.3550, 42.4392),
    ("Mont Kenya", -0.1521, 37.3084),
    ("Mont Toubkal", 31.0606, -7.9150),
    ("Mont Olympe", 40.0850, 22.3586),
    ("Mont Vinson", -78.5254, -85.6171),
    ("Puncak Jaya", -4.0784, 137.1582),
    ("Chimborazo", -1.4690, -78.8175),
    ("Mont Whitney", 36.5785, -118.2923),
    ("Mont Rainier", 46.8523, -121.7603),
    ("Mauna Kea", 19.8207, -155.4681),
    ("Mont Ararat", 39.7019, 44.2983),
    ("Aoraki / Mont Cook", -43.5950, 170.1418),
    ("Mont Sinaï", 28.5394, 33.9750),
    ("Pic du Teide", 28.2724, -16.6425),
    ("Etna", 37.7510, 14.9934),
    ("Mont Logan", 60.5672, -140.4055),
    ("Mont Cameroun", 4.2030, 9.1700),
]


def main():
    data = [{"name": n, "lat": lat, "lng": lng} for n, lat, lng in PEAKS]
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(data)} sommets -> {OUT}")


if __name__ == "__main__":
    main()
