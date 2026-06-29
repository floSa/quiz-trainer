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

// QCM de pays : bonne réponse + distracteurs (même région en priorité).
function countryOptions(correct, cands, k = 3) {
  const same = shuffle(
    cands.filter((c) => c.iso3 !== correct.iso3 && c.region === correct.region)
  );
  const others = shuffle(
    cands.filter((c) => c.iso3 !== correct.iso3 && c.region !== correct.region)
  );
  return shuffle([correct, ...same.concat(others).slice(0, k)]);
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
    options: textOpts(countryOptions(c, cands), (x) => x.name),
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
    options: textOpts(countryOptions(c, cands), (x) => x.name),
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
  const same = shuffle(non.filter((x) => x.region === c.region));
  const others = shuffle(non.filter((x) => x.region !== c.region));
  const pool = shuffle([correct, ...same.concat(others).slice(0, 3)]);
  return q({
    skill: "neighbors",
    item: c.iso3,
    correct: correct.iso3,
    stimulus: { kind: "text", value: `<b>${c.name}</b> : lequel de ces pays est frontalier ?` },
    interaction: "options",
    optionKind: "text",
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
};
export const FR_TOTALS = { fr_region: 13, fr_dept: 96, fr_city: 122, fr_arr: 20, fr_domtom: 10 }; // fr_city = nb dans cities.json (sans arrondissements)
export const CITY_THRESHOLD_KM = 35; // tolérance de clic pour « place la ville »
export const DOMTOM_THRESHOLD_KM = 600; // large : on veut situer le territoire sur le globe

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
  { key: "drapeaux", title: "🚩 Drapeaux", sub: "Le drapeau → le pays", build: buildFlag, context: "world" },
  { key: "trouve_drapeau", title: "🎯 Trouve le drapeau", sub: "Clique le bon drapeau", build: buildPickFlag, context: "world" },
  { key: "capitales", title: "🏛️ Capitales", sub: "Le pays → sa capitale", build: buildCapital, context: "world" },
  { key: "capitale_pays", title: "🏙️ Capitale → pays", sub: "La capitale → le pays", build: buildCapitalToCountry, context: "world" },
  { key: "voisins", title: "🤝 Voisins", sub: "Trouve un pays frontalier", build: buildNeighbor, context: "world" },
  { key: "fr_region", title: "🇫🇷 Régions de France", sub: "Place la région sur la carte", build: buildFrRegion, context: "france-regions" },
  { key: "fr_dept", title: "🇫🇷 Départements", sub: "Place le département", build: buildFrDept, context: "france-departements" },
  { key: "fr_city", title: "🇫🇷 Villes de France", sub: "Place la ville (> 50 000 hab.)", build: buildFrCity, context: "france-cities" },
  { key: "fr_arr", title: "🇫🇷 Arrondissements de Paris", sub: "Place l'arrondissement sur le plan", build: buildFrArr, context: "paris-arrondissements" },
  { key: "fr_domtom", title: "🌴 DOM-TOM", sub: "Place le territoire sur le globe", build: buildFrDomtom, context: "world" },
  { key: "us_state", title: "🇺🇸 États américains", sub: "Place l'état sur la carte", build: buildUsState, context: "usa-states" },
];
