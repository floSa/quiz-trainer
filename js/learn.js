// Page « Apprendre » : tableaux de référence (drapeaux, capitales, miniatures
// de localisation, villes…). Aucune carte Leaflet ici — les miniatures sont des
// SVG pré-générés (data/thumbs/) servis en <img loading="lazy">.
import * as data from "./data.js";

// --- helpers de rendu ------------------------------------------------------ //
const flag = (iso2) => `<img class="l-flag" loading="lazy" src="${data.flagUrl(iso2, 80)}" alt="">`;
const thumb = (group, id) => `<img class="l-thumb" loading="lazy" src="data/thumbs/${group}/${id}.svg" alt="">`;

// Centroïde du plus grand polygone (= masse continentale principale), pour le
// tri ; évite que les territoires lointains (Guyane…) faussent la position.
function mainCentroid(geom) {
  const polys = geom.type === "Polygon" ? [geom.coordinates] : geom.coordinates;
  let best = null, bestN = -1;
  for (const poly of polys) {
    const ring = poly[0];
    if (ring.length > bestN) { bestN = ring.length; best = ring; }
  }
  const xs = best.map((p) => p[0]);
  const ys = best.map((p) => p[1]);
  return { lng: (Math.min(...xs) + Math.max(...xs)) / 2, lat: (Math.min(...ys) + Math.max(...ys)) / 2 };
}

// --- blocs continentaux (mêmes regroupements que build_thumbs.py) ---------- //
const BLOCKS = {
  Europe: ["Western Europe", "Eastern Europe", "Northern Europe", "Southern Europe", "Central Europe", "Southeast Europe"],
  Afrique: ["Northern Africa", "Western Africa", "Eastern Africa", "Middle Africa", "Southern Africa"],
  Asie: ["Central Asia", "Eastern Asia", "Western Asia", "Southern Asia", "South-Eastern Asia"],
  "Amérique du Nord": ["North America", "Central America", "Caribbean"],
  "Amérique du Sud": ["South America"],
  Océanie: ["Australia and New Zealand", "Melanesia", "Micronesia", "Polynesia"],
};
const BLOCK_ORDER = ["Europe", "Afrique", "Asie", "Amérique du Nord", "Amérique du Sud", "Océanie"];
const WEST_EAST = new Set(["Europe", "Océanie"]); // tri ouest→est ; les autres nord→sud
const blockOf = (sub) => BLOCK_ORDER.find((b) => BLOCKS[b].includes(sub));

// villes par pays (depuis cities_world), du plus peuplé au moins peuplé
function citiesByIso3() {
  const by = {};
  for (const c of data.citiesWorld() || []) (by[c.iso3] = by[c.iso3] || []).push(c.name);
  return by;
}

// --- section : Pays --------------------------------------------------------- //
function sectionPays() {
  const geoById = Object.fromEntries(data.geo().features.map((f) => [f.id, f]));
  const cities = citiesByIso3();
  const groups = {};
  for (const c of data.countries()) {
    const b = blockOf(c.subregion);
    if (b) (groups[b] = groups[b] || []).push(c);
  }

  let rows = `<thead><tr><th>Drapeau</th><th>Pays</th><th>Capitale</th><th>Localisation</th><th>Grandes villes</th></tr></thead><tbody>`;
  for (const block of BLOCK_ORDER) {
    const list = (groups[block] || []).filter((c) => geoById[c.iso3]);
    const cen = Object.fromEntries(list.map((c) => [c.iso3, mainCentroid(geoById[c.iso3].geometry)]));
    // Pacifique : les longitudes < -25° (au-delà de l'antiméridien) sont
    // ramenées au-dessus de 180° pour un vrai ordre ouest→est en Océanie.
    const lng = (iso) => (cen[iso].lng < -25 ? cen[iso].lng + 360 : cen[iso].lng);
    list.sort((a, b) => WEST_EAST.has(block)
      ? lng(a.iso3) - lng(b.iso3)               // ouest → est
      : cen[b.iso3].lat - cen[a.iso3].lat);     // nord → sud
    const sens = WEST_EAST.has(block) ? "ouest → est" : "nord → sud";
    rows += `<tr class="l-block"><td colspan="5">${block} <span class="l-sens">${sens}</span></td></tr>`;
    for (const c of list) {
      const v = (cities[c.iso3] || []).slice(0, 6).join(", ");
      rows += `<tr>
        <td>${flag(c.iso2)}</td>
        <td class="l-name">${c.name}</td>
        <td>${c.capital || "—"}</td>
        <td>${thumb("countries", c.iso3)}</td>
        <td class="l-cities">${v || "—"}</td></tr>`;
    }
  }
  return `<table class="l-table">${rows}</tbody></table>`;
}

// --- section : Départements ------------------------------------------------ //
function sectionDept() {
  const fr = data.france();
  const pref = fr.prefectures || {};
  // ordre officiel : 01…19, 2A, 2B, 21…95 (Corse intercalée)
  const key = (id) => (id === "2A" ? 20.1 : id === "2B" ? 20.2 : parseInt(id, 10));
  const feats = [...fr.dep.features].sort((a, b) => key(a.id) - key(b.id));
  let rows = `<thead><tr><th>Localisation</th><th>Département</th><th>Préfecture</th></tr></thead><tbody>`;
  for (const f of feats) {
    rows += `<tr>
      <td>${thumb("dept", f.id)}</td>
      <td class="l-name">${f.id} · ${f.properties.nom}</td>
      <td>${pref[f.id] || "—"}</td></tr>`;
  }
  return `<table class="l-table">${rows}</tbody></table>`;
}

// --- section : Monuments de France ----------------------------------------- //
function sectionMonuments() {
  const mons = data.france().monuments || [];
  let rows = `<thead><tr><th>Photo</th><th>Monument</th><th>Localisation</th></tr></thead><tbody>`;
  for (const m of mons) {
    const photo = m.img
      ? `<img class="l-photo" loading="lazy" src="data/thumbs/monument-photo/${m.img}" alt="">`
      : `<div class="l-photo l-noimg">📷</div>`;
    rows += `<tr>
      <td>${photo}</td>
      <td class="l-name">${m.name}</td>
      <td>${thumb("monument", m.slug)}</td></tr>`;
  }
  return `<table class="l-table">${rows}</tbody></table>`;
}

// --- catalogue des sections (s'étoffera) ----------------------------------- //
const SECTIONS = [
  { key: "pays", label: "🌍 Pays", build: sectionPays },
  { key: "dept", label: "🇫🇷 Départements", build: sectionDept },
  { key: "monument", label: "🏛️ Monuments", build: sectionMonuments },
];

let current = SECTIONS[0].key;

export function render(root) {
  const sec = SECTIONS.find((s) => s.key === current) || SECTIONS[0];
  root.innerHTML = `
    <h1>📚 Apprendre</h1>
    <p class="muted">Tableaux de référence pour réviser avant de jouer.</p>
    <div class="l-subnav">${SECTIONS.map((s) =>
      `<button class="l-chip ${s.key === current ? "active" : ""}" data-sec="${s.key}">${s.label}</button>`).join("")}</div>
    <div class="l-content">${sec.build()}</div>`;
  root.querySelectorAll(".l-chip").forEach((b) => (b.onclick = () => { current = b.dataset.sec; render(root); root.scrollTop = 0; }));
}
