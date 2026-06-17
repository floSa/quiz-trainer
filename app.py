"""Géo — entraînement adaptatif. Page d'accueil : tableau de bord des
connaissances. Les jeux sont dans la barre latérale (dossier pages/)."""

import time

import plotly.graph_objects as go
import streamlit as st

from geo import data, quiz, srs, store

st.set_page_config(page_title="Géo — entraînement", page_icon="🌍", layout="wide")

st.title("🌍 Géo — entraîne-toi intelligemment")
st.markdown(
    "**14 jeux** dans la barre de gauche (carte, drapeaux, capitales, "
    "continents, voisins, superficies…). Le plus efficace : **🧠 Révision "
    "intelligente**, qui te pose automatiquement ce que tu maîtrises le moins. "
    "Les pays que tu rates reviennent vite, ceux que tu maîtrises s'espacent. "
    "Ton **niveau** ci-dessous mesure tes connaissances réelles — pas le score "
    "d'un quiz."
)

state = store.load()
countries = data.load_countries()
skills = list(quiz.SKILLS)
now = time.time()


def mastery(skill, iso3):
    return store.get_item(state, skill, iso3)["m"]


all_vals = [mastery(s, c["iso3"]) for c in countries for s in skills]
total = len(all_vals)
overall = sum(all_vals) / total if total else 0.0
learned = sum(1 for v in all_vals if v >= srs.LEARNED)
in_progress = sum(1 for v in all_vals if 0.0 < v < srs.LEARNED)
due = sum(
    1
    for c in countries
    for s in skills
    if (it := store.get_item(state, s, c["iso3"]))["seen"] and now >= it["due"]
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Niveau global", f"{round(overall * 100)} %")
c2.metric("Connaissances acquises", f"{learned} / {total}")
c3.metric("En cours d'apprentissage", in_progress)
c4.metric("À revoir maintenant", due)

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Par compétence")
    for skill, label in quiz.SKILLS.items():
        vals = [mastery(skill, c["iso3"]) for c in countries]
        avg = sum(vals) / len(vals) if vals else 0.0
        st.write(f"{label} — **{round(avg * 100)} %**")
        st.progress(avg)

with right:
    st.subheader("Par région")
    for region in data.regions():
        cs = data.countries_in([region])
        vals = [mastery(s, c["iso3"]) for c in cs for s in skills]
        avg = sum(vals) / len(vals) if vals else 0.0
        st.write(f"{region} — **{round(avg * 100)} %**")
        st.progress(avg)

st.divider()
st.subheader("🗺️ La carte de tes connaissances")
st.caption("Maîtrise moyenne par pays (toutes compétences confondues).")

isos = [c["iso3"] for c in countries]
agg = [
    round(sum(mastery(s, iso) for s in skills) / len(skills) * 100) for iso in isos
]
names = [c["name"] for c in countries]
fig = go.Figure(
    go.Choropleth(
        locations=isos,
        z=agg,
        text=names,
        locationmode="ISO-3",
        colorscale=[[0, "#f3f3f3"], [0.5, "#9bd49b"], [1, "#2e7d32"]],
        zmin=0,
        zmax=100,
        marker_line_color="white",
        marker_line_width=0.4,
        colorbar=dict(title="Maîtrise %"),
        hovertemplate="%{text} : %{z} %<extra></extra>",
    )
)
fig.update_geos(
    projection_type="natural earth",
    showframe=False,
    showcoastlines=False,
    showocean=True,
    oceancolor="#dceaf6",
    bgcolor="rgba(0,0,0,0)",
)
fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=480)
st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

with st.sidebar:
    st.divider()
    with st.expander("⚙️ Réinitialiser ma progression"):
        st.caption("Efface tout l'historique d'apprentissage. Irréversible.")
        if st.checkbox("Je confirme"):
            if st.button("Tout effacer", type="primary"):
                store.reset()
                st.rerun()
