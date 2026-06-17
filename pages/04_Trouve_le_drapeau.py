"""Pays → drapeau : choisir le bon drapeau parmi plusieurs (compétence : drapeau)."""

import streamlit as st

from geo import components, games

st.set_page_config(page_title="Trouve le drapeau", page_icon="🎯", layout="centered")
st.title("🎯 Trouve le bon drapeau")

components.play("trouve_drapeau", games.build_pick_flag)
