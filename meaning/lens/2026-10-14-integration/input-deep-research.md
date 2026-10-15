# DR Lab: Independent Reconstruction of Meaning, Evidence, and a Unified Trader Interface

## Executive conclusion

**What DR Lab is actually building.** DR Lab is not, and should not become, an ontology browser, a probability oracle, or a machine trading system. Its defensible product is narrower and more valuable: **a live price-time workspace in which the trader can see what has happened in the current DR/IDR session, ask a concrete question from the current closed-M5 state, and inspect what happened historically after states defined without using unavailable future information.** The repository itself already states the essential boundary: historical frequencies are descriptions of selected historical cases, not forecasts, and the formal claim layer contains no admitted C2 predictive or C3 action-authority claim. fileciteturn25file0 fileciteturn40file0

The independent diagnosis is that **the main missing link is no longer “more ontology.”** By October 14, 2026, DR Lab already has an unusually substantial semantic substrate: SC-1.1, a LinkML-backed registry, estimands with explicit case sets and denominators, claim forms with forbidden readings, a fail-closed publication gate, Semantic Trace, and FOM-1.2 impact/term/facet/presentation checks. FOM itself explicitly preserved the calculations, contract, and working UI and extended the existing trace rather than introducing RDF/OWL/PROV infrastructure. fileciteturn41file0 fileciteturn26file0 fileciteturn32file0

The remaining product problem is primarily the **transition from correct historical knowledge to one stable human interaction**:

> **price now → explicit question → exact historical reference set → outcome/support → admissible historical statement → visible relation to price and time**

The repository’s own applied-work study reached essentially the same diagnosis from a different direction: after DR confirmation, the operator’s confirmed questions largely already had measurements; what was missing was access, composition, and perceptual coherence. Answers were scattered across the summary, family windows, another mode, and hover interactions, while the operator’s principal DR Lab decision was described as “where to expect the pullback.” Before confirmation there was a genuine knowledge gap because the confirmed-family object did not yet exist. fileciteturn33file0

There is, however, a second and more serious issue: **the historical matching rule is not automatically justified merely because it is semantically clean.** The Q1 comparability study directly falsifies one attractive architectural assumption: that the same frozen “family” is necessarily the best conditioning population for every trader question. For Q1, the weekday-conditioned matcher was worse than a simple distance-to-target × remaining-time reference and answered far fewer cases; a less restrictive matcher improved modestly, while a large part of GEO’s apparent advantage disappeared when support size was equalized. fileciteturn29file0 This means the canonical architecture should preserve family identity but **must not make “family membership” synonymous with “best comparison population.”**

My recommended product architecture is therefore:

**Keep the accepted market semantics and contract; keep Semantic Trace; retain FOM only as derived semantic tooling; make questions and their eligible historical subsets first-class; and build one price-time interface with a question-anchored answer rail plus an on-demand historical-detail tray.**

That implies several selective reversals of accumulated work:

| Existing idea | Verdict | Reason |
|---|---|---|
| SC-1.1 + machine registry + fail-closed claims | **Keep** | This is the strongest part of the system: explicit estimands, denominators, claim classes, forbidden readings, machine checking. fileciteturn26file0 fileciteturn40file0 |
| Frozen BASE family identity | **Keep** | It is a legitimate historical object and protects denominator identity; it should not mutate as today evolves. fileciteturn41file0 |
| “One family answers every question” | **Reject** | Q1 provides direct contrary evidence. fileciteturn29file0 |
| Semantic Trace | **Keep and integrate** | It closes real provenance/future-leakage/presentation gaps without changing numbers. fileciteturn36file0 |
| FOM-1.2 | **Keep, but demote from product architecture to derived verification/query tooling** | Its ten facets and impact graph are useful for audit; they mix domain, epistemic, computational, and presentation properties and should not become the user-facing ontology. fileciteturn37file0 |
| Q1 pilot’s immutable releases and UNKNOWN handling | **Keep** | These solve real evidence-integrity problems independently of the pilot UI. fileciteturn22file0 |
| Separate Q1 user interface | **Do not ship** | The operator asked for one working interface; the pilot is valuable as a diagnostic harness. fileciteturn22file0 fileciteturn23file0 |
| ARRIVE “Отсюда” presentation | **Reuse calculation, redesign presentation and matching policy** | Useful question, but its default conditioning rule is challenged by later research. fileciteturn23file0 fileciteturn29file0 |
| Family Path | **Keep as selected-question detail** | It directly connects a historical answer to actual M5 trajectories, but should not become another competing top-level screen. fileciteturn39file0 |
| Constellations/clusters | **Keep as secondary distribution view** | They genuinely convey joint price-time distributions of final historical outcomes; they are not a substitute for the current question’s answer. fileciteturn25file0 |
| New RDF/OWL knowledge stack | **Reject for now** | The current LinkML/trace architecture already supplies the needed closed-world product checks; OWL/SHACL would add value mainly if cross-system RDF inference/interoperability became an actual requirement. citeturn9search1turn9search2turn8search0turn7search0 |

**Important evidence boundary.** I independently inspected repository/branch/PR metadata, source documents, schemas, registries, studies, commit ancestry, and implementation descriptions. I did **not** have the local G3 market tape, `lab/.runtime` databases, preserved live TradingView state, or a running operator screen in this research environment. Therefore, reported “ALL GOOD,” reconciliation counts, browser checks, screenshots, and market-derived figures below are identified as **branch-reported results**, not experiments I reran. The repository itself notes that market data are deliberately absent from these branches and that several studies require local G3/runtime state to reproduce. fileciteturn18file0 fileciteturn20file0 fileciteturn22file0

As of this inspection, `main` is still exactly `2672841da928f7379e5d7bc27eef8ff3e0fa5738`; none of the research below implies authorization to modify it. fileciteturn42file0

## Reconstructed system and canonical semantic model

The repository already contains three different ontologies. A major source of architectural drift has been treating them as though one structure should simultaneously represent all three.

**The market ontology** describes what exists or happens in the DR/IDR domain. The strategy and semantics distinguish M5 observations; the DR wick range; the IDR body range; DR confirmation by a closed M5 outside DR; a subsequent DR break; a directed IDR-width coordinate; and final retracement/extension outcomes measured over a historical session horizon. A historical final R or X is therefore an outcome of a completed historical horizon; today’s current low/high or already-seen retracement is an observation available at the present cut, not the same object. fileciteturn24file0 fileciteturn25file0

**The computational/epistemic ontology** describes how DR Lab is allowed to know something: observation cut, information availability, historical case-set definition, outcome, denominator, estimator, unknown cases, claim class, provenance, release, and validation. The existing registry already encodes important identity rules that are easy to lose in UI code: R and X are different estimands, and changing a horizon creates a different estimand rather than a cosmetic variant. fileciteturn26file0

**The human-work ontology** describes what the trader is trying to do: inspect the current session, choose or notice a place, ask whether a pullback/continuation/arrival remains historically plausible, inspect the historical trajectories behind an answer, replay an old cut, pin a question, and return to live operation. These are neither market entities nor computational entities. The repository’s trader-work study explicitly separates DR Lab from the operator’s TradingView work: entries, stops, rejects and imbalances remain elsewhere, while DR Lab is used across the session to understand historical behavior and, especially, where a retracement might be expected. fileciteturn33file0

### The minimal canonical model

The economical model I recommend is not a replacement ontology framework. It is a clarification of identities already mostly present in SC-1.1/Semantic Trace.

| Canonical object | Identity and role |
|---|---|
| **Observation** | A market datum plus its market/event time and the time at which it is admissible to the system. Closed M5 observations control confirmed state; the currently forming price must not silently acquire closed-M5 authority. |
| **ObservationCut** | The last admissible information boundary for a live or replay scene. Everything used in an answer must be available at or before it. |
| **DomainState** | What follows deterministically from observations at that cut: before confirmation, confirmed direction, DR intact/broken, current extrema, places already reached. |
| **FamilyDefinition** | The rule defining a stable historical family, such as instrument × block × direction × activation window × possibly weekday. It is a definition, not an estimator of every question. |
| **FamilySnapshot** | The actual members and fixed `N` produced when a family is instantiated. BASE-24’s frozen family remains a valid product object. |
| **QuestionInstance** | A concrete trader question at a cut, e.g. “From this M5 close, did historically comparable cases reach −0.5 before the end of the block?” Target, cut, horizon, method version and observation state are part of its identity. |
| **EligibleCaseSet** | Cases that are legally comparable for that question. It may be derived from a FamilySnapshot or from a broader parent population. It is **not** automatically the frozen BASE family. |
| **Outcome** | Per-case result under that question: YES, NO, UNKNOWN, or an explicitly separate non-applicability state. |
| **Estimate** | Historical count/share/distribution calculated from a named numerator, denominator and unknown policy. |
| **EvidenceStatus** | What has been established about the estimator itself: historical description only, exploratory comparative evidence, temporally out-of-sample validation, or trading-decision evidence. |
| **Claim** | The sentence the evidence allows the system to make. Existing C0/C1 forms already cover most current product statements. |
| **PresentationBinding** | The exact chart/panel relation representing that claim, including how it disappears or changes when invalid. |
| **Release/Provenance** | Versioned evidence of what inputs, definitions, calculation and claim produced an answer. |

This yields a closed product path:

```text
market observation
       │
       ▼
 ObservationCut ──► DomainState
                       │
                       ▼
                 QuestionInstance
                       │
             comparison rule/version
                       │
                       ▼
                EligibleCaseSet
                       │
                  per-case outcomes
                       │
                       ▼
         Estimate + support + UNKNOWN
                       │
                 EvidenceStatus
                       │
                       ▼
                Admissible Claim
                       │
               PresentationBinding
                       │
                       ▼
                 trader perceives
              price ↔ history ↔ limits
```

This is deliberately close to Semantic Trace’s existing path—observation → state → question → set → outcome → calculation → estimate/support → admission → screen—because that implementation found real gaps while changing no numeric definition. fileciteturn36file0 Rebuilding this as a parallel “new ontology” would create exactly the duplication the user asked to avoid.

### Non-negotiable semantic invariants

**Historical final ≠ current observation.** Final R/X are defined over the historical session’s completed measurement horizon. Today’s low, today’s retracement-so-far, or a newly observed extreme is a different object even if it ultimately happens to equal the final value. The registry and FOM term work already make these distinctions explicitly. fileciteturn25file0 fileciteturn32file0

**Frequency ≠ predictive probability.** A fraction such as 14 historical YES outcomes among known comparable cases is a conditional historical frequency. The current claim registry explicitly forbids readings such as “chance today,” “where price will be today,” and “time of entry,” and the edition contains no predictive admission or policy/action authority. fileciteturn40file0

**A family and a conditional subset are not the same identity.** The frozen BASE family can retain one `N`, while a question such as “from here to L” legitimately has a changing eligible subset because cases that had already reached L by their corresponding cut cannot answer the same remaining-path question. PR #7 already reveals this: each target place gets its own set, so the rows are not nested and do not share one denominator. fileciteturn23file0

**UNKNOWN ≠ NO; unavailable ≠ zero.** The semantics and Q1 pilot distinguish incomplete observation from a known failure to reach the target, and the Q1 implementation suppresses the percentage at small support while preserving counters. fileciteturn25file0 fileciteturn22file0

**Event time ≠ knowledge time.** A market event can have occurred at one M5 while becoming admissible only after that M5 closes or after another condition is established. I recommend expressing both `event_time` and `available_at`/`known_at` explicitly wherever the distinction exists. This does not require a bitemporal database; it requires an invariant that an answer at cut `t` may not depend on an entity whose availability exceeds `t`. PROV makes a similar useful distinction between an entity, the activity generating/using it, and generation/usage times; the conceptual distinction can be borrowed without installing a PROV stack. citeturn8search1

**Dependency ≠ causality.** FOM’s impact path is correctly useful for statements such as “changing this definition can invalidate or alter these downstream calculations.” It does not establish that the market variable causally produces the historical outcome. FOM’s own implementation notes already warn that a formal dependency does not guarantee a numerical change in every instance. fileciteturn32file0

**A green test proves its encoded predicate—not the framing.** FOM’s mutant checks, Semantic Trace’s counterexamples, LinkML conformance and browser relations are valuable proofs of implementation consistency. They cannot establish that the estimator transports to 2026, that the trader understands the graphic, or that a historical regularity creates trading advantage. The repository itself leaves human reading and practical utility open. fileciteturn32file0

### What semantic closure means here

DR Lab does **not** need a philosophical proof of complete ontology. It needs closure over what the product is actually allowed to show. For every visible conditional number or distribution, the following path should be machine-recoverable:

```text
visible element
→ presentation binding
→ claim/fact form
→ estimand
→ concrete question
→ historical case-set snapshot
→ eligibility rule
→ outcome definition
→ numerator / denominator / unknown policy
→ observation cut and information boundary
→ evidence status
→ source/version/release
```

SC-1.1 already provides much of the middle; Semantic Trace provides most of the end-to-end path; FOM adds reverse impact queries and presentation-relational checks. fileciteturn26file0 fileciteturn36file0 fileciteturn32file0

Closure should be declared **only for the bounded v1 product surface** when every visible assertion has that chain and invalidation behavior. It should explicitly remain open for prospective 2026 transfer, C2 prediction, C3 trading advantage, human perceptual acceptance, full raw-minute provenance, and any unaccepted PRE semantics. Those are different proof obligations, not missing ontology nodes. fileciteturn32file0

## Scientific, ontology, and architecture audit

### The most important empirical result is negative for the architecture

The strongest new information in the accumulated work is not FOM. It is the Q1 comparability result because it tests whether the semantic architecture is conditioning on variables that actually improve the historical answer.

The study defines Q1 as: after a cut, before the end of the session block, did price reach an as-yet-unreached target `L ∈ {0, −0.5, −0.7}`? Its declared evaluation set contains 296,738 15-minute-cut rows from NQ/ES/YM ODR/RDR, with earlier dates only as comparison cases, an intact DR, complete prefix, open target, and known target outcome. It compares the existing position/family variants against a deliberately simple reference `BASE_D`: same distance-to-target bin and same time cut, without side, activation window or weekday. fileciteturn28file0

The study is unusually disciplined for an internal exploratory analysis. It reports Brier loss, block-bootstrap intervals by ISO week, temporal epochs, support and coverage, equal-`n` diagnostics, calibration by distance/time, a shuffled negative control, and a synthetic positive control; its decision thresholds were declared before counting. fileciteturn28file0 fileciteturn29file0 Those are sensible choices: proper scoring rules are the correct class of tools for assessing probabilistic estimates, while Brier decomposition specifically separates reliability/calibration from resolution and irreducible event uncertainty. citeturn12search1turn12search0

The results materially change the architecture:

| Q1 estimator | Shared evaluated rows | Brier estimator / baseline | Reported interpretation |
|---|---:|---:|---|
| `NODEPOS_WD` — position + side + activation window + weekday | 66,461 | 0.2161 / 0.2130 | **Worse** than distance × time; −1.4% skill; only about 22% common-row coverage |
| `NODEPOS_ALL` — position + side + activation window | 200,487 | 0.1794 / 0.1817 | Modestly better; +1.2% reported skill; same favorable sign across epochs |
| `GEO` — position only | 208,358 | 0.1773 / 0.1806 | +1.8% nominal skill, but approximately no advantage once larger support is equalized |
| `CLOCK` — time without distance | 208,358 | worse by about 0.0118 Brier | Clearly worse; distance carries useful information |

These are branch-reported results from the visible 2006–2025 history, not my rerun. fileciteturn29file0

That gives a decisive architectural conclusion: **weekday family identity is a useful object of historical description, but it has no demonstrated right to be the default comparison population for Q1.** In this study it is actually inferior to a much simpler question-specific reference. fileciteturn29file0

This matters far beyond Q1. DR Lab should adopt the principle:

> **Historical object identity and estimator conditioning are separate design decisions.**

A family can answer “what were the final R/X outcomes of this historically defined family?” without being the best estimator for “from this exact current distance and time, how often was target L reached?” That distinction is the single most important conceptual simplification I recommend.

### The Q1 study also finds a concrete matching defect

Near a target, the “stood in the same place” window does not actually equalize distance to the target well. In the reported 0.05–0.25 IDR distance region, GEO/NODEPOS estimates understate observed arrival frequencies by roughly 6–10 percentage points, while their selected historical members are on average about 0.10–0.16 IDR farther from the target than today’s price. This affected a minority of rows—about 3.6%—but it occurs precisely where the trader is closest to the selected place and the answer is most salient. fileciteturn29file0

The study also finds that IDR width carries substantial information beyond normalized distance and time—reported arrival frequency was about 11.4 percentage points higher for narrow boxes and 9.7 points lower for wide ones relative to ordinary width—and that depth of retracement already made from the maximum showed progressively larger conditional differences, with an augmented depth estimator improving Brier across reported epochs. fileciteturn29file0

These findings **do not justify adding both features to the product now.** The study explicitly says width and pullback depth have not been tested jointly and may partly represent the same underlying phenomenon—how the day’s actual scale relates to the IDR unit. It proposes a joint test and recognizes that its “established” findings remain exploration on already-visible history rather than confirmation on new data. fileciteturn30file0

This distinction is essential in financial research. Repeatedly choosing rules after inspecting the same history produces data-snooping risk; that problem is well documented specifically for technical trading rules. citeturn11search0 Time-series validation also requires care because serial dependence and nonstationarity make ordinary random cross-validation assumptions nontrivial. citeturn11search3

Accordingly, the present evidence hierarchy should be:

**C0 — retrospective fact/distribution.** “In this fixed historical family, final R lay here in 33 of 156 sessions.”

**C1 — conditional historical frequency.** “Among cases eligible under method M at this cut, 14 of the known cases later reached L.” This is where Q1/ARRIVE belongs today. PR #6 explicitly labels itself C1 and outside the main SC gate. fileciteturn22file0

**C2 — prospectively validated forecast.** Requires an estimator frozen before consuming the held-out period, temporally out-of-sample scoring against a preregistered baseline, calibration/coverage analysis, and no retroactive tuning on those cases. Nothing inspected establishes this level. The current claim registry explicitly contains no predictive admission. fileciteturn40file0

**C3 — trading advantage.** Requires more than prediction: an executable decision policy, entry and exit semantics, stop/target ordering, fills/slippage/commissions, risk allocation and out-of-sample utility/P&L. `docs/STRATEGY.md` itself warns that several descriptive DR regularities did not translate into positive mechanical trading results in local tests and that descriptive geometry is not a proven profitable system. fileciteturn24file0

### The ontology is already sufficient in the parts that matter

LinkML is an appropriate substrate for the current product problem. Its formal specification covers schema structures, derived schemas, validation and mappings, and LinkML validation is specifically defined in terms of structural and semantic conformance of instances to a schema. citeturn9search1turn9search2 DR Lab already uses it for a typed, executable registry rather than just prose. fileciteturn41file0

The external ontology methods are most useful as **diagnostic lenses**, not replacement technologies.

**Competency questions are strongly applicable.** Grüninger and Fox’s formulation treats the questions an ontology must answer as benchmarks that both characterize and drive ontology construction. citeturn13search14 FOM’s strongest feature is exactly this: explicit bounded questions, counterexamples, and predeclared affected/unaffected sets. fileciteturn32file0 The right improvement is therefore “better competency questions tied to trader tasks,” not “more classes.”

**OntoUML would be useful for a one-time identity audit, not as the runtime stack.** UFO/OntoUML explicitly distinguishes structural object types, roles, relations, events, and related categories. citeturn13search5 That vocabulary could help review distinctions such as Session vs Session-at-Cut, FamilyDefinition vs FamilySnapshot, Outcome vs Observation, or trader-selected role vs intrinsic market object. But migrating SC-1.1 to a new formalism would duplicate a working executable contract without evidence that runtime reasoning over those foundational distinctions is presently missing.

**Faceted classification is useful as a query discipline, not as the ontology of the market.** Broughton’s work describes facets as a major technique for knowledge organization and retrieval and also emphasizes the broader role of semantic factors in modeling subject domains. citeturn13search0turn13search1 More recent work explicitly notes substantial variation in what “facet” and “facet analysis” mean across systems. citeturn13search10 That warning matters here.

FOM’s ten facets are:

- category,
- market phase,
- knowledge availability,
- price frame,
- temporal alignment,
- set role,
- denominator rule,
- claim form,
- grounds,
- presentation surface. fileciteturn37file0

They are **not ten orthogonal dimensions of one subject classification**. They intentionally mix market semantics, epistemic state, computational policy, evidence provenance and presentation. That is perfectly legitimate as a multi-axis query index. It becomes misleading only if the project starts calling them the fundamental ontology of DR Lab or requires UI structure to follow them.

My verdict is therefore: **keep all ten as derived FOM query projections where they demonstrably answer competency questions; do not create more facets merely to achieve theoretical symmetry; do not organize the trader interface around them.**

### External architecture comparison

| Architecture | Concrete advantage for DR Lab | Error class it removes | Cost / duplication | Verdict |
|---|---|---|---|---|
| **Current SC-1.1 + Semantic Trace + reduced FOM** | Typed identities, denominators, claim admission, reverse lineage, stale-source detection, presentation obligations | Denominator substitution, future leakage, claim escalation, stale mappings, presentation-number mismatch | Lowest; already implemented | **Recommended** |
| **RDF + OWL + SHACL + PROV** | Standard graph interoperability; formal ontology inference; RDF graph validation; standardized provenance exchange | Valuable if DR Lab must interoperate with heterogeneous knowledge graphs or requires generic DL inference | High: duplicates current LinkML/trace representation and introduces a graph runtime/toolchain | **Do not adopt without a concrete interoperability/inference requirement** |
| **OntoUML-first redesign** | Stronger discipline around object identity, roles, events and type distinctions | Could expose conceptual category mistakes earlier | Moderate/high redesign cost; little direct runtime gain today | **Use as review method only** |
| **UI-only integration without semantic machinery** | Fastest apparent path | None of the difficult semantic failures | Cheap initially, expensive once denominators/knowledge boundaries diverge again | **Reject** |

OWL 2 provides formally defined semantics for classes, properties and individuals and supports reasoning such as consistency/subsumption; SHACL validates RDF graphs against shapes; PROV distinguishes entities, activities, generation, usage and derivation. These are real capabilities, not buzzwords. citeturn8search0turn7search0turn8search1 But none solves a currently demonstrated DR Lab problem more cheaply than the existing typed registry plus trace. FOM’s own implementer independently reached the same engineering decision and deliberately added no RDF/OWL/PROV service. fileciteturn32file0

SKOS has one particularly useful principle worth borrowing without adopting an RDF stack: mappings of different strengths should not be silently treated as identity; notably, `closeMatch` is deliberately non-transitive. citeturn7search1 DR Lab should apply the analogous discipline to words such as “place,” “current low,” “final R,” “arrival,” “same position,” and “same future”: similarity or retrieval convenience must never become semantic equivalence by transitive accident.

## PR provenance, dependency reconstruction, and disposition

The PR list substantially overstates the number of independent achievements because several later PRs are stacked on earlier branches or opened against `main` while containing long ancestral chains. The correct unit of integration is therefore **unique semantic/code delta, not PR changed-file count**.

The inspected `main` anchor is still `2672841...`. fileciteturn42file0 The real graph is approximately:

```text
main@2672841
│
├── PR #2  resheniya-08-10
│      b7a52f1
│        │
│        └── PR #7  ekran-24-otsyuda
│              1412567
│                 │
│                 └── PR #8  semantic-trace
│                       3031c95
│                       ├── PR #9  family-path-linked-summary
│                       │      0f1ae26
│                       │      └─ also incorporates Summary candidate a2d076a
│                       │
│                       └── PR #10 FOM line
│                              7c51037 → 720e5ad → 6d488cd → f954046
│
├── PR #3  KADR-1.0
│      af90505
│        └── PR #4 KADR-1.1 + measurements
│              47e2fd0
│                └── PR #5 Q1 handoff
│                      3dac913
│                        └── PR #6 Q1 pilot
│                              e9b5bc6
│                                ╲
│                                 ╲ merged into #7 lineage
│
├── PR #11   duplicate publication/head of the 08.10 line
│
├── PR #12   cumulative stack + Q1 comparability study
│
└── PR #13   Summary candidate a2d076a
               ╲
                ╲ used as a basis inside PR #9
```

PR #7 explicitly says its base is PR #2 and that a merge commit brings in the Q1 pilot and the #3–#5 packages beneath it. fileciteturn23file0 PR #8 then bases Semantic Trace on PR #7, so by that point the formerly separate UI/SWPC and KADR/Q1 lines coexist. fileciteturn36file0 PR #10 was opened against `main`, but its FOM baseline commit has Semantic Trace `3031c95` as parent, followed by two recorded expectation corrections and the final `f954046` implementation; its very large PR diff is consequently not 24 independent FOM features. fileciteturn35file0 PR #9 states that the earlier `a2d076a` Summary candidate is included as a basis, while PR #13 separately publishes that Summary candidate against `main`. fileciteturn39file0 fileciteturn38file0

The disposition I recommend is:

| PR | Actual contribution | Decision | Exact transfer principle |
|---|---|---|---|
| **#1 Design 24** | Established the accepted Screen 24 semantic foundation and corrected percentage/identity problems | **Keep** | Already in `main`; treat as canonical baseline, not something to re-import. |
| **#2 SWPC / 08.10 / PRE / NOW** | SWPC candidate, applied trader-work study, NOW visual anchoring/phase work, PRE candidate, low-support handling | **Split and rework** | Transfer individually validated SWPC fixes, `meaning/17` findings, NOW anchoring and generic low-support behavior. PRE remains subject to its semantic standing; do not import the entire 87-file branch merely because it is ancestral. PR body itself recorded outstanding operator acceptance items and unrun H tasks. fileciteturn18file0 |
| **#3 KADR-1.0** | First “film/moment” semantic proposal | **Archive as provenance** | Its conceptual line is superseded/refined by #4; no separate product merge. fileciteturn19file0 |
| **#4 KADR-1.1** | Refined “from here” semantics and A–E measurements | **Keep as research/specification source** | Retain study definitions and conclusions; do not turn the document hierarchy into runtime architecture. Reproduction needs local G3/runtime data. fileciteturn20file0 |
| **#5 Q1 handoff** | Precise C1 pilot contract, immutable-release design and engineering roadmap | **Keep as design record** | Preserve invariants; implementation is superseded by #6. fileciteturn21file0 |
| **#6 Q1 pilot** | Isolated Q1 engine, immutable releases, outcome attachment, UNKNOWN/support/future-boundary tests | **Keep the engine/invariants; retire it as a product UI** | Reuse `lab/q1/*`, storage/replay semantics and relevant tests. The pilot’s own page remains a diagnostic harness. Its reported reconciliation is valuable but was not independently rerun here. fileciteturn22file0 |
| **#7 ARRIVE-24** | Integrates Q1 answer into Screen 24; `arrive24.py`, profile/contract bindings, target hover behavior | **Keep calculation adapter; redesign default method and UI composition** | Transfer engine/adapter, exact target identities, unknown/low-support behavior, gateway/reference checks. Do not preserve weekday-family default merely by ancestry; #12 undermines it. fileciteturn23file0 fileciteturn29file0 |
| **#8 Semantic Trace** | End-to-end lineage, rendered-page evidence, future-analogue mutation tests, reverse dependency, profile-standing gap | **Keep; high priority** | This is the best integration base conceptually. Preserve BND-02/BND-03 as explicit debt rather than hiding them. fileciteturn36file0 |
| **#9 Family Path + linked Summary** | Question-linked historical trajectories and unified interaction candidate | **Keep interaction concept, recompose into detail tray** | Transfer exact-case linkage and hover/pin behavior. Do not ship another top-level mode that competes with the live price canvas. fileciteturn39file0 |
| **#10 FOM-1.2** | Executable dependency/term/facet/research/presentation map | **Keep a reduced FOM layer** | Port only unique commits after `3031c95`—not the entire 24-commit stack. Retain CQs, impact/why, stale-source checks, guarded terms and presentation obligations that service the v1 UI. Do not make the catalog itself the product ontology. fileciteturn35file0 fileciteturn32file0 |
| **#11 duplicate 08.10 line** | Overlapping publication of already represented branch content | **Reject as independent integration source** | Use the canonical original commits once; never transfer both publications. |
| **#12 Q1 comparability** | The scientifically decisive baseline/matcher study | **Keep research and reproducibility artifacts; do not merge cumulative ancestry** | Preserve the unique study script/readme/results. Product changes must be made deliberately from its conclusion, not by merging the whole stacked PR. fileciteturn28file0 fileciteturn29file0 |
| **#13 Summary** | “Сегодня · По цене · Ориентир” candidate | **Conceptually merge into unified answer rail; no separate cherry-pick if #9 source already contains it** | PR #9 already records `a2d076a` as its visual basis. fileciteturn38file0 fileciteturn39file0 |

Two details from Semantic Trace deserve preservation even if most surrounding architecture is simplified.

First, **BND-02 is a genuine semantic-governance bug**: a machine reading only the registry can misinterpret candidate profile standing because operator acceptance is not represented independently enough. Semantic Trace therefore reads decision sources and reports the discrepancy. fileciteturn36file0 The right fix is a small explicit standing axis—accepted/candidate/declined/perceptually-unverified or equivalent—not a larger ontology.

Second, the future-leakage work exposed how a green gate can hide a bad upstream calculation. An early analogue-future mutation changed only some fields, and another version created false failures because stored DR-break state was not recomputed consistently. The eventual test had to modify all OHLC data, recompute derived break state, and inspect calculation before publication suppression. fileciteturn36file0 This is exactly the kind of counterexample-based testing that deserves to survive integration.

## Unified trader interface specification

The user interface should be **price/time-centered, question-anchored, and spatially stable**.

I considered three materially different organizing principles:

| Candidate | Strength | Failure mode | Verdict |
|---|---|---|---|
| **Ontology/facet-centered** | Excellent discoverability for researchers | Forces the trader to translate market → ontology → answer; exposes implementation abstractions | Reject for working UI |
| **Question-centered screen switching** | Explicitly matches trader questions | Risks mode proliferation and loss of visual momentum/context when each question becomes its own screen | Use questions, but not separate screens |
| **Stable price-time canvas + question-anchored answer rail** | Keeps current market context fixed while changing only the historical question and linked evidence | Requires disciplined layering to avoid chart clutter | **Recommended** |

The recommendation follows both the repository’s binding visual intent and external human-factors evidence. Screen 24 rules say the current session is the product, candles are primary, desktop operation should be one screen without scrolling, explanatory prose should not consume chart space, panel lines should link directly to chart objects, one selection should be active, and replay should preserve the chart while changing the cut. fileciteturn34file0 Ecological Interface Design similarly argues that interfaces for complex work should support necessary cognitive control without forcing the operator to a higher level of reasoning than the task itself requires. citeturn10search1

### Spatial architecture

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ NQ · RDR · LIVE                     cut 11:10 ET          data/claim status │
├───────────────────────────────────────────────────────┬────────────────────┤
│                                                       │ TODAY              │
│                                                       │ confirmed ↑ 10:45 │
│                 LIVE PRICE / TIME                     │ DR intact          │
│                                                       │ current R seen ... │
│  candles                                             │                    │
│  DR / IDR / mid / STD                                │ HISTORICAL ANSWER  │
│  confirmation / break facts                          │ Selected question: │
│  selected target line                                │ “from here to mid” │
│  selected historical relation                        │ 14 yes / 21 no    │
│                                                       │ 2 unknown · n=37  │
│                                                       │ historical C1      │
│                                                       │                    │
│                                                       │ STATUS             │
│                                                       │ support / withheld │
│                                                       │ definition/version │
├───────────────────────────────────────────────────────┴────────────────────┤
│ DETAIL TRAY — only when requested/pinned                                  │
│  Paths                 Distribution / constellations        Frequencies    │
│  exact historical      final R/X or selected outcome        exact counts   │
│  M5 cases                                                               │
└────────────────────────────────────────────────────────────────────────────┘
```

The labels above are semantic slots, not necessarily the final Russian strings. Final operator-facing wording should remain trader language and obey the no-explanatory-prose rule. The UI should not expose “ontology,” “estimand,” “facet,” or “C1” as routine trading vocabulary; those remain in the inspector/passport. This follows the existing repository mandate that the operator judges the product by the screen and that semantic-agent lenses are inputs rather than operator decisions. fileciteturn41file0

**The central chart never changes identity.** It is always the same price-time scene. Questions alter linked historical overlays and the right-side answer, not the trader’s spatial frame.

**The right rail has three conceptual functions, not three independent dashboards.**

“Today” contains only observed or deterministically derived facts available at the cut: confirmation, break, current observed extremes, whether the selected place has already been reached.

“History” answers one selected question. Every displayed fraction has a named comparison rule, support and unknown policy in its passport even when the compact visible wording omits those technical details.

“Status” explains why an answer is available, weak, or withdrawn. “No answer,” “low support,” “unknown outcomes” and “zero historical YES” must remain visually and semantically distinct.

### How existing visual ideas survive

**Candles, DR/IDR levels and live/replay remain the stable ground.** This is already protected by Design 24’s rules. fileciteturn34file0

**Constellations and clusters remain available for final R/X distributions.** They are useful precisely because they answer a two-dimensional historical question—where and when completed extrema occurred. They should appear as secondary context when that question is selected, not be interpreted as a general likelihood field for today. `docs/SEMANTICS.md` already says a cluster cell is a historical distribution over final outcomes and not a forecast or trade. fileciteturn25file0

**Family Path is retained as the principal “why does this answer look this way?” trajectory view.** PR #9’s most valuable idea is that selecting a question reveals the actual M5 paths of the exact cases supporting the answer and links those paths to the same cases’ final outcomes. fileciteturn39file0 It belongs in the bottom detail tray, because permanently displaying dozens of trajectories would compete with the live candles and violate the existing hierarchy of attention.

**The Summary candidate is absorbed rather than preserved as a separate competing composition.** Its “Today / price / reference” structure is directionally correct, but its content becomes the stable answer rail. PR #13 therefore contributes presentation work, not another product mode. fileciteturn38file0

**The ladder remains where it conveys level geometry or whole-horizon historical reach.** Q1 must not be duplicated both in a ladder row and a Summary block with subtly different denominator semantics. A selected target may visually align with the ladder’s level, but there should be one authoritative current answer.

### The Q1 answer should become question-specific rather than family-first

This is the largest proposed semantic change to the candidate ARRIVE design.

For v1, I recommend that the primary “from here to this place” reference be the **minimal distance × remaining-time baseline (`BASE_D`)**, not the weekday BASE family. The rationale is not aesthetic: in the inspected Q1 study, the weekday-conditioned estimator was demonstrably worse and had far lower coverage, while the simpler baseline was better calibrated near the target. fileciteturn29file0

A family-conditioned `NODEPOS_ALL` answer may remain as a research comparator because it showed a small reported Brier improvement beyond the baseline on visible history. It should not displace the simpler reference in the trader-facing answer until prospective validation establishes that the extra conditioning transfers. fileciteturn29file0

This does **not** destroy family identity. It says:

- BASE family continues answering family questions such as final R/X, DR outcome and common-clock paths.
- Q1 obtains its own QuestionInstance and comparison population.
- Every answer states internally exactly which population and denominator it used.
- A trader-selected target is one market place; different estimators of that target remain separate releases, as the Q1 handoff already requires. fileciteturn21file0

### Behavior across real session states

**Before confirmation.** There is no confirmed BASE family. The screen should show the live box, IDR/DR geometry and observed M5 facts. If PRE-24 is eventually accepted, its history can answer pre-confirmation questions such as historical direction/time of confirmation under its exact pre-confirmation definition. Otherwise the honest state is “confirmed-family history is not defined yet,” not an artificial extrapolation of the post-confirmation family. PR #2 itself treated PRE as a separate profile/candidate. fileciteturn18file0

**Immediately after confirmation.** Instantiate and freeze the BASE FamilySnapshot. Its membership and `N` do not change merely because the next M5 arrives. Default visual attention should shift to the pullback side because the operator study identifies “where to expect the pullback” as the central DR Lab decision. fileciteturn33file0

**Each new closed M5.** Extend today’s observed path and derive a new DomainState. The BASE family remains fixed. A pinned question is recomputed only insofar as its QuestionInstance legitimately depends on the new cut—for example, “from here to L” has a new remaining horizon and potentially a new eligible subset. The spatial layout does not move merely because values change.

**When the selected level has already been reached today.** The primary answer becomes an observed fact: “reached at HH:MM” under the appropriate closed-M5/event definition. The previous conditional historical percentage must not continue to look like the current answer. Historical context can remain available in the detail tray.

**On pullback or renewed continuation.** Today’s observed extrema update. A historical Q1 answer may change because the current distance and state changed. This must never silently rewrite what the earlier answer meant; a pinned historical release can remain inspectable as an earlier QuestionInstance.

**After DR break.** Any claim requiring an intact DR is withdrawn. The observed candles, selected level and historical facts remain visible; only inapplicable conditional graphics disappear or acquire an explicit unavailable status. This is consistent with SWPC’s principle that a withheld number takes its drawing with it. fileciteturn41file0

**With insufficient historical support.** Show “insufficient history” or the agreed equivalent plus support `n`; show no percentage. PR #6/#7 already implement the `n < 20` suppression logic in their candidate profiles. fileciteturn22file0 fileciteturn23file0

**With UNKNOWN outcomes.** Preserve YES/NO/UNKNOWN separately. Unknown history must never disappear into the denominator or become a zero outcome. fileciteturn22file0

**In replay.** The same spatial interface remains on screen. Clicking a candle changes ObservationCut and recomputes everything that is legally knowable at that cut. Future candles may remain visually present only where the accepted replay rule permits them, but they cannot feed the answer. The current UI rules already specify candle-based replay with the same chart and a return to live on repeat click. fileciteturn34file0

**Returning to live.** Restore the live cut. A pinned semantic target may persist if it still denotes the same place in the same session; a cut-specific historical answer must refresh. If its definition is no longer applicable, clear it and state why rather than silently carrying stale graphics forward.

### Hover, pinning, color, and motion

Hover should be **transient linking**: hovering an answer illuminates the exact target/area and its corresponding historical evidence.

Click should be **semantic pinning**: the selected QuestionInstance becomes persistent across incidental mouse motion and, where valid, new M5 updates. Clicking the active object again or empty chart space clears it. This reuses the operator’s existing one-active-pick rule. fileciteturn34file0

Color should express **role**, not apparent trade desirability. Design 24 already assigns amber to R and sky blue to X. fileciteturn34file0 Do not revive green/yellow/red as probability/action semantics for C1 historical answers; that visual grammar can turn a descriptive share into a recommendation even when the words do not.

Animation should be minimal. The new M5 and changed status may update; the workspace itself should not reorganize. The point is to make change perceptible **against a stable reference frame**, not to increase visual activity.

The cognitive hypothesis in the user’s brief is supported in direction, although not yet empirically proven for DR Lab. Ecological Interface Design specifically aims to avoid forcing higher-level cognitive processing than the task requires. citeturn10search1 In current project evidence, the same pullback question can require the trader to mentally traverse the chart, Summary, hidden family windows, another mode and a hover state; the repository’s own applied-work study calls out that scattering. fileciteturn33file0 The new design target is therefore **one stable chart plus at most one explicit question selection to obtain the answer**, with deeper provenance available without being mandatory.

That target still requires human validation; FOM correctly leaves perceptual comprehension open. fileciteturn32file0

## Engineering handoff, validation, and residual operator decisions

The next engineering activity should **not** be “merge PRs #2–#13.” It should be a new controlled integration from the verified `main@2672841...`, with source-level provenance for each imported delta. `main` is currently still at that SHA. fileciteturn42file0

### Target implementation

**Scope.** Produce one Screen 24 successor on the existing working route. Do not add a second product UI. Preserve the current live/replay chart, accepted BASE/NOW calculations, existing shortcut/runtime behavior and the C0/C1 claim boundary. Diagnostic Q1 and candidate servers may continue to exist as test harnesses but are not operator surfaces. These constraints follow the repository’s normative agent map and current UI rules. fileciteturn41file0 fileciteturn34file0

**Protected decisions.** The implementation must preserve:

- DR/IDR and closed-M5 definitions;
- accepted SC-1.1 meaning for BASE-24 and NOW-1.0;
- frozen BASE-family identity;
- R/X distinction;
- UNKNOWN semantics;
- no C2/C3 language;
- Screen 24 as one price-centered workspace;
- one active selection and replay semantics;
- no real-order authority. fileciteturn41file0 fileciteturn40file0

### Integration sequence

**Semantic core first.** Port the minimal Semantic Trace implementation from PR #8 needed to reconstruct every visible v1 assertion. Preserve its counterexamples, rendered-screen evidence, reverse lineage and source-version checks. Add an explicit machine-readable profile-standing field to remove BND-02 only after the standing values faithfully reproduce existing operator decisions; the field must not turn ARRIVE/PRE candidates into accepted profiles merely because they exist. fileciteturn36file0

Observable result: without changing the UI, one command/query path can return, for every existing BASE/NOW visible number, observation → state → question → set → outcomes → estimate → claim → surface, and a mutated dependency or stale source makes the trace fail.

**Reduced FOM second.** Port only FOM’s unique post-`3031c95` commits or equivalent changes—not the entire PR #10 ancestry. Its commit chain explicitly begins with a FOM baseline on Semantic Trace, includes two documented expectation corrections, and culminates at `f954046`. fileciteturn35file0 Keep the guarded term queries, impact/why functionality, relevant competency questions, research-boundary records, and alpha/omega presentation obligations. Remove or defer catalog entities that no accepted v1 UI, test, or impact query needs.

Observable result: the reduced FOM still detects the declared semantic and presentation mutants, but no server calculation depends on FOM. That preserves the implementation’s current separation. fileciteturn32file0

**Q1 calculation third.** Extract the Q1 engine/release invariants from PR #6 and the Screen 24 adapter/reference-gate logic from PR #7. Do not inherit the weekday family as the canonical estimator merely because it is present in the branch. Implement the question interface so that the comparison method is versioned and replaceable. For the first integrated C1 presentation, my recommendation is the distance × remaining-time reference as the primary Q1 answer; retain `NODEPOS_ALL` only as a research comparator until prospective evidence warrants promotion. The Q1 study is the evidence for that choice. fileciteturn22file0 fileciteturn23file0 fileciteturn29file0

Do **not** add IDR width and prior-pullback depth to the production matcher yet. Their joint contribution is explicitly untested and may be one phenomenon represented twice. fileciteturn30file0

Observable result: for each `(session, cut, target, method-version)`, the engine returns a stable QuestionInstance identifier, eligible `n`, YES/NO/UNKNOWN, historical rate when support permits it, and a complete provenance path. Editing the target’s own future must not change the answer available at the cut; changing an analogue’s post-cut future may change its outcome but must not retroactively change eligibility unless that eligibility legitimately uses the changed information.

**Unified presentation fourth.** Start from the existing Screen 24 spatial architecture. Fold the useful Summary candidate into the right answer rail and the useful PR #9 Family Path interaction into the bottom detail tray. Do not independently cherry-pick PR #13 and then also transfer the PR #9 version that already incorporates `a2d076a`. fileciteturn39file0 fileciteturn38file0

Observable result: the operator remains on one screen while moving through pre-confirmation, confirmation, new M5, selected target, reached target, DR break, low support, replay and live return. No mode switch is necessary to answer the primary selected question.

### Required tests

The semantic tests should explicitly encode the failures the project is trying to prevent, rather than merely snapshotting the chosen implementation:

| Test family | Required falsifier |
|---|---|
| **Identity** | Change the horizon, target or estimator version and assert that the QuestionInstance/estimand identity changes; update today’s M5 and assert BASE FamilySnapshot identity does not. |
| **Information boundary** | Mutate all post-cut OHLC fields and all derived state that depends on them; assert pre-cut eligibility and answer inputs do not change. This incorporates the lesson from Semantic Trace’s earlier incomplete mutation. fileciteturn36file0 |
| **Denominator** | Substitute family `N` for question-specific eligible `n`; test must fail. Substitute one target’s eligible set for another target; test must fail. |
| **UNKNOWN** | Remove future observation from a historical case without showing target reach; it must become UNKNOWN, never NO. |
| **Claim admission** | Attempt to render “probability today,” “will reach,” or action language from C1; publication must fail. Current claim forms already provide the forbidden-reading basis. fileciteturn40file0 |
| **Low support** | `n < threshold` removes the numerical share and every visual encoding implying that share while preserving observed price facts. |
| **Presentation relation** | Corrupt the target line while leaving the correct text, and corrupt the text while leaving the correct target line; each must be caught separately. |
| **Replay** | For every replay cut, compare the visible answer with the same engine called on that historical prefix; future information must be irrelevant. |
| **Release integrity** | Saved Q1 answer bytes remain immutable; later realized outcome is attached separately; correction creates a new outcome revision rather than rewriting history. PR #6 already reports this pattern. fileciteturn22file0 |
| **Regression** | Existing accepted BASE/NOW bundles on representative scenes remain byte/value/word-equivalent unless a deliberately approved semantic change says otherwise. |

Machine tests should be followed by an **operator task test**, because no amount of Semantic Trace or FOM proves comprehension. SWPC itself calls the view perceptually unverified until human tasks run. fileciteturn41file0

The acceptance session should use unfamiliar replay scenes and ask the operator, without coaching, to answer concrete market questions such as: what is known now; whether DR is confirmed/broken; which selected place is still ahead; what exactly the historical fraction describes; whether the place was already reached; what “unknown” means; what changed after the next M5; and whether the screen is live or replay. Record **semantic correctness first**, time/hesitation second, preference last. The comparison should be between the current working composition and the unified candidate, not between abstract architecture descriptions.

### Scientific gate for C2

After the C1 product is stable, freeze one Q1 estimator and one baseline **before opening the held-out 2026 outcome data**. That held-out period is valuable precisely because the project has not yet consumed it in the reported research. The repository repeatedly records 2026 as hidden. fileciteturn25file0 fileciteturn28file0

The prospective gate should compare the frozen estimator against the frozen distance × time baseline with a proper score such as Brier, report calibration/reliability, resolution, support, coverage and temporal variation, and prohibit tuning on the 2026 results. Proper scoring-rule theory and Brier reliability/resolution decomposition support that evaluation structure. citeturn12search1turn12search0 Only a successful prespecified prospective result warrants a C2 claim.

C3 should remain a completely separate project. It requires a defined trade action and cost/risk model; a good target-arrival forecast does not itself imply a profitable or suitable trade. The strategy document already recognizes the separation between descriptive regularities and mechanical edge. fileciteturn24file0

### Safe Git integration

The integration engineer should work from the verified main ancestor and transfer **unique commits or file-level patches**, not merge all open heads. Before every transfer, compare ancestry and patch equivalence with Git’s merge-base/cherry/patch-id mechanisms so repeated ancestry from #2/#7/#8/#10/#12/#13 cannot enter twice.

Each integration commit should record:

```text
source PR / branch / commit
files or semantic objects transferred
whether code, calculation, semantics, or presentation changed
accepted vs candidate standing
tests proving non-duplication and regression behavior
```

The critical duplication cases are known in advance: PR #7 already imports the #3–#6 chain; PR #8 stands on #7; PR #10 stands semantically on #8 despite being opened against `main`; PR #9 already uses the Summary candidate that #13 publishes separately; PR #11 overlaps the 08.10 line. fileciteturn23file0 fileciteturn36file0 fileciteturn35file0 fileciteturn39file0

Keep semantic-core, Q1-calculation and UI-composition changes in separate revertible commits. A UI rejection should therefore allow the trace/calculation improvements to survive; a Q1 estimator rejection should not require rolling back unrelated semantic trace fixes.

### Merge gate and rollback

The final integration should not enter `main` until all of the following are simultaneously true:

**Machine semantic closure:** every visible conditional result has the complete lineage chain; every missing or invalid link fails closed.

**Numerical equivalence:** unchanged BASE/NOW calculations match the accepted implementation; new Q1 calculations match their declared engine/reference for all reproducible cases.

**Leakage resistance:** future-day and future-analogue counterfactuals pass at the calculation layer, not merely after the publication gate has removed a bad number.

**Presentation consistency:** the exact chart object and textual answer withdraw together when a claim becomes inadmissible.

**Cold-start integration:** the normal operator launch path still opens the one working UI; candidate/test servers are not required. This is a binding operational expectation in `AGENTS.md`. fileciteturn41file0

**Human semantic acceptance:** on unfamiliar scenes the operator reliably distinguishes today’s facts, final historical outcomes, conditional historical frequencies, UNKNOWN/low support, and live/replay state.

Rollback is straightforward if these layers are kept separate: revert the UI composition while retaining semantic core; revert the Q1 estimator while retaining its diagnostic harness; or revert the reduced FOM without touching calculations because production computation should not depend on FOM.

### Decisions that genuinely remain with the operator

Most old branch questions should **not** be returned to the operator. D1 has acquired empirical evidence; D2 is mainly an interface-composition problem; much of the remaining implementation is engineering.

Only four issues materially change protected semantics, evidence consumption, or perceptual preference.

**Whether Q1 may cease to be family-first.** My recommendation is **yes**: use distance × remaining time as the primary C1 historical reference for “from here to this place,” while preserving the frozen family for the questions it actually defines. If the operator requires a family-conditioned Q1 by product intent, use the all-days `NODEPOS_ALL` candidate rather than weekday-family matching, because the latter was empirically worse in the inspected study. This is the one proposed semantic change that should be consciously ratified because it changes what “comparable history” means for a trader-visible answer. fileciteturn29file0

**Whether the linked Family Path detail genuinely helps reading.** This cannot be settled by code tests. Present the unified candidate against the current screen on unfamiliar replay states; keep the trajectory detail only if it improves semantic correctness or materially reduces effort without obscuring the live chart. FOM itself says human reading remains open. fileciteturn32file0

**Whether to encode profile standing explicitly in the normative machine contract.** I recommend **yes**, provided the change merely records existing authority—accepted, candidate, declined, perceptually unverified—and grants no new profile acceptance. Semantic Trace’s BND-02 demonstrates the present ambiguity. fileciteturn36file0 Because SC-1.1 is operator-controlled and pinned, the normative edition change itself requires operator authority. fileciteturn41file0

**Whether to consume the hidden 2026 tape for prospective validation after the estimator is frozen.** This decision is irreversibly evidence-consuming: once 2026 has been inspected for this model-selection question, it no longer serves as untouched confirmation data for the same choice. The repository correctly keeps it closed today. fileciteturn28file0

The resulting end state is deliberately simpler than the accumulated branch architecture: **one market canvas, one explicit question at a time, one historically honest answer tied to its price and cut, one optional evidence tray, and one machine-verifiable path from what the trader sees back to the observations and definitions that license it.** SC-1.1 supplies the semantic law, Semantic Trace supplies the chain of custody, a reduced FOM supplies semantic regression tests, and empirical studies decide which conditioning rules deserve to influence trader-visible answers. The ontology remains behind the product, doing its job; the trader sees the market, the historical evidence, and the boundary of what is actually known.