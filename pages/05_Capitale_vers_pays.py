"""Capitale → pays (compétence : capitale, sens inverse)."""

import streamlit as st

from geo import components, games

st.set_page_config(page_title="Capitale → pays", page_icon="🏙️", layout="centered")
st.title("🏙️ Quelle capitale, quel pays ?")

components.play("capitale_pays", games.build_capital_to_country)
