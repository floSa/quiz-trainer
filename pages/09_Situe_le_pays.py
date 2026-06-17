"""Nom → bonne carte parmi plusieurs (compétence : situer, sens inverse)."""

import streamlit as st

from geo import components, games

st.set_page_config(page_title="Situe le pays", page_icon="📍", layout="centered")
st.title("📍 Situe le pays")
st.caption("Choisis la carte où le bon pays est surligné.")

components.play("situe", games.build_situate)
