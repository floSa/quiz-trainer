"""Génération des questions : sélection pondérée d'un pays + choix de QCM."""

import random

from . import srs, store

# Compétences suivies (maîtrise par compétence × pays, ex. « flag:FRA »).
# Plusieurs jeux peuvent tester la même compétence.
SKILLS = {
    "locate": "Situer sur la carte",
    "flag": "Reconnaître le drapeau",
    "capital": "Connaître la capitale",
}


def pick_country(candidates, state, skill, recent=(), now=None):
    """Choisit un pays à interroger, pondéré vers les connaissances faibles.

    `recent` = iso3 récemment posés, pour éviter les répétitions immédiates.
    """
    recent = set(recent)
    pool = [c for c in candidates if c["iso3"] not in recent] or list(candidates)
    weights = [
        srs.weight(store.get_item(state, skill, c["iso3"]), now=now) for c in pool
    ]
    return random.choices(pool, weights=weights, k=1)[0]


def options(correct, candidates, k=3):
    """k+1 pays mélangés : la bonne réponse + k distracteurs.

    Les distracteurs viennent en priorité de la même région, pour corser.
    """
    same = [
        c for c in candidates
        if c["iso3"] != correct["iso3"] and c["region"] == correct["region"]
    ]
    others = [
        c for c in candidates
        if c["iso3"] != correct["iso3"] and c["region"] != correct["region"]
    ]
    random.shuffle(same)
    random.shuffle(others)
    opts = [correct] + (same + others)[:k]
    random.shuffle(opts)
    return opts
