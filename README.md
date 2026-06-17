# 🌍 Géo — entraînement adaptatif

Petite app Streamlit pour réviser la géographie (pays, drapeaux, capitales) avec
de la **répétition espacée** : les connaissances qu'on rate reviennent vite,
celles qu'on maîtrise s'espacent. On ne note pas le quiz, on suit la
**connaissance réelle** accumulée.

## Les jeux

| Jeu | Compétence travaillée |
|---|---|
| 🗺️ **Carte** | Situer un pays (il est surligné, on le nomme) |
| 🚩 **Drapeaux** | Reconnaître un drapeau → pays |
| 🏛️ **Capitales** | Capitale d'un pays |
| 🎯 **Trouve le drapeau** | Pays → choisir le bon drapeau |

Les deux jeux de drapeaux nourrissent la **même** connaissance (« drapeau du
pays X »), dans les deux sens.

## Comment ça marche

- Chaque connaissance = **compétence × pays** (ex. `capital:PER`) a une
  **maîtrise** entre 0 et 1. Une bonne réponse la fait monter, une mauvaise la
  fait chuter fort.
- La **prochaine échéance** dépend de la maîtrise : faible → revient dans la
  session, élevée → revient dans plusieurs jours.
- Le tirage des questions est **pondéré** vers les connaissances faibles ou en
  retard, donc on travaille surtout ce qu'on connaît mal.
- Le **niveau** affiché agrège la maîtrise sur tous les pays et toutes les
  compétences.
- La progression est sauvegardée dans `progress/progress.json` (local, ignoré
  par git). Filtre les continents à réviser dans la barre latérale.

## Démarrer

```bash
cd ~/Projets/geo-trainer
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Données

- Pays / capitales / régions : dataset [mledoze/countries](https://github.com/mledoze/countries)
  (licence ODbL), filtré aux ~194 États membres de l'ONU. Régénérable avec
  `python scripts/build_data.py`.
- Drapeaux : images [flagcdn.com](https://flagcdn.com) (chargées en ligne — une
  connexion est nécessaire pour les jeux de drapeaux).
- Quelques capitales sont francisées (Londres, Moscou, Pékin…) ; les autres
  gardent leur forme internationale. Ajuste `CAPITAL_FR` dans
  `scripts/build_data.py` si besoin.
