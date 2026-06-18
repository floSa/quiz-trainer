// Persistance de la progression (mono-utilisateur) dans localStorage.
import * as srs from "./srs.js";

const KEY = "quiztrainer.progress.v1";

export function load() {
  try {
    const d = JSON.parse(localStorage.getItem(KEY));
    if (d && typeof d === "object" && !Array.isArray(d)) {
      d.items = d.items || {};
      return d;
    }
  } catch (e) {
    /* JSON corrompu → repart de zéro */
  }
  return { items: {} };
}

export function save(state) {
  localStorage.setItem(KEY, JSON.stringify(state));
}

export function itemKey(skill, iso3) {
  return `${skill}:${iso3}`;
}

export function getItem(state, skill, iso3) {
  return state.items[itemKey(skill, iso3)] || srs.newItem();
}

export function record(state, skill, iso3, correct, now) {
  const updated = srs.review(getItem(state, skill, iso3), correct, now);
  state.items[itemKey(skill, iso3)] = updated;
  save(state);
  return updated;
}

export function reset() {
  localStorage.removeItem(KEY);
}
