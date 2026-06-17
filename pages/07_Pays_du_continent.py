"""Continent → pays : lequel s'y trouve ? (compétence : continent)."""

import streamlit as st

from geo import components, games

st.set_page_config(page_title="Pays du continent", page_icon="🌎", layout="centered")
st.title("🌎 Qui vit sur ce continent ?")

components.play("pays_continent", games.build_region_to_country)
