"""Jeu « Carte → nomme le pays » : un pays est surligné, on le reconnaît."""

import streamlit as st

from geo import components

st.set_page_config(page_title="Carte", page_icon="🗺️", layout="centered")
st.title("🗺️ Quel est ce pays ?")
st.caption("Le pays surligné en rouge — choisis son nom.")


def prompt(question):
    components.render_map(question["country"])


components.play_text_choice(
    page_key="carte",
    skill="locate",
    prompt=prompt,
    label=lambda c: c["name"],
)
