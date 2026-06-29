// Orchestrateur : navigation, filtre par zone, contextes de carte (monde /
// France), cycle de jeu, tableau de bord.
import * as data from "./data.js";
import * as store from "./store.js";
import * as games from "./games.js";
import * as mapMod from "./map.js";

const ZONES_KEY = "quiztrainer.zones.v1";

let state = store.load();
let gameKey = games.GAMES[0].key;
let candidates = [];
let selectedRegions = [];
let mapContext = null; // "world" | "france-regions" | "france-departements" | "france-cities"
const recent = {};
const session = {};
let currentQ = null;
let answered = false;
let navToken = 0; // anti-désync quand on change de jeu pendant un chargement
let advanceTimer = null; // enchaînement auto vers la question suivante
const ADVANCE_OK = 850; // ms affichés quand c'est bon
const ADVANCE_KO = 2100; // ms quand c'est raté (le temps de lire la bonne réponse)

const $ = (id) => document.getElementById(id);

async function init() {
  await data.load();
  mapMod.ensureMap("map");
  mapMod.onFeatureClick(onFeatureClick);
  mapMod.onMapClick(onRawClick);
  selectedRegions = loadZones();
  candidates = data.countriesIn(selectedRegions);
  buildSidebar();
  selectGame(gameKey);
  data.loadFrance().catch(() => {}); // préchargement en tâche de fond
  data.loadUsa().catch(() => {});
}

function loadZones() {
  try {
    const z = JSON.parse(localStorage.getItem(ZONES_KEY));
    if (Array.isArray(z) && z.length) return z;
  } catch (e) {}
  return data.regions();
}

// --------------------------------------------------------------------------- //
function buildSidebar() {
  const nav = $("nav");
  nav.innerHTML = "";
  games.GAMES.forEach((g) => {
    const b = document.createElement("button");
    b.className = "nav-item";
    b.dataset.game = g.key;
    b.innerHTML = `<span class="nav-title">${g.title}</span>${g.sub ? `<span class="nav-sub">${g.sub}</span>` : ""}`;
    b.onclick = () => selectGame(g.key);
    nav.appendChild(b);
  });
  const dash = document.createElement("button");
  dash.className = "nav-item nav-dash";
  dash.innerHTML = `<span class="nav-title">📊 Tableau de bord</span>`;
  dash.onclick = selectDashboard;
  nav.appendChild(dash);

  const zl = $("zone-list");
  zl.innerHTML = "";
  data.regions().forEach((r) => {
    const wrap = document.createElement("label");
    wrap.className = "zone";
    wrap.innerHTML = `<input type="checkbox" value="${r}" ${selectedRegions.includes(r) ? "checked" : ""}> ${r}`;
    wrap.querySelector("input").onchange = onZoneChange;
    zl.appendChild(wrap);
  });

  $("reset").onclick = () => {
    if (confirm("Effacer toute ta progression ?")) {
      store.reset();
      state = store.load();
      $("dashboard").hidden ? selectGame(gameKey) : selectDashboard();
    }
  };
}

function onZoneChange() {
  selectedRegions = [...$("zone-list").querySelectorAll("input:checked")].map((i) => i.value);
  localStorage.setItem(ZONES_KEY, JSON.stringify(selectedRegions));
  candidates = data.countriesIn(selectedRegions);
  recent[gameKey] = [];
  if ($("dashboard").hidden) newRound();
}

// --------------------------------------------------------------------------- //
// Synchrone : les données France sont déjà chargées (préchargement / await amont).
function setContext(ctx) {
  if (ctx === mapContext) return;
  if (ctx === "world") {
    mapMod.setLayer(data.geo());
  } else if (ctx === "usa-states") {
    mapMod.setLayer(data.usa());
  } else {
    const fr = data.france();
    if (ctx === "france-regions") mapMod.setLayer(fr.reg);
    else if (ctx === "france-departements") mapMod.setLayer(fr.dep);
    else mapMod.setLayer(fr.dep, { interactive: false }); // villes : fond + clic libre
  }
  mapContext = ctx;
}

async function selectGame(key) {
  const token = ++navToken;
  clearTimeout(advanceTimer);
  gameKey = key;
  $("dashboard").hidden = true;
  $("game").hidden = false;
  document.querySelectorAll(".nav-item").forEach((b) => b.classList.toggle("active", b.dataset.game === key));
  const g = games.GAMES.find((x) => x.key === key);
  $("g-title").textContent = g.title;
  $("g-sub").textContent = g.sub || "";
  // on vide l'écran précédent tout de suite (sinon il reste affiché pendant
  // le chargement des données France → impression de blocage)
  $("options").innerHTML = "";
  $("options").hidden = true;
  $("feedback").innerHTML = "";
  $("prompt").innerHTML = g.context === "world" ? "" : "⏳ Chargement de la carte…";

  if (g.context !== "world") {
    try {
      if (g.context.startsWith("usa")) await data.loadUsa();
      else await data.loadFrance();
    } catch (e) {
      if (token === navToken) $("prompt").textContent = "⚠️ Impossible de charger les données : " + e.message;
      return;
    }
  }
  if (token !== navToken) return; // un clic plus récent a pris la main → on abandonne
  setContext(g.context);
  newRound();
}

const recentOf = () => (recent[gameKey] = recent[gameKey] || []);
const sessionOf = () => (session[gameKey] = session[gameKey] || { asked: 0, ok: 0 });

function newRound() {
  clearTimeout(advanceTimer);
  const g = games.GAMES.find((x) => x.key === gameKey);
  currentQ = g.build(candidates, state, recentOf());
  answered = false;
  renderStimulus(currentQ);
  renderOptions(currentQ);
  $("feedback").innerHTML = "";
  renderSession();
}

// --------------------------------------------------------------------------- //
function renderStimulus(q) {
  const stim = $("stim");
  const map = $("map");
  $("prompt").innerHTML = q.ask || (q.stimulus.kind === "text" ? q.stimulus.value : "");

  const useMap = q.stimulus.kind === "map" || q.interaction === "mapclick" || q.interaction === "rawclick";
  map.style.display = useMap ? "block" : "none";

  // mode d'affichage du stimulus → comportement de la zone (.stim) en hauteur
  const mode = useMap ? "mode-map" : q.stimulus.kind === "flag" ? "mode-flag" : "mode-text";
  const gameEl = $("game");
  gameEl.classList.remove("mode-map", "mode-flag", "mode-text");
  gameEl.classList.add(mode);

  let flag = $("flag-stim");
  if (q.stimulus.kind === "flag") {
    if (!flag) {
      flag = document.createElement("img");
      flag.id = "flag-stim";
      flag.className = "flag-stim";
      stim.appendChild(flag);
    }
    flag.src = data.flagUrl(q.stimulus.value.iso2, 320);
    flag.style.display = "block";
  } else if (flag) {
    flag.style.display = "none";
  }

  if (useMap) {
    mapMod.invalidate();
    mapMod.clearMarkers(); // efface marqueurs + lignes de correction de la manche précédente
    if (q.stimulus.kind === "map") {
      mapMod.highlight(q.stimulus.value); // monde : pays surligné
    } else if (mapContext === "world") {
      mapMod.focusIds(candidates.map((c) => c.iso3)); // place le pays
    } else {
      // France : on efface l'ancien surlignage et on recadre
      mapMod.resetBase();
      mapMod.fitAll();
    }
  }
}

function renderOptions(q) {
  const box = $("options");
  box.innerHTML = "";
  if (q.interaction !== "options") {
    box.hidden = true;
    return;
  }
  box.hidden = false;
  box.className = "options " + (q.optionKind === "flag" ? "flags" : "text");
  q.options.forEach((o) => {
    const b = document.createElement("button");
    b.dataset.id = o.id;
    if (q.optionKind === "flag") {
      b.className = "opt-flag";
      const img = document.createElement("img");
      img.src = data.flagUrl(o.country.iso2, 160);
      b.appendChild(img);
    } else {
      b.className = "opt";
      b.textContent = o.label;
    }
    b.onclick = () => answer(o.id);
    box.appendChild(b);
  });
}

// --------------------------------------------------------------------------- //
function onFeatureClick(id) {
  if (answered || !currentQ || currentQ.interaction !== "mapclick") return;
  answer(id);
}

function onRawClick(latlng) {
  if (answered || !currentQ || currentQ.interaction !== "rawclick") return;
  const c = currentQ.city;
  const d = haversine(latlng, c);
  const correct = d <= games.CITY_THRESHOLD_KM;
  grade(correct);
  mapMod.addMarker(c.lat, c.lng, "#2e7d32");
  if (correct) {
    mapMod.panTo(c.lat, c.lng, 6);
  } else {
    // montrer le clic ET la ville cherchée ensemble, même si on était zoomé loin
    mapMod.addMarker(latlng.lat, latlng.lng, "#e8453c");
    mapMod.fitPoints([{ lat: c.lat, lng: c.lng }, latlng]);
  }
  currentQ.explain = `${c.name} — ton clic était à ${Math.round(d)} km`;
  showFeedback(correct);
}

function answer(chosenId) {
  if (answered) return;
  const correct = chosenId === currentQ.correct;
  grade(correct);
  if (currentQ.interaction === "options") markOptions(chosenId);
  else mapMod.markResult(currentQ.correct, chosenId, correct);
  showFeedback(correct);
}

function grade(correct) {
  answered = true;
  store.record(state, currentQ.skill, currentQ.item, correct);
  const r = recentOf();
  r.push(currentQ.item);
  if (r.length > 8) r.splice(0, r.length - 8);
  const s = sessionOf();
  s.asked++;
  if (correct) s.ok++;
  renderSession();
}

function markOptions(chosenId) {
  document.querySelectorAll("#options [data-id]").forEach((b) => {
    b.disabled = true;
    if (b.dataset.id === currentQ.correct) b.classList.add("good");
    else if (b.dataset.id === chosenId) b.classList.add("bad");
  });
}

function labelFor(id) {
  if (currentQ.correctLabel && id === currentQ.correct) return currentQ.correctLabel;
  const o = (currentQ.options || []).find((o) => o.id === id);
  if (o) return o.label;
  const c = data.byIso3(id);
  return c ? c.name : id;
}

function showFeedback(correct) {
  const fb = $("feedback");
  const badge = correct
    ? `<span class="badge ok">✅ Bravo !</span>`
    : `<span class="badge ko">❌ Raté — <b>${labelFor(currentQ.correct)}</b></span>`;
  const pct = Math.round((store.getItem(state, currentQ.skill, currentQ.item).m || 0) * 100);
  const skillName = games.SKILLS[currentQ.skill] || games.FR_SKILLS[currentQ.skill] || games.US_SKILLS[currentQ.skill] || currentQ.skill;
  let sub = `Maîtrise « ${skillName} » : ${pct} %`;
  if (currentQ.explain) sub += ` · ${currentQ.explain}`;

  let reveal = "";
  if (currentQ.reveal && currentQ.reveal.kind === "flag") {
    const c = currentQ.reveal.value;
    reveal = `<img class="reveal-flag" src="${data.flagUrl(c.iso2, 160)}" alt=""><span class="reveal-name">${c.name}</span>`;
  }

  fb.innerHTML = `
    <div class="fb-row">${badge}</div>
    <div class="fb-sub">${reveal}${sub}</div>`;
  // enchaînement automatique ; Entrée ou un clic passe plus vite
  fb.onclick = newRound;
  const onMap = currentQ.stimulus.kind === "map" || currentQ.interaction === "mapclick" || currentQ.interaction === "rawclick";
  let delay = correct ? ADVANCE_OK : ADVANCE_KO;
  if (onMap && !correct) delay += 1000; // +1 s sur carte : le temps de situer l'erreur
  clearTimeout(advanceTimer);
  advanceTimer = setTimeout(newRound, delay);
}

function renderSession() {
  const s = sessionOf();
  $("session").textContent = s.asked ? `Session : ${s.ok}/${s.asked} bonnes réponses` : "";
}

function haversine(a, b) {
  const R = 6371;
  const rad = (x) => (x * Math.PI) / 180;
  const dLat = rad(b.lat - a.lat);
  const dLng = rad(b.lng - a.lng);
  const s = Math.sin(dLat / 2) ** 2 + Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(s));
}

// --------------------------------------------------------------------------- //
function selectDashboard() {
  $("game").hidden = true;
  $("dashboard").hidden = false;
  document.querySelectorAll(".nav-item").forEach((b) => b.classList.remove("active"));
  const cs = data.countries();
  const skills = Object.keys(games.SKILLS);
  const now = Date.now() / 1000;

  const all = [];
  cs.forEach((c) => skills.forEach((s) => all.push(store.getItem(state, s, c.iso3).m || 0)));
  const total = all.length;
  const overall = total ? all.reduce((a, b) => a + b, 0) / total : 0;
  const learned = all.filter((m) => m >= 0.8).length;
  const inProgress = all.filter((m) => m > 0 && m < 0.8).length;
  let due = 0;
  cs.forEach((c) =>
    skills.forEach((s) => {
      const it = store.getItem(state, s, c.iso3);
      if (it.seen && now >= it.due) due++;
    })
  );

  const bar = (label, frac) =>
    `<div class="row"><span>${label}</span><b>${Math.round(frac * 100)} %</b></div>
     <div class="track"><div class="fill" style="width:${Math.round(frac * 100)}%"></div></div>`;

  const skillBars = skills.map((s) => bar(games.SKILLS[s], mean(cs.map((c) => store.getItem(state, s, c.iso3).m || 0)))).join("");
  const regionBars = data.regions().map((r) => {
    const rc = data.countriesIn([r]);
    return bar(r, mean(rc.flatMap((c) => skills.map((s) => store.getItem(state, s, c.iso3).m || 0))));
  }).join("");

  const itemsSum = (skill) =>
    Object.keys(state.items)
      .filter((k) => k.startsWith(skill + ":"))
      .reduce((a, k) => a + (state.items[k].m || 0), 0);
  const placeBars = (sk, tot) =>
    Object.keys(sk).map((s) => bar(sk[s], tot[s] ? itemsSum(s) / tot[s] : 0)).join("");
  const frBars = placeBars(games.FR_SKILLS, games.FR_TOTALS);
  const usBars = placeBars(games.US_SKILLS, games.US_TOTAL);

  // libellés lisibles par item, pour le détail
  const frReg = {}, frDep = {}, usMap = {};
  if (data.france()) {
    data.france().reg.features.forEach((f) => (frReg[f.id] = f.properties.nom));
    data.france().dep.features.forEach((f) => (frDep[f.id] = f.properties.nom));
  }
  if (data.usa()) data.usa().features.forEach((f) => (usMap[f.id] = f.properties.nom));
  const itemLabel = (skill, id) => {
    if (skill === "fr_region") return frReg[id] || id;
    if (skill === "fr_dept") return frDep[id] || id;
    if (skill === "us_state") return usMap[id] || id;
    if (skill === "fr_city") return id;
    const c = data.byIso3(id);
    return c ? c.name : id;
  };

  // détail par connaissance : chaque item déjà rencontré, du plus faible au plus sûr
  const allSkills = { ...games.SKILLS, ...games.FR_SKILLS, ...games.US_SKILLS };
  const detail = Object.keys(allSkills).map((skill) => {
    const prefix = skill + ":";
    const rows = Object.keys(state.items)
      .filter((k) => k.startsWith(prefix))
      .map((k) => ({ label: itemLabel(skill, k.slice(prefix.length)), m: state.items[k].m || 0 }))
      .sort((a, b) => a.m - b.m);
    if (!rows.length) return "";
    const learnedN = rows.filter((r) => r.m >= 0.8).length;
    const chips = rows.map((r) => {
      const cls = r.m >= 0.8 ? "good" : r.m > 0.4 ? "mid" : "low";
      return `<span class="chip ${cls}">${r.label} · ${Math.round(r.m * 100)} %</span>`;
    }).join("");
    return `<details><summary>${allSkills[skill]} — ${learnedN}/${rows.length} acquis</summary><div class="chips">${chips}</div></details>`;
  }).join("");

  $("dashboard").innerHTML = `
    <h1>📊 Tableau de bord</h1>
    <p class="muted">Ton niveau mesure tes connaissances réelles — pas le score d'un quiz. Les questions ratées reviennent plus souvent.</p>
    <div class="metrics">
      <div class="metric"><div class="big">${Math.round(overall * 100)} %</div><div>Niveau global (monde)</div></div>
      <div class="metric"><div class="big">${learned} / ${total}</div><div>Connaissances acquises</div></div>
      <div class="metric"><div class="big">${inProgress}</div><div>En cours</div></div>
      <div class="metric"><div class="big">${due}</div><div>À revoir</div></div>
    </div>
    <div class="cols">
      <div><h3>Par compétence (monde)</h3>${skillBars}</div>
      <div><h3>Par région (monde)</h3>${regionBars}</div>
      <div><h3>🇫🇷 France</h3>${frBars}</div>
      <div><h3>🇺🇸 États-Unis</h3>${usBars}</div>
    </div>
    ${detail ? `<h3 style="margin-top:22px">Détail par connaissance</h3>
    <p class="muted">Ta maîtrise pour chaque item déjà rencontré (du plus faible au plus sûr).</p>
    <div class="detail">${detail}</div>` : ""}`;
}

function mean(arr) {
  return arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
}

document.addEventListener("keydown", (e) => {
  if ($("game").hidden) return;
  if (e.key === "Enter" && answered) newRound();
  else if (/^[1-9]$/.test(e.key) && !answered) {
    const btns = [...document.querySelectorAll("#options [data-id]")];
    const i = parseInt(e.key, 10) - 1;
    if (btns[i]) btns[i].click();
  }
});

init();
