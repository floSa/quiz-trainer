"""Drapeau → continent (compétence : continent, indice par le drapeau)."""

import streamlit as st

from geo import components, games

st.set_page_config(page_title="Drapeau → continent", page_icon="🧭", layout="centered")
st.title("🚩 Sur quel continent flotte ce drapeau ?")

components.play("drapeau_continent", games.build_flag_to_region)
