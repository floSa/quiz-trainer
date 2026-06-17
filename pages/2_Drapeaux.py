"""Jeu « Drapeau → pays » : on montre un drapeau, on nomme le pays."""

import streamlit as st

from geo import components, data

st.set_page_config(page_title="Drapeaux", page_icon="🚩", layout="centered")
st.title("🚩 De quel pays est ce drapeau ?")


def prompt(question):
    st.image(data.flag_url(question["country"]["iso2"]), width=300)


components.play_text_choice(
    page_key="drapeaux",
    skill="flag",
    prompt=prompt,
    label=lambda c: c["name"],
)
