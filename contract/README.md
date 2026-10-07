# The machine contract of DR-LAB-SC-1.1

The normative text is `spec/DR-LAB-Semantic-Contract-1.1-(patched).md` (`DR-LAB-SC-1.1`). It is the source of truth:
where this folder disagrees with it, this folder is the defect. Everything here represents that text in a form a
program can check, and the server and screen 24 enforce it on every number they show. The operator accepted SC-1.1 as
the semantic target of this work on 2026-10-07; the record of that act, its scope and what it does not establish are in
`registry/00-editions.yaml` (the record preserves the act, it does not create it).

## What is where

```
schema/dr_lab_sc.yaml        the LinkML schema: every object of the contract as a class (passport fields as required
                             slots and rules, sc_ref = the clause it represents), the runtime records (ContractEnvelope,
                             StatisticalResultBundle, Estimate, SupportRecord, Claim ...) and the enums of the document
schema/linkml-lint.yaml      the project's lint configuration
registry/00-editions.yaml    editions (SC-1.0 previous, SC-1.1 accepted for this work, pinned by SHA-256), profiles, sources
registry/10-...yaml          observation sources, the clock, the DR/IDR rule, measurement frames and grids, knowledge cuts
registry/20-...yaml          case sets (base families, NOW sets), comparisons (M1-M3), outcomes (P0.1-P0.3), regions
registry/30-...yaml          trader questions, the 53 estimands (Q1-Q8 each) and their estimators
registry/40-claims.yaml      one explicit claim form per estimand (class, statement, the words next to its number on
                             each surface = labels, forbidden readings) and the fact forms (observed facts, no claim)
registry/50-validation.yaml  validation records (V3): walk-forward of NOW-1.0, E1 as a hypothesis, zone studies
registry/60-surfaces.yaml    every route of lab/server.py with its profile; the meaning of every number of the SC-1.1 routes
registry/70-obligations.yaml §14.4: every obligation with the mechanisms and exact checks that enforce it; the examples
                             K01-K33 (the document's own words) with the checks that execute them; coverage notes
tools/build.py               lint, closed-world validation of every registry file, references, semantic checks, products
build/                       the products (committed, never edited by hand): registry.json, runtime_spec.json,
                             page_registry.json, dr_lab_sc.schema.json - each stamped with the SHA-256 of its sources
requirements-linkml.txt      the LinkML environment (only for building and for the LinkML parts of the tests)
setup-linkml.ps1             creates .venv-linkml with those packages and checks the products
```

At run time nothing here needs LinkML. `lab/contract.py` (standard library) reads `build/`:

- **the gate** of the routes `/api/d24/family`, `/api/d24/now`, `/api/d24/day`: before a response leaves, the family
  snapshot is re-derived from the session base by the reference definitions (membership, paths, R / X, DR outcome,
  order, counts, identities), the zones by the reference zone-map-3, today's two axes (reachability, history clock),
  and every NOW number at its cut. What fails is withheld and named. Each published statistic becomes a bundle
  (derivation with its input versions, estimates, supports, and the claim of its registry form), published only if the
  claim's class is admissible for that evidence (`admissible_claims`: a base family admits C0, a named selection at a
  cut C1; no C2 and no C3 exist in this edition). A number of an SC-1.1 route that no field encoding declares makes the
  response a violation. The envelope is `body.contract`; the header `X-DR-Lab-Contract` marks every route
  (legacy routes: `status=OUTSIDE_SC11`);
- **fail closed**: if a source (schema, registry file, the document) differs from the stamps of the products, the
  contract is `CONTRACT_STALE` and the statistical routes publish nothing (the day's candles are still served);
- `GET /api/contract` serves the compiled registry and the runtime status; `POST /api/d24/verify` recomputes passports
  of the page by the reference definitions.

Screen 24 (`design/sozvezdiya-24/src`, built by its `build.py`, which embeds `build/page_registry.json`):

- every number is a passport of a registered estimand with its parameters, counts and N (`pp`, `bindPassport`); its
  claim form must be admissible on the family's case set; the value form decides bounds for unknown mass;
- the words next to a number are the registered labels of its claim form or of a fact form (`lbl`); the page writes
  none of them itself;
- the page compares its own counts with the bundles of the envelope (`envCounts`), refuses a family whose envelope is
  missing or comes from another registry (`regFault`), shows a NOW number only with its published bundle (`nowBundle`),
  and sends every passport to `POST /api/d24/verify` shortly after showing it (`verifyNow`);
- a violation withholds the number («—») and stands at the top of the panel (`scNotice`); it is never ignored.

## Changing the contract

1. Edit the schema or a registry file (a change of meaning needs a new version of the object, §14.1; the words of the
   screen are labels in `registry/40-claims.yaml`).
2. `.venv-linkml\Scripts\python.exe contract/tools/build.py` (set `PYTHONUTF8=1` in a cp1251 console). It refuses to
   build if the document's SHA-256 differs from the pinned edition: a changed contract text is reconciled with the
   schema by a person first.
3. `python design/sozvezdiya-24/src/build.py` - the page embeds the new registry; a page built with another registry
   refuses every family («Числа не публикуются: страница собрана с другим реестром контракта»).
4. The running server reloads `build/registry.json` by itself; a change of `lab/*.py` needs a restart (`AGENTS.md`).
5. `python -B tests/contract_sc11.py` and the page check `tests/ui_check24.js` (section 11 and the markers [K..]).

Between steps 1 and 2 the server answers `CONTRACT_STALE` and screen 24 shows no statistic. That is the contract
working, not a crash.

## Checks

- `tests/contract_sc11.py`: the products equal what the sources produce (`build.py --check`), the pins, the enforcement
  map names only existing checks, K01-K33 carry the document's words and each is executed (synthetic paths on the
  reference definitions and the working code; K05, K08, K26-K28, K30, K31 on the session base), coverage of every card,
  the enums against the document, every route declared and marked, no undeclared number, live envelopes valid for the
  runtime validator and for LinkML (in a temporary folder), the stale state, the page's contract layer.
- `tests/ui_check24.js` in the page: every passport bound to an estimand and a claim form, recomputed by the reference
  with no mismatch, no violation, binary shares with bounds (K16), a drawing change changes no count (K30), the NOW
  block in historical grammar (K33).

A green run proves these predicates. It does not prove the honesty of a history selection, the statistical meaning of
a target, a transfer to the future or an authority (§14.4): those stay with the validation records and the operator.

## Known limits of this edition

- The operator accepted SC-1.1 (2026-10-07) as the normative contract of the working profile DR Lab 24 — BASE-24 and
  NOW-1.0 — and of every further change of them; the legacy surfaces (/22/, the classic screen, the dashboard,
  /sem-v1/) stay outside it for now (`registry/00-editions.yaml`).
- C2 (`PredictiveClaim`), C3 (`DecisionClaim`), policies and authorities are defined by the schema and instantiated
  nowhere: no number of this tool admits a forecast or a decision (K28, K32, K33).
- The words of the NOW block are the operator's (2026-10-07, K33): «В истории: R позже углублялся… / Если
  углублялся…», symmetric for X.
