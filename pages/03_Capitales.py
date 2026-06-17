"""Pays → capitale (compétence : capitale)."""

import streamlit as st

from geo import components, games

st.set_page_config(page_title="Capitales", page_icon="🏛️", layout="centered")
st.title("🏛️ Quelle est la capitale ?")

components.play("capitales", games.build_capital)
