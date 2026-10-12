// Counterexamples for the 10 October essay/engineering handoff.
// Synthetic records only. Not a production engine or an independent market test.
import assert from 'node:assert/strict';

const passed = [];
function check(name, f) { f(); passed.push(name); }
const K = { lo: 40, hi: 60 }, D = 20, U = 100;
const B = (t, o, l, h, c) => ({ t, o, l, h, c }); // t = M5 close
const overlap = b => b.l < K.hi && b.h >= K.lo;
const gapOver = (previousClose, b) => (previousClose < K.lo && b.o >= K.hi) || (previousClose >= K.hi && b.o < K.lo);
const risk = b => D < b.c && b.c < U;

// Five adverse moves now happen ON the contact M5, unlike the previous example.
const cases = [
  ...Array.from({ length: 12 }, (_, i) => ({ id: `remaining-${i}`, contact: B(10, 75, 50, 80, 55), next: B(15, 55, 50, 110, 105) })),
  ...Array.from({ length: 5 }, (_, i) => ({ id: `fast-through-${i}`, contact: B(10, 75, 0, 80, 10), next: B(15, 10, 0, 110, 105) })),
  ...Array.from({ length: 3 }, (_, i) => ({ id: `no-contact-${i}`, contact: B(10, 75, 70, 90, 80), next: B(15, 80, 70, 110, 105) })),
];
const visitors = cases.filter(c => overlap(c.contact));
const closeLedger = {
  inside: visitors.filter(c => risk(c.contact)),
  below: visitors.filter(c => c.contact.c <= D),
  above: visitors.filter(c => c.contact.c >= U),
};
check('fast-through cases remain visible in the contact ledger', () => {
  assert.equal(cases.length, 20);
  assert.equal(visitors.length, 17);
  assert.equal(closeLedger.below.length, 5);
  assert.equal(closeLedger.inside.length, 12);
  assert.equal(closeLedger.above.length, 0);
  assert.equal(closeLedger.inside.length + closeLedger.below.length + closeLedger.above.length, visitors.length);
  assert.deepEqual([...closeLedger.inside, ...closeLedger.below, ...closeLedger.above].map(c => c.id).sort(), visitors.map(c => c.id).sort());
});
check('the residual 12/12 is not a 17-case contact result', () => {
  const upperAfterClose = closeLedger.inside.filter(c => c.next.h >= U && c.next.l > D).length;
  assert.equal(upperAfterClose, 12);
  assert.equal(upperAfterClose / closeLedger.inside.length, 1);
  assert.notEqual(upperAfterClose / visitors.length, 1);
  assert.equal(closeLedger.below.length / visitors.length, 5 / 17);
});
function contactAnchorStatus(b) {
  return b.h >= U || b.l <= D ? 'ANCHOR_INTERVAL_UNRESOLVED' : 'NO_BOUNDARY_IN_CONTACT_BAR';
}
check('contact-bar facts do not manufacture a physical-contact anchor', () => {
  assert.equal(contactAnchorStatus(closeLedger.below[0].contact), 'ANCHOR_INTERVAL_UNRESOLVED');
  assert(closeLedger.below[0].contact.l <= D);
  assert.equal(contactAnchorStatus(B(10, 75, 0, 110, 55)), 'ANCHOR_INTERVAL_UNRESOLVED');
  assert.equal(contactAnchorStatus(closeLedger.inside[0].contact), 'NO_BOUNDARY_IN_CONTACT_BAR');
});
check('gap, range overlap and boundary overshoot are different predicates', () => {
  const skipped = B(10, 30, 20, 35, 25);
  assert(gapOver(75, skipped));
  assert(!overlap(skipped));
  const overshotU = B(15, 110, 105, 120, 115);
  assert(overshotU.h >= U);
  assert(!(overshotU.l <= U && U <= overshotU.h));
  const gapThenReturn = B(10, 30, 20, 80, 70);
  assert(gapOver(75, gapThenReturn) && overlap(gapThenReturn));
});

// Deliberately narrow M5 episode rule: a full disjoint M5 rearms the next episode.
function episodes(bars, activationClose) {
  let active = false, ordinal = 0, ordinalKnown = true;
  const out = [];
  for (const b of bars) {
    if (!b) { ordinalKnown = false; active = false; continue; }
    if (b.t <= activationClose) continue;
    if (!overlap(b)) { active = false; continue; }
    if (!active) { ordinal++; out.push({ t: b.t, ordinal: ordinalKnown ? ordinal : null }); }
    active = true;
  }
  return out;
}
const repeatPath = [B(5, 75, 70, 85, 75), B(10, 75, 45, 80, 55), B(15, 70, 65, 90, 75), B(20, 75, 45, 80, 55)];
check('first after activation is not first in a later window', () => {
  const e = episodes(repeatPath, 0);
  assert.deepEqual(e.map(x => x.ordinal), [1, 2]);
  assert.equal(e[0].t, 10);
  assert.equal(e.find(x => x.t > 15 && x.t <= 25).ordinal, 2);
});
check('activation candle and pre-activation contacts are excluded from post-activation search', () => {
  assert.deepEqual(episodes([B(5, 75, 45, 80, 55), B(10, 75, 45, 80, 75), B(15, 75, 45, 80, 55)], 10), [{ t: 15, ordinal: 1 }]);
  assert.deepEqual(episodes(repeatPath, 20), []);
});
check('missing intervals do not preserve a fabricated episode ordinal', () => {
  assert.equal(episodes([repeatPath[0], null, repeatPath[3]], 0)[0].ordinal, null);
});

check('equal first-event classes retain different event times and ages', () => {
  const results = [{ type: 'U_FIRST', close: 15, anchor: 10 }, { type: 'U_FIRST', close: 250, anchor: 10 }];
  assert.equal(new Set(results.map(x => x.type)).size, 1);
  assert.deepEqual(results.map(x => [x.close - 5 - x.anchor, x.close - x.anchor]), [[0, 5], [235, 240]]);
  const joint = new Map(results.map(x => [`${x.type}@${x.close}`, 1]));
  assert.equal(joint.size, 2);
  assert.equal(720 - 645, 75);
  assert.equal(720 - 715, 5); // same market clock, different age
});

function updateType(oldIssue, newIssue) {
  if (oldIssue.target !== newIssue.target) return 'RETARGET';
  if (oldIssue.model !== newIssue.model) return 'REMODEL';
  if (oldIssue.data !== newIssue.data) return 'DATA_REVISION';
  if (newIssue.resolved) return 'RESOLVED';
  return 'OBSERVATION_UPDATE';
}
check('a new cut is not necessarily an update of the same target', () => {
  const a = { target: 'A=10,U=100,D=20,H=100', cut: 10, model: 'm1', data: 'd1' };
  assert.equal(updateType(a, { ...a, cut: 15 }), 'OBSERVATION_UPDATE');
  assert.equal(updateType(a, { ...a, cut: 15, target: 'A=15,U=100,D=20,H=100' }), 'RETARGET');
  assert.equal(updateType(a, { ...a, model: 'm2' }), 'REMODEL');
  assert.equal(updateType(a, { ...a, data: 'd2' }), 'DATA_REVISION');
  assert.equal(updateType(a, { ...a, resolved: true }), 'RESOLVED');
});

check('unknown observations are not an additional physical market class', () => {
  const possibilities = [
    ...Array.from({ length: 6 }, () => new Set(['U'])),
    ...Array.from({ length: 8 }, () => new Set(['D'])),
    ...Array.from({ length: 4 }, () => new Set(['NONE'])),
    new Set(['U', 'D']), new Set(['U', 'D']),
  ];
  const bound = y => ({ lower: possibilities.filter(s => s.size === 1 && s.has(y)).length / 20,
    upper: possibilities.filter(s => s.has(y)).length / 20 });
  assert.deepEqual(bound('U'), { lower: 0.3, upper: 0.4 });
  assert.deepEqual(bound('D'), { lower: 0.4, upper: 0.5 });
  assert.deepEqual(bound('NONE'), { lower: 0.2, upper: 0.2 });
  assert.equal(possibilities.filter(s => s.size > 1).length, 2);
  assert(!possibilities.some(s => s.has('UNKNOWN')));
});

console.log(JSON.stringify({ synthetic: true, status: 'PASS', groups: passed.length,
  contactLedger: { family: cases.length, visitors: visitors.length, alreadyBelowDAtContactClose: closeLedger.below.length,
    remainingAtRisk: closeLedger.inside.length }, passed,
  boundary: 'Semantic counterexamples only; not full implementation, market validation or UI acceptance.' }, null, 2));
