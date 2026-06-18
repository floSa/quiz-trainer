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
  size: "Comparer les superficies",
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

export function buildFlagToCapital(cands, state, recent, country) {
  const c = country || pickCountry(cands, state, "capital", recent);
  return q({
    skill: "capital",
    item: c.iso3,
    correct: c.iso3,
    stimulus: { kind: "flag", value: c },
    ask: "Quelle est la capitale de ce pays ?",
    interaction: "options",
    optionKind: "text",
    options: textOpts(countryOptions(c, cands), (x) => x.capital),
    explain: `${c.name} → ${c.capital}`,
  });
}

// --- neighbors ------------------------------------------------------------- //
export function buildNeighbor(cands, state, recent, country) {
  const candIso = new Set(cands.map((c) => c.iso3));
  const nin = (c) => data.neighbors(c).filter((n) => candIso.has(n.iso3));
  const eligible = cands.filter((c) => nin(c).length);
  if (!eligible.length) return buildLargest(cands, state, recent);
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

export function buildNeighborCount(cands, state, recent) {
  const eligible = cands.filter((c) => data.neighbors(c).length);
  if (!eligible.length) return buildLargest(cands, state, recent);
  const c = pickCountry(eligible, state, "neighbors", recent);
  const nbrs = data.neighbors(c);
  const count = nbrs.length;
  const set = new Set();
  for (const d of [-2, -1, 1, 2, 3]) {
    const v = Math.max(0, count + d);
    if (v !== count) set.add(v);
  }
  const nums = shuffle([count, ...shuffle([...set]).slice(0, 3)]);
  return q({
    skill: "neighbors",
    item: c.iso3,
    correct: String(count),
    stimulus: { kind: "text", value: `<b>${c.name}</b> : combien de pays frontaliers ?` },
    interaction: "options",
    optionKind: "text",
    options: valueOpts(nums),
    explain: "Voisins : " + nbrs.map((n) => n.name).join(", "),
  });
}

// --- size ------------------------------------------------------------------ //
export function buildLargest(cands, state, recent) {
  const pool = cands.filter((c) => c.area);
  const focus = pickCountry(pool, state, "size", recent);
  const others = shuffle(pool.filter((c) => c.iso3 !== focus.iso3)).slice(0, 3);
  const four = shuffle([focus, ...others]);
  const correct = four.reduce((a, b) => (b.area > a.area ? b : a));
  const explain = four
    .slice()
    .sort((a, b) => b.area - a.area)
    .map((x) => `${x.name} : ${Math.round(x.area).toLocaleString("fr-FR")} km²`)
    .join("  ·  ");
  return q({
    skill: "size",
    item: correct.iso3,
    correct: correct.iso3,
    stimulus: { kind: "text", value: "Lequel est le <b>plus grand</b> pays (superficie) ?" },
    interaction: "options",
    optionKind: "text",
    options: textOpts(four, (x) => x.name),
    explain,
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

// --- catalogue des jeux (ordre du menu) ------------------------------------ //
export const GAMES = [
  { key: "revision", title: "🧠 Révision intelligente", sub: "Ce que tu maîtrises le moins", build: buildSmart },
  { key: "carte", title: "🗺️ Carte", sub: "Le pays surligné → son nom", build: buildLocate },
  { key: "place", title: "📍 Place le pays", sub: "Clique le bon pays sur la carte", build: buildPlace },
  { key: "drapeaux", title: "🚩 Drapeaux", sub: "Le drapeau → le pays", build: buildFlag },
  { key: "trouve_drapeau", title: "🎯 Trouve le drapeau", sub: "Clique le bon drapeau", build: buildPickFlag },
  { key: "capitales", title: "🏛️ Capitales", sub: "Le pays → sa capitale", build: buildCapital },
  { key: "capitale_pays", title: "🏙️ Capitale → pays", sub: "La capitale → le pays", build: buildCapitalToCountry },
  { key: "drapeau_capitale", title: "🚩 Drapeau → capitale", sub: "Le drapeau → la capitale", build: buildFlagToCapital },
  { key: "voisins", title: "🤝 Voisins", sub: "Trouve un pays frontalier", build: buildNeighbor },
  { key: "nb_voisins", title: "🔢 Combien de voisins", sub: "Nombre de frontières", build: buildNeighborCount },
  { key: "plus_grand", title: "📏 Le plus grand", sub: "La plus grande superficie", build: buildLargest },
];
