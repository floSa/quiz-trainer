"""Chargement et accès au jeu de données pays (data/countries.json).

Un « pays » est un dict : iso2, iso3, name, capital, region, subregion.
"""

import functools
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.normpath(os.path.join(HERE, "..", "data", "countries.json"))

# Régions (continents) → scope de carte Plotly, pour zoomer sur le bon
# continent. Plotly ne propose pas de scope « Océanie », on retombe alors
# sur la carte du monde.
_REGION_SCOPE = {
    "Afrique": "africa",
    "Asie": "asia",
    "Europe": "europe",
}


@functools.lru_cache(maxsize=1)
def load_countries():
    """Liste de tous les pays, triée par nom."""
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


@functools.lru_cache(maxsize=1)
def by_iso3():
    return {c["iso3"]: c for c in load_countries()}


@functools.lru_cache(maxsize=1)
def regions():
    """Régions disponibles, triées."""
    return sorted({c["region"] for c in load_countries()})


def countries_in(selected_regions):
    """Pays appartenant à l'une des régions données (toutes si vide/None)."""
    if not selected_regions:
        return load_countries()
    wanted = set(selected_regions)
    return [c for c in load_countries() if c["region"] in wanted]


def flag_url(iso2, width=320):
    """URL d'image du drapeau (flagcdn.com). Nécessite une connexion."""
    return f"https://flagcdn.com/w{width}/{iso2.lower()}.png"


def neighbors(country):
    """Pays (de notre jeu) partageant une frontière terrestre avec celui-ci."""
    idx = by_iso3()
    return [idx[b] for b in country.get("borders", []) if b in idx]


def map_scope(country):
    """Scope Plotly adapté pour situer ce pays sur la carte."""
    region = country.get("region", "")
    if region == "Amériques":
        sub = country.get("subregion", "")
        return "south america" if sub == "South America" else "north america"
    return _REGION_SCOPE.get(region, "world")
