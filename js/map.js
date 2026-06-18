// Helpers Leaflet. Pas de tuiles : on dessine seulement les polygones des pays
// sur un fond neutre (pas d'étiquettes → pas de triche, et hors-ligne).
import * as data from "./data.js";

let map = null;
let layer = null;
const byIso = {}; // iso3 -> couche Leaflet du pays
let clickHandler = null;

const BASE = { color: "#aab6c2", weight: 0.6, fillColor: "#e9edf1", fillOpacity: 1 };
const DIM = { color: "#cdd5dd", weight: 0.4, fillColor: "#f4f6f8", fillOpacity: 1 };
const HILITE = { color: "#fff", weight: 1, fillColor: "#e8453c", fillOpacity: 1 };
const GOOD = { color: "#fff", weight: 1, fillColor: "#2e7d32", fillOpacity: 1 };
const BAD = { color: "#fff", weight: 1, fillColor: "#e8453c", fillOpacity: 1 };

export function ensureMap(containerId) {
  if (map) return map;
  map = L.map(containerId, {
    zoomControl: true,
    attributionControl: false,
    worldCopyJump: true,
    minZoom: 1,
    maxZoom: 7,
  });
  map.setView([25, 10], 2);
  layer = L.geoJSON(data.geo(), {
    style: () => BASE,
    onEachFeature: (f, l) => {
      byIso[f.id] = l;
      l.on("click", () => clickHandler && clickHandler(f.id));
    },
  }).addTo(map);
  return map;
}

export function invalidate() {
  if (map) setTimeout(() => map.invalidateSize(), 50);
}

export function resetBase() {
  if (layer) layer.setStyle(BASE);
}

export function setClickHandler(fn) {
  clickHandler = fn;
}

function fitTo(iso3, maxZoom = 6) {
  const l = byIso[iso3];
  if (l) map.fitBounds(l.getBounds(), { padding: [30, 30], maxZoom });
}

// Surligne un pays et zoome dessus (jeu « Carte »).
export function highlight(iso3) {
  resetBase();
  if (byIso[iso3]) byIso[iso3].setStyle(HILITE);
  fitTo(iso3);
}

// Prépare le jeu « Place le pays » : dim hors-zone, cadre sur la zone.
export function focusZone(isoList) {
  const set = new Set(isoList);
  layer.eachLayer((l) => l.setStyle(set.has(l.feature.id) ? BASE : DIM));
  const inZone = isoList.map((i) => byIso[i]).filter(Boolean);
  if (inZone.length) {
    let b = inZone[0].getBounds();
    inZone.slice(1).forEach((l) => (b = b.extend(l.getBounds())));
    map.fitBounds(b, { padding: [20, 20] });
  }
}

// Marque la correction sur la carte (vert = bon, rouge = clic erroné).
export function markResult(correctIso, clickedIso) {
  if (byIso[correctIso]) byIso[correctIso].setStyle(GOOD);
  if (clickedIso && clickedIso !== correctIso && byIso[clickedIso])
    byIso[clickedIso].setStyle(BAD);
  fitTo(correctIso);
}

// Tableau de bord : colore chaque pays selon sa maîtrise (0→1).
export function choropleth(masteryByIso) {
  resetBase();
  layer.eachLayer((l) => {
    const m = masteryByIso[l.feature.id] || 0;
    l.setStyle({
      color: "#fff",
      weight: 0.4,
      fillOpacity: 1,
      fillColor: m <= 0 ? "#eef0f2" : mix(m),
    });
  });
  map.setView([25, 10], 2);
}

// dégradé gris clair → vert
function mix(m) {
  const from = [155, 212, 155];
  const to = [46, 125, 50];
  const c = from.map((f, i) => Math.round(f + (to[i] - f) * m));
  return `rgb(${c[0]},${c[1]},${c[2]})`;
}
