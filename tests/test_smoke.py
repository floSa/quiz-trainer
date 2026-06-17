"""Test de fumée : charge chaque page et joue une manche, sans erreur.

Lancer depuis la racine du projet :  python tests/test_smoke.py

Streamlit ajoute le dossier de l'entrypoint au sys.path lors d'un vrai
`streamlit run` ; le harnais AppTest ne le fait pas, on l'ajoute donc ici.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from streamlit.testing.v1 import AppTest  # noqa: E402

PAGES = [
    "app.py",
    "pages/1_Carte.py",
    "pages/2_Drapeaux.py",
    "pages/3_Capitales.py",
    "pages/4_Drapeau_express.py",
]


def test_pages_load():
    for f in PAGES:
        at = AppTest.from_file(f, default_timeout=60).run()
        assert not at.exception, f"{f}: {at.exception}"
        print(f"{f:28} OK  (boutons: {len(at.button)})")


def test_answer_cycle():
    at = AppTest.from_file("pages/1_Carte.py", default_timeout=60).run()
    opts = [b for b in at.button if b.key and b.key.startswith("carte_opt")]
    assert len(opts) == 4, f"attendu 4 options, vu {len(opts)}"

    at.button(key="carte_opt0").click().run()
    assert not at.exception, at.exception
    feedback = [m.value for m in list(at.success) + list(at.error)]
    assert feedback, "aucun retour après la réponse"
    print("feedback:", feedback[0])

    at.button(key="carte_next").click().run()
    assert not at.exception, at.exception
    opts2 = [b for b in at.button if b.key and b.key.startswith("carte_opt")]
    assert len(opts2) == 4, "la question suivante ne s'est pas régénérée"
    print("cycle réponse → feedback → suivant OK")


if __name__ == "__main__":
    test_pages_load()
    test_answer_cycle()
    print("ALL GOOD")
