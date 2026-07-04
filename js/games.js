// Générateurs de questions. Chaque générateur renvoie une « question » au
// format unique consommé par app.js :
//   { skill, item, correct, stimulus:{kind,value}, interaction, options,
//     optionKind, explain, reveal }
//   - stimulus.kind : "text" (html) | "flag" (pays) | "map" (iso3 surligné)
//   - interaction   : "options" (QCM) | "mapclick" (cliquer le bon pays)
//   - optionKind    : "text" | "flag" | null
import * as data from "./data.js";
import * as srs from "./srs.js";
import * as store from "./store.js";
import * as settings from "./settings.js";

export const SKILLS = {
  locate: "Situer sur la carte",
  flag: "Reconnaître le drapeau",
  capital: "Connaître la capitale",
  neighbors: "Connaître les voisins",
};

// --- petits utilitaires aléatoires ---------------------------------------- //
function shuffle(a) {
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}
function choice(a) {
  return a[Math.floor(Math.random() * a.length)];
}
function weightedPick(items, weights) {
  const total = weights.reduce((s, w) => s + w, 0);
  let r = Math.random() * total;
  for (let i = 0; i < items.length; i++) {
    r -= weights[i];
    if (r <= 0) return items[i];
  }
  return items[items.length - 1];
}

export function pickCountry(cands, state, skill, recent = []) {
  const rec = new Set(recent);
  let pool = cands.filter((c) => !rec.has(c.iso3));
  if (!pool.length) pool = cands.slice();
  const w = pool.map((c) => srs.weight(store.getItem(state, skill, c.iso3)));
  return weightedPick(pool, w);
}

// --- proximité géographique (pour la difficulté) --------------------------- //
// Centroïde du plus grand polygone de chaque pays (masse principale), calculé
// une fois depuis les géométries.
let _cent = null;
function centroidOf(iso3) {
  if (!_cent) {
    _cent = {};
    for (const f of data.geo().features) {
      const polys = f.geometry.type === "Polygon" ? [f.geometry.coordinates] : f.geometry.coordinates;
      let ring = polys[0][0];
      for (const p of polys) if (p[0].length > ring.length) ring = p[0];
      let x0 = 999, x1 = -999, y0 = 999, y1 = -999;
      for (const q2 of ring) {
        if (q2[0] < x0) x0 = q2[0];
        if (q2[0] > x1) x1 = q2[0];
        if (q2[1] < y0) y0 = q2[1];
        if (q2[1] > y1) y1 = q2[1];
      }
      _cent[f.id] = { lng: (x0 + x1) / 2, lat: (y0 + y1) / 2 };
    }
  }
  return _cent[iso3];
}
export function distKm(a, b) {
  const A = typeof a === "string" ? centroidOf(a) : a;
  const B = typeof b === "string" ? centroidOf(b) : b;
  if (!A || !B) return 1e9;
  const R = 6371, rad = (x) => (x * Math.PI) / 180;
  const dLat = rad(B.lat - A.lat), dLng = rad(B.lng - A.lng);
  const s = Math.sin(dLat / 2) ** 2 + Math.cos(rad(A.lat)) * Math.cos(rad(B.lat)) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(s));
}

// Distracteurs selon la difficulté globale :
//   facile     → autres continents en priorité
//   normal     → même continent en priorité (comportement historique)
//   difficile  → voisins frontaliers, puis les plus proches géographiquement
//                (léger tirage dans le peloton de tête pour varier les manches ;
//                 les îles, sans frontières, tombent sur « les plus proches »)
function distractors(anchor, pool, k) {
  const mode = settings.difficulty();
  if (mode === "facile") {
    const far = shuffle(pool.filter((x) => x.region !== anchor.region));
    const rest = shuffle(pool.filter((x) => x.region === anchor.region));
    return far.concat(rest).slice(0, k);
  }
  if (mode === "difficile") {
    const borders = new Set(anchor.borders || []);
    const scored = pool.map((x) => ({
      x,
      d: distKm(anchor.iso3, x.iso3) - (borders.has(x.iso3) ? 1e7 : 0) - (x.subregion === anchor.subregion ? 1e5 : 0),
    }));
    scored.sort((a, b) => a.d - b.d);
    const head = scored.slice(0, Math.max(k * 2 + 1, 7)).map((s) => s.x);
    return shuffle(head).slice(0, k);
  }
  const same = shuffle(pool.filter((x) => x.region === anchor.region));
  const others = shuffle(pool.filter((x) => x.region !== anchor.region));
  return same.concat(others).slice(0, k);
}

// QCM de pays : bonne réponse + distracteurs selon la difficulté.
function countryOptions(correct, cands, k = 3) {
  const pool = cands.filter((c) => c.iso3 !== correct.iso3);
  return shuffle([correct, ...distractors(correct, pool, k)]);
}
function textOpts(countries, label) {
  return countries.map((c) => ({ id: c.iso3, label: label(c), country: c }));
}
function valueOpts(values) {
  return values.map((v) => ({ id: String(v), label: String(v) }));
}
function q(o) {
  return Object.assign(
    { options: [], optionKind: null, explain: null, reveal: null },
    o
  );
}

// --- locate ---------------------------------------------------------------- //
export function buildLocate(cands, state, recent, country) {
  const c = country || pickCountry(cands, state, "locate", recent);
  return q({
    skill: "locate",
    item: c.iso3,
    correct: c.iso3,
    stimulus: { kind: "map", value: c.iso3 },
    ask: "Quel est ce pays ? (surligné en rouge)",
    interaction: "options",
    optionKind: "text",
    options: textOpts(countryOptions(c, cands), (x) => x.name),
  });
}

// Silhouette : forme du pays seule (sans les voisins) → son nom.
export function buildSilhouette(cands, state, recent, country) {
  const c = country || pickCountry(cands, state, "locate", recent);
  return q({
    skill: "locate",
    item: c.iso3,
    correct: c.iso3,
    stimulus: { kind: "shape", value: c.iso3 },
    ask: "Quel est ce pays ? (forme seule)",
    interaction: "options",
    optionKind: "text",
    options: textOpts(countryOptions(c, cands), (x) => x.name),
  });
}

export function buildPlace(cands, state, recent, country) {
  const c = country || pickCountry(cands, state, "locate", recent);
  return q({
    skill: "locate",
    item: c.iso3,
    correct: c.iso3,
    stimulus: { kind: "text", value: `Place ce pays sur la carte : <b>${c.name}</b>` },
    interaction: "mapclick",
    reveal: { kind: "map", value: c.iso3 },
  });
}

// --- flag ------------------------------------------------------------------ //
// Groupes de drapeaux visuellement proches (couleurs/motifs) : en difficile,
// les distracteurs sont piochés dans le groupe du pays cible.
const FLAG_CONFUSIONS = [
  ["TCD", "ROU", "AND", "MDA"],
  ["IDN", "MCO", "POL", "SGP"],
  ["NLD", "LUX", "RUS", "PRY"],
  ["NOR", "ISL", "DNK", "SWE", "FIN"],
  ["AUS", "NZL", "FJI", "TUV"],
  ["IRL", "CIV", "ITA", "MEX", "NGA"],
  ["MLI", "SEN", "GIN", "CMR"],
  ["COL", "ECU", "VEN"],
  ["SVN", "SVK", "RUS", "SRB", "HRV"],
  ["QAT", "BHR"],
  ["JOR", "KWT", "ARE", "SDN"],
  ["EGY", "YEM", "SYR", "IRQ"],
  ["HND", "SLV", "NIC", "ARG", "GTM"],
  ["HUN", "BGR", "IRN", "TJK"],
  ["USA", "LBR", "MYS"],
  ["CUB", "CZE", "PHL"],
  ["JPN", "BGD", "PLW"],
  ["THA", "CRI", "PRK"],
  ["TUR", "TUN"],
  ["GRC", "URY"],
  ["CHN", "VNM"],
  ["BEL", "DEU"],
];

// Options pour les jeux de drapeaux : en difficile, groupe de confusion d'abord.
function flagOptions(correct, cands, k = 3) {
  if (settings.difficulty() === "difficile") {
    const grp = FLAG_CONFUSIONS.find((g) => g.includes(correct.iso3));
    if (grp) {
      const picks = shuffle(grp.filter((i) => i !== correct.iso3))
        .map((i) => data.byIso3(i))
        .filter(Boolean)
        .slice(0, k);
      if (picks.length < k) {
        const taken = new Set([correct.iso3, ...picks.map((p) => p.iso3)]);
        picks.push(...distractors(correct, cands.filter((c) => !taken.has(c.iso3)), k - picks.length));
      }
      return shuffle([correct, ...picks]);
    }
  }
  return countryOptions(correct, cands, k);
}

export function buildFlag(cands, state, recent, country) {
  const c = country || pickCountry(cands, state, "flag", recent);
  return q({
    skill: "flag",
    item: c.iso3,
    correct: c.iso3,
    stimulus: { kind: "flag", value: c },
    ask: "De quel pays est ce drapeau ?",
    interaction: "options",
    optionKind: "text",
    options: textOpts(flagOptions(c, cands), (x) => x.name),
  });
}

export function buildPickFlag(cands, state, recent, country) {
  const c = country || pickCountry(cands, state, "flag", recent);
  return q({
    skill: "flag",
    item: c.iso3,
    correct: c.iso3,
    stimulus: { kind: "text", value: `<b>${c.name}</b> : quel est son drapeau ?` },
    interaction: "options",
    optionKind: "flag",
    options: textOpts(flagOptions(c, cands), (x) => x.name),
    reveal: { kind: "flag", value: c },
  });
}

// --- capital --------------------------------------------------------------- //
export function buildCapital(cands, state, recent, country) {
  const c = country || pickCountry(cands, state, "capital", recent);
  return q({
    skill: "capital",
    item: c.iso3,
    correct: c.iso3,
    stimulus: { kind: "text", value: `<b>${c.name}</b> : quelle est sa capitale ?` },
    interaction: "options",
    optionKind: "text",
    options: textOpts(countryOptions(c, cands), (x) => x.capital),
  });
}

export function buildCapitalToCountry(cands, state, recent, country) {
  const c = country || pickCountry(cands, state, "capital", recent);
  return q({
    skill: "capital",
    item: c.iso3,
    correct: c.iso3,
    stimulus: { kind: "text", value: `<b>${c.capital}</b> est la capitale de quel pays ?` },
    interaction: "options",
    optionKind: "text",
    optionFlags: true, // drapeau à côté de chaque pays proposé
    options: textOpts(countryOptions(c, cands), (x) => x.name),
  });
}

// --- neighbors ------------------------------------------------------------- //
export function buildNeighbor(cands, state, recent, country) {
  const candIso = new Set(cands.map((c) => c.iso3));
  const nin = (c) => data.neighbors(c).filter((n) => candIso.has(n.iso3));
  const eligible = cands.filter((c) => nin(c).length);
  if (!eligible.length) return buildCapital(cands, state, recent);
  const c = country && nin(country).length
    ? country
    : pickCountry(eligible, state, "neighbors", recent);
  const nbrs = data.neighbors(c);
  const correct = choice(nin(c));
  const excluded = new Set([...nbrs.map((n) => n.iso3), c.iso3]);
  const non = cands.filter((x) => !excluded.has(x.iso3));
  // distracteurs = NON-voisins ; en difficile ils sont proches de c → piégeux
  const pool = shuffle([correct, ...distractors(c, non, 3)]);
  return q({
    skill: "neighbors",
    item: c.iso3,
    correct: correct.iso3,
    stimulus: { kind: "text", value: `<img class="q-flag" src="${data.flagUrl(c.iso2, 40)}" alt=""> <b>${c.name}</b> : lequel de ces pays est frontalier ?` },
    interaction: "options",
    optionKind: "text",
    optionFlags: true, // drapeau à côté de chaque pays proposé
    options: textOpts(pool, (x) => x.name),
    explain: "Voisins : " + nbrs.map((n) => n.name).join(", "),
  });
}

// --- révision intelligente ------------------------------------------------- //
const CANON = {
  locate: buildLocate,
  flag: buildFlag,
  capital: buildCapital,
  neighbors: buildNeighbor,
};

export function buildSmart(cands, state, recent) {
  const rec = new Set(recent);
  const candIso = new Set(cands.map((c) => c.iso3));
  const gather = (skipRecent) => {
    const pool = [];
    for (const c of cands) {
      if (skipRecent && rec.has(c.iso3)) continue;
      for (const skill of Object.keys(CANON)) {
        if (skill === "neighbors" && !data.neighbors(c).some((n) => candIso.has(n.iso3)))
          continue;
        pool.push({ w: srs.weight(store.getItem(state, skill, c.iso3)), skill, c });
      }
    }
    return pool;
  };
  let pool = gather(true);
  if (!pool.length) pool = gather(false);
  const chosen = weightedPick(pool, pool.map((p) => p.w));
  return CANON[chosen.skill](cands, state, recent, chosen.c);
}

// --- France ---------------------------------------------------------------- //
export const FR_SKILLS = {
  fr_region: "Régions de France",
  fr_dept: "Départements",
  fr_city: "Villes de France",
  fr_arr: "Arrondissements de Paris",
  fr_domtom: "DOM-TOM",
  fr_monument: "Monuments de France",
};
export const FR_TOTALS = { fr_region: 13, fr_dept: 96, fr_city: 122, fr_arr: 20, fr_domtom: 10, fr_monument: 100 }; // fr_city = nb dans cities.json (sans arrondissements)
export const CITY_THRESHOLD_KM = 35; // tolérance de clic pour « place la ville »
export const DOMTOM_THRESHOLD_KM = 600; // large : on veut situer le territoire sur le globe
export const MONUMENT_THRESHOLD_KM = 15; // monuments : clic plus précis sur la carte FR

function pickWeighted(items, idOf, state, skill, recent) {
  const rec = new Set(recent);
  let pool = items.filter((x) => !rec.has(idOf(x)));
  if (!pool.length) pool = items.slice();
  const w = pool.map((x) => srs.weight(store.getItem(state, skill, idOf(x))));
  return weightedPick(pool, w);
}

const FR_ADMIN_KIND = {
  fr_region: "la région",
  fr_dept: "le département",
  fr_arr: "l'arrondissement",
};

function buildFrAdmin(features, skill) {
  return (cands, state, recent) => {
    const f = pickWeighted(features(), (x) => x.id, state, skill, recent);
    const label = f.properties.nom;
    return q({
      skill,
      item: f.id,
      correct: f.id,
      correctLabel: label,
      stimulus: { kind: "text", value: `Place ${FR_ADMIN_KIND[skill]} : <b>${label}</b>` },
      interaction: "mapclick",
    });
  };
}

export const buildFrRegion = buildFrAdmin(() => data.france().reg.features, "fr_region");
export const buildFrDept = buildFrAdmin(() => data.france().dep.features, "fr_dept");
export const buildFrArr = buildFrAdmin(() => data.france().paris.features, "fr_arr");

export function buildFrCity(cands, state, recent) {
  const c = pickWeighted(data.france().cities, (x) => x.name, state, "fr_city", recent);
  return q({
    skill: "fr_city",
    item: c.name,
    correct: c.name,
    correctLabel: c.name,
    stimulus: { kind: "text", value: `Place la ville : <b>${c.name}</b>` },
    interaction: "rawclick",
    city: c,
  });
}

// Monuments : placer le monument sur la carte de France (clic libre).
export function buildFrMonument(cands, state, recent) {
  const m = pickWeighted(data.france().monuments, (x) => x.name, state, "fr_monument", recent);
  return q({
    skill: "fr_monument",
    item: m.name,
    correct: m.name,
    correctLabel: m.name,
    stimulus: { kind: "text", value: `Place ce monument : <b>${m.name}</b>` },
    interaction: "rawclick",
    city: m,
    threshold: MONUMENT_THRESHOLD_KM,
  });
}

// DOM-TOM : placer le territoire sur la carte du monde (clic libre, tolérance large).
export function buildFrDomtom(cands, state, recent) {
  const t = pickWeighted(data.france().domtom, (x) => x.name, state, "fr_domtom", recent);
  return q({
    skill: "fr_domtom",
    item: t.name,
    correct: t.name,
    correctLabel: t.name,
    stimulus: { kind: "text", value: `Place ce territoire d'outre-mer : <b>${t.name}</b>` },
    interaction: "rawclick",
    city: t,
    threshold: DOMTOM_THRESHOLD_KM,
  });
}

// --- Monde : villes, fleuves, géographie physique -------------------------- //
export const WORLD_SKILLS = {
  world_city: "Grandes villes du monde",
  river: "Fleuves",
  sea: "Mers & océans",
  desert: "Déserts",
  range: "Chaînes de montagnes",
  peak: "Sommets",
};
export const WORLD_TOTAL = { world_city: 616, river: 33, sea: 30, desert: 17, range: 26, peak: 24 };
export const WORLD_CITY_THRESHOLD_KM = 150; // clic libre sur la carte du monde

// Générateur générique « zone surlignée en rouge → son nom » (QCM).
// Données = liste de { name, geometry } chargée à la demande (data.set(key)).
function buildHighlight(key, skill, ask) {
  return (cands, state, recent) => {
    const items = data.set(key) || [];
    const it = pickWeighted(items, (x) => x.name, state, skill, recent);
    const others = shuffle(items.filter((x) => x.name !== it.name)).slice(0, 3);
    const opts = shuffle([it, ...others]).map((x) => ({ id: x.name, label: x.name }));
    return q({
      skill,
      item: it.name,
      correct: it.name,
      stimulus: { kind: "region", value: it },
      ask,
      interaction: "options",
      optionKind: "text",
      options: opts,
    });
  };
}

export const buildSea = buildHighlight("seas", "sea", "Quelle est cette mer / cet océan ? (en rouge)");
export const buildDesert = buildHighlight("deserts", "desert", "Quel est ce désert ? (en rouge)");
export const buildRange = buildHighlight("ranges", "range", "Quelle est cette chaîne de montagnes ? (en rouge)");

// Sommets : un triangle rouge sur le pic → son nom (QCM).
export function buildPeak(cands, state, recent) {
  const peaks = data.set("peaks");
  const p = pickWeighted(peaks, (x) => x.name, state, "peak", recent);
  const others = shuffle(peaks.filter((x) => x.name !== p.name)).slice(0, 3);
  const opts = shuffle([p, ...others]).map((x) => ({ id: x.name, label: x.name }));
  return q({
    skill: "peak",
    item: p.name,
    correct: p.name,
    stimulus: { kind: "peak", value: p },
    ask: "Quel est ce sommet ? (au triangle rouge)",
    interaction: "options",
    optionKind: "text",
    options: opts,
  });
}

// Fleuves : un fleuve surligné en rouge sur le planisphère → son nom (QCM).
export function buildRiver(cands, state, recent) {
  const rivers = data.rivers();
  const r = pickWeighted(rivers, (x) => x.name, state, "river", recent);
  const others = shuffle(rivers.filter((x) => x.name !== r.name)).slice(0, 3);
  const opts = shuffle([r, ...others]).map((x) => ({ id: x.name, label: x.name }));
  return q({
    skill: "river",
    item: r.name,
    correct: r.name,
    stimulus: { kind: "river", value: r },
    ask: "Quel est ce fleuve ? (en rouge)",
    interaction: "options",
    optionKind: "text",
    options: opts,
  });
}

// Noms de ville partagés par plusieurs pays → on gardera l'indice pays pour eux.
let _ambiguousCities = null;
function ambiguousCities() {
  if (!_ambiguousCities) {
    const n = {};
    for (const c of data.citiesWorld()) n[c.name] = (n[c.name] || 0) + 1;
    _ambiguousCities = new Set(Object.keys(n).filter((k) => n[k] > 1));
  }
  return _ambiguousCities;
}

export function buildWorldCity(cands, state, recent) {
  const idOf = (x) => `${x.name} (${x.country})`;
  const c = pickWeighted(data.citiesWorld(), idOf, state, "world_city", recent);
  // On ne révèle PAS le pays (sinon trop facile), sauf si le nom est ambigu
  // (plusieurs villes du même nom dans des pays différents).
  const hint = ambiguousCities().has(c.name)
    ? ` <span style="color:#9aa4b2">(${c.country})</span>`
    : "";
  return q({
    skill: "world_city",
    item: idOf(c),
    correct: idOf(c),
    correctLabel: idOf(c),
    stimulus: { kind: "text", value: `Place la ville : <b>${c.name}</b>${hint}` },
    interaction: "rawclick",
    city: c,
    threshold: WORLD_CITY_THRESHOLD_KM,
  });
}

// --- États-Unis ------------------------------------------------------------ //
export const US_SKILLS = { us_state: "États américains" };
export const US_TOTAL = { us_state: 48 };

export function buildUsState(cands, state, recent) {
  const f = pickWeighted(data.usa().features, (x) => x.id, state, "us_state", recent);
  return q({
    skill: "us_state",
    item: f.id,
    correct: f.id,
    correctLabel: f.properties.nom,
    stimulus: { kind: "text", value: `Place l'état : <b>${f.properties.nom}</b>` },
    interaction: "mapclick",
  });
}

// --- catalogue des jeux (ordre du menu) ------------------------------------ //
export const GAMES = [
  { key: "revision", title: "🧠 Révision intelligente", sub: "Ce que tu maîtrises le moins", build: buildSmart, context: "world" },
  { key: "carte", title: "🗺️ Carte", sub: "Le pays surligné → son nom", build: buildLocate, context: "world" },
  { key: "place", title: "📍 Place le pays", sub: "Clique le bon pays sur la carte", build: buildPlace, context: "world" },
  { key: "silhouette", title: "🕵️ Silhouette", sub: "La forme seule → le pays", build: buildSilhouette, context: "world" },
  { key: "drapeaux", title: "🚩 Drapeaux", sub: "Le drapeau → le pays", build: buildFlag, context: "world" },
  { key: "trouve_drapeau", title: "🎯 Trouve le drapeau", sub: "Clique le bon drapeau", build: buildPickFlag, context: "world" },
  { key: "capitales", title: "🏛️ Capitales", sub: "Le pays → sa capitale", build: buildCapital, context: "world" },
  { key: "capitale_pays", title: "🏙️ Capitale → pays", sub: "La capitale → le pays", build: buildCapitalToCountry, context: "world" },
  { key: "voisins", title: "🤝 Voisins", sub: "Trouve un pays frontalier", build: buildNeighbor, context: "world" },
  { key: "world_city", title: "🌍 Grandes villes du monde", sub: "Place la ville sur la carte", build: buildWorldCity, context: "world" },
  { key: "river", title: "🌊 Fleuves", sub: "Le fleuve surligné → son nom", build: buildRiver, context: "world" },
  { key: "sea", title: "🌊 Mers & océans", sub: "La zone surlignée → son nom", build: buildSea, context: "world", needs: ["seas"] },
  { key: "desert", title: "🏜️ Déserts", sub: "Le désert surligné → son nom", build: buildDesert, context: "world", needs: ["deserts"] },
  { key: "range", title: "⛰️ Chaînes de montagnes", sub: "La chaîne surlignée → son nom", build: buildRange, context: "world", needs: ["ranges"] },
  { key: "peak", title: "🏔️ Sommets du monde", sub: "Place le sommet sur la carte", build: buildPeak, context: "world", needs: ["peaks"] },
  { key: "fr_region", title: "🇫🇷 Régions de France", sub: "Place la région sur la carte", build: buildFrRegion, context: "france-regions" },
  { key: "fr_dept", title: "🇫🇷 Départements", sub: "Place le département", build: buildFrDept, context: "france-departements" },
  { key: "fr_city", title: "🇫🇷 Villes de France", sub: "Place la ville (> 50 000 hab.)", build: buildFrCity, context: "france-cities" },
  { key: "fr_monument", title: "🏛️ Monuments de France", sub: "Place le monument sur la carte", build: buildFrMonument, context: "france-cities" },
  { key: "fr_arr", title: "🇫🇷 Arrondissements de Paris", sub: "Place l'arrondissement sur le plan", build: buildFrArr, context: "paris-arrondissements" },
  { key: "fr_domtom", title: "🌴 DOM-TOM", sub: "Place le territoire sur le globe", build: buildFrDomtom, context: "world" },
  { key: "us_state", title: "🇺🇸 États américains", sub: "Place l'état sur la carte", build: buildUsState, context: "usa-states" },
];
