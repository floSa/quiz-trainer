// Helpers Leaflet. Pas de tuiles : on dessine les polygones (monde OU France)
// sur un fond neutre. Couche interchangeable via setLayer().
let map = null;
let layer = null;
let byId = {}; // id de feature -> couche
let markers = [];
let featureClick = null;
let mapClick = null;

// Terres claires sur océan bleu (cf. --ocean en CSS). Coastline bleu-gris.
const BASE = { color: "#7e96a9", weight: 0.7, fillColor: "#e8efe2", fillOpacity: 1 };
const DIM = { color: "#bcc9bf", weight: 0.4, fillColor: "#eef2ea", fillOpacity: 1 };
const HILITE = { color: "#fff", weight: 1.2, fillColor: "#e8453c", fillOpacity: 1 };
const GOOD = { color: "#fff", weight: 1.2, fillColor: "#2e7d32", fillOpacity: 1 };
const BAD = { color: "#fff", weight: 1.2, fillColor: "#e8453c", fillOpacity: 1 };

export function ensureMap(containerId) {
  if (map) return map;
  map = L.map(containerId, {
    zoomControl: true,
    attributionControl: false,
    worldCopyJump: true,
    minZoom: 1,
    maxZoom: 8,
  });
  map.setView([25, 10], 2);
  map.on("click", (e) => mapClick && mapClick(e.latlng));
  return map;
}

// Remplace la couche affichée (monde, régions FR, départements FR…).
export function setLayer(geojson, { interactive = true } = {}) {
  if (layer) layer.remove();
  byId = {};
  clearMarkers();
  layer = L.geoJSON(geojson, {
    interactive,
    style: () => BASE,
    onEachFeature: (f, l) => {
      byId[f.id] = l;
      if (interactive) l.on("click", () => featureClick && featureClick(f.id));
    },
  }).addTo(map);
  return layer;
}

export function invalidate() {
  if (map) setTimeout(() => map.invalidateSize(), 50);
}
export function onFeatureClick(fn) { featureClick = fn; }
export function onMapClick(fn) { mapClick = fn; }
export function resetBase() { if (layer) layer.setStyle(BASE); }

function fitTo(id, maxZoom = 6) {
  const l = byId[id];
  if (l) map.fitBounds(l.getBounds(), { padding: [30, 30], maxZoom, animate: false });
}

export function highlight(id) {
  resetBase();
  if (byId[id]) byId[id].setStyle(HILITE);
  fitTo(id);
}

export function focusIds(idList) {
  const set = new Set(idList);
  layer.eachLayer((l) => l.setStyle(set.has(l.feature.id) ? BASE : DIM));
  const inSet = idList.map((i) => byId[i]).filter(Boolean);
  if (inSet.length) {
    let b = inSet[0].getBounds();
    inSet.slice(1).forEach((l) => (b = b.extend(l.getBounds())));
    map.fitBounds(b, { padding: [20, 20] });
  }
}

export function fitAll() {
  if (layer) map.fitBounds(layer.getBounds(), { padding: [15, 15] });
}

export function markResult(correctId, clickedId, wasCorrect) {
  if (byId[correctId]) byId[correctId].setStyle(GOOD);
  if (clickedId && clickedId !== correctId && byId[clickedId]) byId[clickedId].setStyle(BAD);
  // Si on a bon, on ne bouge pas (la bonne réponse est sous le curseur). Si on
  // a faux, on recadre sur la bonne réponse pour qu'elle soit visible même si
  // on était zoomé ailleurs.
  if (!wasCorrect) fitTo(correctId);
}

// Marqueurs ponctuels (jeu « place la ville »).
export function addMarker(lat, lng, color) {
  const m = L.circleMarker([lat, lng], {
    radius: 7,
    color: "#fff",
    weight: 2,
    fillColor: color,
    fillOpacity: 1,
  }).addTo(map);
  markers.push(m);
  return m;
}
export function clearMarkers() {
  markers.forEach((m) => m.remove());
  markers = [];
}
export function panTo(lat, lng, zoom = 6) {
  if (map) map.setView([lat, lng], zoom);
}

// Tableau de bord : colore chaque pays selon sa maîtrise (0→1).
export function choropleth(masteryById) {
  resetBase();
  layer.eachLayer((l) => {
    const m = masteryById[l.feature.id] || 0;
    l.setStyle({ color: "#fff", weight: 0.4, fillOpacity: 1, fillColor: m <= 0 ? "#e8efe2" : mix(m) });
  });
  map.setView([25, 10], 2);
}
function mix(m) {
  const from = [155, 212, 155];
  const to = [46, 125, 50];
  const c = from.map((f, i) => Math.round(f + (to[i] - f) * m));
  return `rgb(${c[0]},${c[1]},${c[2]})`;
}
