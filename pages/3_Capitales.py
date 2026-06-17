"""Jeu « Pays → capitale » : on donne un pays, on choisit sa capitale."""

import streamlit as st

from geo import components

st.set_page_config(page_title="Capitales", page_icon="🏛️", layout="centered")
st.title("🏛️ Quelle est la capitale ?")


def prompt(question):
    st.subheader(f"Capitale de **{question['country']['name']}** ?")


components.play_text_choice(
    page_key="capitales",
    skill="capital",
    prompt=prompt,
    label=lambda c: c["capital"],
)
