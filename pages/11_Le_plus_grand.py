"""Le plus grand pays par superficie (compétence : superficies)."""

import streamlit as st

from geo import components, games

st.set_page_config(page_title="Le plus grand", page_icon="📏", layout="centered")
st.title("📏 Le plus grand pays")

components.play("plus_grand", games.build_largest)
