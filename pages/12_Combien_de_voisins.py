"""Combien de pays frontaliers ? (compétence : voisins)."""

import streamlit as st

from geo import components, games

st.set_page_config(page_title="Combien de voisins", page_icon="🔢", layout="centered")
st.title("🔢 Combien de voisins ?")

components.play("nb_voisins", games.build_neighbor_count)
