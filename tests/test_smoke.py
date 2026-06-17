"""Test de fumée Streamlit : chaque page se charge et un tour se joue sans erreur.

Lancer depuis la racine :  python tests/test_smoke.py

Streamlit ajoute le dossier de l'entrypoint au sys.path lors d'un vrai
`streamlit run` ; le harnais AppTest ne le fait pas, on l'ajoute donc ici.
"""

import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from streamlit.testing.v1 import AppTest  # noqa: E402

PAGES = ["app.py"] + sorted(glob.glob("pages/*.py"))

# (fichier, clé de page) couvrant chaque mécanique d'affichage.
CYCLES = [
    ("pages/01_Carte.py", "carte"),             # carte + options texte
    ("pages/04_Trouve_le_drapeau.py", "trouve_drapeau"),  # options drapeaux
    ("pages/09_Situe_le_pays.py", "situe"),     # options cartes
    ("pages/06_Continent.py", "continent"),     # réponse = continent
    ("pages/12_Combien_de_voisins.py", "nb_voisins"),     # réponse numérique
    ("pages/14_Revision_intelligente.py", "revision"),    # mélange adaptatif
]


def test_pages_load():
    assert len(PAGES) == 15, f"attendu 14 pages + accueil, vu {len(PAGES)}"
    for f in PAGES:
        at = AppTest.from_file(f, default_timeout=90).run()
        assert not at.exception, f"{f}: {at.exception}"
    print(f"{len(PAGES)} pages chargées sans erreur")


def test_answer_cycles():
    for f, key in CYCLES:
        at = AppTest.from_file(f, default_timeout=90).run()
        assert not at.exception, f"{f}: {at.exception}"
        opts = [b for b in at.button if b.key and b.key.startswith(f"{key}_opt")]
        assert len(opts) >= 2, f"{f}: {len(opts)} options"

        at.button(key=f"{key}_opt0").click().run()
        assert not at.exception, f"{f} (réponse): {at.exception}"
        feedback = [m.value for m in list(at.success) + list(at.error)]
        assert feedback, f"{f}: aucun retour après réponse"

        at.button(key=f"{key}_next").click().run()
        assert not at.exception, f"{f} (suivant): {at.exception}"
        print(f"{f:42} cycle OK")


if __name__ == "__main__":
    test_pages_load()
    test_answer_cycles()
    print("ALL GOOD")
