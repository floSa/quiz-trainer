// Tests du moteur de maîtrise (srs.js), pur et déterministe (param `now`).
// Lancer :  node tests/run.mjs   (ou : npm test)
import * as srs from "../js/srs.js";

let failures = 0;
const approx = (a, b, eps = 1e-9) => Math.abs(a - b) < eps;
function ok(cond, msg) {
  if (cond) {
    console.log("  ok  -", msg);
  } else {
    console.error("  FAIL-", msg);
    failures++;
  }
}

// --- newItem ---
const fresh = srs.newItem();
ok(fresh.m === 0 && fresh.reps === 0 && fresh.lapses === 0, "newItem démarre à zéro");

// --- review : bonne réponse ---
const r1 = srs.review({ m: 0, reps: 0, lapses: 0 }, true, 1000);
ok(approx(r1.m, srs.GAIN), "bonne réponse depuis 0 → m = GAIN");
ok(r1.reps === 1 && r1.lapses === 0, "bonne réponse → reps++");
ok(r1.due === 1000 + srs.interval(r1.m), "due = now + interval(m)");
ok(r1.seen === 1000, "seen = now");

// --- review : mauvaise réponse ---
const r2 = srs.review({ m: 0.8, reps: 5, lapses: 0 }, false, 2000);
ok(approx(r2.m, 0.8 * srs.PENALTY), "mauvaise réponse → m × PENALTY");
ok(r2.lapses === 1, "mauvaise réponse → lapses++");

// --- convergence : plusieurs bonnes réponses → acquis, sans dépasser 1 ---
let it = { m: 0, reps: 0, lapses: 0 };
for (let i = 0; i < 10; i++) it = srs.review(it, true, 0);
ok(it.m > srs.LEARNED, "10 bonnes réponses → acquis (> LEARNED)");
ok(it.m < 1, "la maîtrise reste sous 1");

// --- interval : croissant avec la maîtrise ---
let prev = -1, mono = true;
for (let m = 0; m <= 1.0001; m += 0.05) {
  const v = srs.interval(m);
  if (v < prev) mono = false;
  prev = v;
}
ok(mono, "interval est non décroissant avec m");

// --- weight : plus faible = plus prioritaire ; en retard = ×4 ---
ok(srs.weight({ m: 0.1 }, 0) > srs.weight({ m: 0.9 }, 0), "poids plus fort pour une maîtrise faible");
const notDue = srs.weight({ m: 0.5 }, 0);
const overdue = srs.weight({ m: 0.5, seen: 1, due: 100 }, 200);
ok(approx(overdue, notDue * 4), "en retard → poids ×4");

// --- isLearned : seuil ---
ok(!srs.isLearned({ m: 0.79 }) && srs.isLearned({ m: 0.8 }), "isLearned au seuil LEARNED");

console.log("");
if (failures) {
  console.error(`${failures} test(s) en échec`);
  process.exit(1);
}
console.log("Tous les tests srs OK");
