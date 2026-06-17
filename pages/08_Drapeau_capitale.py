"""Drapeau → capitale (compétence : capitale, indice par le drapeau)."""

import streamlit as st

from geo import components, games

st.set_page_config(page_title="Drapeau → capitale", page_icon="🏙️", layout="centered")
st.title("🚩 La capitale derrière le drapeau")
st.caption("Reconnais le pays à son drapeau, puis donne sa capitale.")

components.play("drapeau_capitale", games.build_flag_to_capital)
