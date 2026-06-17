"""Lecteur de jeu générique partagé par toutes les pages.

Un générateur de `geo.games` produit une *question* ; ce module l'affiche,
corrige, met à jour la maîtrise et enchaîne. Tous les jeux passent par `play`.
"""

import plotly.graph_objects as go
import streamlit as st

from . import data, quiz, store


# --------------------------------------------------------------------------- #
# Barre latérale : régions à réviser (partagée entre toutes les pages)
# --------------------------------------------------------------------------- #
def region_sidebar():
    all_regions = data.regions()
    with st.sidebar:
        st.markdown("### 🌍 Régions à réviser")
        sel = st.multiselect(
            "Continents",
            all_regions,
            default=st.session_state.get("regions", all_regions),
            key="regions",
            label_visibility="collapsed",
        )
    return sel or all_regions


# --------------------------------------------------------------------------- #
# Carte du monde avec un pays surligné
# --------------------------------------------------------------------------- #
def render_map(country, height=430, color="#e8453c", scope=None):
    fig = go.Figure(
        go.Choropleth(
            locations=[country["iso3"]],
            z=[1],
            locationmode="ISO-3",
            colorscale=[[0, color], [1, color]],
            showscale=False,
            marker_line_color="white",
            marker_line_width=0.6,
            hoverinfo="skip",
        )
    )
    sc = scope or data.map_scope(country)
    geo = dict(
        scope=sc,
        showcountries=True,
        countrycolor="#c9c9c9",
        showland=True,
        landcolor="#efefef",
        showocean=True,
        oceancolor="#dceaf6",
        showframe=False,
        showcoastlines=False,
        bgcolor="rgba(0,0,0,0)",
    )
    if sc == "world":
        geo["projection_type"] = "natural earth"
    fig.update_geos(**geo)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=height)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def _render_visual(spec, big=True):
    """Affiche un stimulus (carte / drapeau / texte)."""
    kind, payload = spec
    if kind == "map":
        render_map(payload)
    elif kind == "flag":
        if big:
            st.image(data.flag_url(payload["iso2"]), width=320)
        else:
            st.image(data.flag_url(payload["iso2"]), width=240, caption=payload["name"])
    elif kind == "text":
        st.subheader(payload)


# --------------------------------------------------------------------------- #
# Machine à états
# --------------------------------------------------------------------------- #
def _ss(page_key, suffix):
    return f"{page_key}_{suffix}"


def _grade(page_key, q, chosen_id, candidates):
    correct = chosen_id == q["correct"]
    state = store.load()
    updated = store.record(state, q["skill"], q["item"], correct)
    store.save(state)

    recent = st.session_state.get(_ss(page_key, "recent"), [])
    recent.append(q["item"])
    cap = max(1, min(8, len(candidates) // 3))
    st.session_state[_ss(page_key, "recent")] = recent[-cap:]

    st.session_state[_ss(page_key, "answered")] = True
    st.session_state[_ss(page_key, "correct")] = correct
    st.session_state[_ss(page_key, "m")] = updated["m"]
    st.session_state[_ss(page_key, "asked")] = (
        st.session_state.get(_ss(page_key, "asked"), 0) + 1
    )
    if correct:
        st.session_state[_ss(page_key, "ok")] = (
            st.session_state.get(_ss(page_key, "ok"), 0) + 1
        )


def _render_options(page_key, q, candidates):
    opts = q["options"]
    kind = opts[0]["kind"]
    if kind == "text":
        cols = st.columns(2)
        for i, o in enumerate(opts):
            if cols[i % 2].button(
                o["label"], key=_ss(page_key, f"opt{i}"), width="stretch"
            ):
                _grade(page_key, q, o["id"], candidates)
                st.rerun()
    else:  # "flag" ou "map" : grille d'images cliquables
        for row in range(0, len(opts), 2):
            cols = st.columns(2)
            for j, o in enumerate(opts[row : row + 2]):
                with cols[j]:
                    if kind == "flag":
                        st.image(data.flag_url(o["country"]["iso2"]), width="stretch")
                    else:
                        render_map(o["country"], height=200, scope="world")
                    if st.button(
                        "Choisir", key=_ss(page_key, f"opt{row + j}"), width="stretch"
                    ):
                        _grade(page_key, q, o["id"], candidates)
                        st.rerun()


def _feedback(page_key, q):
    correct = st.session_state[_ss(page_key, "correct")]
    correct_opt = next((o for o in q["options"] if o["id"] == q["correct"]), None)
    label = correct_opt["label"] if correct_opt and correct_opt["label"] else q["correct"]
    if correct:
        st.success("✅ Bravo !")
    else:
        st.error(f"❌ Raté — la bonne réponse : **{label}**.")
    if q.get("reveal"):
        _render_visual(q["reveal"], big=False)
    if q.get("explain"):
        st.caption(q["explain"])
    m = st.session_state.get(_ss(page_key, "m"), 0.0)
    st.caption(f"Maîtrise « {quiz.SKILLS[q['skill']]} » : {round(m * 100)} %")
    if st.button("Suivant ▶", type="primary", key=_ss(page_key, "next")):
        st.session_state[_ss(page_key, "q")] = None
        st.rerun()


def _session_caption(page_key):
    asked = st.session_state.get(_ss(page_key, "asked"), 0)
    if asked:
        ok = st.session_state.get(_ss(page_key, "ok"), 0)
        st.caption(f"Session : {ok}/{asked} bonnes réponses")


def play(page_key, build):
    """Boucle de jeu : `build(candidates, state, recent)` fabrique la question."""
    candidates = data.countries_in(region_sidebar())
    if st.session_state.get(_ss(page_key, "q")) is None:
        recent = st.session_state.get(_ss(page_key, "recent"), [])
        st.session_state[_ss(page_key, "q")] = build(candidates, store.load(), recent)
        st.session_state[_ss(page_key, "answered")] = False
    q = st.session_state[_ss(page_key, "q")]

    _render_visual(q["prompt"])
    if not st.session_state[_ss(page_key, "answered")]:
        _render_options(page_key, q, candidates)
    else:
        _feedback(page_key, q)
    _session_caption(page_key)
