"""Pays → continent (compétence : continent)."""

import streamlit as st

from geo import components, games

st.set_page_config(page_title="Continent", page_icon="🧭", layout="centered")
st.title("🧭 Sur quel continent ?")

components.play("continent", games.build_region)
