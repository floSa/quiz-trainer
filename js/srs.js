// Moteur de maîtrise — répétition espacée (port de l'ancien srs.py).
// Pur : aucune dépendance au DOM ni au stockage.

const MIN = 60;
const DAY = 86400;

// [seuil de maîtrise, délai avant réapparition (s)]
const INTERVALS = [
  [0.25, 45],          // presque inconnu  → revient tout de suite
  [0.45, 5 * MIN],     // fragile          → dans la session
  [0.65, DAY],         // en cours         → demain
  [0.80, 3 * DAY],
  [0.92, 7 * DAY],
  [1.01, 21 * DAY],    // solide           → trois semaines
];

export const GAIN = 0.30;     // part de l'écart vers 1 gagnée à la réussite
export const PENALTY = 0.35;  // maîtrise multipliée par ça à l'échec
export const LEARNED = 0.80;  // seuil « connaissance acquise »

export function newItem() {
  return { m: 0, reps: 0, lapses: 0, due: 0, seen: 0 };
}

export function interval(m) {
  for (const [threshold, secs] of INTERVALS) if (m < threshold) return secs;
  return INTERVALS[INTERVALS.length - 1][1];
}

export function review(item, correct, now = Date.now() / 1000) {
  let m = item.m || 0;
  let reps = item.reps || 0;
  let lapses = item.lapses || 0;
  if (correct) {
    m = m + GAIN * (1 - m);
    reps += 1;
  } else {
    m = m * PENALTY;
    lapses += 1;
  }
  return { m, reps, lapses, due: now + interval(m), seen: now };
}

export function weight(item, now = Date.now() / 1000) {
  const m = (item && item.m) || 0;
  let w = (1 - m) ** 2 + 0.05;
  if (item && item.seen && now >= (item.due || 0)) w *= 4; // en retard → priorité
  return w;
}

export function isLearned(item) {
  return ((item && item.m) || 0) >= LEARNED;
}
