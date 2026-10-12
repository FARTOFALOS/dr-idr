// Synthetic semantic examples, not market research or a production estimator.
// Run: node studies/semantic_paths_2026_10_10/check.mjs
import assert from 'node:assert/strict';

const bar = (t, o, l, h, c) => ({ t, o, l, h, c }); // t is M5 CLOSE; arbitrary integer price units
const touches = (b, K) => b !== null && b.l < K.hi && b.h >= K.lo;

function firstVisit(path, grid, K, from, through) {
  let missing = false;
  for (let j = 0; j < grid.length; j++) {
    if (grid[j] <= from || grid[j] > through) continue;
    const b = path[j];
    if (!b) { missing = true; continue; }
    if (touches(b, K)) return { visited: 'YES', firstKnown: !missing, t: missing ? null : grid[j] };
  }
  return { visited: missing ? 'UNKNOWN' : 'NO', firstKnown: false, t: null };
}

// A deliberately narrow, same-clock prefix matcher. Threshold is an example,
// not an adopted DR Lab matcher. No future field is read by this function.
function stateAt(path, grid, K, cut) {
  const end = grid.indexOf(cut);
  if (end < 0 || path.slice(0, end + 1).some(b => b === null)) return null;
  const p = path.slice(0, end + 1), b = p.at(-1);
  const hadVisit = p.some(x => touches(x, K));
  const phase = !hadVisit ? 'BEFORE' : b.c < K.lo ? 'BELOW' : b.c >= K.hi ? 'ABOVE_AFTER' : 'IN';
  const approach = p.length > 1 ? Math.sign(b.c - p.at(-2).c) : 0;
  return { close: b.c, phase, approach };
}
function membersNow(family, grid, K, cut, today, tolerance) {
  const a = stateAt(today, grid, K, cut);
  if (!a) return { status: 'UNKNOWN_PREFIX', ids: [] };
  return { status: 'OK', ids: family.filter(m => {
    const b = stateAt(m.path, grid, K, cut);
    return b && b.phase === a.phase && b.approach === a.approach && Math.abs(b.close - a.close) <= tolerance;
  }).map(m => m.id) };
}

// Which explicitly fixed boundary was reached FIRST AFTER the decision cut?
// Later motion cannot rewrite an already established first outcome.
function nextOutcome(path, grid, cut, H, D, U, closeAtCut) {
  assert(D < U);
  if (cut >= H) return 'NO_PERIOD';
  if (!(D < closeAtCut && closeAtCut < U)) return 'NOT_AT_RISK';
  let missing = false;
  for (let j = 0; j < grid.length; j++) {
    if (grid[j] <= cut || grid[j] > H) continue;
    const b = path[j];
    if (!b) { missing = true; continue; }
    const up = b.h >= U, down = b.l <= D;
    if (!up && !down) continue;
    if (missing) return 'UNKNOWN_PRIOR';
    // The open can establish first passage even when the candle spans both.
    if (b.o >= U) return 'UP_FIRST';
    if (b.o <= D) return 'DOWN_FIRST';
    if (up && down) return 'UNKNOWN_ORDER';
    return up ? 'UP_FIRST' : 'DOWN_FIRST';
  }
  return missing ? 'UNKNOWN_DATA' : 'NO_EVENT';
}

const grid = [5, 10, 15, 20, 25], K = { lo: 40, hi: 60 };
const common = [bar(5, 75, 70, 85, 75), bar(10, 75, 50, 80, 55)];
const family = [
  ...Array.from({ length: 12 }, (_, i) => ({ id: `up-${i}`, path: [...common,
    bar(15, 55, 50, 110, 105), bar(20, 105, -10, 108, 0), bar(25, 0, -20, 55, 45)] })),
  ...Array.from({ length: 5 }, (_, i) => ({ id: `through-${i}`, path: [...common,
    bar(15, 55, 0, 58, 10), bar(20, 10, 5, 110, 105), bar(25, 105, -20, 108, 0)] })),
  ...Array.from({ length: 3 }, (_, i) => ({ id: `away-${i}`, path: [
    bar(5, 75, 70, 85, 75), bar(10, 75, 70, 90, 80), bar(15, 80, 70, 110, 105),
    bar(20, 105, 80, 120, 110), bar(25, 110, 80, 115, 90)] })),
];
const arrivals = family.filter(m => firstVisit(m.path, grid, K, 5, 10).visited === 'YES');
assert.equal(arrivals.length, 17);
assert.equal(arrivals.filter(m => m.id.startsWith('through-')).length, 5);
const counts = { UP_FIRST: 0, DOWN_FIRST: 0 };
for (const m of arrivals) counts[nextOutcome(m.path, grid, 10, 25, 20, 100, m.path[1].c)]++;
assert.deepEqual(counts, { UP_FIRST: 12, DOWN_FIRST: 5 });
assert.equal(12 / 20, (17 / 20) * (12 / 17));
assert(family[0].path.at(-1).l < K.lo);
assert.equal(nextOutcome(family[0].path, grid, 10, 25, 20, 100, 55), 'UP_FIRST');

// Same close-by-time distributions can hide opposite within-session sequences.
const a = [[50, 110], [90, 0]], b = [[50, 0], [90, 110]];
for (let j = 0; j < 2; j++) assert.deepEqual(a.map(x => x[j]).sort(), b.map(x => x[j]).sort());
assert.equal(a.filter(x => x[0] === 50 && x[1] >= 100).length, 1);
assert.equal(b.filter(x => x[0] === 50 && x[1] >= 100).length, 0);

// Retrospective labels cannot influence current membership.
const before = membersNow(family, grid, K, 10, family[0].path, 10);
const mutated = family.map(m => ({ ...m, path: m.path.map((x, j) => j <= 1 ? x : bar(grid[j], 55, -999, 999, 0)) }));
assert.deepEqual(membersNow(mutated, grid, K, 10, family[0].path, 10), before);
assert.equal(before.ids.length, 17);
const later = membersNow(family, grid, K, 15, family[0].path, 10);
assert.equal(later.ids.length, 12);
assert.equal(family.length, 20);
assert.equal(arrivals.length, 17); // history not rewritten by today's new candle

const pathWith = (b15, b20 = bar(20, 55, 50, 60, 55)) => [...common, b15, b20, bar(25, 55, 50, 60, 55)];
assert.equal(nextOutcome(pathWith(bar(15, 55, 0, 110, 60)), grid, 10, 25, 20, 100, 55), 'UNKNOWN_ORDER');
assert.equal(nextOutcome(pathWith(bar(15, 105, 0, 110, 60)), grid, 10, 25, 20, 100, 55), 'UP_FIRST');
assert.equal(nextOutcome(pathWith(null, bar(20, 55, 50, 110, 105)), grid, 10, 25, 20, 100, 55), 'UNKNOWN_PRIOR');
assert.equal(nextOutcome(pathWith(bar(15, 55, 50, 110, 105), null), grid, 10, 25, 20, 100, 55), 'UP_FIRST');
assert.equal(nextOutcome(pathWith(bar(15, 55, 50, 60, 55)), grid, 10, 25, 20, 100, 55), 'NO_EVENT');
assert.equal(nextOutcome(family[0].path, grid, 25, 25, 20, 100, 45), 'NO_PERIOD');
assert.equal(nextOutcome(family[0].path, grid, 10, 25, 20, 100, 110), 'NOT_AT_RISK');
assert.equal(firstVisit([bar(5, 75, 70, 85, 75), bar(10, 30, 20, 35, 25)], [5, 10], K, 5, 10).visited, 'NO');
assert.equal(firstVisit([null, common[1]], [5, 10], K, 0, 10).firstKnown, false);
assert.equal(membersNow(family, grid, K, 10, [common[0], null], 10).status, 'UNKNOWN_PREFIX');

console.log(JSON.stringify({ synthetic: true, status: 'PASS', family: family.length,
  visitors: arrivals.length, after_contact: counts,
  visit_share: '17/20', upper_first_given_contact: '12/17', whole_chain: '12/20',
  current_members_at_contact: before.ids.length, current_members_after_new_bar: later.ids.length,
  boundaries_checked: ['later low preserves earlier outcome', 'no future membership leakage',
    'same-time marginals are not sequences', 'M5 ambiguity', 'gap open order',
    'missing data', 'no event vs no period', 'already beyond boundary', 'gap is not a visit'],
  note: 'Logical examples only; no market edge, calibration or UI acceptance established.' }, null, 2));
