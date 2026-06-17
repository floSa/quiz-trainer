"""Révision intelligente : pioche automatiquement ta connaissance la plus
faible (toutes compétences confondues) et pose la question adaptée."""

import streamlit as st

from geo import components, games

st.set_page_config(page_title="Révision intelligente", page_icon="🧠", layout="centered")
st.title("🧠 Révision intelligente")
st.caption(
    "Carte, drapeau, capitale, continent ou voisins : on te pose ce que tu "
    "maîtrises le moins. Le meilleur mode pour progresser."
)

components.play("revision", games.build_smart)
