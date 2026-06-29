# Guide du dépôt (pour Claude)

App web perso de quiz géo (répétition espacée), dépôt distant **floSa/quiz-trainer**
(cf. mémoire identités : commits perso FloSa, remote `github.com-perso`). Le
périmètre s'élargira au-delà de la géo (d'où « quiz-trainer »).

Stack : **HTML/CSS/JS statique + Leaflet** (CDN). Aucun build, aucun backend.
Progression dans `localStorage`. Une 1ʳᵉ version Streamlit a été remplacée par
cette app web (carte cliquable fluide).

## Lancer

```bash
python3 -m http.server 8531   # depuis la racine du projet → http://localhost:8531
```
Toujours servir en http (les modules ES + `fetch` ne marchent pas en `file://`).

## Architecture (js/, modules ES)

Flux : **data → srs/store → games → app/map → DOM**.

- `srs.js` — maîtrise `m∈[0,1]` + échéance. **Pur** (pas de DOM/stockage). Testable seul.
- `store.js` — `load/save/getItem/record/reset` dans `localStorage`. Clé `"skill:iso3"`.
- `data.js` — `load()` (countries.json + world.geojson), `countries`, `regions`,
  `countriesIn`, `flagUrl`, `neighbors`, `byIso3`, `geo` ; et **à la demande**
  `loadFrance`/`france`, `loadUsa`/`usa`.
- `games.js` — `SKILLS` (monde), `FR_SKILLS`/`US_SKILLS` + `*_TOTALS`,
  `pickCountry`/`pickWeighted` (tirage pondéré), un `build*` par jeu, `CANON`
  (compétence monde → générateur, pour `buildSmart`), et `GAMES` (catalogue du
  menu, chaque entrée a un `context`). Format **question** ci-dessous.
- `map.js` — singleton Leaflet sans tuiles, **couche interchangeable** :
  `ensureMap`, `setLayer(geojson,{interactive})` (monde/France/US), `highlight(id)`,
  `focusIds(idList)`, `fitAll`, `resetBase`, `onFeatureClick`/`onMapClick`,
  `markResult`, `addMarker`/`clearMarkers`/`panTo`, `choropleth`.
- `app.js` — navigation (**jeton anti-désync** car async), filtre régions,
  `setContext` (couche monde/France/US ; données préchargées au démarrage), cycle
  de manche (build → afficher → corriger → feedback **en ligne** → suivant),
  tableau de bord (dont **détail par item**).

### Format « question » (contrat games ↔ app)

```js
{
  skill, item,                 // item = clé de maîtrise (iso3 / code dept / nom état…)
  correct,                     // id de la bonne réponse
  correctLabel,                // (option.) libellé lisible si id ≠ libellé (France/US)
  stimulus: {kind, value},     // kind: "text"(html) | "flag"(pays) | "map"(iso3)
  ask,                         // (option.) question affichée pour stimulus flag/map
  interaction: "options"|"mapclick"|"rawclick",  // rawclick = clic libre, correction à la distance
  city,                        // (rawclick) {name,lat,lng}
  optionKind: "text"|"flag"|null,
  options: [{id, label, country}],
  explain, reveal,             // (option.) reveal: {kind:"map"|"flag", value}
}
```
Correction : `chosenId === correct` (ou distance ≤ `CITY_THRESHOLD_KM` pour
`rawclick`). `app` met à jour la maîtrise de `(skill, item)`.

## Ajouter un jeu

1. `build*(cands, state, recent, country)` dans `games.js` renvoyant une question
   (réutiliser `pickCountry`, `countryOptions`, `textOpts`, `valueOpts`). Nouvelle
   compétence → l'ajouter à `SKILLS` (et à `CANON` si elle a une forme canonique
   pour la révision intelligente).
2. L'ajouter au catalogue `GAMES` (clé, title, sub, build).

## Données

Régénérer via `scripts/build_data.py` (pays) et `scripts/build_geo.py`
(world.geojson, Natural Earth 50m réduit). Stdlib Python uniquement. Ne pas
éditer les JSON à la main.

## Conventions

- FR pour le code et les intitulés. Intitulés sans article : « Pays : question ? ».
- `srs.js` reste pur. Toute persistance via `store.js`.
- Carte sans tuiles (pas d'étiquettes → pas de triche, et hors-ligne hors drapeaux).

## Modules France & États-Unis (faits)

Couche Leaflet interchangeable (`map.setLayer`). Jeux place-sur-carte :
- **France** : régions (13) / départements (96) par clic du polygone, villes >50k
  (153) par **clic libre** corrigé à la distance (`CITY_THRESHOLD_KM`). Compétences
  `fr_region/fr_dept/fr_city`. Données `scripts/build_france.py` → `data/france/`.
- **États-Unis** : 48 états contigus (noms FR) par clic du polygone, compétence
  `us_state`, contexte `usa-states`. Données `scripts/build_usa.py` → `data/usa/`.

Le tableau de bord agrège ces compétences (sections dédiées) + un **détail par
item** (chaque pays/département/ville/état rencontré avec sa maîtrise %).

## Pièges connus

- `[hidden]{display:none!important}` est requis : `.view{display:flex}` écrasait
  l'attribut `hidden` → le dashboard masqué occupait la moitié de l'écran.
- `selectGame` est async (chargement France/US) → **jeton de navigation** pour
  ignorer une sélection devenue obsolète (évite titre/contenu désynchronisés).

## Tests

`node tests/run.mjs` (ou `npm test`) : harnais sans dépendance pour `srs.js`
(logique pure, déterministe via le paramètre `now`). `package.json` a
`"type": "module"` pour que node importe les `.js` en ESM.

## À faire / pistes

- Quelques capitales restent en forme internationale (ex. « Tashkent » → « Tachkent ») :
  compléter `CAPITAL_FR` dans `scripts/build_data.py`.
- Tests sur les générateurs `games` (injecter des données factices).
