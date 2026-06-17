"""Jeu « Pays → drapeau » : on donne un pays, on choisit le bon drapeau."""

import streamlit as st

from geo import components

st.set_page_config(page_title="Trouve le drapeau", page_icon="🎯", layout="centered")
st.title("🎯 Trouve le bon drapeau")

components.play_flag_choice(page_key="drapeau_express", skill="flag")
