"""Test unitaire des générateurs de questions (sans Streamlit).

Vérifie que chaque jeu produit une question cohérente, sur de nombreux tirages
aléatoires. Lancer :  python tests/test_builders.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from geo import data, games, quiz, srs, store  # noqa: E402

BUILDERS = [
    games.build_locate,
    games.build_situate,
    games.build_flag,
    games.build_pick_flag,
    games.build_capital,
    games.build_capital_to_country,
    games.build_flag_to_capital,
    games.build_region,
    games.build_flag_to_region,
    games.build_region_to_country,
    games.build_neighbor,
    games.build_neighbor_count,
    games.build_largest,
    games.build_smart,
]


def test_builders_are_coherent():
    cands = data.load_countries()
    isos = {c["iso3"] for c in cands}
    state = {"items": {}}
    for build in BUILDERS:
        for _ in range(150):
            q = build(cands, state, [])
            assert q["skill"] in quiz.SKILLS, (build.__name__, q["skill"])
            assert q["item"] in isos, (build.__name__, q["item"])
            ids = [o["id"] for o in q["options"]]
            assert len(ids) >= 2, (build.__name__, "trop peu d'options", ids)
            assert len(ids) == len(set(ids)), (build.__name__, "options en double", ids)
            assert q["correct"] in ids, (build.__name__, q["correct"], ids)
            kinds = {o["kind"] for o in q["options"]}
            assert len(kinds) == 1, (build.__name__, "kinds mixtes", kinds)
    print(f"{len(BUILDERS)} générateurs OK (×150 tirages)")


def test_srs_dynamics():
    """Réussir monte la maîtrise et espace ; échouer la fait chuter."""
    item = srs.new_item()
    for _ in range(5):
        item = srs.review(item, correct=True, now=0)
    assert item["m"] > 0.8, item["m"]
    assert item["due"] > 0
    after_fail = srs.review(item, correct=False, now=0)
    assert after_fail["m"] < item["m"]
    assert srs.weight(after_fail, now=0) > srs.weight(item, now=0)
    print("dynamique SRS OK (maîtrise ↑ à la réussite, ↓ à l'échec)")


def test_sampler_favours_weak():
    """Le tirage doit privilégier les connaissances faibles."""
    import statistics

    cands = data.load_countries()
    state = {"items": {}}
    for i, c in enumerate(cands):  # une moitié sue, une moitié fragile
        m = 0.9 if i % 2 == 0 else 0.05
        state["items"][f"flag:{c['iso3']}"] = {
            "m": m, "reps": 3, "lapses": 0, "due": 0, "seen": 0
        }
    picks = [
        store.get_item(state, "flag", quiz.pick_country(cands, state, "flag")["iso3"])["m"]
        for _ in range(800)
    ]
    selected = statistics.mean(picks)
    overall = statistics.mean(c2["m"] for c2 in state["items"].values())
    assert selected < overall, (selected, overall)
    print(f"tirage biaisé vers le faible OK (m tiré {selected:.2f} < global {overall:.2f})")


if __name__ == "__main__":
    test_builders_are_coherent()
    test_srs_dynamics()
    test_sampler_favours_weak()
    print("ALL GOOD")
