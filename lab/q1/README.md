# Q1 pilot — the historical answer «дойдёт ли отсюда до места» (Q1-PILOT-0.2, C1)

An isolated, reproducible historical pilot. A trader picks a historical session, a closed M5 cut and one place L, gets
the historical answer about reaching L before the block end, inspects the sessions behind it, saves the answer as an
immutable issue, reopens and reproduces it, and attaches its later outcome as a separate record.

Scope and meaning come from the frozen handoff (PR #5, commit `3dac913`):
[Q1-PILOT-0.2](../../meaning/lens/2026-10-12-independent-srs/03-q1-historical-pilot.md) (mandatory scope),
[roadmap](../../meaning/lens/2026-10-12-independent-srs/04-engineer-roadmap.md) (sequence and acceptance),
[KADR-1.1 ed. 2](../../meaning/lens/2026-10-12-kurator/02-specifikaciya.md) §§3-5 (definitions),
[SRS 0.2](../../meaning/lens/2026-10-12-independent-srs/02-srs.md) (direction). AGENTS.md and DR-LAB-SC-1.1 govern.

**What it is not.** Not a profile of the accepted SC-1.1 gate (every response says
`X-DR-Lab-Contract: profile=Q1-PILOT-0.2; claim=C1; status=PILOT_OUTSIDE_SC11_GATE`); not a forecast (C1 = the history
of a named set); not a change of the working DR Lab — its server (8767), routes, registry, screen 24, BASE-24 / NOW-1.0
numbers, settings and shortcuts are untouched. GEO is a named research candidate, not a default; D1, D2, N5 and PR #2
stay the operator's.

**On screen 24 (branch `ekran-24-otsyuda`, operator 2026-10-12).** The same engine answers the block «Отсюда до места»
of screen 24 (`lab/arrive24.py`, profile ARRIVE-24 of SC-1.1 §12.6) on the family on screen — «день недели» = the
weekday family (`NODEPOS_WD`), «все дни» = the key without the weekday (`NODEPOS_ALL`); `tests/arrive24.py` checks the
identity with `Table.attempt`. This page stays the diagnostic stand: issues, outcomes, reproduction, the sessions behind an
answer, the comparison of sets and GEO live here, not on the screen.

## Open it

Double-click the desktop shortcut **«DR Lab Q1 (пилот)»** (→ `start-q1-pilot.cmd`): it starts the pilot's own server on
`http://127.0.0.1:8771/` (hidden; logs in `lab/.q1-pilot/`) and opens the page. `stop-q1-pilot.cmd` stops it (port 8771
only). A scene can be opened by its address, e.g. `http://127.0.0.1:8771/#inst=NQ&block=RDR&date=2025-12-17&cut=7&level=-1%2F2`.

On the page: instrument, session, date (only days whose session has an established confirmation), cut (closes after the
confirmation), place (0 / −0,5 / −0,7); then choose the comparison set (none is preselected). The chart shows the
session up to the cut only; its later candles appear only after «Показать исход» on a saved answer.

## Pieces

| File | What it does |
|---|---|
| `engine.py` | The question: the target's state from its own prefix (its later rows are cut off before anything is computed), the three named parents, the selection (eligible at the common clock cut — the B0 rule of `lab/now24.py::series` —, not yet at L, `now24._near` within 1/4), YES / NO / UNKNOWN, the counters, the publication rule (no number below n 20), the input digest (the target's prefix + every session of the block before its date), the second implementation from raw rows, the outcome of the target's own future |
| `store.py` | Issues and outcomes written once (exclusive create; same id + same payload = idempotent, different payload = refused), outcomes as separate files linked by the issue's payload hash, read-only files, `verify()` |
| `passport.py` | What the pilot claims and in which words (the page writes none of its own) |
| `server.py`, `web/` | The isolated review scene |
| `recon.py` | Reconciliation with the original A/D procedure, case by case |
| `demo.py` | The acceptance walk-through on a real scene in a fresh store |
| `../../tests/q1_pilot.py` | The contract's discriminating examples (synthetic) and the storage invariants |

Runtime records (issues, outcomes, reconciliation output, logs) live in `lab/.q1-pilot/` — case-level, local, git-ignored.
In a git worktree the base is read from the main checkout's `lab/.runtime` by path (read only); `DR_IDR_RUNTIME`
overrides it.

## Architecture choices (and why)

1. **One issue per attempt on an open target**, whatever its publication: a number, «мало сессий» (n < 20), or «исход
   неизвестен у всех». The method's coverage is then counted over stored attempts, not over convenient answers. A
   resolved target (L already reached today), a hole in today's prefix, a broken DR, no prefix yet or the block's end
   are facts of today's prefix: shown with their reason, never issued, not in the coverage denominator.
2. **The input digest covers exactly what an attempt may read**: the target's prefix (its box without the later DR
   break, its M5 up to the cut) and every session of the block before the target date. A rewritten future of the
   target therefore leaves the issue byte-identical, its id included; a rewritten future of an analogue changes the
   input snapshot, so a recomputation is another issue (tested synthetically and on the real base, `demo.py` step 5).
   A digest of the whole base file would have let the target's own future into the issue's identity.
3. **An outcome resolves one issue**, after checking the invariant that makes the target's event the same for every
   open cut: same target, same prefix digest, L not reached and no M5 missing up to the cut. The observation (label,
   first reach, missing M5) is the target's; the link is per issue, with that issue's payload hash. A changed basis is a
   new revision that supersedes the last; the issue never changes.
4. **Two implementations, honestly named**: the vectorised selection (reused primitives of NOW-1.0) and a scalar
   re-derivation from the raw rows. Their agreement proves arithmetic and membership under the same definitions — not
   that the definitions answer the trader's question; that is what the contract's examples in `tests/q1_pilot.py` (each
   expected value written from Q1's text) and the operator's reading are for. A disagreement withholds the number
   (`REFERENCE_MISMATCH`).
5. **One answer, three ways to choose history**: the page answers for the set the operator picks; «Сравнить наборы»
   shows the same question over the other sets, with their own denominators. The question, cut, place, horizon and
   today's state are shared; the set, its counters, members, share and issue are not.
6. **The page cannot see the future**: `/api/q1/scene` returns candles up to the cut; the later candles come only from
   `/api/q1/outcome`, and only once an outcome is on record. A late answer of an earlier scene is dropped.
7. **Dropped on purpose**: a hash-chained journal (it would detect, not prevent, and the Q1 invariants hold without it;
   outcome links carry the issue hash instead), automatic issuing of every viewed answer, time distributions.

## Repeat the acceptance

```bash
python -B tests/q1_pilot.py          # contract examples + storage invariants (offline, synthetic)
python -B lab/q1/recon.py --golden   # A/D: the original functions re-run, then case-by-case comparison (~10 min)
python -B lab/q1/demo.py             # the end-to-end walk-through on a real scene in a fresh store
```

The evidence of the last runs and what they do and do not establish: `studies/q1_pilot_2026_10_12/README.md`.
