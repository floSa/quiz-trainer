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
- `data.js` — `load()` (fetch countries.json + world.geojson), `countries`,
  `regions`, `countriesIn`, `flagUrl`, `neighbors`, `byIso3`, `geo`.
- `games.js` — `SKILLS`, `pickCountry` (tirage pondéré), un `build*` par jeu,
  `CANON` (compétence → générateur canonique, pour `buildSmart`), et `GAMES`
  (catalogue ordonné pour le menu). Format **question** ci-dessous.
- `map.js` — singleton Leaflet sans tuiles (fond neutre, polygones des pays) :
  `ensureMap`, `highlight(iso3)` (zoom serré), `focusZone(isoList)`,
  `setClickHandler`, `markResult`, `choropleth`.
- `app.js` — navigation, filtre régions, cycle de manche (build → afficher →
  corriger → feedback **en ligne** → suivant), tableau de bord.

### Format « question » (contrat games ↔ app)

```js
{
  skill, item,                 // item = iso3 dont la maîtrise est mise à jour
  correct,                     // id de la bonne option (ou iso3 pour mapclick)
  stimulus: {kind, value},     // kind: "text"(html) | "flag"(pays) | "map"(iso3)
  ask,                         // (option.) question affichée pour stimulus flag/map
  interaction: "options"|"mapclick",
  optionKind: "text"|"flag"|null,
  options: [{id, label, country}],
  explain, reveal,             // (option.) reveal: {kind:"map"|"flag", value}
}
```
Correction : `chosenId === correct`. `app.answer()` met à jour `(skill, item)`.

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

## À faire / pistes

- **Module France** : régions, départements, villes > 50 000 hab. (mêmes
  mécaniques place-sur-carte, par zone) — données : france-geojson + communes.
- Tests JS (la logique `srs`/`games` est pure → testable en node avec données injectées).
- Quelques capitales restent en forme internationale (ex. « Tashkent » → « Tachkent ») :
  compléter `CAPITAL_FR` dans `scripts/build_data.py`.
- Carte des connaissances (choroplèthe) dans le tableau de bord (`map.choropleth` existe déjà).
