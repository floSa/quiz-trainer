"""Moteur de maîtrise — répétition espacée simplifiée.

Chaque « connaissance » (compétence × pays) a un état :
    m      : maîtrise dans [0, 1]
    reps   : bonnes réponses cumulées
    lapses : échecs cumulés
    due    : timestamp (epoch s) de prochaine échéance
    seen   : timestamp de dernière présentation

La maîtrise monte vite quand on réussit et chute fort quand on échoue.
L'échéance est d'autant plus proche que la maîtrise est faible : un pays raté
revient dans la session, un pays su revient dans plusieurs jours.
"""

import time

_MIN = 60
_DAY = 86400

# (seuil de maîtrise, délai avant réapparition en secondes)
_INTERVALS = [
    (0.25, 45),          # presque inconnu  → revient tout de suite
    (0.45, 5 * _MIN),    # fragile          → revient dans la session
    (0.65, _DAY),        # en cours         → demain
    (0.80, 3 * _DAY),
    (0.92, 7 * _DAY),
    (1.01, 21 * _DAY),   # solide           → dans trois semaines
]

GAIN = 0.30      # part de l'écart vers 1 gagnée à chaque réussite
PENALTY = 0.35   # maîtrise multipliée par ce facteur à chaque échec
LEARNED = 0.80   # seuil « connaissance acquise »


def new_item():
    return {"m": 0.0, "reps": 0, "lapses": 0, "due": 0.0, "seen": 0.0}


def interval(m):
    for threshold, secs in _INTERVALS:
        if m < threshold:
            return secs
    return _INTERVALS[-1][1]


def review(item, correct, now=None):
    """Renvoie le nouvel état de l'item après une réponse."""
    now = time.time() if now is None else now
    m = item.get("m", 0.0)
    if correct:
        m = m + GAIN * (1.0 - m)
        reps = item.get("reps", 0) + 1
        lapses = item.get("lapses", 0)
    else:
        m = m * PENALTY
        reps = item.get("reps", 0)
        lapses = item.get("lapses", 0) + 1
    return {
        "m": m,
        "reps": reps,
        "lapses": lapses,
        "due": now + interval(m),
        "seen": now,
    }


def weight(item, now=None):
    """Poids de tirage : élevé pour les items faibles et/ou en retard."""
    now = time.time() if now is None else now
    m = item.get("m", 0.0)
    w = (1.0 - m) ** 2 + 0.05
    if item.get("seen", 0.0) and now >= item.get("due", 0.0):
        w *= 4.0   # en retard → priorité
    return w


def is_learned(item):
    return item.get("m", 0.0) >= LEARNED
