# DR/IDR Lab Semantic Reconstruction and the Proper Role of LinkML

## Evidence base and semantic archaeology

The governing research brief explicitly requires reconstruction **before ontology design**, separates strategy semantics from research/statistical/trading semantics, demands provenance for every important meaning, and treats the current code, UI, and earlier ontology proposals as evidence rather than authority. fileciteturn0file0 That methodological constraint is essential here because the repository itself contains several successive semantic regimes under persistent words such as *cluster*, *family*, *R*, *X*, *similar*, and *probability*.

The first high-confidence finding is therefore about provenance rather than trading.

**The default `main` branch is not, by itself, an adequate statement of current DR Lab meaning.** The repository explicitly says that design 24 became the working screen on October 1, 2026 on branch `design-24`, was intentionally kept unmerged from `main`, and that its semantic foundation is `DR-LAB-SEM-1.0`; it also says that the October 6 NOW layer belongs to that branch. fileciteturn36file0L2-L2 This matters because earlier hard rules on `main` prohibited final extremes, while design 24 deliberately makes final post-activation R/X extremes first-class descriptive objects. The apparent contradiction is mostly a **version/provenance conflict**, not evidence that one statement can simply overwrite the other.

The repository also has an unusually explicit authority model. The operator decides product meaning; semantic-agent and implementation-agent texts are proposals/evidence, not decisions; code establishes what is implemented but not what ought to mean; and important semantic changes are supposed to be traceable through a decision chain and commits. fileciteturn41file0L2-L2 This is already close to the provenance discipline a future semantic contract should preserve.

The primary public DR/IDR strategy evidence independently confirms the oldest skeleton of the method: TheMas7er’s public DR/IDR V1 describes a five-minute method, RDR formation from 09:30–10:30 New York time, ODR from 03:00–04:00, and “confirmation” as an M5 close above or below the DR boundary; later release notes added ADR and SD levels. citeturn2search0 The Lab’s strategy reconstruction is much broader: it records a corpus of 156 author videos/streams from 2022–2026, distinguishes author rules, heuristics, author-reported numbers, Lab measurements, and compiler/operator choices, and documents changes in the method through time. fileciteturn37file0L2-L2 I could independently verify the public 2022–2023 first-party TradingView specification, but **not every later QuantX/time-and-price detail in the Lab’s subtitle-derived reconstruction against an independently indexable first-party public artifact**. Those later details should therefore retain their repository provenance rather than silently acquiring the stronger status `PRIMARY_STRATEGY_SOURCE`.

A useful source hierarchy is consequently not “newest wins,” but:

| Evidence class | What it can establish | What it cannot establish |
|---|---|---|
| `OPERATOR_INTENT` | What the product is intended to mean and which product question is authorized | Whether the implementation actually realizes it |
| `PRIMARY_STRATEGY_SOURCE` | What the external DR/IDR method publicly states | Whether DR Lab should inherit every author construct |
| `DRLAB_SEMANTIC_DECISION` | Adopted Lab-specific meaning at a named version/branch | Empirical validity |
| `IMPLEMENTATION_FACT` | What the running calculation actually computes | Normative correctness of that calculation |
| `UI_FACT` | What the interface actually encodes or suggests | Whether the suggested inference is justified |
| `RESEARCH_HYPOTHESIS` | A falsifiable candidate explanation/feature/model | Product truth or trading permission |
| `HISTORICAL_SUPERSEDED` | An earlier denotation valuable for genealogy | Current semantics |
| `UNRESOLVED` | A real conflict with more than one defensible resolution | A license to choose silently |

The repository’s own decision history demonstrates why this distinction is necessary. On September 28, agents turned the operator’s “where and when price often got to” question into end-of-session final extremes; this generated clusters near the session end. On September 29, final extremes were explicitly replaced by first arrivals for design 22. On September 30, the semantics moved again toward an M5 family field, with first arrival demoted to a derived projection; family membership and one fixed denominator were then frozen. fileciteturn42file0L2-L2 fileciteturn43file0L2-L2 On October 1, design 24 intentionally changed the question again and adopted one final R and one final X per family session as the base endpoint representation. The repository marks the former design-22 cluster semantics as historical and explicitly states that design 24 has a different foundation. fileciteturn44file0L2-L2

That sequence is genuine **semantic drift**, but not all drift is error. There are two fundamentally different cases:

1. **Unintended substitution:** “where price visited” is implemented as “where its final extreme occurred.” That is a semantic defect.
2. **Explicit question replacement:** a new design intentionally changes from visit semantics to endpoint semantics and versions the change. That is model evolution.

Failure to distinguish them would make semantic governance too conservative: it would prevent intentional research evolution as effectively as it prevents bugs.

The test suite provides strong implementation evidence but does not close the conceptual question. `tests/sem24.py` carries 32 synthetic reference tests plus real-family consistency checks, including horizon exclusion, activation-M5 exclusion, missing-data handling, long/short reflection, fixed-N arithmetic, separation of price-band and joint-region shares, and invariance of the present state to replacement of future candles. fileciteturn39file0L2-L2 `tests/now24.py` explicitly tests common-clock alignment, no future leakage in matching, ties not being new extrema, unknown-outcome bounds, minimum support, phase exit after DR break, and the independence of zone reachability from the historical event clock. fileciteturn40file0L2-L2 These are unusually valuable semantic regression tests, but a green test proves that code satisfies **the encoded semantic proposition**; it cannot prove that the proposition answers the trader’s intended question.

The principal archaeology can be summarized as follows:

| Period | Dominant object | Important semantic lesson |
|---|---|---|
| Initial Lab | “Clusters from similar sessions” | *Cluster* lacked an observation-unit definition |
| Late September | Final session extreme in time × price | Endpoint substituted for “where price went” |
| Design 22 | First-arrival / M5 family field | Visits, first arrivals, endpoint extremes, and path states were separated |
| Frozen-family revision | One family `F`, one `N`, M5 projections | Conditioning and base population were separated |
| Design 24 | Final R/X endpoint distributions | “One session → one endpoint” became an explicit descriptive question |
| Zone-map-3 | Density-derived regions of R or X endpoints | Semantic event separated from region-detection algorithm |
| October NOW | State-at-cut → later continuation | Conditional forecasting became a distinct layer rather than rewriting the base family |

That history supports a strong conclusion: **DR Lab’s largest semantic failures have not usually been arithmetic errors; they have been type errors in meaning—using a mathematically valid statistic over the wrong event, population, horizon, or epistemic state.**

The major conclusions below use the status vocabulary requested in the brief.

| Claim | Evidence | Semantic consequence | Strong alternative | Status / confidence | Falsifier |
|---|---|---|---|---|---|
| DR and IDR are strategy-derived constructions over observations, not primitive market objects | Primary DR/IDR rules define ranges from a timed M5 window; Lab formalization does the same. citeturn2search0 fileciteturn37file0L2-L2 | Their identity includes observation convention and strategy rule | Treat DR/IDR as intrinsic market structures | `FOUNDATIONAL` / HIGH | A strategy-independent operational definition yielding the same objects without the DR/IDR rule |
| Final R/X require an activation, orientation, observation atom, and horizon | `scene24` measures them after own activation to block end; tests show activation/horizon changes alter the event. fileciteturn39file0L2-L2 | “R” without horizon is semantically incomplete | Treat horizon as merely a query parameter on one timeless R | `FOUNDATIONAL` / HIGH | Proof that changing horizon cannot alter identity/value |
| Question-independent and question-dependent objects coexist | Raw/M5 observations and strategy activations exist before statistical questions; visit/end-point/first-arrival claims require projections and populations | Neither “all objects preexist questions” nor “questions create everything” is adequate | Pure object ontology or pure query ontology | `FOUNDATIONAL` / HIGH | A complete model where one side alone explains all current computations without ambiguity |
| One-session-one-point is an endpoint representation, not a universal historical observation rule | Design 24 deliberately uses one R/X endpoint; design 22 used path/visit semantics. fileciteturn44file0L2-L2 | Observation unit must be declared per analysis | Make “session” the universal observational unit | `RESEARCH_CONSTRUCT` / HIGH | A proof that endpoints are sufficient statistics for every Lab question |
| “Similar session” is not one primitive relation | Frozen family keys and NOW matchers implement different selection operations. fileciteturn34file0L2-L2 | Universe, conditioning, metric similarity, and weighting need different types | One generic `similar_to` relation | `FOUNDATIONAL` / HIGH | A single relation with precise semantics reproducing all these operations without hidden parameters |
| Reachability, historical frequency, and predictive probability are distinct | Zone-map status is a geometric/today-path relation; zone share is count/N; NOW produces separately validated continuation statistics. fileciteturn31file0L2-L2 fileciteturn35file0L2-L2 | They cannot share an unlabeled percentage/probability type | Interpret all as degrees of belief | `FOUNDATIONAL` / HIGH | A formal mapping proving equivalence under stated assumptions |
| Cluster meaning precedes clustering algorithm | The Lab has used first-arrival fields, main-cluster criteria, and zone-map-3 over different primary events | Algorithm version and semantic event must be separate | Define “cluster” as whatever current algorithm returns | `DERIVED` / HIGH | Product meaning intentionally defined solely by a named algorithm/version |
| Structural schema validity cannot establish trading-question validity | LinkML validates schema conformance; its own docs distinguish schema modeling from OWL ontology and acknowledge validation-backend limits. citeturn4search1turn3search2 | LinkML requires runtime semantic tests and claim provenance companions | Put all semantics into LinkML rules | `FOUNDATIONAL` / HIGH | Demonstration that all temporal, statistical, epistemic and provenance invariants can be expressed and reliably validated by the chosen LinkML toolchain |

## Reconstructed semantic architecture

The best reconstruction is **layered and process/event-centric**, not a flat list of nouns copied from the current UI.

The market does not contain a literal object called an R, X, family, zone, or cluster. There is a market price process; the Lab receives a recording of that process; it aggregates and timestamps observations; the DR/IDR rules construct ranges and activation events; measurement rules create coordinates; research questions project histories into endpoints, paths, visits, or states; population rules assemble historical cases; estimators aggregate them; and UI code renders claims. The separation between the physical/market phenomenon and its measurement representation mirrors a central metrological distinction: the International Vocabulary of Metrology distinguishes the quantity intended to be measured from measurement procedures/results rather than treating representation and phenomenon as the same thing. citeturn8search0

A technology-neutral architecture that survives removal of the current code is:

| Layer | What exists here | Dependence |
|---|---|---|
| **Market process** | Transactions/quotes and the evolving price process | Independent of DR Lab |
| **Observation record** | Available samples, OHLC bars, missingness, timestamps, source | Depends on data source and aggregation |
| **Strategy interpretation** | Session window, DR, IDR, confirmation, break, direction | Depends on DR/IDR rules |
| **Measurement frame** | Origin, orientation, IDR width, normalized coordinate, grid | Depends on strategy object + coordinate convention |
| **Epistemic state** | What is knowable at a named cut | Depends on observation availability and knowledge time |
| **Historical case frame** | Universe, family/cohort, eligibility, conditioned/matched set | Depends on question and membership rule |
| **Outcome projection** | Endpoint, visit, first arrival, trajectory, swing, future continuation | Depends on event definition and horizon |
| **Statistical object** | Estimand, estimator, estimate, support/uncertainty | Depends on target question/population/outcome |
| **Claim/presentation** | Human-readable assertion and visual encoding | Depends on what evidence warrants |
| **Decision/policy** | Entry/no-entry/stop/target/size/execution | Requires evidence beyond descriptive statistics |

This architecture rejects both extreme philosophical positions in the brief.

**Position A is partly right:** an M5 bar, an observed confirmation event, and a fully parameterized final session endpoint do not come into existence merely because a trader asks a question.

**Position B is also partly right:** “6/73” has no complete statistical meaning without specifying what 73 represents, what event the 6 denotes, what horizon defines it, and what claim is being made. The ICH estimand framework is domain-specific to clinical trials, but its methodological distinction is directly useful here: it insists that the scientific question be specified before the estimator and estimate, and separates the target estimand from its numerical estimate. citeturn8search5turn8search4

The previous candidate architecture

`Question → Population → Observation → Outcome → Statistic → Claim`

therefore captures one important **research-query pipeline**, but it is not the fundamental ontology. It omits the prior observation/strategy/measurement/epistemic layers, and it wrongly suggests that every object is downstream of a question. A better relation is:

`market process`
→ `record`
→ `aggregation`
→ `strategy interpretation`
→ `measurement frame`
→ `epistemic state`

and then a query branches:

`research question`
→ `case-frame/population rule`
→ `projection/outcome`
→ `estimand`
→ `estimator`
→ `estimate + support`
→ `licensed claim`
→ optional `decision policy`.

**Time is not one slot.** OWL-Time itself distinguishes temporal entities, instants, intervals, positions, durations, and temporal reference systems; a timestamp alone does not exhaust those distinctions. citeturn6search0 DR Lab needs at least these separate time semantics:

| Temporal coordinate | Meaning | Example |
|---|---|---|
| **Market clock time** | Position in the exchange/session clock | 11:50 ET |
| **Session-relative time** | Position within the session/block | 80 minutes after RDR trading window begins |
| **Activation time** | When the strategy event that starts analysis occurs | confirmation M5 |
| **State age** | Elapsed M5 bars since that activation | six completed M5s after confirmation |
| **Event time** | When a defined market-derived event occurred | first M5 reaching the eventual R price |
| **Knowledge time / cut** | Earliest point at which the observer is permitted to use information | close of current M5 |
| **Evaluation horizon** | Boundary through which an outcome is defined | block end |
| **Outcome-completion time** | When enough information exists to know the final object | often the horizon, even if its event time was earlier |

The distinction between **event time** and **knowledge time** is especially important. A session’s final R can have an event time at 11:20, because that is when its eventual deepest price first occurred, yet at 11:20 an honest observer generally does not know it is *final*. Its value becomes final only when the horizon closes without a deeper R. Design 24’s code preserves the first event time of the final endpoint while its live/prefix logic separately restricts what can be known at the cut. fileciteturn39file0L2-L2

This is why **horizon is part of semantic identity for final-type outcomes**, not merely a numerical tuning parameter. “Final R through 13:00” and “final R through 16:00” can differ even on the same path. So can “DR held,” “no new extreme,” “final X,” and time-to-event censored at different endpoints.

Clock alignment and event-relative alignment are likewise **different estimands, not two implementations of the same query**.

With clock alignment, historical state at today’s 11:50 is compared with historical state at 11:50. It preserves common market-clock regime—open/close proximity, scheduled intraday structure, and absolute remaining horizon—but different sessions may have different ages since confirmation. Current NOW deliberately uses this common-clock cut while excluding each member’s own activation M5 and requiring an honest post-activation prefix. fileciteturn40file0L2-L2

With event-relative alignment, historical cases are compared after the same number of bars since their own activation. It controls state age but destroys equality of clock context and gives different cases different amounts of remaining session time. Neither is universally superior. They answer respectively:

> “What tended to happen from this market-clock state?”

versus

> “What tended to happen at this stage of a newly activated scenario?”

Any switch between them must therefore create a different query specification or estimand identifier.

**Price has a similar layered structure.**

Absolute traded price is not the same thing as an OHLC observation. An M5 low is already an aggregation-derived observation and cannot recover the trade sequence that produced it. Directed DR coordinates then express price relative to a confirmation orientation. Dividing by IDR width produces a dimensionless normalized coordinate. If origin, direction, and width are retained, conversion between absolute price and normalized coordinate is principally a coordinate transformation; if those references are discarded, the representation becomes lossy. If normalized values are subsequently used to define distance thresholds, similarity, bins, families, or outcomes, normalization becomes more than display: it enters the **measurement definition**.

This leads to an important decomposition:

`absolute price`  
≠ `observed M5 OHLC`  
≠ `directed displacement`  
≠ `IDR-normalized displacement`  
≠ `binned coordinate`  
≠ `region`  
≠ `density`  
≠ `cluster`.

A width-normalized retracement and a 20-point retracement can be transformations of the same underlying price movement but are not interchangeable measurable quantities for every research question.

The epistemic state should also not be represented by one catch-all status enum. The current Lab already provides evidence for several independent axes: missing future data makes an outcome unknown; geometric/path constraints can make an endpoint impossible; validation status can be unvalidated; support can be insufficient; a concept can be superseded. NOW deliberately treats a missing future as unknown rather than “no,” including interval bounds when unknown outcomes remain. fileciteturn40file0L2-L2

The correct conceptual model is orthogonal:

- **Observation availability:** known / missing / incomplete / out-of-horizon.
- **Logical reachability:** holds-now / possible / impossible.
- **Historical clock relation:** future-present / future-empty / past-only.
- **Statistical support:** supported / insufficient-support.
- **Validation state:** validated / not-validated / stale / unstable.
- **Lifecycle state:** current / deprecated / superseded.

The October 6 correction is a direct empirical reason to do this: the Lab explicitly separated today’s reachability from the family-history clock after discovering that a zone can remain possible today even when no family events remain ahead of the current cut. `zonemap24.status` and `history_clock` now implement these as two independent axes. fileciteturn33file0L2-L2 fileciteturn40file0L2-L2

## Historical comparison, clusters, and statistical claims

The word **similar** currently hides several fundamentally different operations.

The design-24 base family is not, mathematically, a similarity metric. It is closer to an equality-defined historical cohort: instrument × session × weekday × direction × confirmation-window, frozen for the snapshot. The earlier decision history explicitly adopted one family `F`, one fixed denominator `N`, no removal of sessions that later broke DR, and separately labeled any filters based on already-lived path. fileciteturn43file0L2-L2

The NOW layer is different. It constructs eligibility at the current common-clock cut and then candidate matchers: B0 uses all eligible family cases, M1 uses proximity in observed R or X, M2 combines observed R and X, and M3 adds recent path-shape agreement. Membership uses only information available through the cut. fileciteturn34file0L2-L2

Thus at least five concepts need separate names:

| Concept | Membership meaning | May depend on today? | May depend on future outcome? |
|---|---|---:|---:|
| **Historical universe** | All admissible historical sessions before research-specific restrictions | No | No |
| **Strategy family/cohort** | Sessions satisfying a frozen strategy-key definition | Only through the key used to instantiate the cohort | No |
| **Eligible-at-cut set** | Cohort members with valid observable state at the cut | Yes, via the cut definition | No |
| **Conditioned/matched set** | Eligible members satisfying prefix-state conditions/distance | Yes | Must not |
| **Outcome-known subset** | Members whose future outcome can be determined | No for membership in estimand; yes for estimator handling | Yes, by definition of outcome knowledge |

A statistical sample may coincide with any one of these only after its sampling/eligibility semantics are explicitly stated. “Family,” “population,” “cohort,” “sample,” and “matched sessions” should therefore not be aliases.

The cluster investigation produces an even stronger result: **“cluster” should not be a primitive domain class without an explicit event/projection type.**

Possible cluster-like objects differ before the clustering algorithm is even chosen:

| Apparent “cluster” | One session contributes | Uses future beyond cut? | What the region means | Valid question |
|---|---|---:|---|---|
| Occupancy cluster | many observed states | Prefix-dependent | where price often occupied | “Where was price often?” |
| Visit cluster | one/many visit events | Depends on horizon | areas frequently entered | “Where did sessions visit?” |
| First-arrival cluster | first qualifying visit | Depends on query cut/horizon | where a target was first reached | “Where did arrival first occur?” |
| Swing cluster | selected turning events | Usually | concentration of defined swings | “Where did defined swings occur?” |
| Endpoint R cluster | one final R | Yes | where terminal retracement endpoints concentrate | “Where did final R occur?” |
| Endpoint X cluster | one final X | Yes | where final extension endpoints concentrate | “Where did final X occur?” |
| Reversal cluster | reversal event under a reaction definition | Usually | where a defined reaction begins | “Where was a reversal followed?” |
| Time-price path density | multiple states along a trajectory | Can be prefix-only or full horizon | where paths commonly occupied time × price | “Where did trajectories spend/visit states?” |

Two regions can occupy the same pixels and still be different objects because their observation units differ. That is the required **same representation, different meaning** adversarial test.

Conversely, DBSCAN, KDE, connected-cell superlevel sets, or manually selected contiguous cells could in principle all estimate the *same semantic concentration object* if the primary event, population, geometry, and target construct are held fixed. That is the **same meaning, different representation/algorithm** test.

The current zone-map implementation is a useful example. It starts from **one known event of a single type, R or X, per family session**, maps those events into price × time cells, computes local 3×3 density, extracts connected half-height regions around their own maxima, imposes minimum support, and calculates zone share as zone-member sessions divided by the full family `N`; unknown/no-event sessions remain in `N` but receive no location. fileciteturn31file0L2-L2 This is a coherent endpoint-density construction. It does **not** thereby become a reversal zone, occupancy zone, first-arrival zone, or probability that today will end there.

Its own research history reinforces the distinction. The preceding “main cluster” study imposed several robustness criteria on endpoint concentration; later zone-map-3 replaced the screen algorithm while retaining the idea that the region is descriptive and diagnostics are properties of the region rather than permission to reinterpret it. The Lab’s current implementation even labels the historical transfer/status research as exploratory and “not today’s chance.” fileciteturn31file0L2-L2

The null study is semantically important: the repository reports that sign-flipped path nulls can generate comparable structures, weakening any interpretation that the observed endpoint zones are evidence of a special market mechanism. That does not erase the descriptive concentration; it constrains the allowed claim. fileciteturn31file0L2-L2

The statistical layer therefore needs an explicit contract analogous to, though more general than, an estimand framework. For any displayed number:

`Research question`
→ `target domain/population`
→ `observational unit`
→ `outcome variable/event`
→ `horizon`
→ `summary/estimand`
→ `estimator`
→ `estimate`
→ `support/uncertainty`
→ `licensed display claim`.

This decomposition is not merely nomenclature. In statistical methodology, an estimand is the quantity the study intends to estimate, while an estimator is the procedure and the estimate is its realized numeric output; ICH E9(R1) formalized this distinction specifically to stop analysis mechanics from implicitly redefining the research question. citeturn8search5turn8search4

Applied to a DR Lab zone number, for example:

> **Question:** In this frozen family, what share of sessions have their horizon-final R endpoint inside region Z?

> **Target population/domain:** the specified family snapshot.

> **Observation unit:** one session.

> **Outcome:** final R endpoint lies in Z, with stated missingness treatment.

> **Estimand:** empirical/full-corpus family share under that event definition, or a population probability if a broader inferential model is explicitly adopted.

> **Estimator:** `n_zone / N_family`.

> **Estimate:** e.g. 0.081.

> **Support:** `n_zone`, `N`, unknown count, stability diagnostics.

> **Permitted claim:** “8.1% of this historical family’s sessions have their defined final R event in this zone.”

> **Not permitted:** “There is an 8.1% chance today reverses here,” “this is the most likely trade,” or “the zone causes reversals.”

That last boundary is fundamental. A descriptive historical share does not automatically become a probability forecast, and a conditional empirical frequency does not automatically become a causal effect. Causal claims require a causal identification argument not present merely because a region is statistically dense.

**Denominator semantics should be treated as object identity.** Design 24’s strongest improvement was to freeze `N` and keep unknown/no-event cases in the population rather than quietly renormalizing surviving cases. fileciteturn44file0L2-L2 If a developer switches from `6/73` to `6/42` because only 42 cases are currently eligible, that is not a formatting change. It is a new statistical object unless the estimand explicitly defined conditionalization on eligibility.

A minimal identity for a share is therefore not:

`label + number`

but something closer to:

`population_definition × membership_cut × observation_unit × outcome_definition × horizon × missingness_policy × summary_measure`.

Change one component and the claim identifier/version should normally change.

The same applies to the numerator. These predicates are non-equivalent:

`ever_touched(Z)`  
`first_touched(Z)`  
`endpoint_in(Z)`  
`deepest_excursion_in(Z)`  
`was_present_in(Z, t)`  
`reversed_after_entering(Z)`  
`target_before_stop_after_entering(Z)`.

No generic `success: true` is semantically adequate.

NOW provides a good positive example. It asks a distinctly different question from the frozen endpoint map: at a common clock cut, among historical sessions with a valid comparable observable state, did a *strictly new* R/X occur later; how much farther did the eventual endpoint go; and how long until the first new extreme? Its implementation separately records total matched support, known outcomes, unknown outcomes, conditional frequency, bounds induced by unknowns, remaining-movement quantiles, and time-to-new-extreme. fileciteturn34file0L2-L2

Crucially, its path matchers did not simply get promoted because they existed. The repository’s walk-forward investigation did not validate M1–M3 over the time baseline for the confirmation family, so the product falls back to the time baseline; path-conditioned outputs remain research-only unless the validation passport says they are validated and support is sufficient. fileciteturn35file0L2-L2 That is a healthy boundary between **research construct**, **validated predictor**, and **product claim**.

## Transformations, invariants, and semantic failure modes

The semantic architecture becomes clearest as a transformation graph.

| Transformation | Output | Information lost / assumption added | Semantic risk |
|---|---|---|---|
| Market process → recorded tape | finite observation record | unrecorded microstructure/source limitations | treating record as complete reality |
| Tape → minute/M5 OHLC | candle sequence | ordering and multiplicity inside bar | inferring path/order unavailable at M5 |
| M5 window → DR/IDR | strategy range | none relative to inputs, but strategy rule added | treating rule-derived range as market primitive |
| DR/IDR + close → activation | confirmation/break event | depends on threshold, close convention, M5 atom | shifting open/close timestamps changes event |
| Absolute price → directed coordinate | strategy-oriented price | orientation/reference required | dropping reference makes reconstruction impossible |
| Directed coordinate → IDR-normalized coordinate | dimensionless geometry | width assumed meaningful scaling unit | treating normalized distances as absolute distances |
| Path → final R/X endpoint | one endpoint/event-time pair | visits, order, dwell time, intermediate swings | answering trajectory question with endpoint |
| Path → first arrival | one event | later revisits/reactions/endpoints | treating arrival as reversal or final extreme |
| Endpoint → price/time cell | discrete bin | sub-cell location | bin-boundary artifacts |
| Cells → density/zone | region | individual arrangement compressed; algorithm parameters added | equating algorithmic region with causal/trading zone |
| Events → share | scalar | individual paths and heterogeneity | denominator/numerator ambiguity |
| Estimate → UI encoding | color/label/geometry | statistical qualifications may disappear | user reads frequency as probability |
| Historical result → trading policy | action | requires utility, execution, costs, validation, risk | descriptive evidence silently becomes a trade rule |

The path→endpoint edge is particularly lossy. Design 24 correctly demonstrates that two sessions can have the same R and X values but different order; the synthetic tests explicitly check “same extreme values, different order.” fileciteturn39file0L2-L2 Once only endpoints remain, a question about whether R happened before X is no longer recoverable. Therefore the endpoint is not a compressed *equivalent* of the path; it is a projection sufficient only for a class of endpoint questions.

The current “Path of the family” and “move boundaries” should thus be understood as **different projections from a richer session trajectory object**, not rival definitions of the same thing. One preserves time-indexed path state; the other preserves final extrema and their event times. Neither dominates the other for all questions.

Several semantic invariants follow from the reconstruction.

| Semantic invariant | Why violation changes meaning |
|---|---|
| **Every outcome has an explicit horizon.** | Finality, hold/break, and time-to-event can change when the horizon changes. |
| **Every live/prefix-conditioned membership predicate is evaluable using information available at its knowledge cut.** | Otherwise historical matching leaks future outcomes. |
| **Event time and knowledge time are independent fields when finality is retrospective.** | The eventual final extreme may occur long before it becomes knowable as final. |
| **Every percentage carries its population/denominator definition.** | Changing denominator changes the estimand or descriptive object. |
| **Every numerator has an explicit event predicate.** | Visit, endpoint, first arrival, and reversal are non-equivalent. |
| **Unknown is not coerced to false.** | Missing future evidence cannot justify a negative outcome. |
| **Logical impossibility does not redistribute historical mass.** | Removing impossible outcomes and renormalizing creates a conditional object that did not exist before. |
| **A base cohort cannot be conditioned on its members’ future outcomes unless the research question explicitly targets that selected population.** | Otherwise population membership leaks the outcome. |
| **Clock alignment and activation-age alignment cannot share the same estimand identifier.** | They condition on different temporal states. |
| **Changing semantic event type requires a new object/version even if pixels are unchanged.** | Same representation can denote different events. |
| **Changing only a rendering algorithm need not create a new semantic object if the represented quantity is unchanged.** | Same meaning can admit multiple visual implementations. |
| **Cluster/event semantics and cluster-detection algorithm/version are separate fields.** | A different detector need not imply a different research question. |
| **A transformation declared lossless must retain enough reference state to invert it.** | Normalized price without origin/width/direction is not invertible. |
| **A descriptive statistic cannot be labeled predictive without an explicit validation/evaluation layer.** | Historical description and out-of-sample prediction make different claims. |
| **A predictive statistic cannot be labeled causal without a causal identification argument.** | Predictive association alone does not identify interventions. |
| **A research result cannot become a trading policy without a policy contract.** | Entries, stops, targets, costs, utility and risk are additional semantic objects. |

This produces a corresponding **forbidden-transformation catalogue**. These are mathematically computable operations that should be rejected semantically unless a newly identified query explicitly authorizes them:

`final_extreme → relabel as visit`

`visit → relabel as reversal`

`first_arrival → relabel as final endpoint`

`N_family → delete impossible-today cases → recompute same displayed percentage`

`unknown → false`

`missing future → no event`

`full-horizon endpoint → compare with shorter-horizon endpoint under same object identifier`

`event clock → substitute elapsed-since-confirmation while retaining same claim label`

`future outcome → use as current-day matching feature`

`DR-true-only historical filter → describe result as whole-family frequency`

`R-zone share + X-zone share → add as if parts of one partition`

`price-band marginal share → display as joint price×time region share`

`descriptive density → label “probability of reversal”`

`conditional historical frequency → label causal effect`

`post-hoc matcher performance → promote as validated predictor on the same history`

`normalized coordinate → drop normalization reference → later reconstruct absolute meaning`

The Lab’s own tests already encode several of these: band share differs from joint-region share; levels form nested reach events rather than mutually exclusive categories; unknowns stay in full `N`; future candle replacements cannot change prefix membership; and an observed later future can change the outcome without changing pre-cut membership. fileciteturn39file0L2-L2 fileciteturn40file0L2-L2

UI deserves its own semantic audit because representation can imply relations that the backend never asserts. The visual journal records exactly this risk. For example, R and X are drawn together in a single price column for comparison, but the journal explicitly warns that they are shares of different entities with separate “hundreds” and must not be added. It also dims impossible zones because they are no longer relevant to today’s final endpoint while retaining their historical information. fileciteturn45file0L2-L2

This leads to several UI-level adversarial tests:

| Same picture | Two possible meanings the UI must distinguish |
|---|---|
| 8.1% inside a region | endpoint family share **vs** predictive probability today |
| Same price band | ever visited **vs** final extreme ended there |
| Same star position | first arrival **vs** final event time |
| Dimmed zone | impossible as today’s final endpoint **vs** historically nonexistent |
| “No number” | insufficient support **vs** probability zero |
| Same 11:50 marker | market-clock cut **vs** 80 minutes after activation |
| Same normalized −0.7 | same relative IDR geometry **vs** same absolute market distance |

The largest current blind spot is therefore not an absent class name. It is the absence of a **machine-readable semantic passport connecting every output claim to its population, event predicate, time basis, horizon, epistemic cut, estimator and evidence provenance**. Much of this information exists in prose and tests, but not yet as a stable object crossing research → backend → UI → agent.

A second blind spot is branch/version authority. The repository documents that design 24 intentionally lives outside `main`; this is a legitimate workflow choice, but an autonomous agent that assumes default-branch semantics can reconstruct the wrong current ontology. fileciteturn36file0L2-L2 Semantic version/ref must therefore be part of provenance, not merely source-control metadata.

A third blind spot is the semantic relationship between *research diagnostics* and *product validity*. Zone stability, bootstrap recovery, null comparisons, and transfer tests are valuable, but they are heterogeneous evidence dimensions. A zone may be geometrically stable yet non-predictive; predictive yet unstable under an arbitrary grid; or descriptive but indistinguishable from a null geometry. Those are not one generic `quality` score.

## Competing architectures and LinkML fit–gap

LinkML is a strong candidate for part of this architecture, but **it should not be designated “the DR Lab ontology.”**

Its formal specification describes LinkML as a technology-independent data modeling language for typed tree-like/object-oriented instances, with classes, slots and schema-level conformance/inference rules. citeturn5search12turn5search13 The main LinkML tooling treats classes, slots, types, enums, identifiers/keys, inheritance and mixins as core modeling constructs; slots support explicit cardinalities, identifiers/keys and unique-key mechanisms. citeturn0search0turn3search5 LinkML’s own OWL documentation makes the distinction explicit: **OWL is an ontology language; LinkML is a schema language**, although LinkML schemas can be rendered into OWL. citeturn3search2

For DR Lab, the most accurate description is:

> **LinkML can be the typed semantic-contract and interchange layer for the reconstructed conceptual model.**

It can also generate documentation and implementation artifacts, participate in linked-data mappings, and provide a common source for several structural validators. It should not itself be assigned responsibility for statistical truth, causal identification, anti-leakage behavior over time-series history, or operator intent.

LinkML currently provides a broad multi-target toolchain: JSON Schema, Pydantic, Python and other code models, JSON-LD/RDF, SHACL, OWL, documentation and diagrams. citeturn3search0 It supports class rules with preconditions/postconditions, logical class expressions, and an expression language for controlled calculations. citeturn5search0turn4search7 It also supports metadata, mappings, annotations and deprecation metadata. citeturn3search9turn5search5 Schema-release guidance recommends semantic versioning, and LinkML provides explicit deprecation/replacement metadata that can preserve old URIs through staged evolution. citeturn10search0turn10search1

But enforcement is target-dependent. LinkML’s own validation documentation says its common validation path generates JSON Schema, and acknowledges that some LinkML features are not supported by JSON Schema; the validator architecture therefore supports plugins and alternative strategies. citeturn4search1 The JSON Schema generator can compile some LinkML rules into `if/then/else`, but JSON Schema cannot enforce LinkML `unique_keys` generally. citeturn0search7 SHACL shapes can be generated for RDF, but RDF shape validation itself uses an external SHACL processor. citeturn3search3turn4search1 OWL generation enables logical/ontology tooling, but the LinkML documentation explicitly notes the semantic mismatch: OWL is open-world whereas LinkML validation is substantially closed-world. citeturn3search6

This fit-gap matrix follows.

| DR Lab requirement | LinkML status | Reason / enforcement owner |
|---|---|---|
| Named semantic entity types | **EXPRESSIBLE / VALIDATABLE** | Classes and class ranges are core LinkML. citeturn5search12turn0search0 |
| Required population, event, horizon references | **EXPRESSIBLE / VALIDATABLE** | Slots, required cardinality, class ranges |
| Enumerated provenance/status categories | **EXPRESSIBLE / VALIDATABLE** | Enums |
| Identifiers and versioned semantic objects | **EXPRESSIBLE / PARTLY VALIDATABLE** | Identifiers/keys supported; version policy remains project governance. citeturn0search0turn10search0 |
| Deprecation / supersession metadata | **EXPRESSIBLE** | Native deprecation/replacement metadata. citeturn10search1 |
| Human definitions, examples, mappings | **EXPRESSIBLE / DOCUMENTABLE** | Metadata, annotations, mappings |
| Unit/coordinate metadata | **EXPRESSIBLE** | LinkML supports explicit unit metadata. citeturn10search3 |
| Cardinality and type constraints | **VALIDATABLE** | Core structural validation |
| Conditional field requirements | **PARTIAL FIT** | Rules can express many local if/then conditions; generator support varies. citeturn5search0turn0search7 |
| “Every statistic must name a denominator/population” | **VALIDATABLE structurally** | Can require a reference; cannot prove it is the *correct* population |
| “Outcome horizon must equal the event projection horizon” | **PARTIAL / REQUIRES RUNTIME** | Simple local equality may be expressible; cross-object/domain semantics should be runtime-tested |
| “No future information may enter membership at cut t” | **REQUIRES RUNTIME** | Requires inspecting dependency lineage and time-indexed source data |
| Frozen family membership | **REQUIRES RUNTIME / provenance** | A schema can carry snapshot IDs/members but not guarantee upstream selection did not mutate |
| Endpoint computed from correct path/horizon | **REQUIRES RUNTIME** | Algorithmic invariant over time series |
| Event time ≤ knowledge/finality time | **PARTIAL / runtime** | Fields can be modeled; reliable cross-field/time semantics require runtime validation |
| Clock vs event-age alignment correctness | **REQUIRES RUNTIME** | Depends on query execution semantics |
| No denominator drift | **REQUIRES RUNTIME + tests** | Needs provenance/identity checks across transformations |
| Statistical estimator validity | **NOT LINKML’S JOB** | Requires statistical logic/tests |
| Out-of-sample predictive validity | **NOT LINKML’S JOB** | Requires empirical evaluation |
| Causal validity | **NOT LINKML’S JOB** | Requires causal assumptions/design |
| Trading expectancy and execution validity | **NOT LINKML’S JOB** | Requires costs, policy, risk and market execution model |
| No semantic drift by developers/agents | **DOCUMENTABLE + governance, not guaranteed** | Schema can make drift visible but cannot ensure humans/LLMs interpret definitions correctly |
| Claim warranted by underlying evidence | **REQUIRES EXTERNAL LOGIC / review** | Semantic entailment between evidence and natural-language claim exceeds structural validation |

LinkML’s linter is useful for another layer: it validates a schema against the LinkML metamodel and configurable quality conventions. citeturn4search0 That can catch malformed or poorly documented schema elements; it cannot detect that `EndpointCluster` was accidentally populated with visit events.

PROV-O is the strongest standards companion if graph provenance becomes necessary. It models entities, activities, generation and use relations, allowing a derived number to be traced through the activity that consumed upstream entities and generated it. citeturn6search2 That maps naturally onto DR Lab’s transformation graph: source bars → strategy measurement → snapshot → endpoint extraction → zone algorithm → estimate → claim.

OWL-Time is useful as vocabulary inspiration for intervals/instants/reference systems, but it does not by itself solve DR Lab’s **knowledge-time** or evaluation-horizon semantics. It provides the temporal representational primitives, while DR Lab must define its own distinctions such as “event happened at t” versus “finality became knowable at H.” citeturn6search0

SHACL becomes worthwhile only if the semantic instances are represented as RDF and graph-level constraints justify the extra stack. Its purpose is validating RDF graphs against shapes, including SPARQL-based constraints. citeturn7search0 It is more appropriate than OWL for many closed-world data-quality requirements. OWL is appropriate if the project eventually needs formal class/property inference and reusable ontology alignment; it should not be introduced merely because LinkML can generate it. OWL 2 is explicitly an ontology language with formal model-theoretic semantics. citeturn6search1

Three architecture options are therefore genuinely competitive.

| Architecture | Composition | Strengths | Weaknesses | Judgment |
|---|---|---|---|---|
| **Lean semantic contracts** | Versioned Markdown + Python types + runtime/property tests | Minimum machinery; easy to evolve while conceptual model still changes | Prose/code drift; weak machine-readable interoperability; agents can miss constraints | Better than premature ontology, but DR Lab has outgrown it |
| **Typed semantic contract** | LinkML source model + generated JSON Schema/Pydantic/docs + explicit runtime semantic validators + semantic regression tests + provenance IDs | Strong shared vocabulary; useful generated artifacts; keeps hard temporal/statistical logic in code; low enough complexity | Two enforcement layers must be maintained; schema validity can still be misunderstood as semantic truth | **Recommended** |
| **Formal semantic stack** | LinkML + RDF/PROV-O + SHACL + selected OWL/OWL-Time alignments + runtime statistical/temporal validators | Rich provenance, graph queries, ontology alignment, more machine reasoning | High complexity; open/closed-world mismatches; little benefit until graph queries or multi-system interoperability are real requirements | Defer until demonstrated need |

For LLMs and agents, LinkML is useful but insufficient. The LinkML ecosystem already uses schemas for LLM-oriented structured extraction and inference, including OntoGPT/schema-driven facilities and an LLM schema annotator. citeturn10search5turn9search10 That demonstrates the practical value of schemas as machine-readable structure. It does **not** establish that an LLM filling valid fields understands the intended DR Lab event.

An agent can produce a perfectly valid object:

```text
event_type = FINAL_R
population = family_123
share = 0.081
```

while having selected `family_123` through future outcome, computed R only to 13:00 instead of session end, or described the 8.1% in prose as a reversal probability. All fields may pass structural validation.

For agent grounding, the semantic package should therefore include not only schema, but:

`definition + provenance + version + invariants + forbidden transformations + positive examples + counterexamples + question context + claim limitations + tests`.

This is the clearest answer to the “formal validation ≠ semantic truth” requirement: **LinkML can constrain the syntax and declared structure of meaning. It cannot guarantee that the declared meaning matches how the value was generated or how a human/LLM subsequently interprets it.**

## Minimal semantic kernel and LinkML proof of concept

Removing all current UI, backend classes, and historical names reveals that surprisingly few semantic commitments are truly indispensable.

The minimal kernel is not `R`, `X`, `cluster`, `zone`, or `family`. Those are derived domain concepts. The irreducible kernel is closer to this:

| Kernel element | Why fundamental | What can derive from it | Failure if absent |
|---|---|---|---|
| **Observation source and observation** | Establishes what market evidence exists | OHLC series, missingness, strategy ranges | Cannot distinguish market event from record |
| **Temporal frame** | Establishes clock/reference system and intervals | sessions, cuts, event times, ages | 11:50 vs elapsed-time semantics collapse |
| **Knowledge cut** | Defines honest information boundary | live/prefix state | Future leakage cannot be detected |
| **Evaluation horizon** | Defines completion boundary | final extremes, holds, time-to-event | “Final” becomes undefined |
| **Strategy rule/version** | Converts observations into strategy events | DR/IDR, confirmation, break | Market and strategy constructions collapse |
| **Measurement frame** | Defines coordinate origin, orientation, scale | directed/normalized values | Same number can mean different prices |
| **Historical case** | Unit carrying one session/path and provenance | family members, outcomes | Observation-unit ambiguity |
| **Case-set specification** | Defines universe/cohort/eligible/conditioned membership | families, matched sets | Denominator ambiguity and leakage |
| **Projection/outcome specification** | Says what one case contributes | endpoint, visit, arrival, path, swing | Numerator ambiguity |
| **Research question / estimand specification** | Binds population, outcome, horizon and summary | statistical target | Valid calculations can answer wrong question |
| **Estimator/estimate** | Separates computational method from target | percentages, quantiles, models | Method and target become conflated |
| **Evidence/support record** | Carries N, unknowns, uncertainty/validation | display qualification | False precision and unsupported prediction |
| **Claim** | Defines what humans/agents are permitted to infer | UI text, API semantic result | Number acquires accidental meaning |
| **Transformation provenance** | Connects every derived object to inputs/rules/versions | audit/reproduction | Semantic drift becomes untraceable |

This is predominantly an **event/process/measurement/claim ontology**, not an ontology of static trading things.

`DR`, for example, becomes a named strategy-derived range produced by a particular rule from observations over a temporal interval.

`R` becomes a particular outcome projection: an extremum of a strategy-oriented trajectory over a declared post-activation horizon.

`Zone` becomes a region produced by an algorithm from events of one explicit outcome type under one historical case-set snapshot.

`NOW continuation` becomes an estimand/estimate over an eligible-at-cut historical state.

That is substantially safer than creating classes first called `DR`, `R`, `X`, `Cluster`, `Family`, `Zone`, and trying to infer later what they really mean.

A minimal LinkML proof-of-concept can now legitimately be used—not as ontology discovery, but as a test of whether the reconstructed distinctions survive serialization:

```yaml
id: https://example.org/drlab/semantic-poc
name: drlab-semantic-poc

prefixes:
  dr: https://example.org/drlab/
  linkml: https://w3id.org/linkml/

default_prefix: dr
imports:
  - linkml:types

enums:
  AlignmentMode:
    permissible_values:
      MARKET_CLOCK:
      EVENT_RELATIVE:

  KnowledgeMode:
    permissible_values:
      PREFIX:
      RETROSPECTIVE:

  ClaimKind:
    permissible_values:
      DESCRIPTIVE:
      CONDITIONAL_DESCRIPTIVE:
      PREDICTIVE:
      CAUSAL:
      DECISION_RELEVANT:

classes:

  TemporalBoundary:
    description: >
      A semantically named temporal boundary; its role is not inferred
      from a bare timestamp.
    attributes:
      timestamp:
        range: datetime
        required: true
      role:
        range: string
        required: true

  MeasurementFrame:
    attributes:
      frame_id:
        identifier: true
        range: string
      orientation:
        range: integer
        required: true
      origin_price:
        range: decimal
        required: true
      scale_width:
        range: decimal
        required: true
        minimum_value: 0

  CaseSetSpecification:
    description: >
      The rule defining membership of a historical set. This is not
      interchangeable with the realized member list.
    attributes:
      case_set_id:
        identifier: true
        range: string
      defined_at:
        range: TemporalBoundary
        required: true
      membership_rule_version:
        range: string
        required: true
      knowledge_cut:
        range: TemporalBoundary
      outcome_independent_membership:
        range: boolean
        required: true

  OutcomeSpecification:
    description: >
      Defines what one historical case contributes to an analysis.
    attributes:
      outcome_id:
        identifier: true
        range: string
      event_predicate:
        range: string
        required: true
      horizon:
        range: TemporalBoundary
        required: true
      knowledge_mode:
        range: KnowledgeMode
        required: true
      alignment:
        range: AlignmentMode

  EstimandSpecification:
    description: >
      The statistical quantity intended by a research question,
      before choosing an estimator.
    attributes:
      estimand_id:
        identifier: true
        range: string
      question:
        range: string
        required: true
      target_case_set:
        range: CaseSetSpecification
        required: true
      outcome:
        range: OutcomeSpecification
        required: true
      summary_measure:
        range: string
        required: true

  Estimate:
    attributes:
      estimate_id:
        identifier: true
        range: string
      estimates:
        range: EstimandSpecification
        required: true
      estimator_version:
        range: string
        required: true
      value:
        range: decimal
      numerator_count:
        range: integer
      denominator_count:
        range: integer
      unknown_count:
        range: integer
      generated_from_snapshot:
        range: string
        required: true

  DisplayClaim:
    attributes:
      claim_id:
        identifier: true
        range: string
      supported_by:
        range: Estimate
        required: true
      claim_kind:
        range: ClaimKind
        required: true
      text:
        range: string
        required: true
      does_not_support:
        range: string
        multivalued: true
```

This POC is intentionally missing `R`, `X`, `cluster`, `zone`, and trading-policy classes. That is a feature. It tests the deeper distinctions first.

LinkML can ensure, for example, that an `Estimate` references an `EstimandSpecification`, that the estimand names a case-set and outcome, and that the outcome has a horizon. Its generated JSON Schema/Pydantic artifacts can enforce much of that structural contract. LinkML’s generator ecosystem is explicitly designed to compile a source model into such downstream artifacts. citeturn3search0turn3search1

It still cannot prove that:

- `event_predicate` was actually executed as written;
- no post-cut candle entered `CaseSetSpecification`;
- `denominator_count` equals the correct realized membership;
- the final endpoint used the declared horizon;
- a displayed predictive claim was validated out of sample;
- `outcome_independent_membership: true` is truthful.

Those belong in executable semantic validators.

The recommended enforcement architecture is therefore:

| Responsibility | Primary mechanism |
|---|---|
| Concept names, stable IDs, relationships, cardinality, enums | **LinkML** |
| JSON/API shape | **Generated JSON Schema / Pydantic** |
| Documentation and agent-readable structural contract | **Generated LinkML docs + authored semantic definitions** |
| RDF interoperability if needed | **JSON-LD/RDF generation** |
| Transformation lineage | **Project provenance model; optionally PROV-O** citeturn6search2 |
| Complex RDF graph constraints if graph layer adopted | **SHACL** citeturn7search0 |
| No-leakage, frozen membership, horizon consistency | **Runtime semantic validators + property tests** |
| Statistical assumptions, calibration, OOS validation | **Research/validation code** |
| Claim qualification | **Claim compiler/validator + tests** |
| Concept changes and operator authority | **Versioned decision provenance** |
| Whether an output belongs in a trading policy | **Explicit operator/policy decision** |

The first implementation artifact should therefore not be a giant ontology. It should be a **Semantic Passport** object that every new statistic must instantiate *before its calculation is accepted*. At minimum it should identify the question, semantic version, knowledge cut, time alignment, measurement frame, horizon, case-set rule, outcome specification, estimator, denominator policy, unknown policy, intended claim type, and prohibited interpretations.

Only after that passport validates structurally should runtime code be allowed to compute the number. Only after executable invariants pass should the UI be allowed to publish its human claim.

## Open decisions and final synthesis

Only a small number of issues remain genuinely open after the reconstruction.

| Decision | Option A | Option B | Evidence and consequence | Recommendation | Confidence |
|---|---|---|---|---|---|
| **Whether final R/X identity is always tied to the strategy block end or may support first-class alternative horizons** | Canonical strategy R/X always use fixed block end; other horizons get different outcome types | `FinalExtreme` is generic and horizon parameter is part of its identity | Current design 24 fixes the own post-activation block horizon; research naturally creates shorter horizons. Treating all as “R” risks silent comparisons. fileciteturn39file0L2-L2 | Keep canonical DR-Lab R/X names for the strategy horizon; represent other horizons as separately identified projections | HIGH |
| **Whether clock-aligned and event-age-aligned state comparison belong under one generic matcher abstraction** | One matcher type with explicit alignment mode | Distinct semantic types | They answer different conditioning questions, but share machinery | One abstract `StateComparisonSpecification`, mandatory alignment mode, and distinct estimand IDs | HIGH |
| **Whether semantic instances need an RDF graph layer immediately** | LinkML/JSON/Pydantic + provenance records only | LinkML + RDF/PROV-O/SHACL from the start | Current need is correctness of computation-to-claim; graph reasoning is not yet a demonstrated bottleneck | Defer mandatory RDF; preserve stable identifiers/mappings so graph projection remains available | HIGH |
| **Whether “cluster” should remain a user-facing umbrella term** | Keep it as UI-language umbrella with explicit subtype/passport | Remove the term and expose only event-specific zones/densities | Operator visually reasons in clusters/constellations, but repository history shows the word repeatedly hid observation-unit changes | Keep only as a presentation/category term; no bare computational `Cluster` without event semantics | MEDIUM |
| **How much of later M7/QuantX semantics should become canonical `PRIMARY_STRATEGY_SOURCE`** | Accept repository subtitle reconstruction as primary-equivalent | Keep it as repository-derived strategy reconstruction until specific first-party artifacts are attached | Public TheMas7er DR/IDR V1 verifies the basic skeleton, but not every later reconstructed QuantX detail in this audit. citeturn2search0 fileciteturn37file0L2-L2 | Preserve per-claim source provenance; upgrade only when corresponding first-party artifact is linked | MEDIUM |

Several apparently open questions are **not** open enough to deserve the ledger.

It is no longer defensible to treat unknown as false; the code, tests and statistical semantics all contradict that. fileciteturn40file0L2-L2

It is no longer defensible to collapse reachability and historical event timing; the repository found and corrected that exact error. fileciteturn33file0L2-L2

It is no longer defensible to make dynamic path matching silently redefine the frozen base family; NOW itself now demonstrates the correct separation. fileciteturn34file0L2-L2

It is no longer defensible to infer a trade setup from a dense endpoint zone. The current zone implementation and exploratory null diagnostics do not license that transition. fileciteturn31file0L2-L2

The recommended implementation sequence follows directly from these findings rather than from LinkML enthusiasm:

**First, freeze a technology-neutral semantic specification.** Define the kernel objects above and give current design-24 outputs semantic passports. Do not begin by converting current Python dictionaries into LinkML classes.

**Second, build executable semantic invariants around current behavior.** Existing `sem24.py` and `now24.py` already provide a strong foundation. Add adversarial tests specifically for denominator identity, horizon mismatch, knowledge-time/event-time confusion, endpoint-versus-visit substitution, clock-versus-age alignment, claim-classification changes, and provenance/version mismatch. fileciteturn39file0L2-L2 fileciteturn40file0L2-L2

**Third, introduce the small LinkML contract represented by the POC.** Generate Pydantic/JSON Schema and documentation from it, and make backend result objects reference semantic-passport identifiers rather than embedding unversioned prose. LinkML’s current tooling supports precisely this multi-artifact schema workflow. citeturn3search0turn4search1

**Fourth, make claims first-class.** A backend should not send `{value: 0.081}` to the UI. It should send, conceptually, `{estimate, estimand_id, support, claim_kind, semantic_version, provenance}`. The UI should not invent whether that means “historical share,” “chance today,” or “reversal probability.”

**Fifth, add provenance across transformations.** At minimum, store hashes/IDs for source snapshot, semantic specification, membership rule, event specification, estimator and implementation version. PROV-O is a reasonable future interoperability mapping because its Entity–Activity–generation/use model directly represents derived artifacts and transformation chains. citeturn6search2

**Sixth, only then decide whether RDF/SHACL/OWL provide enough additional value to justify their complexity.** LinkML deliberately acts as a bridge to these representations rather than requiring them. citeturn3search0turn3search10

The deeper answer to “What is DR Lab as a system of knowledge production?” is:

> **DR Lab is best understood as a strategy-indexed historical trajectory query and conditional-state research system, with a descriptive endpoint-analysis subsystem and an emerging validated decision-support boundary.**

It is not merely a DR/IDR strategy implementation, because a large fraction of its objects—families, endpoint distributions, zones, path fields, historical comparisons, NOW matchers, estimators and validation passports—are research constructs built *about* the strategy.

It is not merely a historical query engine, because its strategy semantics determine which events and coordinate systems exist.

It is not yet, in the strong semantic sense, a trading system, because descriptive and conditional research objects do not themselves specify entries, stops, targets, position size, execution, transaction costs or expected utility.

It is not fundamentally a “cluster system,” because clusters are only one lossy aggregation of more primary historical events/trajectories.

And it is not fundamentally an ontology, because its core activity is a chain of observation, interpretation, measurement, projection, population formation, estimation and claim production.

The final question from the brief can therefore be answered directly.

> **If all UI, backend code and historical class names were deleted, what would have to be reconstructed so that the rebuilt system answered the same real trader questions without changing their meaning between market and percentage?**

It would have to recover:

**what was observed; when and under which clock/reference system it was observed; which observations were unavailable; which DR/IDR rule/version transformed those observations into a strategy state; what event activated the analysis; what coordinate frame made prices comparable; what was honestly knowable at each cut; what horizon defines each retrospective outcome; what one historical case contributes to the question; how the historical population is formed without future leakage; whether comparison is by common clock or event age; whether the outcome is a visit, first arrival, trajectory state, swing or endpoint; how unknowns are treated; what exact population and event define numerator and denominator; what estimand is intended; what estimator produced the number; what support and validation justify it; what human claim the evidence permits; what neighboring claims it does not permit; and which source, semantic version and transformation chain generated it.**

Everything else—including `R`, `X`, “family,” “zone,” “cluster,” the exact screen design, and ultimately LinkML itself—is downstream of those obligations.

That is the minimal semantic architecture.

LinkML fits **after** that reconstruction as a versioned, machine-readable semantic-contract language: strong enough to name and connect the distinctions, generate implementation/documentation artifacts, and reject many malformed objects; deliberately not strong enough to certify that history was selected honestly, that a statistical estimand was appropriate, that a predictor generalizes, that a causal interpretation is warranted, or that a trader should act. LinkML’s own specification and toolchain make that division of responsibility natural rather than a limitation to hide. citeturn5search12turn4search1turn3search2