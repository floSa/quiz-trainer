// Chargement et accès aux données : pays (countries.json) + géométries
// (world.geojson, clé = iso3).

let _countries = null;
let _geo = null;
let _byIso = null;
let _fr = null;
let _usa = null;
let _citiesWorld = null;
let _rivers = null;

export async function load() {
  if (_countries) return;
  const [c, g, cw, rv] = await Promise.all([
    fetch("data/countries.json").then((r) => r.json()),
    fetch("data/world.geojson").then((r) => r.json()),
    fetch("data/cities_world.json").then((r) => r.json()),
    fetch("data/rivers.json").then((r) => r.json()),
  ]);
  _countries = c.slice().sort((a, b) => a.name.localeCompare(b.name, "fr"));
  _geo = g;
  _byIso = Object.fromEntries(c.map((x) => [x.iso3, x]));
  _citiesWorld = cw;
  _rivers = rv;
}

export function citiesWorld() {
  return _citiesWorld;
}
export function rivers() {
  return _rivers;
}

export function countries() {
  return _countries;
}

export function geo() {
  return _geo;
}

export function byIso3(iso) {
  return _byIso[iso];
}

export function regions() {
  return [...new Set(_countries.map((c) => c.region))].sort((a, b) =>
    a.localeCompare(b, "fr")
  );
}

export function countriesIn(regs) {
  if (!regs || !regs.length) return _countries;
  const s = new Set(regs);
  return _countries.filter((c) => s.has(c.region));
}

export function flagUrl(iso2, w = 320) {
  return `https://flagcdn.com/w${w}/${iso2.toLowerCase()}.png`;
}

export function neighbors(c) {
  return (c.borders || []).map((b) => _byIso[b]).filter(Boolean);
}

// --- France (chargé à la demande) ---
export async function loadFrance() {
  if (_fr) return _fr;
  const [reg, dep, cities, paris, domtom, monuments] = await Promise.all([
    fetch("data/france/regions.geojson").then((r) => r.json()),
    fetch("data/france/departements.geojson").then((r) => r.json()),
    fetch("data/france/cities.json").then((r) => r.json()),
    fetch("data/france/paris.geojson").then((r) => r.json()),
    fetch("data/france/domtom.json").then((r) => r.json()),
    fetch("data/france/monuments.json").then((r) => r.json()),
  ]);
  _fr = { reg, dep, cities, paris, domtom, monuments };
  return _fr;
}
export function france() {
  return _fr;
}

// --- États-Unis (chargé à la demande) ---
export async function loadUsa() {
  if (_usa) return _usa;
  _usa = await fetch("data/usa/states.geojson").then((r) => r.json());
  return _usa;
}
export function usa() {
  return _usa;
}

