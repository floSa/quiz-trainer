// Helpers Leaflet. Pas de tuiles : on dessine les polygones (monde OU France)
// sur un fond neutre. Couche interchangeable via setLayer().
let map = null;
let layer = null;
let byId = {}; // id de feature -> couche
let markers = [];
let featureClick = null;
let mapClick = null;

const OCEAN = "#a9d2ea"; // doit coller à --ocean (CSS) : sert au fondu silhouette
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
    maxZoom: 14, // assez profond pour le plan de Paris (sans tuiles → pur vectoriel)
    // zoom fractionnaire : sinon fitBounds arrondit le zoom à l'entier inférieur
    // et la carte ne remplit que ~50 % du cadre (jusqu'à 2× de vide).
    zoomSnap: 0,
    zoomDelta: 0.5,
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

// Synchrone et AVANT tout cadrage : sinon Leaflet calcule fitBounds contre une
// taille de conteneur périmée (carte qui vient de passer de display:none à
// block) → vue trop dézoomée / surlignage hors cadre.
export function invalidate() {
  if (map) map.invalidateSize(false);
}
export function onFeatureClick(fn) { featureClick = fn; }
export function onMapClick(fn) { mapClick = fn; }
export function resetBase() { if (layer) layer.setStyle(BASE); }

function fitTo(id, maxZoom = 6) {
  const l = byId[id];
  if (l) map.fitBounds(l.getBounds(), { padding: [30, 30], maxZoom, animate: false });
}

// Recadre pour montrer tous les polygones donnés (ex. bonne réponse + choix).
// maxZoom élevé : pour des entités proches (arrondissements voisins) on veut
// rester zoomé, pas dézoomer à l'échelle d'un pays.
function fitToIds(ids, maxZoom = 10) {
  const ls = ids.map((i) => byId[i]).filter(Boolean);
  if (!ls.length) return;
  let b = ls[0].getBounds();
  ls.slice(1).forEach((l) => (b = b.extend(l.getBounds())));
  map.fitBounds(b, { padding: [45, 45], maxZoom, animate: false });
}

// Recadre pour montrer tous les points donnés (ex. ville cherchée + clic).
export function fitPoints(latlngs, maxZoom = 7) {
  if (!latlngs || !latlngs.length) return;
  const b = L.latLngBounds(latlngs.map((p) => [p.lat, p.lng]));
  map.fitBounds(b, { padding: [70, 70], maxZoom, animate: false });
}

export function highlight(id) {
  resetBase();
  if (byId[id]) byId[id].setStyle(HILITE);
  fitTo(id);
}

// Silhouette : on ne montre QUE le pays cible (les autres fondus dans l'océan,
// donc invisibles) et on zoome dessus → reconnaître la forme sans les voisins.
export function silhouette(id) {
  if (!layer) return;
  layer.eachLayer((l) => {
    if (l.feature.id === id) l.setStyle({ color: "#5a6b7a", weight: 1.4, fillColor: "#e8efe2", fillOpacity: 1 });
    else l.setStyle({ color: OCEAN, weight: 0, fillColor: OCEAN, fillOpacity: 1 });
  });
  fitTo(id, 9);
}

export function focusIds(idList) {
  const set = new Set(idList);
  layer.eachLayer((l) => l.setStyle(set.has(l.feature.id) ? BASE : DIM));
  const inSet = idList.map((i) => byId[i]).filter(Boolean);
  if (inSet.length) {
    let b = inSet[0].getBounds();
    inSet.slice(1).forEach((l) => (b = b.extend(l.getBounds())));
    map.fitBounds(b, { padding: [8, 8] });
  }
}

export function fitAll() {
  if (layer) map.fitBounds(layer.getBounds(), { padding: [8, 8] });
}

export function markResult(correctId, clickedId, wasCorrect) {
  if (byId[correctId]) byId[correctId].setStyle(GOOD);
  if (clickedId && clickedId !== correctId && byId[clickedId]) byId[clickedId].setStyle(BAD);
  if (wasCorrect) return; // bonne réponse sous le curseur : on ne bouge pas
  // Faux : on montre LE CHOIX et LA BONNE RÉPONSE ensemble pour situer l'erreur,
  // même si on était zoomé loin.
  if (clickedId && clickedId !== correctId && byId[clickedId] && byId[correctId]) {
    fitToIds([correctId, clickedId]);
  } else {
    fitTo(correctId);
  }
}

// Trace un fleuve (GeoJSON MultiLineString) en surbrillance et cadre dessus.
export function addRiver(geometry, color = "#e8453c") {
  const l = L.geoJSON(geometry, {
    style: { color, weight: 3, opacity: 0.95, lineCap: "round", lineJoin: "round" },
  }).addTo(map);
  markers.push(l); // nettoyé par clearMarkers()
  try {
    map.fitBounds(l.getBounds(), { padding: [30, 30], maxZoom: 7, animate: false });
  } catch (e) {}
  return l;
}

// Trace une zone (GeoJSON polygone : mer, désert, chaîne) en surbrillance.
export function addRegion(geometry, color = "#e8453c") {
  const l = L.geoJSON(geometry, {
    style: { color, weight: 1.2, opacity: 0.9, fillColor: color, fillOpacity: 0.4 },
  }).addTo(map);
  markers.push(l); // nettoyé par clearMarkers()
  try {
    map.fitBounds(l.getBounds(), { padding: [25, 25], maxZoom: 6, animate: false });
  } catch (e) {}
  return l;
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

// Carte des connaissances du tableau de bord : instance Leaflet DÉDIÉE (le
// conteneur est recréé à chaque rendu du dashboard, donc on repart à neuf).
let dashMap = null;
export function choroplethMap(containerId, geojson, masteryById) {
  if (dashMap) { dashMap.remove(); dashMap = null; }
  dashMap = L.map(containerId, {
    zoomControl: false, attributionControl: false, dragging: true,
    scrollWheelZoom: false, minZoom: 1, maxZoom: 6, zoomSnap: 0,
  });
  const layer = L.geoJSON(geojson, {
    interactive: false,
    style: (f) => {
      const m = masteryById[f.id] || 0;
      return { color: "#1b2027", weight: 0.4, fillOpacity: 1, fillColor: m <= 0 ? "#39414e" : mix(m) };
    },
  }).addTo(dashMap);
  setTimeout(() => {
    dashMap.invalidateSize(false);
    try { dashMap.fitBounds(layer.getBounds(), { padding: [6, 6] }); } catch (e) {}
  }, 60);
}
