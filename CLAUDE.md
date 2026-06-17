# Guide du dépôt (pour Claude)

App Streamlit perso de révision de géographie (répétition espacée). Projet
séparé d'Elivie. Commits sous l'identité **perso FloSa**
(`florian.horellou@gmail.com`), remote via l'hôte SSH `github.com-perso`.

## Lancer / tester

```bash
source .venv/bin/activate
streamlit run app.py
python tests/test_builders.py   # logique, hors Streamlit (rapide)
python tests/test_smoke.py      # AppTest sur les 14 pages
```

Sur cette machine WSL : `python3-venv` est incomplet et pip « externally
managed ». Recréer le venv avec `python3 -m venv .venv --without-pip` puis
amorcer pip via `get-pip.py` (voir README § Environnement).

## Architecture

Flux : **data → quiz → games → components → pages**.

- `geo/data.py` — charge `data/countries.json` (pays = `{iso2, iso3, name,
  capital, region, subregion, borders, area}`), expose `countries_in`,
  `regions`, `flag_url`, `neighbors`, `map_scope`.
- `geo/srs.py` — maîtrise `m∈[0,1]` + échéance. **Pur, sans I/O ni Streamlit.**
  `review(item, correct)`, `weight(item)`, `is_learned`.
- `geo/store.py` — `load/save/record` la progression dans
  `progress/progress.json`. Clé d'item = `"<skill>:<iso3>"`.
- `geo/quiz.py` — `SKILLS` (locate, flag, capital, region, neighbors, size),
  `pick_country` (tirage pondéré), `options` (QCM pays), `mcq_values` (QCM
  valeurs).
- `geo/games.py` — un générateur `build_xxx(cands, state, recent, country=None)`
  par jeu. Renvoie une **question** (voir format ci-dessous). `CANON` mappe une
  compétence → son générateur canonique, utilisé par `build_smart` (révision).
- `geo/components.py` — `play(page_key, build)` : machine à états d'une manche
  (tirage → affichage → correction → maîtrise → suivant). Affichage piloté par
  le format question, donc générique.
- `pages/NN_*.py` — ~5 lignes : `set_page_config`, titre, `components.play(...)`.

### Format « question » (contrat entre games et components)

```python
{
  "skill":   "capital",                 # clé de quiz.SKILLS, met à jour la maîtrise
  "item":    "FRA",                      # iso3 dont la maîtrise est mise à jour
  "prompt":  ("text", "...") | ("map", country) | ("flag", country),
  "options": [{"id": str, "label": str, "kind": "text"|"flag"|"map",
               "country": dict|None}, ...],  # toutes les options ont le même kind
  "correct": "<id de la bonne option>",
  "explain": str | None,                 # affiché après réponse
  "reveal":  ("map"|"flag", country) | None,
}
```

Correction : `chosen_id == correct`. La maîtrise de `(skill, item)` est mise à
jour, puis sauvegardée.

## Ajouter un jeu

1. Écrire `build_xxx(cands, state, recent, country=None)` dans `geo/games.py`
   renvoyant une question (réutiliser `quiz.pick_country`, `quiz.options`,
   `quiz.mcq_values`, `_country_opts`, `_value_opts`). Si la compétence est
   nouvelle, l'ajouter à `quiz.SKILLS`.
2. Créer `pages/NN_Nom.py` appelant `components.play("clé_unique", games.build_xxx)`.
3. Ajouter le jeu (ou sa clé) aux tests : liste `BUILDERS` (test_builders) et,
   si la mécanique d'affichage est inédite, `CYCLES` (test_smoke).

## Conventions

- Code et libellés en **français**. Docstrings courtes et utiles.
- `srs.py` reste pur (testable sans Streamlit). Toute l'I/O passe par `store`.
- Pas d'`use_container_width` (déprécié) → `width="stretch"`.
- Régénérer les données via `scripts/build_data.py` (ne pas éditer le JSON à la
  main).
