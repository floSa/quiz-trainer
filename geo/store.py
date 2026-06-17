"""Persistance de la progression (mono-utilisateur) dans progress/progress.json.

État global : {"items": {"<skill>:<iso3>": <item srs>, ...}}
"""

import json
import os

from . import srs

HERE = os.path.dirname(os.path.abspath(__file__))
PROGRESS_DIR = os.path.normpath(os.path.join(HERE, "..", "progress"))
PROGRESS_PATH = os.path.join(PROGRESS_DIR, "progress.json")


def item_key(skill, iso3):
    return f"{skill}:{iso3}"


def load():
    try:
        with open(PROGRESS_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    data.setdefault("items", {})
    return data


def save(state):
    os.makedirs(PROGRESS_DIR, exist_ok=True)
    tmp = PROGRESS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, PROGRESS_PATH)


def get_item(state, skill, iso3):
    return state["items"].get(item_key(skill, iso3), srs.new_item())


def record(state, skill, iso3, correct, now=None):
    """Met à jour l'item et renvoie son nouvel état (n'écrit pas sur disque)."""
    updated = srs.review(get_item(state, skill, iso3), correct, now=now)
    state["items"][item_key(skill, iso3)] = updated
    return updated


def reset():
    try:
        os.remove(PROGRESS_PATH)
    except FileNotFoundError:
        pass
