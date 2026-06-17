# 🌍 Géo — entraînement adaptatif

App Streamlit pour réviser la géographie avec de la **répétition espacée** : les
connaissances qu'on rate reviennent vite, celles qu'on maîtrise s'espacent. On
ne note pas le quiz, on suit la **connaissance réelle** accumulée.

## Les 14 jeux

Tous partagent le même moteur de maîtrise. Une connaissance = **compétence ×
pays** ; plusieurs jeux peuvent nourrir la même compétence.

| Jeu | Compétence |
|---|---|
| 🗺️ Carte | Situer (pays surligné → son nom) |
| 📍 Situe le pays | Situer (nom → la bonne carte) |
| 🚩 Drapeaux | Drapeau → pays |
| 🎯 Trouve le drapeau | Pays → le bon drapeau |
| 🏛️ Capitales | Pays → capitale |
| 🏙️ Capitale → pays | Capitale → pays |
| 🚩 Drapeau → capitale | Drapeau → capitale du pays |
| 🧭 Continent | Pays → continent |
| 🌎 Pays du continent | Continent → quel pays s'y trouve |
| 🚩 Drapeau → continent | Drapeau → continent |
| 🤝 Voisins | Quel pays partage une frontière |
| 🔢 Combien de voisins | Nombre de frontières terrestres |
| 📏 Le plus grand | Plus grande superficie parmi 4 |
| 🧠 **Révision intelligente** | Mélange : pose ce qu'on maîtrise le moins |

La **Révision intelligente** est le mode le plus efficace : elle pioche
automatiquement la connaissance la plus faible, toutes compétences confondues.

## Comment ça marche

- Chaque connaissance (ex. `capital:PER`, `flag:FRA`) a une **maîtrise** entre 0
  et 1. Une bonne réponse la fait monter (`m += 0.30·(1−m)`), une mauvaise la
  fait chuter fort (`m ×= 0.35`).
- La **prochaine échéance** dépend de la maîtrise : faible → revient dans la
  session (45 s à 5 min), élevée → revient dans 1 à 21 jours.
- Le **tirage** des questions est pondéré vers les connaissances faibles ou en
  retard (`poids = (1−m)² + 0,05`, ×4 si en retard), avec un anti-répétition
  immédiate. On travaille donc surtout ce qu'on connaît mal.
- Le **niveau** affiché agrège la maîtrise sur tous les pays et compétences ; le
  tableau de bord montre le suivi par compétence, par région, et une **carte de
  tes connaissances** qui verdit au fil des progrès.
- La progression est sauvegardée dans `progress/progress.json` (local, ignoré
  par git). Filtre les continents à réviser dans la barre latérale.

## Démarrer

```bash
cd ~/Projets/geo-trainer
# venv déjà présent ; sinon le recréer (voir « Environnement » plus bas)
source .venv/bin/activate
streamlit run app.py
```

## Structure

```
app.py                 Accueil + tableau de bord
pages/                 Les 14 jeux (1 fichier = 1 jeu, ~5 lignes chacun)
geo/
  data.py              Chargement des pays, drapeaux, voisins, scope carte
  srs.py               Maîtrise + répétition espacée (pur, sans I/O)
  store.py             Persistance JSON de la progression
  quiz.py              Compétences + tirage pondéré + helpers QCM
  games.py             Un générateur de question par jeu
  components.py        Lecteur de jeu Streamlit générique (play)
data/countries.json    Jeu de données embarqué (généré)
scripts/build_data.py  Régénère le dataset
tests/                 test_builders.py (logique) + test_smoke.py (Streamlit)
```

Un jeu se résume à une page de ~5 lignes appelant `components.play(clé,
games.build_xxx)` : voir [CLAUDE.md](CLAUDE.md) pour ajouter le sien.

## Données

- Pays / capitales / régions / frontières / superficie : dataset
  [mledoze/countries](https://github.com/mledoze/countries) (licence ODbL),
  filtré aux ~194 États membres de l'ONU. Régénérable :
  `python scripts/build_data.py`.
- Drapeaux : images [flagcdn.com](https://flagcdn.com) (chargées en ligne — une
  **connexion** est nécessaire pour les jeux de drapeaux ; les emojis 🇫🇷 ne sont
  pas utilisés car ils s'affichent en lettres sur Windows).
- Quelques capitales sont francisées (Londres, Moscou, Pékin…) ; les autres
  gardent leur forme internationale. Ajuste `CAPITAL_FR` dans
  `scripts/build_data.py` si besoin.

## Tests

```bash
source .venv/bin/activate
python tests/test_builders.py   # logique des jeux, hors Streamlit (rapide)
python tests/test_smoke.py      # charge les 14 pages + joue un tour (AppTest)
```

## Environnement

Recréer le venv au besoin (sur cette machine `python3-venv` est incomplet et pip
est « externally managed », d'où l'amorçage manuel) :

```bash
python3 -m venv .venv --without-pip
source .venv/bin/activate
curl -sSL https://bootstrap.pypa.io/get-pip.py | python
pip install -r requirements.txt
```
