"""Drapeau → pays (compétence : drapeau)."""

import streamlit as st

from geo import components, games

st.set_page_config(page_title="Drapeaux", page_icon="🚩", layout="centered")
st.title("🚩 De quel pays est ce drapeau ?")

components.play("drapeaux", games.build_flag)
