"""Pays voisins : qui partage une frontière ? (compétence : voisins)."""

import streamlit as st

from geo import components, games

st.set_page_config(page_title="Voisins", page_icon="🤝", layout="centered")
st.title("🤝 Pays voisins")

components.play("voisins", games.build_neighbor)
