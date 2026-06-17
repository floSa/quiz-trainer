"""Carte → nomme le pays (compétence : situer)."""

import streamlit as st

from geo import components, games

st.set_page_config(page_title="Carte", page_icon="🗺️", layout="centered")
st.title("🗺️ Quel est ce pays ?")
st.caption("Le pays surligné en rouge — choisis son nom.")

components.play("carte", games.build_locate)
