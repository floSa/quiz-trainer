# 🌍 Quiz-Trainer

App web pour réviser la géographie (et bientôt plus) avec de la **répétition
espacée** : ce qu'on rate revient vite, ce qu'on maîtrise s'espace. On ne note
pas le quiz, on suit la **connaissance réelle** accumulée.

Pas de build, pas de serveur applicatif : du **HTML/CSS/JS** statique +
[Leaflet](https://leafletjs.com) pour la carte. La progression est stockée dans
le navigateur (`localStorage`).

## Démarrer

```bash
cd ~/Projets/geo-trainer
python3 -m http.server 8531    # ou n'importe quel serveur statique
# → http://localhost:8531
```

(Un simple serveur statique suffit ; ouvrir le fichier en `file://` ne marche
pas — les modules JS et `fetch` exigent http.)

## Les jeux

| Jeu | Compétence |
|---|---|
| 🧠 **Révision intelligente** | pose ce qu'on maîtrise le moins (tous types) |
| 🗺️ Carte | pays surligné → son nom |
| 📍 **Place le pays** | clique le bon pays sur la carte |
| 🕵️ Silhouette | la forme du pays seule (sans les voisins) → son nom |
| 🚩 Drapeaux | drapeau → pays |
| 🎯 Trouve le drapeau | pays → clique le bon drapeau |
| 🏛️ Capitales | pays → capitale |
| 🏙️ Capitale → pays | capitale → pays |
| 🤝 Voisins | trouve un pays frontalier |
| 🌍 Grandes villes du monde | place la ville (1 à 10 par pays selon sa taille) sur la carte |
| 🌊 Fleuves | fleuve surligné en rouge → son nom (33 grands fleuves) |
| 🇫🇷 Régions de France | place la région sur la carte |
| 🇫🇷 Départements | place le département sur la carte |
| 🇫🇷 Villes de France | place la ville > 50 000 hab. (clic, tolérance 35 km) |
| 🏛️ Monuments de France | place le monument (~100 célèbres) sur la carte (clic, tolérance 15 km) |
| 🇫🇷 Arrondissements de Paris | place l'arrondissement (1er → 20e) sur le plan |
| 🌴 DOM-TOM | place le territoire d'outre-mer sur le globe (clic, tolérance 600 km) |
| 🇺🇸 États américains | place l'état sur la carte (48 contigus, noms FR) |

Filtre les **régions** (du monde) à réviser dans la barre latérale (les jeux de
carte se cadrent alors sur la zone choisie). Les jeux 🇫🇷 portent sur la France
métropolitaine, le jeu 🇺🇸 sur les 48 états contigus.

## Comment ça marche

- Chaque connaissance = **compétence × pays** (ex. `capital:PER`) a une
  **maîtrise** ∈ [0,1]. Bonne réponse → elle monte ; mauvaise → elle chute fort.
- L'**échéance** dépend de la maîtrise : faible → revient dans la session,
  élevée → dans plusieurs jours.
- Le **tirage** est pondéré vers les connaissances faibles/en retard.
- Le **niveau** (tableau de bord) agrège la maîtrise sur tous les pays et
  compétences. Un **détail par connaissance** liste chaque pays/département/état
  déjà rencontré avec sa maîtrise % (du plus faible au plus sûr).

## Données

- Pays / capitales / régions / frontières / superficie :
  [mledoze/countries](https://github.com/mledoze/countries) (ODbL), filtré aux
  ~194 membres de l'ONU.  → `python scripts/build_data.py`
- Géométries (carte) : [Natural Earth 50m](https://www.naturalearthdata.com/)
  via nvkelso, réduit aux 194 pays (clé ISO3, coordonnées arrondies).
  → `python scripts/build_geo.py`
- Drapeaux : [flagcdn.com](https://flagcdn.com) (en ligne).
- France : régions/départements [france-geojson](https://github.com/gregoiredavid/france-geojson)
  + villes [GeoNames](https://www.geonames.org/).  → `python scripts/build_france.py`
- États-Unis : [PublicaMundi/MappingAPI](https://github.com/PublicaMundi/MappingAPI)
  (us-states), 48 états contigus, noms FR.  → `python scripts/build_usa.py`
- Arrondissements de Paris : [opendata.paris.fr](https://opendata.paris.fr) (ODbL).
  → `python scripts/build_paris.py`
- DOM-TOM : liste curatée (5 DROM + collectivités).  → `python scripts/build_domtom.py`
- Grandes villes du monde : [GeoNames](https://www.geonames.org/) (villes +
  `countryInfo` pour la population), 1 à 10 villes/pays.  → `python scripts/build_cities_world.py`
- Monuments de France : [Wikidata](https://www.wikidata.org) (SPARQL), ~100
  monuments triés par notoriété.  → `python scripts/build_monuments.py`
- Fleuves : [Natural Earth 50m](https://www.naturalearthdata.com/) rivers, 33
  grands fleuves (segments agrégés, noms FR).  → `python scripts/build_rivers.py`

Les scripts n'utilisent que la bibliothèque standard de Python.

## Structure

```
index.html
css/style.css
js/
  srs.js      moteur de maîtrise (répétition espacée, pur)
  store.js    persistance localStorage
  data.js     chargement pays + géométries (monde, France, US — à la demande)
  games.js    un générateur de question par jeu
  map.js      helpers Leaflet (couches monde/France/US, surlignage, clic, choroplèthe)
  app.js      navigation, filtre régions, cycle de jeu, tableau de bord
data/
  countries.json   world.geojson
  france/          regions.geojson, departements.geojson, cities.json
  usa/             states.geojson
scripts/    build_data.py, build_geo.py, build_france.py, build_usa.py
```

> Historique : une première version Streamlit (branche/historique git) a été
> remplacée par cette app web pour une carte cliquable fluide. Voir
> [CLAUDE.md](CLAUDE.md) pour l'architecture et l'ajout d'un jeu.
