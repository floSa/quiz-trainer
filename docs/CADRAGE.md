# Cadrage — Quiz-Trainer

Le **POURQUOI** : objectifs, périmètre, hypothèses et décisions produit. Le
**COMMENT** (modules, flux, moteur, difficulté) est dans
[ARCHITECTURE.md](ARCHITECTURE.md).

## 1. Pitch

Application web pour **réviser la géographie** par **répétition espacée** : on ne
note pas un quiz, on suit la **connaissance réelle** accumulée. Trois capacités :

1. **Jouer** à une vingtaine de jeux géo (pays, drapeaux, capitales, voisins,
   villes, fleuves, mers, déserts, chaînes, sommets, France, États-Unis…) où ce
   qu'on rate revient vite et ce qu'on maîtrise s'espace.
2. **Régler la difficulté** globalement (facile/normal/difficile) : les leurres
   et les tolérances de clic deviennent plus piégeux à mesure qu'on monte.
3. **Apprendre et suivre sa progression** : une page 📚 Apprendre (tableaux de
   référence) et un 📊 tableau de bord (niveau global, connaissances acquises,
   détail par item, carte des connaissances).

---

## 2. Objectifs & périmètre

**Dans le périmètre** :
- App **statique**, jouable depuis un simple serveur de fichiers, sans compte.
- Une **progression persistante** locale, pilotée par un moteur de maîtrise.
- Un **catalogue de jeux** couvrant monde, géographie physique, France, USA.
- Un **système de difficulté** unique s'appliquant à tous les jeux.
- Des **données reproductibles** via scripts Python sans dépendances.

**Hors périmètre** :
- Pas de **backend**, de **comptes** ni de **synchronisation multi-appareils**.
- Pas de **classement/score compétitif** entre joueurs (on mesure la maîtrise,
  pas un score de partie).
- Pas de **build/bundler** ni de framework front.
- Pas de **fond de carte tuilé** (uniquement les polygones).

---

## 3. Contraintes (fermes)

| Contrainte | Détail |
|---|---|
| Déploiement | **statique** : n'importe quel serveur de fichiers HTTP (pas de `file://`) |
| Dépendances runtime | JS maison + **Leaflet** (CDN unpkg) + drapeaux (flagcdn.com) ; rien d'autre |
| Génération de données | **Python bibliothèque standard uniquement** (aucun `pip install`) |
| Stockage | navigateur (`localStorage`), mono-utilisateur |
| Licences | open-source, sources de données créditées (ODbL, Natural Earth…) |

---

## 4. Hypothèses

- **Un seul utilisateur par navigateur** : la progression `localStorage` n'est
  pas partagée ; changer de machine ou vider le site perd les données. Ce qui la
  remettrait en cause : un besoin multi-appareils → imposerait export/import ou
  backend.
- **Connexion réseau disponible** : Leaflet (unpkg) et les drapeaux (flagcdn)
  sont chargés en ligne ; hors-ligne, la carte et les drapeaux ne s'affichent
  pas. Remise en cause : usage hors-ligne → héberger ces ressources en local.
- **Données géographiques stables** : elles sont figées au moment de la
  génération ; frontières/capitales évoluent rarement. Remise en cause : mise à
  jour → relancer les scripts `build_*.py`.
- **La maîtrise ∈ [0,1] suffit** à représenter la connaissance (pas besoin d'un
  ordonnancement Anki fin). Remise en cause : besoin d'un SRS plus riche.

---

## 5. Stack technique

| Brique | Choix | Licence |
|---|---|---|
| Front | HTML/CSS/JS statique (modules ES), sans build | — (code du projet, MIT) |
| Cartographie | Leaflet 1.9.4 (CDN unpkg) | BSD-2-Clause |
| Drapeaux | flagcdn.com (en ligne) | service tiers — `<à confirmer>` |
| Persistance | `localStorage` navigateur | — |
| Données | scripts Python (stdlib) | MIT (code) ; sources créditées (§9) |
| Tests | Node (runner maison) | — |

> Détail des versions et des flux : [ARCHITECTURE.md §3](ARCHITECTURE.md#3-stack-technologique).

---

## 6. Décisions

**Figées ✅**
- **App statique + `localStorage`** plutôt qu'app serveur : mono-utilisateur,
  hébergement trivial. (Remplace une **première version Streamlit**, abandonnée
  pour une carte cliquable fluide.)
- **Moteur de maîtrise maison** (`srs.js`, port de `srs.py`) plutôt qu'une lib
  SRS : besoin simple, pur et testable.
- **Difficulté globale unique** plutôt que par jeu : un réglage lisible et
  cohérent.
- **Données pré-générées en Python stdlib** plutôt qu'appels réseau à
  l'exécution : reste servable en statique, scripts sans dépendances.
- **Leaflet en polygones sans tuiles** : ni clé d'API ni quota.

**À trancher 🔲**
- **Difficulté par jeu** (le commentaire de `settings.js` note « pour
  l'instant » un réglage unique) — reco : garder global tant qu'il n'y a pas de
  demande.
- **Export/import de la progression** pour le multi-appareils — reco : export
  JSON simple avant tout backend.
- **Statut de `data/world.geojson`** (régénérable, absent du dépôt) — reco :
  clarifier s'il doit être committé ou toujours régénéré.

---

## 7. Roadmap

L'ordre de construction n'est pas documenté explicitement dans le dépôt.
`<à confirmer>` — l'historique git montre au moins : socle statique + moteur de
maîtrise → catalogue de jeux monde → France/USA & géographie physique → page
Apprendre & tableau de bord → **système de difficulté multi-niveaux** (ajout
récent).

---

## 8. Stratégie de tests

- **Moteur de maîtrise** (`srs.js`) : couvert par [`tests/run.mjs`](../tests/run.mjs)
  (`node tests/run.mjs` ou `npm test`) — logique pure et déterministe (paramètre
  `now` injectable) : `newItem`, `review` (gain/pénalité), convergence bornée
  à 1, monotonie de `interval`, poids de tirage, `isLearned`.
- **Non couvert** : générateurs de questions, application de la difficulté,
  couche carte (dépend du DOM/Leaflet). `<à confirmer : tests d'intégration UI>`.

---

## 9. Références

Sources de données (créditées dans le [README](../README.md)) :
[mledoze/countries](https://github.com/mledoze/countries) (ODbL),
[Natural Earth](https://www.naturalearthdata.com/),
[france-geojson](https://github.com/gregoiredavid/france-geojson),
[GeoNames](https://www.geonames.org/),
[Wikidata](https://www.wikidata.org) / [Wikimedia Commons](https://commons.wikimedia.org),
[opendata.paris.fr](https://opendata.paris.fr) (ODbL),
[PublicaMundi/MappingAPI](https://github.com/PublicaMundi/MappingAPI).

Renvois internes : [ARCHITECTURE.md](ARCHITECTURE.md) pour le COMMENT.
