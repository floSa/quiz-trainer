"""Briques d'interface partagées par les pages de jeu.

Une « manche » suit toujours le même cycle :
    1. tirer une question (pays + options) si aucune n'est active ;
    2. afficher le stimulus (carte / drapeau / texte) ;
    3. proposer les réponses ;
    4. corriger, mettre à jour la maîtrise, afficher le retour, puis « Suivant ».
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
def render_map(country, height=430, color="#e8453c"):
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
    scope = data.map_scope(country)
    geo = dict(
        scope=scope,
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
    if scope == "world":
        geo["projection_type"] = "natural earth"
    fig.update_geos(**geo)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=height)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


# --------------------------------------------------------------------------- #
# Machine à états interne
# --------------------------------------------------------------------------- #
def _ss(page_key, suffix):
    return f"{page_key}_{suffix}"


def _new_question(page_key, skill, candidates, n_choices):
    state = store.load()
    recent = st.session_state.get(_ss(page_key, "recent"), [])
    country = quiz.pick_country(candidates, state, skill, recent=recent)
    opts = quiz.options(country, candidates, k=n_choices - 1)
    st.session_state[_ss(page_key, "q")] = {"country": country, "options": opts}
    st.session_state[_ss(page_key, "answered")] = False


def _grade(page_key, skill, chosen, candidates):
    q = st.session_state[_ss(page_key, "q")]
    target = q["country"]["iso3"]
    correct = chosen["iso3"] == target

    state = store.load()
    updated = store.record(state, skill, target, correct)
    store.save(state)

    recent = st.session_state.get(_ss(page_key, "recent"), [])
    recent.append(target)
    cap = max(1, min(8, len(candidates) // 3))
    st.session_state[_ss(page_key, "recent")] = recent[-cap:]

    st.session_state[_ss(page_key, "answered")] = True
    st.session_state[_ss(page_key, "correct")] = correct
    st.session_state[_ss(page_key, "chosen")] = chosen["iso3"]
    st.session_state[_ss(page_key, "m")] = updated["m"]
    st.session_state[_ss(page_key, "asked")] = (
        st.session_state.get(_ss(page_key, "asked"), 0) + 1
    )
    if correct:
        st.session_state[_ss(page_key, "ok")] = (
            st.session_state.get(_ss(page_key, "ok"), 0) + 1
        )


def _session_caption(page_key):
    asked = st.session_state.get(_ss(page_key, "asked"), 0)
    if asked:
        ok = st.session_state.get(_ss(page_key, "ok"), 0)
        st.caption(f"Session : {ok}/{asked} bonnes réponses")


def _feedback(page_key, skill, reveal):
    q = st.session_state[_ss(page_key, "q")]
    correct = st.session_state[_ss(page_key, "correct")]
    country = q["country"]
    if correct:
        st.success(f"✅ Bravo — c'est bien **{country['name']}**.")
    else:
        st.error(f"❌ Raté — c'était **{country['name']}**.")
    if reveal:
        reveal(q, correct)
    m = st.session_state.get(_ss(page_key, "m"), 0.0)
    st.caption(
        f"Maîtrise « {quiz.SKILLS[skill]} » pour {country['name']} : {round(m * 100)} %"
    )
    if st.button("Suivant ▶", type="primary", key=_ss(page_key, "next")):
        st.session_state[_ss(page_key, "q")] = None
        st.rerun()


# --------------------------------------------------------------------------- #
# Jeu à choix « texte » : carte, drapeau→pays, capitales
# --------------------------------------------------------------------------- #
def play_text_choice(page_key, skill, prompt, label, reveal=None, n_choices=4):
    """`prompt(question)` affiche le stimulus ; `label(country)` est le texte
    d'un bouton-réponse ; `reveal(question, correct)` (optionnel) ajoute un
    complément au retour."""
    candidates = data.countries_in(region_sidebar())
    if st.session_state.get(_ss(page_key, "q")) is None:
        _new_question(page_key, skill, candidates, n_choices)
    q = st.session_state[_ss(page_key, "q")]

    prompt(q)

    if not st.session_state[_ss(page_key, "answered")]:
        cols = st.columns(2)
        for i, opt in enumerate(q["options"]):
            if cols[i % 2].button(
                label(opt), key=_ss(page_key, f"opt{i}"), width="stretch"
            ):
                _grade(page_key, skill, opt, candidates)
                st.rerun()
    else:
        _feedback(page_key, skill, reveal)
    _session_caption(page_key)


# --------------------------------------------------------------------------- #
# Jeu « choisis le bon drapeau » : pays→drapeau (grille d'images)
# --------------------------------------------------------------------------- #
def play_flag_choice(page_key, skill="flag", n_choices=4):
    candidates = data.countries_in(region_sidebar())
    if st.session_state.get(_ss(page_key, "q")) is None:
        _new_question(page_key, skill, candidates, n_choices)
    q = st.session_state[_ss(page_key, "q")]

    st.subheader(f"Quel est le drapeau de **{q['country']['name']}** ?")

    if not st.session_state[_ss(page_key, "answered")]:
        for row in range(0, len(q["options"]), 2):
            cols = st.columns(2)
            for j, opt in enumerate(q["options"][row : row + 2]):
                with cols[j]:
                    st.image(data.flag_url(opt["iso2"]), width="stretch")
                    if st.button(
                        "Celui-ci", key=_ss(page_key, f"opt{row + j}"),
                        width="stretch",
                    ):
                        _grade(page_key, skill, opt, candidates)
                        st.rerun()
    else:
        def reveal(question, correct):
            st.image(
                data.flag_url(question["country"]["iso2"]),
                width=240,
                caption=question["country"]["name"],
            )
        _feedback(page_key, skill, reveal)
    _session_caption(page_key)
