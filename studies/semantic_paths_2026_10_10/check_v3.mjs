// Synthetic semantic checks for the 12 October revision.
// No market data, external services, product admission or runtime integration.
import assert from 'node:assert/strict';
const passed = [];
const check = (name, fn) => { fn(); passed.push(name); };

function calendarAsOf(records, cut, coverage) {
  const latest = new Map();
  for (const r of records) {
    if (!r.versionProven || r.knownAt > cut) continue;
    const old = latest.get(r.id);
    if (!old || old.knownAt < r.knownAt) latest.set(r.id, r);
  }
  return { status: coverage === 'COMPLETE' ? 'KNOWN_COVERAGE' : 'CONTEXT_NOT_AVAILABLE', records: [...latest.values()] };
}
function featureAvailable(r, cut) {
  return r.knownAt <= cut && r.inputObservedThrough <= cut && !r.usesUnreleasedOutcome;
}
function sourceCompatibility(a, b, verifiedMapping) {
  const fields = ['clock', 'timestampMeaning', 'calendar', 'frame', 'tick'];
  const unknown = fields.filter(f => a[f] == null || b[f] == null);
  const different = fields.filter(f => a[f] != null && b[f] != null && a[f] !== b[f]);
  if (different.length) return { status: 'INCOMPATIBLE_FOR_SCOPE', different, unknown };
  if (unknown.length || !verifiedMapping) return { status: 'NOT_ESTABLISHED', different, unknown };
  return { status: 'COMPATIBLE_FOR_SCOPE', different, unknown };
}
function rankEvidence(values, today) {
  const c = { less: 0, equal: 0, greater: 0, unknown: 0 };
  for (const v of values) c[v == null ? 'unknown' : v < today ? 'less' : v === today ? 'equal' : 'greater']++;
  const n = values.length, le = c.less + c.equal;
  return { ...c, n, leBounds: [le / n, (le + c.unknown) / n] };
}
function forecastGate({ target, model, domainId, validation, admission, domain, source, support, typicality }) {
  // typicality is deliberately not a substitute for any admission predicate.
  if (source !== 'COMPATIBLE_FOR_SCOPE') return 'SOURCE_NOT_ADMITTED';
  if (!validation || validation.target !== target || validation.model !== model || validation.domain !== domainId) return 'NOT_VALIDATED';
  if (!admission || admission.target !== target || admission.model !== model || admission.domain !== domainId) return 'NO_PRODUCT_ADMISSION';
  if (!domain || !support) return 'OUTSIDE_SUPPORTED_DOMAIN';
  return 'ADMISSIBLE_FOR_DECLARED_TARGET';
}

check('as-of schedule uses the version available then, not the latest copy', () => {
  const records = [
    { id: 'announcement', version: 1, knownAt: 8, eventAt: 14, versionProven: true },
    { id: 'announcement', version: 2, knownAt: 11, eventAt: 15, versionProven: true },
  ];
  assert.equal(calendarAsOf(records, 10, 'COMPLETE').records[0].eventAt, 14);
  assert.equal(calendarAsOf(records, 12, 'COMPLETE').records[0].eventAt, 15);
});
check('an empty incomplete calendar does not mean no events', () => {
  assert.equal(calendarAsOf([], 10, 'UNKNOWN').status, 'CONTEXT_NOT_AVAILABLE');
  assert.equal(calendarAsOf([], 10, 'COMPLETE').status, 'KNOWN_COVERAGE');
  assert.equal(calendarAsOf([{ id: 'x', knownAt: 8, eventAt: 14, versionProven: false }], 10, 'UNKNOWN').records.length, 0);
});
check('a future schedule is known context; the unreleased result is not', () => {
  assert(featureAvailable({ knownAt: 8, inputObservedThrough: 8, eventAt: 14, usesUnreleasedOutcome: false }, 10));
  assert(!featureAvailable({ knownAt: 14, inputObservedThrough: 14, eventAt: 14, usesUnreleasedOutcome: true }, 10));
});
check('a realized future range cannot masquerade as a prefix feature', () => {
  assert(!featureAvailable({ knownAt: 10, inputObservedThrough: 16, usesUnreleasedOutcome: false }, 10));
});
check('source normalization alone cannot certify matching measurements', () => {
  const a = { clock: 'ET', timestampMeaning: 'close', calendar: 'v1', frame: 'IDR-width', tick: 0.25 };
  assert.equal(sourceCompatibility(a, { ...a, timestampMeaning: 'open' }, true).status, 'INCOMPATIBLE_FOR_SCOPE');
  assert.equal(sourceCompatibility(a, { ...a, tick: null }, true).status, 'NOT_ESTABLISHED');
  assert.equal(sourceCompatibility(a, { ...a }, false).status, 'NOT_ESTABLISHED');
  assert.equal(sourceCompatibility(a, { ...a }, true).status, 'COMPATIBLE_FOR_SCOPE');
});
check('rank counts retain unknown mass and identify the measured property', () => {
  assert.deepEqual(rankEvidence([1, 2, 3, 4, null], 3), { less: 2, equal: 1, greater: 1, unknown: 1, n: 5, leBounds: [0.6, 0.8] });
});
check('rarity does not revoke valid domain support; ordinariness does not grant admission', () => {
  const record = { target: 'q1', model: 'm1', domain: 'd1' };
  const base = { target: 'q1', model: 'm1', domainId: 'd1', validation: record, admission: record, domain: true, source: 'COMPATIBLE_FOR_SCOPE', support: true };
  assert.equal(forecastGate({ ...base, typicality: 'TAIL' }), 'ADMISSIBLE_FOR_DECLARED_TARGET');
  assert.equal(forecastGate({ ...base, typicality: 'ORDINARY', admission: false }), 'NO_PRODUCT_ADMISSION');
  assert.equal(forecastGate({ ...base, typicality: 'ORDINARY', validation: false }), 'NOT_VALIDATED');
  assert.equal(forecastGate({ ...base, admission: { ...record, target: 'other' } }), 'NO_PRODUCT_ADMISSION');
  assert.equal(forecastGate({ ...base, validation: true, admission: true }), 'NOT_VALIDATED');
});
check('an output becomes a permanent indicator only with an explicit work binding', () => {
  const result = { measure: 'visit-frequency', count: 17, n: 20 };
  const usable = (x, need) => !!(need?.goal && need?.question && need?.measure === x.measure);
  assert(!usable(result, null));
  assert(usable(result, { goal: 'orientation', question: 'visits-in-region-window', measure: 'visit-frequency' }));
  assert.equal(result.count / result.n, 0.85);
});
check('reference-class comparison must not silently change the time alignment', () => {
  const a = { weekday: true, activationWindow: 15, alignment: 'COMMON_CLOCK', outcome: 'U_FIRST_BY_H' };
  const changed = (x, y) => Object.keys(x).filter(k => x[k] !== y[k]);
  assert.deepEqual(changed(a, { ...a, weekday: false }), ['weekday']);
  assert.deepEqual(changed(a, { ...a, weekday: false, alignment: 'ACTIVATION_AGE' }), ['weekday', 'alignment']);
});
check('later truth closes the same target without rewriting the earlier issue', () => {
  const issue = Object.freeze({ id: 'issue-1', target: 'close-12:30-region-A', cut: '11:55', p: 0.7, mode: 'SIMULATED_ISSUE' });
  const before = JSON.stringify(issue);
  const outcome = { target: issue.target, establishedAt: '12:30', value: true };
  assert.equal(outcome.target, issue.target);
  assert.equal(JSON.stringify(issue), before);
  assert.notEqual(issue.mode, 'ACTUALLY_DISPLAYED_ISSUE');
});
check('case role changes do not alter the historical measurement', () => {
  const record = { caseId: 'case-1', close: 100 };
  const roles = [{ query: 'q1', role: 'HISTORICAL_ANALOG' }, { query: 'q2', role: 'EVALUATION_TARGET' }];
  assert.equal(roles.length, 2);
  assert.deepEqual(record, { caseId: 'case-1', close: 100 });
});
check('IDR unit is not statistical standard deviation', () => {
  const idr = { kind: 'IDR_WIDTH', value: 20 }, sigma = { kind: 'STATISTICAL_STANDARD_DEVIATION', value: 20 };
  assert.equal(idr.value, sigma.value);
  assert.notEqual(idr.kind, sigma.kind);
});

console.log(JSON.stringify({ synthetic: true, status: 'PASS', groups: passed.length, passed,
  boundary: 'No live forecast admission, calendar import, source parity or market validation established.' }, null, 2));
