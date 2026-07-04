// Réglages globaux (persistés en localStorage). Pour l'instant : la difficulté,
// qui s'applique à TOUS les quiz (un seul sélecteur, dans la barre latérale).
const KEY = "quiztrainer.difficulty.v1";
const LEVELS = ["facile", "normal", "difficile"];

let _difficulty = null;

export function difficulty() {
  if (_difficulty === null) {
    const v = localStorage.getItem(KEY);
    _difficulty = LEVELS.includes(v) ? v : "normal";
  }
  return _difficulty;
}

export function setDifficulty(v) {
  if (!LEVELS.includes(v)) return;
  _difficulty = v;
  localStorage.setItem(KEY, v);
}

export const DIFFICULTY_LEVELS = [
  { key: "facile", label: "🟢 Facile" },
  { key: "normal", label: "🟡 Normal" },
  { key: "difficile", label: "🔴 Difficile" },
];
