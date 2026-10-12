# From Semantic Truth to Perceptual Entitlement: A Human-Factors Architecture for DR/IDR Lab

## Research finding and reconstruction of the actual DR Lab

The central result is that **“Visual Semantic Architecture” is too narrow if it is interpreted as a mapping from backend meaning to visual properties, and “attention allocation” is too weak as the governing theory**. The missing layer is better understood as a **Semantic–Work–Perceptual Contract**: a contract that determines which distinctions the operator must be able to make, under which temporal and epistemic conditions, before it determines how those distinctions are rendered.

The strongest trace is therefore not:

> semantic importance → visual importance

and not even:

> system state → attention priority → salience

but:

> **what the system can validly assert**  
> → **what distinction or relation the operator must maintain, detect, compare, or recover**  
> → **under what time pressure and error consequence**  
> → **what perceptual job the interface must support**  
> → **what presentation role that job requires**  
> → **which perceptual channels can perform that role without implying a stronger claim**  
> → **what empirical test would falsify the design choice**

This conclusion comes from the conjunction of three things: the actual semantics already enforced by DR-LAB-SC-1.1; the operator-work structure evident in screen 24; and human-factors evidence showing that attention capture, adaptation, spatial rearrangement, and “more salient = better” are not generally valid optimization principles. The empirical literature contains direct counterexamples: an interface that focused operators on the most critical cases improved those cases but degraded performance on other important cases; user-controlled attention was better in those less-critical cases. citeturn15search7turn15search9 Abrupt changes can capture attention, but capture is neither perfectly automatic nor equivalent to task relevance. citeturn16search0turn16search2 Stable spatial context can itself become a learned cue that accelerates search. citeturn14search11

### The system ontology is already unusually strong

DR-LAB-SC-1.1 is not merely a data schema. It separates ten semantic responsibility layers: observation, strategy, measurement, epistemic state, historical case model, projection/outcome, statistical target, estimate/evidence, claim, and policy. It also makes provenance, identity, dependencies, invariants, and forbidden transformations part of an object's semantic passport. fileciteturn1file0

That matters because the contract already rejects several transformations that a visually persuasive UI could accidentally reintroduce. A C0 descriptive claim concerns measured historical records without transfer to an unknown target session; a predictive C2 requires a specific future target, cut, estimand, model or rule, training cutoff, issuance before the outcome, validation, baseline, and failure conditions. Changing language is explicitly insufficient to promote C0/C1 to C2. fileciteturn1file3 fileciteturn1file4

The machine layer is also substantive rather than ceremonial. Screen-24 routes are assigned explicit SC-1.1 profiles, and numeric fields are registered against semantic targets. The runtime family and NOW surfaces carry contract envelopes, while legacy surfaces are explicitly quarantined as outside SC-1.1. fileciteturn12file0 The architecture documentation states that the server re-derives family snapshots, zones, current statuses, and NOW numbers before publication; failed objects can be withheld, and a stale contract suppresses statistics while still permitting candle observations. fileciteturn11file0

This gives the visual architecture a much better starting point than “here is a database ontology; make it intuitive.” The backend already says **what a statement is allowed to mean**. What it does not yet say is **what human discrimination that statement must support, when it deserves persistent screen occupancy, or what graphical implication would exceed its claim class**.

### The actual screen is a multi-timescale cognitive instrument

Screen 24 is the working screen in `main`; its specification explicitly treats the graph, price columns, and time band as projections of a common price-cell × 15-minute-event structure. fileciteturn2file0 fileciteturn8file0 It therefore already has more structural coherence than a conventional “dashboard of widgets.”

Its important semantic objects do not all live on the same clock:

| System object | Actual semantic behavior | Operator-work implication | Initial perceptual classification |
|---|---|---|---|
| **Family / BASE snapshot** | Family and `N_base` are fixed at confirmation, or a distinct family is created at break; moving the cut does not rewrite the original snapshot. fileciteturn2file0 fileciteturn5file0 | Establishes the reference population against which many simultaneous comparisons make sense. | Stable scaffold |
| **Confirmation / break** | Confirmation creates the main family; break is a genuine regime transition and can create a separate break family with another orientation and N. fileciteturn10file0 | Operator must notice a change in what coordinate system and family are being inspected. | Transition event plus persistent mode state |
| **Final R / X distributions** | One final R and X per historical member over the declared horizon; BASE is historical C0. fileciteturn1file5 | Provides historical geometry/context, not a current-session prediction. | Persistent contextual distribution |
| **Zone map** | Zone membership is exact `cell_mask`; cloud contours are drawings, not semantic boundaries. fileciteturn2file0 | Enables simultaneous spatial/temporal comparison of historical concentrations. | Stable relational structure |
| **Zone reachability** | HOLDS/POSSIBLE/IMPOSSIBLE describes today's logical relationship to an outcome region, not probability. fileciteturn5file0 | Operator must discriminate current feasibility from historical frequency. | Dynamic state on a stable object |
| **History clock** | Divides historical event occurrence relative to the common cut; past historical events remain members of the same BASE distribution. fileciteturn1file5 fileciteturn5file0 | Supports “what historically had already happened by this market time?” | Dynamic temporal relation |
| **NOW** | Recomputed at each closed M5 and describes residual movement after an observable-state cut among eligible or matched historical cases; it does not rewrite BASE. fileciteturn5file0 | Supports a different question from BASE and must remain perceptually distinguishable from it. | Fixed presentation location, dynamic contents |
| **Current price path** | Closed M5s determine current DR/IDR state, confirmation, break, extrema, cut, and reachability. fileciteturn6file0 | Primary object for orientation in the live dynamic state. | Foreground scaffold |
| **Unknown / no-period** | Unknown cases remain in denominators and cannot silently become zero or be redistributed into known cells. fileciteturn2file0 | Required to read evidence mass correctly. | Persistent epistemic information where relevant |
| **Support / provenance / passports** | Numbers are tied to their estimand, counts, N, horizon and claim form; contract failures can remove the number. fileciteturn3file0 | Needed for trust calibration and forensic verification, not necessarily continuous detailed reading. | Compact persistent status + on-demand detail |
| **Inspector / member paths** | Detailed explanation is obtained through fixed inspector and selections. fileciteturn7file0 | Supports sequential diagnosis rather than simultaneous monitoring. | On-demand evidence |

This already shows why a scalar “visual priority” is the wrong primitive. BASE may be highly important yet should often **not change visually**. A contract violation may describe no market opportunity at all yet deserves greater immediate salience than a historically dense zone because it invalidates the epistemic right to display numbers. NOW may update every M5 but should not therefore occupy more area. An unknown mass may be operationally boring yet indispensable to the interpretation of a denominator. A break may require strong perceptual acknowledgement because it changes the meaning of the coordinate frame, not because it is “more important” than every object on the screen.

### The ontology of work is different from the ontology of the backend

The screen-24 visualization journal records a clear expert reading strategy: the operator first establishes activation and direction, then asks whether retracement has occurred and what R/X relation remains, reads the screen relative to the present and session end, looks first toward the spatial distribution/cluster field and candles, and uses the summary later. The main working mode is after confirmation. fileciteturn4file0

That should not be treated as a specification of what the science “must prove.” It is evidence about **learned work practice**. It establishes that the operator's work ontology contains things that do not correspond one-to-one with backend entities:

**orientation** — What regime am I in? Which family and direction define the current coordinate frame?

**state maintenance** — What has happened already, what is the cut, what remains logically possible?

**simultaneous comparison** — How do present candles relate to multiple historical spatial and temporal distributions?

**change detection** — Did confirmation, break, reachability, data validity, NOW evidence, or contract state just change?

**trust calibration** — Is this a large robust base, a small-support conditional set, an unknown-heavy result, a time-only fallback, or a withheld quantity?

**diagnosis / forensic analysis** — Why is a zone present, why is it unreachable, which members contributed, what denominator and horizon produced the percentage?

Those are work functions, not backend classes. The UI should arise from the intersection of both ontologies, but **the intersection is mediated by task requirements rather than by graphical representation of every semantic object**.

The most important conceptual shift follows:

> **The primary unit of perceptual architecture is usually not an entity. It is a required discrimination.**

“Zone X2” is an entity-like object. But the perceptual requirements may actually be:

- distinguish **historical mass from current reachability**;
- distinguish **BASE from NOW**;
- distinguish **newly changed from merely currently true**;
- distinguish **unknown from zero**;
- distinguish **another family with another N from an updated estimate of the same family**;
- distinguish **descriptive historical frequency from predictive information**.

Once framed this way, a visual element earns perceptual bandwidth only if it makes one of these required distinctions more reliable, faster, more recoverable after interruption, or less liable to semantic misreading.

## What the evidence says about attention, stability, expertise, and graphical inference

The literature does not support a single doctrine such as “drive the gaze to the important thing.” It supports a more conditional view: **salience, stability, structure, interruption, expertise, and task relevance are partially independent variables**.

### Attention capture is a capability, not a goal

Classic experiments show that abrupt onset can obtain processing priority during visual search. citeturn16search0turn16search13 Later work showed important boundary conditions: a strongly focused attentional state can prevent an onset from overriding the observer's intentions, and attentional capture depends on task conditions rather than being a semantic guarantee. citeturn16search2turn16search12

This distinction is crucial. Animation, blinking, pulsing, sudden resizing, or abrupt contrast changes may increase the probability that something is sampled. They do **not** establish that the sampled object deserved interruption, that the operator will interpret it correctly, or that other important states will remain represented.

The direct operator-interface evidence is even more important. Adelman and colleagues experimentally compared real-time expert-system interfaces. Focusing the operator's attention where the system judged it most needed did help critical cases, but the same strategy produced worse performance for less-critical yet important cases; operator-selectable focus did better for those. citeturn15search7turn15search9 This is close to the DR Lab problem: a system that over-optimizes “look here now” can create **attentional tunneling by policy**, even when every cue individually makes sense.

The stronger design principle is therefore:

> **Use attention capture only when failure to interrupt normal scanning is itself the dominant risk. Use attention support for everything else.**

NASA's current human-spaceflight standard is a domain-specific but useful high-consequence precedent rather than a trading prescription: NASA-STD-3001 Volume 2 is an active agency technical standard, and its human-factors requirements reserve the strongest temporal attention devices such as flashing for conditions requiring immediate crew attention/action and require redundant cues for critical color-coded information. citeturn17search5turn17search11 The U.S. NRC similarly treats displays, alarms, automation, workstation design, degraded states, and integration of HSI resources as one human-factors system rather than independent styling questions. citeturn17search0

For DR Lab, the causal principle transfers; the aerospace palette does not.

### Interruption has a recoverable but real cognitive cost

An interruption does not end when the popup disappears. Altmann and Trafton measured more than 13,000 interruptions and found a gradual recovery over roughly the first ten post-interruption responses, about 15 seconds in their task. citeturn18search1 Even interruptions lasting only a few seconds have been shown to multiply sequence errors in procedural tasks. citeturn18search16 Context matters during recovery: changing visual retrieval cues after interruption impairs resumption, whereas preserved contextual cues assist it. citeturn18search12

This creates a very strong argument against a constantly reflowing “smart” trading UI. Dynamic rearrangement consumes not only visual attention but also **resumption context**. A cue that moves a panel, expands a block, swaps columns, changes coordinate frames silently, or replaces surrounding context may be costly even if the updated arrangement is locally “better.”

### Stable spatial organization has instrumental value

Repeated spatial configurations can become implicit retrieval cues. Chun and Jiang showed that targets embedded in learned recurring spatial configurations were found faster even when participants could not explicitly recognize those configurations. citeturn14search11 The effect is not an unconditional law; later replication work found dependence on search strategy, which is exactly why it should be treated as a reason to preserve useful learned context rather than as a mandate for frozen screens. citeturn14search4

The implication for an expert operator is stronger than for a novice dashboard user. The current screen is not a blank slate. The repository documents repeated operator-driven tuning of right-edge anchoring, vertical range, candle size, time-band height, line placement, constellation size, labels, hover linkage, and inspector behavior. fileciteturn4file0 Those choices have accumulated **interaction history**. Some may be theoretically suboptimal, but moving them imposes a real relearning cost that must be measured rather than ignored.

### Expertise changes scanning but does not abolish perceptual limits

Professional pilots show different scan structure from novices; simulator studies report differences in dwell behavior, distribution of attention, and transitions among instruments as a function of expertise and operating condition. citeturn14search0turn14search5 This supports treating learned expert scan patterns as real system state, not merely “user preference.”

But expertise is not immunity from inattentional blindness. In the well-known radiology experiment by Drew, Võ, and Wolfe, expert observers engaged in a demanding visual search could miss an unexpected highly visible object. citeturn14search3 The general inattentional-blindness phenomenon is well established in dynamic tasks requiring sustained selective attention. citeturn18search7

Therefore personalization should be partitioned into four classes:

| Layer | What should dominate |
|---|---|
| Human perceptual constraints | Non-negotiable baseline: visibility, contrast, peripheral limitations, interruption effects |
| Domain expertise | May determine what relations deserve simultaneous access and how normal scan is organized |
| Individual habit | Valuable when it reduces search/reorientation cost, but not automatically normative |
| Empirically validated personal adaptation | Strongest basis for user-specific departures from generic design |

This argues for **stable personalization and adaptable controls** more strongly than autonomous adaptive rearrangement. In a controlled menu study, static menus were faster than system-adaptive menus, and user-adaptable menus beat adaptive menus under some conditions; most participants preferred the adaptable condition. citeturn15search0 The study is not a trading-display experiment, so its layout solution does not transfer directly, but its causal lesson is relevant: prediction of user needs does not erase the cost of surprising the user's learned access path.

### Change can be missed even when it is visually large

Change blindness and inattentional blindness are separate reasons not to assume that “the interface changed, therefore the operator saw it.” Large scene changes can remain undetected when visual transients are disrupted or attention is allocated elsewhere. citeturn18search15turn18search9 Conversely, unrelated transients can themselves interfere with change localization or identification. citeturn18search6

This suggests an architectural distinction that is more useful than “dynamic/static”:

**state representation** answers “what is true now?”  
**transition representation** answers “what became true since the operator's prior opportunity to observe it?”

A changed color may successfully encode the first while failing at the second. A brief cue may successfully signal the transition but fail to leave a recoverable state after it disappears. A good dynamic operator interface often needs **both**: a transient transition cue plus a stable resulting state.

### Alarm reliability and false positives matter as much as conspicuity

Alarm response is affected by reliability. Empirical alarm research has shown that operator response changes with alarm reliability and contextual alarm conditions. citeturn18search2turn18search10 Sheridan and Parasuraman formalized failure detection as an expected-value problem requiring miss probabilities, false-alarm probabilities, consequences, benefits, and prior failure probability rather than simply “maximize detection.” citeturn19search1

That is directly relevant to DR Lab's interrupt policy. A high historical R/X frequency is not an alarm condition. A newly impossible zone is not automatically an alarm condition. A low-support NOW estimate is not automatically an alarm. By contrast, a contract failure that causes the system to withdraw the semantic warrant for a number is a credible candidate for interruption because continuing to reason from the number is a qualitatively different failure mode.

### Visual encodings change inference, not merely appearance

Uncertainty-visualization research is especially important to the C0/C1 → perceived-C2 problem. Experimental work shows that alternative visual representations change what people remember and infer about uncertain processes; graphical prediction and discrete outcomes can materially alter reasoning about uncertainty. citeturn16search1 The consequence is broader than uncertainty: **presentation is part of the inferential system**.

This is the key scientific basis for treating graphical form as potentially claim-bearing. A visualization can be textually correct and still systematically induce an interpretation that the semantic layer did not license.

### Peripheral and physical geometry matter

A CSS pixel is not a perceptual unit. For a rendered feature of physical size \(s\) viewed at distance \(d\), its visual angle is approximately:

\[
\theta = 2\arctan\left(\frac{s}{2d}\right).
\]

Thus identical pixel geometry can have different perceptual consequences on a laptop, a large high-DPI monitor, or the same monitor viewed from a different distance.

Visual sensitivity changes with retinal eccentricity. Experiments show falling contrast sensitivity and color resolution toward the periphery, with chromatic resolution degrading particularly strongly. citeturn16search7turn16search8 Peripheral chromatic detectability also depends on color direction and stimulus geometry. citeturn16search4 Therefore an architecture that intends something to function as an **ambient peripheral status** cannot validate it only by checking RGB values or CSS contrast in the foveal center.

For DR Lab, future physical validation should record at minimum monitor dimensions, pixel resolution, UI scaling, nominal viewing distance, and ambient-light condition. The architecture should specify task-dependent **minimum effective visual angle / contrast**, not universal pixel dimensions.

## Competing architectures and the stronger synthesis

I considered four genuinely different architectures rather than treating the brief's initial “visual priority” idea as the answer.

| Candidate | Governing idea | What it explains well | Where it fails |
|---|---|---|---|
| **Salience allocator** | Assign each information object a changing priority, then allocate area/contrast/motion accordingly | Fast detection of sparse urgent events; straightforward implementation | Encourages pseudo-precise scores, visual instability, salience bias, over-alerting and C0/C1→C2 leakage; poorly handles stable context |
| **Ecological / constraint representation** | Represent the invariant structure and constraints of the work domain so operators can perceive meaningful relations directly | Novel situations, diagnosis, relationship perception, support across multiple cognitive modes | Does not by itself decide when a newly changed state deserves transient attention; difficult for intentional/statistical rather than purely causal domains |
| **Transition-centric stable scaffold** | Keep topology stable; represent transitions locally and transiently while leaving the resulting state persistent | Spatial memory, interruption recovery, temporal continuity, state-change detection | Can under-signal rare high-consequence events without an explicit interrupt policy |
| **Adaptive / personalized workspace** | Dynamically select/rearrange content according to user and system state | Potential clutter reduction; individualized access patterns | Surprise/relearning, automation opacity, unstable scanning, maintenance complexity; adaptation prediction may be wrong |

Ecological Interface Design is a substantially stronger starting point than a salience allocator because it asks the display to support the underlying work structure and multiple modes of cognitive control rather than merely highlight values. Vicente and Rasmussen's original formulation explicitly sought interfaces that support skill-, rule-, and knowledge-based control without forcing operators to a more cognitively demanding level than the task requires. citeturn15search3turn15search15

But pure EID is not sufficient for DR Lab. The domain contains statistical/historical claims, epistemic states, changing cuts, conditional comparisons, withheld evidence, and legally important distinctions between descriptive and predictive semantics. Those do not map neatly onto a physical process-control constraint hierarchy. The literature itself recognizes that applying ecological approaches to intentional decision domains is less straightforward than application to physically coupled process domains. citeturn15search17

A pure transition architecture is also insufficient: it can tell us that “something changed” without establishing which persistent structural relationships must remain visible for interpretation. A pure adaptive architecture is the weakest default because its principal benefit—conditional simplification—comes with surprise and spatial-memory costs, and system-controlled adaptation has no general empirical superiority. citeturn15search0

The strongest architecture for DR Lab is therefore a **conservative hybrid**:

> **Stable relational scaffold + local state encoding + transient transition cues + narrowly gated interruption + on-demand evidence, all behind a claim-semantics firewall.**

I will call this the **Perceptual Entitlement Architecture** inside the broader **Semantic–Work–Perceptual Contract**.

“Entitlement” is useful because it asks a harder question than importance:

> Why does this information have the right to consume this perceptual resource, in this state, for this operator task?

That right is not permanent and is not proportional to semantic significance.

### The entitlement decision is categorical, not a fake mathematical score

A universal formula such as

\[
priority = importance \times urgency \times uncertainty \times …
\]

would create unjustified precision. None of the evidence supports stable cross-context numeric weights for variables this heterogeneous.

Instead, an object or transition receives one of a small number of **presentation roles**:

| Role | Entitlement condition |
|---|---|
| **Scaffold** | Removing persistent visibility would materially impair orientation, coordinate interpretation, simultaneous comparison, or reacquisition of the task state |
| **Ambient state** | Status needs ongoing awareness but does not justify interruption; it should be detectable during normal scan |
| **Transient transition cue** | A meaningful state changed and timely detection is useful, but delayed detection remains recoverable |
| **Interruptive alert** | Missing the state before a short operational deadline creates large loss, ordinary scan may miss it, the detector is sufficiently reliable, and there is a meaningful response |
| **On-demand evidence** | Information is explanatory, diagnostic, provenance-related, or infrequently compared and sequential access has acceptable cost |
| **Withheld / unavailable** | The system lacks the semantic or evidential right to display the value at all |

This immediately overturns several intuitive hypotheses from the brief.

**Importance does not imply brightness.** Persistent structural information can be important precisely because it is stable and visually quiet.

**Dynamism does not imply salience.** NOW can recompute every M5 yet remain in a stable place without motion.

**Low frequency of access does not imply hiding.** A rarely read contract-validity indicator may need persistent visibility because the cost of silently missing invalid evidence is high.

**High historical frequency does not imply foreground.** A dense historical zone is semantically C0 and may deserve accurate quantitative encoding without any alert-like treatment.

**Large area does not imply importance.** A chart may deserve area because simultaneous spatial comparison and readable temporal geometry require it, while an extremely important contract-validity fact may fit in a small but reliably detectable status location.

**State-dependent UI does not imply state-dependent layout.** The best state adaptation often changes content or local state inside fixed anchors rather than rearranging the workspace.

### Screen real estate should be justified by comparison geometry

Area is best understood as a resource for **perceptual computation**, not a reward for importance.

An element has a stronger case for always-on area when the operator repeatedly needs to compare it simultaneously with another object, when re-acquisition would be expensive, when the spatial relation itself carries meaning, or when sufficient physical size is required for visual discrimination. Conversely, detailed provenance, individual member history, or infrequently used diagnostics can usually be inspector-based when sequential access does not damage the task.

This explains why candles and historical spatial distributions can legitimately occupy far more screen area than a critical integrity warning without claiming they are “more important.”

It also explains an existing screen-24 decision that is probably sound: the bottom time band was reduced because it had consumed about a third of the screen and impaired candle readability, while it still retained enough room to represent the temporal projection. fileciteturn4file0 That is a trade between simultaneous perceptual computations, not an “importance ranking.”

## The Semantic–Work–Perceptual Contract

The new intermediate artifact should not be a second semantic ontology and should not be a pixel specification. SC-1.1 already owns semantic truth. The missing artifact should consume SC-1.1 and add work/perceptual obligations.

I recommend a **Semantic–Work–Perceptual Contract (SWPC)**.

Its basic record would conceptually contain:

| Field | Function |
|---|---|
| `semantic_ref` | Exact SC-1.1 object/estimand/claim bundle |
| `claim_class` | fact / C0 / C1 / C2 / C3 |
| `knowledge_cut` | Time to which the object is epistemically valid |
| `operator_task` | orientation, monitor, compare, detect, diagnose, verify, forensic |
| `required_discrimination` | The state/relation the operator must distinguish |
| `comparison_set` | Objects that must be compared simultaneously |
| `failure_modes` | Likely omission or misinterpretation |
| `consequence_class` | Consequence of miss or false reading |
| `deadline` | Whether useful detection is immediate, bounded, or leisurely |
| `recoverability` | Can the operator recover later without material loss? |
| `presentation_role` | scaffold / ambient / transition / interrupt / on-demand / withheld |
| `spatial_anchor` | Stable region or relation to another object |
| `allowed_channels` | Permissible visual dimensions |
| `forbidden_encodings` | Channels that would imply unsupported semantics |
| `persistence_policy` | Stable, transient with decay, state-latched, on-demand |
| `salience_reason` | What fact licenses any elevated salience |
| `misread_hazards` | Especially C0/C1→C2/C3 |
| `validation_tests` | Human and machine tests required before acceptance |
| `personalization_scope` | What the individual operator may change without changing visual semantics |

This is deliberately categorical. The contract should be small enough to protect invariants, not become an ontology of CSS.

### Presentation primitives should be treated as channels with liabilities

There is no universal one-to-one mapping such as “hue = category; opacity = uncertainty; luminance = priority.” The correct mapping depends on the perceptual task, peripheral/foveal role, co-occurring channels, and likely inference.

The following is the defensible starting policy:

| Channel | Strongest justified roles | Main liabilities in DR Lab |
|---|---|---|
| **Position** | Quantitative coordinates; stable identity; structural relationships | Moving an item to express temporary priority destroys spatial context and can imply changed semantics |
| **Area** | Space for simultaneous comparison, interaction or complex shape | Weak basis for abstract importance; large visual footprint produces salience regardless of intent |
| **Size** | Coarse ordered difference; legibility | Strong “importance/strength” connotation; resizing shifts surrounding layout |
| **Luminance / contrast** | Availability, focus, detection, foreground/background separation | Powerful attention effect; can turn descriptive magnitude into apparent urgency |
| **Hue** | Stable low-cardinality categories such as R/X, provided redundancy | Peripheral color discrimination is weaker; color-vision differences; hue alone is unsuitable for critical state. citeturn16search3turn16search8 |
| **Saturation** | Quiet categorical emphasis/de-emphasis | Poor primary quantitative scale; often conflated with “strength” |
| **Opacity** | Background/context, inactive/unavailable state with redundant explanation | Easily read as absence, low confidence, or unimportance; dangerous for unknown mass |
| **Motion** | Actual movement, true temporal transition, narrowly justified immediate cue | Strong capture and distraction; can imply direction, agency, impending outcome |
| **Persistence** | Whether a fact remains operationally relevant | A disappearing cue can erase recoverability; excessive persistence creates alarm fatigue |
| **Grouping** | Shared denominator, task bundle, causal/semantic relation | Proximity itself makes viewers infer association; dangerous for different denominators |
| **Layering** | Separate current state, history, annotation, evidence | Foreground/background inherently implies hierarchy |
| **Disclosure** | Sequential provenance and forensic detail | Hidden information is unavailable for simultaneous comparison; must not hide critical invalidity |
| **Texture / outline / pattern** | State differences that should not imply numeric ordering | Can become visually noisy; requires testing at actual viewing scale |

This policy is particularly important for the existing adjacent R/X encodings. Screen 24 deliberately puts R and X together while maintaining separate semantics and denominators. The specification itself warns that adjacent R/X percentages do not form one 100% partition. fileciteturn3file0 The architecture should therefore treat **perceptual grouping as semantic pressure**: if two adjacent marks look like parts of one bar, explanatory text may not fully undo that inference.

### “Visual claim” should become a first-class audit concept

I recommend defining a **visual claim** operationally:

> A visual claim is an interpretation about the system, evidence, future, or action that the intended operator reliably infers from the graphical encoding, whether or not the literal text states it.

This is intentionally behavioral. It avoids metaphysical debates about whether a color “really means” probability. The question is empirical: does the intended expert operator systematically read it that way?

The C0/C1 firewall should then obey four rules.

**Graphical magnitude may encode the magnitude of the historical quantity actually being shown.** A bar length corresponding to `n/N` is not inherently predictive when its scope is legible and the context does not convert it into an apparent target.

**Alert-like semantics must never be driven solely by C0/C1 historical frequency.** Pulsing, blinking, directional motion, sudden enlargement, glow, or alert palettes tied to “high historical frequency” strongly risk turning “frequent in this historical set” into “important probable destination now.”

**Current-state salience must be licensed by a current-state fact.** A zone can be visibly changed because its reachability changed; that cue should identify the **transition in reachability**, not make its historical frequency look more predictive.

**A C2 or C3 future must receive a new grammar rather than merely a more intense version of C0/C1.** If DR Lab later validates a predictive model, the presentation contract should require an explicit target, issuance cut, model/validation identity, calibration/support, expiry, and abstention state before predictive encoding is allowed. C3 additionally requires a policy and objective; SC-1.1 already makes decision claims separate from predictive claims. fileciteturn1file4

The current NOW wording demonstrates why this matters. The screen-24 panel was explicitly changed from future-sounding language to formulations such as “in history, R later deepened…” because the current object is historical/conditional rather than a licensed prediction about today. fileciteturn7file0 The same discipline must apply to graphics.

### Attention support and attention capture become separate contracts

**Attention support** improves the probability that ordinary expert scanning finds the right state when it is sought or naturally becomes relevant. Stable grouping, readable contrast, linked highlighting, fixed inspectors, consistent anchors, and subtle local change markers belong here.

**Attention capture** attempts to interrupt the current scan. Abrupt onset and related transients demonstrably can obtain processing priority. citeturn16search0turn16search13 Because interruptions have measurable recovery costs, this is a scarce intervention, not a general interface virtue. citeturn18search1turn18search16

A DR Lab event should be interruptive only when all of the following are true in the validated workflow:

the state has a short useful response window; missing it has materially high cost; normal expert scan is demonstrably insufficient; false alarms are acceptably rare/costed; and there is an intelligible operator response.

Under the current semantic contract, **contract invalidity/data invalidity is a much stronger candidate for interruption than a historically dense price zone**.

## Applying the architecture to Screen 24 across real states

The current screen is neither an error to be replaced nor a sacred endpoint. Several of its existing decisions are already remarkably consistent with the proposed architecture; others expose exactly the C0/C1 perceptual risk the new layer should test.

### What screen 24 already gets right

**BASE and NOW are semantically non-destructive.** BASE remains frozen while NOW answers a different cut-dependent question. NOW explicitly does not delete “past” historical sessions or rewrite BASE percentages. fileciteturn5file0 This is excellent temporal architecture. The visual layer should preserve it rather than pursuing a continuously morphing “most current truth.”

**Historical mass and reachability are partly separated.** When a zone becomes impossible today, its historical percentage retains the size corresponding to its historical share while status is expressed separately through dimming/trace treatment. This behavior was deliberately fixed after earlier coupling of status and percentage size. fileciteturn3file0 That is exactly the right semantic direction: “less reachable now” must not visually rewrite “less common historically.”

**Unknown is not silently normalized away.** Unknown/no-period cases remain in N and are represented separately instead of being redistributed among known spatial cells. fileciteturn2file0 This is essential claim safety.

**Contract failures are epistemically privileged.** A contract violation appears at the top of the panel and invalid numbers are withheld rather than merely decorated with a warning. fileciteturn3file0 This is a superior model to “display the number prominently, add an asterisk.”

**The inspector has a stable home.** The fixed inspector provides a location for hover/pinned explanation rather than spawning moving tooltips over candles. fileciteturn7file0 In light of spatial-memory and interruption-recovery evidence, this is a defensible expert-interface choice. citeturn14search11turn18search12

**The right time edge is anchored.** The visualization journal records that horizontal interactions were deliberately made to preserve the session-end side while changing how much past context is visible. fileciteturn4file0 This is not merely aesthetic; it preserves an important relational invariant in the operator's temporal frame.

**The drawing distinguishes exact semantic geometry from illustrative geometry.** Constellation haze, threads, hill height and glow width are explicitly declared nonnumeric, while zone membership comes from exact cells. fileciteturn2file0 fileciteturn8file0 That is valuable, although declaring a mark “nonnumeric” does not guarantee that a human will not infer strength from it.

### The main unresolved issue is not clutter; it is historical salience on a future-facing chart

Screen 24 uses multiple visual strength channels for historical frequency. Zone-label size rises with historical zone share; price-column saturation/label prominence also rise with share; in-zone points are brighter and larger than residual points; the visualization journal explicitly describes the desired perception of a “strong cluster.” fileciteturn8file0 fileciteturn4file0

Semantically this can be coherent: these are encodings of actual historical mass.

Perceptually it creates a high-risk hypothesis:

> **H-CLAIM:** An expert looking at the current-session chart may interpret the visually strongest historical cluster as the more likely destination of today's future path, even when the literal semantics remain C0/C1.

That is not proven from the repository and should not be declared a defect without an experiment. But it is the single most important claim-safety test because uncertainty-visualization research demonstrates that graphical form can materially change probabilistic inference. citeturn16search1

The correct next action is therefore **not “make clusters less bright.”** It is to test whether current encoding increases a prohibited predictive interpretation relative to a control representation carrying exactly the same historical values.

### Zones versus residual mass deserve an adversarial test

Current zone members can be brighter/larger while residual points are deliberately quieter, even though the specification correctly states that residual mass is still part of the distribution rather than noise. fileciteturn8file0

The design rationale is understandable: zones are algorithmically selected regions and the operator wants to find them.

But the perceptual organization could create a category error:

> zoned historical mass = meaningful/signal  
> residual historical mass = unimportant/noise.

That inference is stronger than the semantic contract.

This should be tested with questions such as:

> “Does the display establish that an event outside the named zones is less plausible today?”  
> “What proportion of the historical distribution is outside zones?”  
> “What does absence of a zone mean?”

A design passes only if faster zone detection does not materially increase false inferential elevation of zones.

### BASE versus NOW is a categorical distinction, not a salience competition

NOW is deliberately a separate estimand family. It describes historical residual outcomes conditional on the common cut and observable state, and the specification insists that path conditioning must beat a time-only baseline before being regarded as adding information. fileciteturn5file0

Therefore the presentation problem is not “make NOW stand out because it is current.” It is:

> **Can the operator reliably distinguish a frozen unconditional historical reference from a cut-dependent conditional historical description without reading explanatory prose?**

A perceptually safe architecture should give BASE and NOW stable categorical identities and positions. Updating NOW may justify a small transition cue; it should not cause BASE to fade, move, resize, or be visually superseded.

This is a case where **dynamic data favors static layout**.

### Confirmation and break justify stronger transitions

A break is not merely one number changing. In the documented break example of December 10, 2025, the default family changes, the denominator changes, the orientation flips, and historical measurements are taken from each member's break rather than confirmation. The original confirmation snapshot remains separately accessible. fileciteturn10file0

This is a genuine change of interpretive frame. It deserves more explicit transition acknowledgement than an ordinary NOW refresh, because silently continuing the old scan model creates semantic risk.

However, the transition should remain **discrete and recoverable**, not a permanent alarm. After acknowledgement, a persistent mode marker and stable new frame are preferable to continued motion or pulsing.

### Early versus late cut should change state, not topology

At an early cut, more event-time space remains ahead and reachability relations differ. At a late cut, many historical final events may lie before the clock cut, but those sessions do not leave BASE. fileciteturn5file0

The architecture should therefore enforce:

**stable BASE geometry and denominator**,  
**a moving cut**,  
**local state treatment for elapsed versus remaining temporal regions**, and  
**explicit NOW/history-clock relations**.

It should forbid the intuitive but semantically wrong visual transformation “remove historical mass that has already happened and visually renormalize what remains.”

### HOLDS / POSSIBLE / IMPOSSIBLE needs a separate channel from historical magnitude

The contract defines today's zone relation as a logical fact with no denominator, while historical zone frequency is C0. fileciteturn1file5

The current screen's separation of font size and status styling is therefore conceptually strong. fileciteturn3file0

The remaining issue is channel independence: if “IMPOSSIBLE” is represented mainly as low opacity, the operator could infer not merely “not reachable for today's final outcome” but “historically unimportant.” That is especially risky when opacity is also used elsewhere for backgrounding.

A future presentation contract should therefore machine-check that **historical magnitude and current reachability do not share the same ordered visual channel**. Human testing must then determine whether the chosen channels remain perceptually separable.

### Unknown and no-period should never be represented as mere absence

The existing invariant is correct: unknown events are not plotted into a price/time location and remain explicit in the totals. fileciteturn3file0

The perceptual extension should be:

> **absence of a mark may not be the only evidence that a state is unknown.**

Otherwise “not known where” and “there was no event there” become visually indistinguishable.

This is one of the strongest candidates for machine-checkable visual semantics.

### Low support is a trust state, not a visual-strength state

The documented break-family example has `N=17`, with no zones meeting minimum support; all known events therefore sit outside zones. The specification correctly warns that this means the family failed the zone-support criterion, not that the market lacks structure. fileciteturn10file0

Low support should therefore modify **evidence interpretation**, not automatically make content tiny, faint, or invisible.

In NOW the support count is already surfaced and validation state is shown. fileciteturn7file0 The architectural test is whether the operator understands “weak evidence / limited support” without reading it as “low historical frequency” or “low probability.”

### Contract violation is the clearest legitimate foreground event

A contract violation is qualitatively different from ordinary market-state change because it revokes publication rights for affected numbers. Current screen 24 already removes the number and displays the violation at the top. fileciteturn3file0

This is one of the few states where stronger foreground treatment is well justified. It should be impossible to hide through ordinary layer controls or personalization.

The distinction is important:

> Contract violation deserves attention because **the display can no longer warrant its own assertion**.  
> A high historical zone does not deserve the same treatment merely because it is statistically prominent.

### Auto-ranging is useful but deserves a stability experiment

The visualization journal says vertical auto-range is recomputed on each closed M5 around candles, the DR box, and reachable/live zones; impossible zones cease to hold the frame. This was introduced to prevent distant historical points from crushing candle readability. fileciteturn4file0

There is a sound work rationale: preserve readable present-price geometry while keeping operationally possible regions visible.

There is also a stability cost: the same price trajectory can shift apparent scale and visual velocity when the y-range changes. The question cannot be settled theoretically.

A direct experiment should compare:

**current auto-range policy** versus **a more hysteretic/sticky range policy**, holding all semantics constant.

Measure present-state reading accuracy, zone-reachability detection, reorientation time after range changes, and operator confidence. The architecture should not prescribe either result before this test.

### Current screen-24 audit in compact form

| Current decision | Assessment |
|---|---|
| Frozen BASE snapshot | **Strongly supported** |
| Separate NOW rather than rewriting BASE | **Strongly supported** |
| Explicit unknown/no-period mass | **Strongly supported** |
| Fixed panel order / inspector location | **Supported by work continuity and spatial-memory evidence** |
| Contract violation withdraws numbers | **Strongly supported** |
| Historical mass and reachability partly separate | **Strong semantic direction** |
| Right-edge temporal anchoring | **Plausibly strong expert-work invariant; retain unless tests contradict** |
| Smaller time band to preserve candle geometry | **Reasonable simultaneous-comparison trade-off** |
| Frequency controls size/brightness/saturation | **Semantically defensible but highest-priority C2-perception test** |
| Zone stars foregrounded, residual dimmed | **Potential “zone = signal” bias; test** |
| Auto-range follows live zones | **Useful but potentially destabilizing; test hysteresis versus current behavior** |
| Past temporal windows dimmed | **Potentially useful current-relevance cue, but test that it does not imply historical mass disappeared** |
| R/X adjacent in one column | **Space-efficient but perceptual denominator/parts-of-whole risk remains** |
| Operator-configurable colors/opacities | **Useful adaptability, but semantic channel identities need guardrails** |

## Machine-checkability, validation, and the cost of changing an expert interface

The SWPC is worth implementing only where it produces enforceable protection. It should **not** try to formally prove human perception.

### What is worth checking automatically

The existing SC-1.1 machinery already demonstrates that semantic publication invariants are practically enforceable. Every screen statistic has a passport, frontend/server counts are checked, and contract-invalid numbers can be withheld. fileciteturn3file0 fileciteturn11file0

A presentation contract can extend that protection with a modest set of invariants:

| Invariant | Machine-checkable interpretation |
|---|---|
| Historical C0/C1 cannot receive predictive grammar | A visual encoding declared `predictive`, directional-target, recommendation, or alert requires an authorized C2/C3 bundle |
| C3 cannot emerge from presentation alone | Action/recommendation components require a PolicySpecification / decision claim |
| Historical magnitude and current reachability use independent channels | Same ordered channel cannot be the sole encoder for both |
| Unknown cannot disappear | When unknown/no-period contributes to the relevant denominator, an explicit accessible representation must exist |
| Withheld evidence cannot masquerade as zero | `WITHHELD` / contract violation maps to an unavailable state, never numeric zero or empty distribution |
| Contract violation cannot be hidden | Integrity status is outside ordinary optional-layer visibility controls |
| Stable anchors stay stable across ordinary cuts | Elements marked as scaffold cannot change region/order on M5 updates |
| True mode changes are explicit | Family/orientation change must emit a mode-transition state |
| Transient cues decay | Every transition-only salience effect has bounded duration or acknowledgement semantics and leaves a persistent resulting state |
| Critical color is redundant | Any safety/integrity state encoded with hue has another discriminable cue; this follows a well-established high-consequence HSI precedent. citeturn17search5turn17search0 |
| Personalization cannot change claim semantics | Operator customization may change permitted presentation parameters but cannot map C0/C1 to a forbidden predictive channel |

The contract should **not** pretend to machine-check whether a cluster “looks predictive,” whether two objects feel grouped, whether the experienced operator's scan has been disrupted, or whether an opacity change produces overconfidence. Those are empirical human questions.

### Validation should use the current interface as the baseline, not an imaginary neutral screen

Screen 24 has accumulated learned operator behavior. The scientifically honest baseline is therefore **current screen 24 after normal familiarization**, not a generic control dashboard.

The validation set should replay real archived scenarios from the repository's own semantic state space:

| Scenario family | Critical discrimination |
|---|---|
| Normal confirmed family, early cut | BASE vs current cut; historical mass vs live path |
| Same family, multiple later cuts | Stable BASE vs changing NOW/reachability/history clock |
| December 10 break case | Original confirmation family vs new break family; changed N/orientation |
| HOLDS → POSSIBLE / POSSIBLE → IMPOSSIBLE | State transition without historical-probability inference |
| Large unknown/no-period mass | Unknown versus zero/absence |
| Low-support / no-zone case | Lack of algorithmic support versus “no structure” |
| NOW time-only baseline versus validated/path-conditioned mode | What conditioning is actually supported |
| History-ahead versus history-exhausted windows | Clock relation without renormalizing BASE |
| Contract violation / stale contract / withheld NOW | Integrity failure versus normal market state |
| C0/C1 high-frequency cluster | Historical magnitude versus perceived prediction |
| R/X adjacent distributions | Independent denominators versus part-to-whole illusion |

The repository itself recommends auditing ordinary families, the December 10 broken session, different ADR/ODR/RDR states, and small-N cases, which makes these scenarios naturally compatible with existing testing practice. fileciteturn3file0

### Primary outcomes must be work outcomes, not eye movements

The principal dependent variables should be:

**state-discrimination accuracy** — Can the operator correctly identify confirmation/break, active family, cut, reachability, unknown state, support state, and contract validity?

**claim-interpretation accuracy** — Can the operator correctly say what a number establishes and does not establish?

**C2/C3 leakage rate** — Given only a C0/C1 display, how often does the operator answer questions as though the screen asserted today's probability, target direction, or recommended action?

**transition detection** — Hit rate, miss rate, false-alarm rate, and latency for transitions that actually require detection.

**task completion** — Accuracy and latency for real operator questions rather than arbitrary symbol identification.

**resumption performance** — Error rate and recovery latency after interruptions.

**confidence calibration** — Does subjective certainty track actual interpretation accuracy?

Signal-detection measures are preferable to raw detection time for transition cues because a system can trivially lower reaction time by making everything alarming while also increasing false positives. The expected-value approach to failure detection explicitly requires false alarms, misses, prior incidence and consequences. citeturn19search1

Eye tracking should be secondary. It is useful for checking whether a supposedly peripheral cue is detected, whether a modification destroys a learned scan route, or whether attention becomes trapped in one region. Expert pilot studies show that scan patterns contain meaningful expertise information. citeturn14search0turn14search5 But fixation is not comprehension, and inattentional-blindness research demonstrates that an observer can look in the relevant area without successfully incorporating the event. citeturn18search9

A better hierarchy is:

> correct interpretation and task result  
> → transition detection and error structure  
> → interruption/recovery cost  
> → confidence calibration  
> → eye movement as diagnostic mechanism.

### Claim safety needs its own controlled experiment

For the existing frequency-driven cluster salience, run a within-operator experiment in which the semantic data are identical but graphical prominence varies.

The key dependent variable is not preference. Present questions such as:

> “According to this display, is price more likely to finish in X2 today?”  
> “Does this display justify choosing X2 as a target?”  
> “What does the 26.1% establish?”  
> “Does making X2 visually stronger change what the system is claiming?”

A representation is safer if historical magnitude remains legible **without increasing false predictive or decision interpretations**.

The operator's expertise makes this test more important, not less. Experts possess learned domain priors and may integrate graphical cues into a richer implicit model. That can be beneficial, but the product must distinguish the operator's personal inference from what DR Lab itself claims.

### Validate peripheral cues at actual physical geometry

For any channel intended to function outside focal inspection, test it at a controlled eccentricity and at the actual or representative monitor/viewing-distance configuration. Peripheral chromatic resolution and contrast sensitivity fall with eccentricity, so “visible when staring at it” is not sufficient evidence for an ambient cue. citeturn16search7turn16search8

The environment profile can remain simple:

`monitor_width_mm`  
`monitor_height_mm`  
`resolution`  
`OS_scale`  
`nominal_view_distance_mm`  
`ambient_condition`

The test harness can convert rendered dimensions into visual angles. This is a legitimate machine-check when the environment profile is known; otherwise the system should refuse to pretend a CSS size has universal perceptual meaning.

### Change cost must be part of acceptance, not a footnote

The correct acceptance criterion for a modification to an expert screen is not:

> new design scores better after five minutes.

It is approximately:

\[
\text{Adoption value}
=
\text{post-learning operational benefit}
-
\text{transition/relearning cost}
-
\text{new semantic risk}
-
\text{maintenance cost}.
\]

This is not proposed as a numeric production formula. It is a causal decomposition of what must be measured.

Repeated spatial structure can facilitate visual search, and interruptions recover faster when contextual cues remain available. citeturn14search11turn18search12 Expert pilot studies further show that scanning structure changes with experience. citeturn14search0turn14search5 Therefore changing an operator's established screen has a real cognitive cost even when the new static screenshot appears cleaner.

A validation study must separate novelty from asymptotic benefit. A credible protocol is:

current screen baseline after normal use →  
variant familiarization →  
post-familiarization scenario trials →  
retention/reacquisition trial after time away.

A redesign is not justified because novices learn it faster if the target user is an expert who already owns a stable scan model.

Changes can be classified qualitatively by migration risk:

**low migration cost:** clearer wording, redundant validity marker, provenance access, a local state cue inside an existing stable anchor;

**moderate cost:** adding a fixed dedicated slot, changing local grouping, changing persistent visual grammar while keeping positions;

**high cost:** moving major regions, changing price/time geometry, reversing established R/X conventions, resizing the workspace dynamically, replacing always-on context with hidden/adaptive content.

High-cost changes require proportionally stronger performance evidence.

### What counts as improvement

A candidate architecture should be accepted only if it reduces meaningful operator error or improves eligible transition detection **without materially increasing** any of the following:

false alarms;  
C0/C1→C2/C3 interpretation;  
interruption/resumption loss;  
state-orientation mistakes;  
confidence miscalibration;  
scan instability after acclimation;  
maintenance or semantic-drift risk.

That is stricter than “faster time-to-detection,” and intentionally so.

## Red-team review and final architecture

The strongest attack on the proposed Semantic–Work–Perceptual Contract is that it could become a sophisticated way to rationalize micromanagement of attention.

That criticism is valid.

A system cannot infer a trader's optimal locus of attention from semantic ontology alone. Attention is partly endogenous, task-set dependent, expertise-dependent, and affected by ongoing strategies. Even strong visual onsets do not always override focused intention. citeturn16search2 Real-time decision-aid research shows that directing attention toward the “most important” cases can damage monitoring elsewhere. citeturn15search7

The architecture must therefore explicitly reject centralized gaze control as its goal.

### Red-team finding: a priority engine would be a likely failure

A dynamic priority score would encourage designers to feed importance, novelty, uncertainty, probability, current state, and actionability into one scalar and then turn the result into brightness, size and motion.

That would fail for DR Lab because:

BASE can be essential but intentionally static;  
unknown can be critical to interpretation but visually non-urgent;  
a contract violation is urgent without being a market signal;  
historical frequency can be large without licensing prediction;  
changing position has a different cognitive cost from changing luminance;  
different operators can have different scan strategies;  
the costs of false capture and missed capture are asymmetric and state-dependent.

**Revision:** the final architecture contains no universal priority score.

### Red-team finding: the architecture could make the UI too dynamic

A state-aware architecture can easily become a state-reactive screen in which everything fades, moves, expands and reorders as conditions change. That would conflict with spatial memory and interruption recovery. citeturn14search11turn18search12

**Revision:** adaptation is local by default. Ordinary state changes may change a marker *inside a stable anchor*. Layout/topology changes require an actual mode transition and explicit justification.

The default temporal pattern becomes:

> stable location → brief change cue → stable new state.

Not:

> state changed → recompose screen.

### Red-team finding: “visual entitlement” could produce pseudo-precision

Trying to score consequence, urgency, frequency and recoverability numerically without empirical calibration would merely hide design judgment behind mathematics.

**Revision:** entitlement classes are categorical. Quantitative thresholds exist only where a specific detector has validated operating characteristics.

### Red-team finding: salience may increase overconfidence and overtrading

This is especially important in a trading context. A visually dominant historical cluster may acquire a psychological meaning far stronger than its C0/C1 semantic status. The combination of future-facing chart position, density, strong color, labels and current candles makes this a credible failure mode even without explicit predictive text.

**Revision:** visual-claim testing is a release requirement for historically weighted salience. Historical-frequency encodings are not automatically forbidden, but they must demonstrate that the operator can read their magnitude without treating them as a current target or recommendation.

### Red-team finding: personal optimization can fragment the visual language

A single experienced operator can benefit from personalized layout, but unconstrained personalization could make “red,” “dim,” “large,” or “hidden” mean different things in different saved states and defeat machine-checkable visual semantics.

**Revision:** personalize **placement, density and optional detail** within declared bounds, while keeping shared claim/state grammar invariant.

A stable personalized layout is preferable to continuously adaptive personalization unless an adaptive behavior has separately demonstrated net benefit.

### Red-team finding: the extra contract could be expensive to maintain

A giant visual ontology would duplicate CSS, semantic schemas and tests while slowing actual contact with the operator.

**Revision:** SWPC should contain only consequential invariants: work discrimination, presentation role, stable anchor, channel permissions/prohibitions, claim hazard, and validation test. Pixel values remain implementation concerns unless physical/perceptual tests require bounds.

### Final architecture

After the adversarial review, the strongest model is narrower and more conservative than the original “Visual Semantic Architecture” hypothesis.

It consists of five coupled layers:

| Layer | Responsibility |
|---|---|
| **Semantic truth layer — existing SC-1.1** | What is known, measured, estimated, unknown, supported, claimed and forbidden |
| **Work layer** | What distinction the operator must make: orient, monitor, detect, compare, diagnose, verify |
| **Perceptual entitlement layer** | Whether that distinction requires scaffold, ambient state, transition cue, interruption, on-demand evidence, or withholding |
| **Presentation grammar** | Which stable anchors and perceptual channels may encode the distinction without making a stronger visual claim |
| **Validation layer** | Whether the intended expert actually detects and interprets it correctly at acceptable cost |

The core invariant is:

> **The system does not earn perceptual bandwidth because an object is semantically important. It earns it because a required operator discrimination would otherwise become materially less reliable, too slow, too costly to reacquire, or dangerously easy to misinterpret.**

And elevated salience has an additional burden:

> **An object does not earn the right to capture attention merely because it changed. The transition must have a justified detection deadline and consequence structure.**

For screen 24 this leads to a concrete temporal architecture without designing a new screen:

**Stable:** current chart coordinate frame, BASE snapshot, family identity, major panel anchors, R/X categorical grammar, evidence locations, inspector, historical percentages within a scene.

**Locally dynamic:** cut, current closed-M5 path, NOW contents, reachability, history-clock state, support/validity state.

**Transiently cued:** meaningful newly observed transitions—confirmation, break, reachability change where timely recognition matters, newly withheld/stale evidence—without moving the underlying objects.

**Interruptive only under a separate alert predicate:** primarily integrity states for which continued use of the screen can produce invalid reasoning; market/historical frequency does not qualify by itself.

**On demand:** detailed derivations, member-level provenance, diagnostics and forensic explanation, except the compact status needed to know that evidence is weak, unknown or invalid.

This also answers the brief's question about whether “foreground” is inherently better than “ambient.” It is not. The stronger system deliberately keeps much of its most important structure ambient and spatially stable because that is what makes foreground transitions interpretable.

The best next architectural artifact is therefore **not a redesigned screen, a salience matrix, or a visual style guide**. It is the minimal SWPC connecting SC-1.1 objects to work discriminations, presentation roles, permitted channels, claim hazards, and validation tests.

The decisive trace for every future visual decision becomes:

> **What does SC-1.1 permit the system to know or claim?**  
> → **What must the operator discriminate in this state?**  
> → **What happens if that discrimination is missed or misread, and how quickly?**  
> → **Does it require stable context, ambient awareness, transition detection, interruption, or only requested explanation?**  
> → **Which channel can support that perceptual job without implying a stronger claim?**  
> → **What competing interpretation does the channel invite?**  
> → **What scenario test would detect that failure?**  
> → **Does the measured gain exceed the cost of changing the expert's learned perceptual model?**

That architecture gives DR Lab a stricter relationship between machine meaning and human perception than “make important things visible.” It also leaves the operator where an expert operator belongs: **not as the endpoint of an attention-control algorithm, but as one component of a joint cognitive system whose stable perceptual environment should expose valid distinctions, make consequential transitions discoverable, preserve epistemic boundaries, and interfere with skilled scanning only when the evidence justifies doing so.**