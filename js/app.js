// Orchestrateur : navigation, filtre par zone, cycle de jeu, tableau de bord.
import * as data from "./data.js";
import * as store from "./store.js";
import * as games from "./games.js";
import * as mapMod from "./map.js";

const ZONES_KEY = "quiztrainer.zones.v1";

let state = store.load();
let gameKey = games.GAMES[0].key; // « Révision intelligente »
let candidates = [];
let selectedRegions = [];
const recent = {}; // gameKey -> [iso3]
const session = {}; // gameKey -> {asked, ok}
let currentQ = null;
let answered = false;

const $ = (id) => document.getElementById(id);

// --------------------------------------------------------------------------- //
async function init() {
  await data.load();
  mapMod.ensureMap("map");
  selectedRegions = loadZones();
  candidates = data.countriesIn(selectedRegions);
  buildSidebar();
  selectGame(gameKey);
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
    const id = "zone-" + r;
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
      if ($("dashboard").hidden) selectGame(gameKey);
      else selectDashboard();
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
function selectGame(key) {
  gameKey = key;
  $("dashboard").hidden = true;
  $("game").hidden = false;
  document.querySelectorAll(".nav-item").forEach((b) => b.classList.toggle("active", b.dataset.game === key));
  const g = games.GAMES.find((x) => x.key === key);
  $("g-title").textContent = g.title;
  $("g-sub").textContent = g.sub || "";
  newRound();
}

function recentOf() {
  return (recent[gameKey] = recent[gameKey] || []);
}
function sessionOf() {
  return (session[gameKey] = session[gameKey] || { asked: 0, ok: 0 });
}

function newRound() {
  if (!candidates.length) {
    $("prompt").textContent = "Coche au moins une région à gauche.";
    $("stim").querySelectorAll(":not(#map)").forEach((e) => e.remove());
    $("map").style.display = "none";
    $("options").innerHTML = "";
    $("feedback").innerHTML = "";
    return;
  }
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

  const useMap = q.stimulus.kind === "map" || q.interaction === "mapclick";
  map.style.display = useMap ? "block" : "none";

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
    if (q.stimulus.kind === "map") {
      mapMod.setClickHandler(null);
      mapMod.highlight(q.stimulus.value);
    } else {
      mapMod.setClickHandler(onMapClick);
      mapMod.focusZone(candidates.map((c) => c.iso3));
    }
  }
}

function renderOptions(q) {
  const box = $("options");
  box.innerHTML = "";
  if (q.interaction === "mapclick") {
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

function onMapClick(iso) {
  answer(iso);
}

// --------------------------------------------------------------------------- //
function answer(chosenId) {
  if (answered) return;
  answered = true;
  const correct = chosenId === currentQ.correct;
  store.record(state, currentQ.skill, currentQ.item, correct);

  const r = recentOf();
  r.push(currentQ.item);
  const cap = Math.max(1, Math.min(8, Math.floor(candidates.length / 3)));
  if (r.length > cap) r.splice(0, r.length - cap);

  const s = sessionOf();
  s.asked++;
  if (correct) s.ok++;

  markOptions(chosenId);
  if (currentQ.interaction === "mapclick") mapMod.markResult(currentQ.correct, chosenId);

  showFeedback(correct);
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
  let sub = `Maîtrise « ${games.SKILLS[currentQ.skill]} » : ${pct} %`;
  if (currentQ.explain) sub += ` · ${currentQ.explain}`;

  let revealHtml = "";
  if (currentQ.reveal && currentQ.reveal.kind === "flag") {
    const c = currentQ.reveal.value;
    revealHtml = `<img class="reveal-flag" src="${data.flagUrl(c.iso2, 160)}" alt=""><span class="reveal-name">${c.name}</span>`;
  }

  fb.innerHTML = `
    <div class="fb-row">${badge}<button id="next" class="next">Suivant ▶</button></div>
    <div class="fb-sub">${revealHtml}${sub}</div>`;
  $("next").onclick = newRound;
}

function renderSession() {
  const s = sessionOf();
  $("session").textContent = s.asked ? `Session : ${s.ok}/${s.asked} bonnes réponses` : "";
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

  const skillBars = skills
    .map((s) => bar(games.SKILLS[s], mean(cs.map((c) => store.getItem(state, s, c.iso3).m || 0))))
    .join("");
  const regionBars = data
    .regions()
    .map((r) => {
      const rc = data.countriesIn([r]);
      return bar(r, mean(rc.flatMap((c) => skills.map((s) => store.getItem(state, s, c.iso3).m || 0))));
    })
    .join("");

  $("dashboard").innerHTML = `
    <h1>📊 Tableau de bord</h1>
    <p class="muted">Ton niveau mesure tes connaissances réelles — pas le score d'un quiz.</p>
    <div class="metrics">
      <div class="metric"><div class="big">${Math.round(overall * 100)} %</div><div>Niveau global</div></div>
      <div class="metric"><div class="big">${learned} / ${total}</div><div>Connaissances acquises</div></div>
      <div class="metric"><div class="big">${inProgress}</div><div>En cours</div></div>
      <div class="metric"><div class="big">${due}</div><div>À revoir</div></div>
    </div>
    <div class="cols">
      <div><h3>Par compétence</h3>${skillBars}</div>
      <div><h3>Par région</h3>${regionBars}</div>
    </div>`;
}

function mean(arr) {
  return arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
}

// --------------------------------------------------------------------------- //
document.addEventListener("keydown", (e) => {
  if ($("game").hidden) return;
  if (e.key === "Enter" && answered) {
    newRound();
  } else if (/^[1-9]$/.test(e.key) && !answered) {
    const btns = [...document.querySelectorAll("#options [data-id]")];
    const i = parseInt(e.key, 10) - 1;
    if (btns[i]) btns[i].click();
  }
});

init();
