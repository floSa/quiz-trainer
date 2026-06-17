"""Générateurs de questions, un par jeu.

Chaque générateur renvoie une **question** (dict) au format unique consommé par
`components.play` :

    skill   : compétence testée (clé de quiz.SKILLS)
    item    : iso3 du pays dont la maîtrise est mise à jour
    prompt  : (kind, payload) — kind ∈ {"map","flag","text"}
    options : [ {id, label, kind, country} ]  (kind ∈ {"text","flag","map"})
    correct : id de la bonne option
    explain : (optionnel) texte affiché après la réponse
    reveal  : (optionnel) (kind, country) illustré après la réponse

Signature commune : build_x(candidates, state, recent, country=None).
Si `country` est fourni (cas de la révision intelligente), on construit la
question pour CE pays ; sinon on en tire un pondéré vers les points faibles.
"""

import random

from . import data, quiz, srs, store


def _q(skill, item, prompt, options, correct, explain=None, reveal=None):
    return {
        "skill": skill,
        "item": item,
        "prompt": prompt,
        "options": options,
        "correct": correct,
        "explain": explain,
        "reveal": reveal,
    }


def _country_opts(countries, label, kind="text"):
    return [
        {"id": c["iso3"], "label": label(c), "kind": kind, "country": c}
        for c in countries
    ]


def _value_opts(values):
    return [{"id": str(v), "label": str(v), "kind": "text", "country": None} for v in values]


# --- Compétence « locate » ------------------------------------------------- #
def build_locate(cands, state, recent, country=None):
    c = country or quiz.pick_country(cands, state, "locate", recent)
    opts = _country_opts(quiz.options(c, cands), lambda x: x["name"])
    return _q("locate", c["iso3"], ("map", c), opts, c["iso3"])


def build_situate(cands, state, recent, country=None):
    """Nom donné → choisir la bonne carte parmi plusieurs."""
    c = country or quiz.pick_country(cands, state, "locate", recent)
    opts = _country_opts(quiz.options(c, cands), lambda x: x["name"], kind="map")
    return _q(
        "locate", c["iso3"],
        ("text", f"Sur quelle carte voit-on **{c['name']}** ?"),
        opts, c["iso3"], reveal=("map", c),
    )


# --- Compétence « flag » --------------------------------------------------- #
def build_flag(cands, state, recent, country=None):
    c = country or quiz.pick_country(cands, state, "flag", recent)
    opts = _country_opts(quiz.options(c, cands), lambda x: x["name"])
    return _q("flag", c["iso3"], ("flag", c), opts, c["iso3"])


def build_pick_flag(cands, state, recent, country=None):
    """Pays donné → choisir le bon drapeau parmi plusieurs."""
    c = country or quiz.pick_country(cands, state, "flag", recent)
    opts = _country_opts(quiz.options(c, cands), lambda x: x["name"], kind="flag")
    return _q(
        "flag", c["iso3"],
        ("text", f"Quel est le drapeau de **{c['name']}** ?"),
        opts, c["iso3"], reveal=("flag", c),
    )


# --- Compétence « capital » ------------------------------------------------ #
def build_capital(cands, state, recent, country=None):
    c = country or quiz.pick_country(cands, state, "capital", recent)
    opts = _country_opts(quiz.options(c, cands), lambda x: x["capital"])
    return _q(
        "capital", c["iso3"],
        ("text", f"Quelle est la capitale de **{c['name']}** ?"),
        opts, c["iso3"],
    )


def build_capital_to_country(cands, state, recent, country=None):
    c = country or quiz.pick_country(cands, state, "capital", recent)
    opts = _country_opts(quiz.options(c, cands), lambda x: x["name"])
    return _q(
        "capital", c["iso3"],
        ("text", f"De quel pays **{c['capital']}** est-elle la capitale ?"),
        opts, c["iso3"],
    )


def build_flag_to_capital(cands, state, recent, country=None):
    c = country or quiz.pick_country(cands, state, "capital", recent)
    opts = _country_opts(quiz.options(c, cands), lambda x: x["capital"])
    return _q(
        "capital", c["iso3"], ("flag", c), opts, c["iso3"],
        explain=f"{c['name']} → {c['capital']}",
    )


# --- Compétence « region » ------------------------------------------------- #
def build_region(cands, state, recent, country=None):
    c = country or quiz.pick_country(cands, state, "region", recent)
    opts = _value_opts(quiz.mcq_values(c["region"], data.regions()))
    return _q(
        "region", c["iso3"],
        ("text", f"Sur quel continent se trouve **{c['name']}** ?"),
        opts, c["region"],
    )


def build_flag_to_region(cands, state, recent, country=None):
    c = country or quiz.pick_country(cands, state, "region", recent)
    opts = _value_opts(quiz.mcq_values(c["region"], data.regions()))
    return _q(
        "region", c["iso3"], ("flag", c), opts, c["region"],
        explain=f"{c['name']} → {c['region']}",
    )


def build_region_to_country(cands, state, recent, country=None):
    c = country or quiz.pick_country(cands, state, "region", recent)
    region = c["region"]
    elsewhere = [x for x in cands if x["region"] != region]
    random.shuffle(elsewhere)
    pool = [c] + elsewhere[:3]
    random.shuffle(pool)
    opts = _country_opts(pool, lambda x: x["name"])
    return _q(
        "region", c["iso3"],
        ("text", f"Lequel de ces pays se trouve en **{region}** ?"),
        opts, c["iso3"],
    )


# --- Compétence « neighbors » ---------------------------------------------- #
def build_neighbor(cands, state, recent, country=None):
    eligible = [x for x in cands if data.neighbors(x)]
    if not eligible:
        return build_region(cands, state, recent)
    if country and data.neighbors(country):
        c = country
    else:
        c = quiz.pick_country(eligible, state, "neighbors", recent)
    nbrs = data.neighbors(c)
    correct = random.choice(nbrs)
    excluded = {n["iso3"] for n in nbrs} | {c["iso3"]}
    non = [x for x in cands if x["iso3"] not in excluded]
    same = [x for x in non if x["region"] == c["region"]]
    others = [x for x in non if x["region"] != c["region"]]
    random.shuffle(same)
    random.shuffle(others)
    pool = [correct] + (same + others)[:3]
    random.shuffle(pool)
    opts = _country_opts(pool, lambda x: x["name"])
    explain = "Voisins : " + ", ".join(n["name"] for n in nbrs)
    return _q(
        "neighbors", c["iso3"],
        ("text", f"Quel pays partage une frontière avec **{c['name']}** ?"),
        opts, correct["iso3"], explain=explain,
    )


def build_neighbor_count(cands, state, recent, country=None):
    eligible = [x for x in cands if data.neighbors(x)]
    if not eligible:
        return build_region(cands, state, recent)
    c = quiz.pick_country(eligible, state, "neighbors", recent)
    nbrs = data.neighbors(c)
    count = len(nbrs)
    distract = sorted({max(0, count + d) for d in (-2, -1, 1, 2, 3)} - {count})
    random.shuffle(distract)
    nums = [count] + distract[:3]
    random.shuffle(nums)
    explain = "Voisins : " + ", ".join(n["name"] for n in nbrs)
    return _q(
        "neighbors", c["iso3"],
        ("text", f"Combien de pays ont une frontière terrestre avec **{c['name']}** ?"),
        _value_opts(nums), str(count), explain=explain,
    )


# --- Compétence « size » --------------------------------------------------- #
def build_largest(cands, state, recent, country=None):
    pool_all = [x for x in cands if x.get("area")]
    focus = quiz.pick_country(pool_all, state, "size", recent)
    others = [x for x in pool_all if x["iso3"] != focus["iso3"]]
    random.shuffle(others)
    four = [focus] + others[:3]
    random.shuffle(four)
    correct = max(four, key=lambda x: x["area"])
    opts = _country_opts(four, lambda x: x["name"])
    explain = " · ".join(
        f"{x['name']} : {int(x['area']):,} km²".replace(",", " ")
        for x in sorted(four, key=lambda x: -x["area"])
    )
    return _q(
        "size", correct["iso3"],
        ("text", "Lequel est le **plus grand** pays (par superficie) ?"),
        opts, correct["iso3"], explain=explain,
    )


# --- Révision intelligente (mélange toutes les compétences) ---------------- #
CANON = {
    "locate": build_locate,
    "flag": build_flag,
    "capital": build_capital,
    "region": build_region,
    "neighbors": build_neighbor,
}


def build_smart(cands, state, recent, country=None):
    """Tire la connaissance (compétence × pays) la plus faible, puis pose la
    question correspondante."""
    recent_set = set(recent)

    def gather(skip_recent):
        pool = []
        for c in cands:
            if skip_recent and c["iso3"] in recent_set:
                continue
            for skill in CANON:
                if skill == "neighbors" and not data.neighbors(c):
                    continue
                w = srs.weight(store.get_item(state, skill, c["iso3"]))
                pool.append((w, skill, c))
        return pool

    pool = gather(skip_recent=True) or gather(skip_recent=False)
    weights = [w for (w, _, _) in pool]
    _, skill, c = random.choices(pool, weights=weights, k=1)[0]
    return CANON[skill](cands, state, recent, country=c)
