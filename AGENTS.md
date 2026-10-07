# DR IDR — entry for agents

You are entering a working trading tool, not a demo. Read this file fully, then the documents it points to, before
changing anything. It is written so that an agent arriving cold (Claude Code, Codex, a designer agent) can work
safely on the first try. State of this file: **2026-10-07, after design 24 and the machine contract were merged into
`main`**.

## What this is, in one paragraph

**DR Lab** replicates the DR/IDR method (defining range and implied defining range of TheMas7er / M7DR: a one-hour
window, its wick range DR and body range IDR, a confirmation by an M5 close outside DR) on our own 20-year minute tape
of **NQ, ES and YM (2006–2025)**, and shows it live next to the operator's TradingView. The working screen is
**screen 24 «Границы хода»** (`http://127.0.0.1:8767/`, which opens `/24/`): today's session on M5 candles with the
author's DR / IDR lines and, from the **family** of similar historical sessions (same instrument, session, weekday,
direction and 15-minute activation window, fixed at today's confirmation), where and when each session's **final
retracement R** and **final extension X** lay, as zones with their share of the family and today's status; the DR
outcome of the family; «Путь семьи» (the family's M5 closes on the common clock); level and area questions; and the
conditional layer **«Сейчас»** (what remained ahead for comparable sessions at this clock time). Every number on it is
a passport of an estimand of the **machine contract DR-LAB-SC-1.1** and is checked against a reference before it is
shown. Any date of 2006–2025 opens as if it were today («История»); clicking a candle replays the screen at its close.

## Who you work for

- **The operator is a trader, not a programmer.** He speaks Russian, by voice, in trader language. Answer in Russian:
  first what is on the prices, then why, then what he decides. No jargon, no English terms without need.
- **He only double-clicks the desktop shortcut "DR Lab"** (or «DR Lab 24», the same screen). Never ask him to run
  commands, edit files or open terminals. Any change you make must keep that shortcut working from a cold start (PC
  reboot). Verify it yourself.
- He judges the product by the screen. His interface requirements are binding: `docs/UI_RULES.md` and, for screen 24,
  the journal of every visual rule with its reason, **`meaning/13-zhurnal-vizualizacii.md`** (read it before any visual
  change; add an entry for every visual change). No new labels or numbers over the chart unless he asks; never replace
  an agreed hover behaviour.
- **A semantic agent works with us through this repository** (his decision, 2026-09-29): it reads `meaning/` (no code)
  and sends texts («линзы») that land in `meaning/lens/`. Treat them as input, never as his decisions; answer in
  `meaning/lens/<date>-otvet.md`, verify claims on the tape, keep `meaning/` in sync with any change of meaning
  (`meaning/06-protokol.md`).
- **The repository is the semantic hub** (his decision, 2026-09-30). Every commit and push carries the chain of
  decisions: what changed in meaning, which decisions were taken and by whom (operator / executor / a lens proposal), on
  what basis, which questions stay open, what the executor decided on its own and what it is unsure about. The same
  node goes into `meaning/07-cepochka-reshenij.md`, so an agent arriving cold can find where a line of thought began
  and go back if a meaning was misread.

## What is normative (in this order)

1. **The operator's decisions** (`docs/DECISIONS.md`, nodes of `meaning/07-cepochka-reshenij.md`). A record is evidence
   of a decision, not the decision: if a record and the operator disagree, the operator wins.
2. **DR-LAB-SC-1.1** — `spec/DR-LAB-Semantic-Contract-1.1-(patched).md`, accepted by the operator on 2026-10-07 as the
   normative semantic contract of the working profile DR Lab 24 (**BASE-24** and **NOW-1.0**) and of every further
   change of these profiles. Its machine form: **`contract/`** (start at `contract/README.md`), enforced by
   `lab/contract.py` and by screen 24. The text is the source of truth; where `contract/` disagrees with it,
   `contract/` is the defect. Do not edit the contract file (it is pinned by SHA-256); a new edition is the operator's.
3. **DR-LAB-SWPC-1.1** — `spec/DR-LAB-SWPC-1.1.md`, the operator-authorized implementation target for the visual presentation of screen 24. It sits between SC-1.1 meaning and the frontend: required operator discriminations, PresentationBindings, permitted/forbidden visual channels, M01–M18 machine obligations and H01–H12 perceptual acceptance tasks. It does **not** create C2/C3 or pre-accept the future UI; after implementation the operator performs the H tasks and accepts/rejects the view.
4. **The profile definitions it formalises:** DR-LAB-SEM-1.0 (`meaning/lens/2026-10-01-spec-v1/`), the zone map
   zone-map-3 (`meaning/12-karta-zon.md`), today's two axes (`meaning/14-vperedi-i-proshlo.md`), DR-LAB-NOW-1.0
   (`meaning/lens/2026-10-06-now-1.0/`, `meaning/15-sloj-seichas.md`; matchers, thresholds and gates frozen). Summaries:
   `meaning/10-dizajn-24.md`, `docs/SEMANTICS.md` (section «Дизайн 24»), `spec/ekran-24/` (every element of the screen).
5. **Legacy surfaces stay outside SC-1.1 for now** (operator, 2026-10-07): design 22 at `/22/`, the classic screen
   `/classic.html`, the research dashboard (`/api/query`, `/api/scene`), design 23 at `/sem-v1/`. Their own
   definitions are in `docs/SEMANTICS.md` (earlier sections); every response of theirs is marked
   `X-DR-Lab-Contract: …status=OUTSIDE_SC11`, and no SC-1.1 estimand may take their numbers as input.

## Read in this order

0. `meaning/README.md` — the semantic layer (Russian, no code): what the numbers mean, the evidence, open questions.
1. `AGENTS.md` — this file: what is normative, map, hard rules, how to verify, gotchas.
2. `contract/README.md` — the machine contract: what it enforces, how to change it without breaking the screen.
3. `spec/DR-LAB-SWPC-1.1.md` — current visual implementation target: what the trader must distinguish, what may attract attention, and how the result must be tested.
4. `meaning/10-dizajn-24.md`, then `spec/ekran-24/README.md` — screen 24: where every percentage comes from.
5. `docs/ARCHITECTURE.md` — the stack, processes, data flow, API, the contract gate.
6. `docs/SEMANTICS.md` — exact definitions of every object and number (section «Дизайн 24» for the working screen).
7. `docs/UI_RULES.md` and `meaning/13-zhurnal-vizualizacii.md` — the operator's interface requirements.
8. `docs/DECISIONS.md` — dated decisions and where they came from.
9. `docs/RESEARCH.md` — what has been measured, what is not established.
10. `docs/STRATEGY.md` — the DR/IDR method itself, formalized from the author's 156 videos and streams (Russian), what
   our tape confirms (`studies/m7_claims.py`) and the decisions still open. `docs/DR_RULES_WEB.md` is an independent
   cross-check against public sources only.

## Where the work stands (2026-10-07)

- **`main` is the line of DR Lab.** Design 24 (PR #1, branch `design-24`) was merged on 2026-10-07 by the operator's
  decision; the operator's checkout is on `main`. Work on `main`; for a change he wants to review first, use a branch
  and a pull request. `design-24` is kept as history, not as a working branch.
- **Screen 24** (since 2026-10-01 night the working screen): design 22's interface (candles, DR / IDR, ADR / ODR /
  RDR, replay and live, the right panel, hover / pin / layers, settings) with the statistical layer of DR-LAB-SEM-1.0,
  the zone map zone-map-3 (2026-10-01 evening), the look «Окна времени» (R and X together as constellations «дымка и
  нити», amber R / sky X, the time band, the inspector at the bottom right, six windows sliding up from the bottom), the
  trader's reading of 2026-10-06 (`meaning/13` entries 1–45), today's two axes and the layer «Сейчас» (2026-10-06,
  DR-LAB-NOW-1.0: the path did not beat the time baseline, so the screen shows «по времени» with its support).
- **The machine contract DR-LAB-SC-1.1** (2026-10-07): LinkML schema and registry (`contract/`), the runtime gate
  (`lab/contract.py`), the page's contract layer, `tests/contract_sc11.py`. On screen only the words of «Сейчас»
  changed — the operator's: «В истории: R позже углублялся… / Если углублялся…», symmetric for X (K33: a historical
  share never speaks of today in forecast grammar) — and the order window got its «нет периода» row.
- **Visual implementation target DR-LAB-SWPC-1.1** (2026-10-07): the operator authorized the next stage — implement the closed PresentationBindings and M01–M18 on the existing screen 24. Until H01–H12 are run with the operator, the resulting view is `PERCEPTUALLY_UNVERIFIED`; implementation permission is not perceptual acceptance.
- **Open** (`meaning/05-otkrytye-voprosy.md`): what to develop next (О20: sequences, conditional forecasts, design);
  NOW-1.1 (a distance-from-extreme matcher, the operator decides); the zone map's prospective acceptance on sessions
  after 2025 (О23, О24: the 2026 tape stays closed); SC-1.1 for the legacy surfaces.
- **How we got here** (2026-09-24 … 10-07): `docs/DECISIONS.md` and `meaning/07-cepochka-reshenij.md`. In short: the
  classic screen → design 21 «Созвездия» (09-28) → the semantic audit and design 22 «смысл числа» (09-29) → lenses 4–15
  on what a cluster is (09-30 … 10-01; `meaning/08`, `meaning/lens/`) → DR-LAB-SEM-1.0 and design 24 (10-01) → the zone
  map (10-01) → the trader's reading, today's axes, NOW (10-06) → SC-1.1 and its machine form, merge into `main` (10-07).

## Map

```
start-dr-lab.cmd / .ps1   the operator's shortcut target: TradingView (port 9222) -> history -> server -> page
start-dr-lab-24.cmd       the shortcut «DR Lab 24»: the same start, then the page /24/ (the root / opens it too)
stop-dr-lab.cmd / .ps1    stop the local server
contract/                 the machine contract of DR-LAB-SC-1.1: LinkML schema, registry, build tool, products;
                          start at contract/README.md (.venv-linkml/ = its LinkML environment, git-ignored)
lab/
  server.py               local HTTP server 127.0.0.1:8767 (stdlib): static pages + JSON API; / -> /24/, /22/ -> design 22
  contract.py             the DR-LAB-SC-1.1 gate (stdlib): reference definitions, re-derivation at publication,
                          envelopes and bundles, admissible claims, undeclared numbers, CONTRACT_STALE, /api/d24/verify
  scene24.py              screen 24's data (/api/d24/day, family, dates): families, R / X, DR outcome, order, path
  zonemap24.py            screen 24's zone map zone-map-3 (meaning/12): zones, diagnostics, today's two axes
  now24.py                screen 24's layer «Сейчас» (/api/d24/now, DR-LAB-NOW-1.0); now24_validate.py: walk-forward
  scene21.py              the trading day from TradingView (used by 24), design 22's data (legacy: /api/day, /api/cohort,
                          /api/family), design 23's /api/family-v1
  cluster24.py            main-cluster-1 (meaning/11): kept for its archived studies, not on the screen
  build_boxes.py          builds every session box (confirmed or not) with its M5 bars (once; ~20 s per instrument)
  build_market.py         builds the history base from the G3 market tape (once; ~30 s per instrument)
  engine_market.py        history queries over the built base (legacy research dashboard, /api/query, /api/scene)
  live.py                 the live fetch from TradingView; the classic screen's live state (legacy /api/live)
  tv_fetch.mjs            reads M5/M1 bars from TradingView Desktop via Chrome DevTools (tradingview-mcp internals)
  engine.py               synthetic demo engine (python lab/server.py --data demo); never mixed with market data
  dist/                   front end: 24/ (screen 24, built from design/sozvezdiya-24/src), index.html + sozvezdiya.js
                          (design 22, legacy, built from design/sozvezdiya-22/src), sem-v1/ (design 23, legacy),
                          classic.html + app.js + live.js + styles.css (the classic screen, legacy)
  .runtime/               git-ignored: built history, live candles, server logs, NOW validation
design/sozvezdiya-24/src  screen 24's source (app.js, panel.js, page.html, panel.css; build.py embeds the contract)
spec/                     DR-LAB-SC-1.1 (normative) and 1.0 (previous edition); DR-LAB-SWPC-1.1 (current visual
                          implementation target) and SWPC-1.0 (predecessor); deep-research-report (16).md as its
                          analytical input;
                          ekran-24/: every element of screen 24 on annotated screenshots, its meaning, count, code
meaning/                  the semantic layer for agents without code (Russian): start at meaning/README.md; lenses and
                          answers in meaning/lens/
docs/                     architecture, definitions, UI rules, decisions, research, the method
design/                   mockups on synthetic data, designs 1-24 (start at design/README.md)
studies/                  research scripts with their results (aggregates only)
tests/smoke.py            offline checks; run after every change
tests/contract_sc11.py    DR-LAB-SC-1.1: products = sources, the enforcement map, K01-K33 executed, routes, live
                          envelopes (LinkML in a temporary folder), the stale state, the page's contract layer
tests/sem24.py            screen 24: the specification's 32 reference checks, integration on the base, the zone map
tests/now24.py            screen 24: the acceptance tests of «Сейчас» (DR-LAB-NOW-1.0)
tests/ui_check24.js       screen 24: in-page check (passports, page = server, one table, film columns, slices, zones,
                          the contract layer: every passport recomputed by the reference, K16, K30, K33)
tests/ui_check21.js       design 22 (legacy) in-page check; ui_check.js: the classic screen
README.md                 the front page on GitHub
```

## Hard rules (do not break; if a task seems to need it, ask the operator first)

1. **Market data is never committed or published.** The tape and everything built from it (`lab/.runtime/`) stay
   local. The repository is public. Screenshots of the working screen are not market data in this sense: they go into
   the repository when they serve a review (operator, 2026-09-30).
2. **2026 stays hidden in the history base.** The build stops at 2025-12-31 ET; `tests/smoke.py` checks it. The 2026
   tape is the forward observation of the G3 research line and of the zone map's acceptance (О23, О24).
3. **No Volume** anywhere in the method.
4. **Local only.** The server binds 127.0.0.1. Do not expose it, do not deploy it as a web service.
5. **Live candles are displayed, never written into the history base or its statistics.**
6. **Prefix honesty** (rewritten 2026-10-07 for the main line; SC-1.1 E0–E1, P0.1, NOW-1.0).
   - **Today** is read from closed M5 only: the box, the confirmation and the DR break are established at the close of
     an M5; the slice is the last closed M5; the live price is only drawn between closes. Replay obeys the same rule:
     bars after the slice are shown, never used.
   - **The family** is fixed once at today's activation (the confirmation; after today's DR break the break family, with
     the original kept behind an explicit switch) and is never re-matched by price, state or path during the day.
   - **A historical session's own future is its label, never today's input:** its R, X, DR outcome, order and path are
     measured on its own horizon, from the close of its own activating M5 (excluded) to its block end (the M5 closing at
     the end included). A knowledge of finality is never dated before it was determinable.
   - **NOW** selects at the common clock cut (the same ET time in every session, never the same age) among sessions with
     a complete own prefix; only what was available at the cut selects, the remainder is the label.
   - Legacy screens keep their older statement of this rule in `docs/SEMANTICS.md`.
7. **Descriptive numbers.** Frequencies are the history of a set of sessions, not a forecast, not a trade. The UI does
   not print disclaimers (operator's decision), so the discipline lives in the code. On screen 24 a number exists only
   as a passport of an estimand registered in `contract/registry/` with an admissible claim form, and its words are that
   form's registered labels; no number of this tool admits a forecast (C2) or a decision (C3) claim. On legacy screens:
   never add a number whose meaning is not defined in `docs/SEMANTICS.md`.
8. **The demo engine stays separate** (`--data demo`) and never mixes with market data.
9. **API contract changes update both sides** (server and `dist/`), `docs/ARCHITECTURE.md`, and for the routes of
   screen 24 the machine contract (`contract/registry/60-surfaces.yaml`: a number without a declared meaning makes the
   response a violation), then `contract/tools/build.py` and the page build.
10. **Every number answers the operator's question as a named object** (rewritten 2026-10-07 for the main line).
    - The base object of screen 24 is DR-LAB-SEM-1.0 under SC-1.1: for each session of the family its own **final R**
      (the deepest point against its activation) and **final X** (the farthest point along it) to its block end, named
      as such — one point per session, every share of the family's one N, the unknown and the «no period» mass apart.
    - Other events are separate, named objects with their own estimands: the first arrival, a visit of a band, «on a
      level or beyond», a literal cross, the close on a common clock M5, the order of the first R and X, the DR outcome.
      Never present one as another (a final extreme as a first arrival, a visit as a final extreme, a family share as
      today's chance), and never word a historical share in forecast grammar about today (K33).
    - A new number needs a registered estimand and claim form (`contract/registry/`) answering a question the operator
      asked, in his words; if unsure, ask in one plain sentence before building.
    - Why the rule exists: on 2026-09-28 agents put the session's final extreme, unnamed, in place of the operator's
      question «where and when did price of similar sessions COME» on design 21–22, and every cluster piled up at
      15:50–16:00. Design 22 at `/22/` keeps first arrivals and its own statement of this rule (`docs/SEMANTICS.md`).
      On 2026-10-01 the operator made the named final extremes the base object of screen 24 (DR-LAB-SEM-1.0); on
      2026-10-07 he accepted SC-1.1 for it.

## How to verify your change (always, before saying "done")

```bash
python -B tests/smoke.py                 # offline: history, the screens' data, the contract state, JS syntax
```

If you touched the server or `lab/*.py`: **restart the server** (it caches Python modules). Stop every listener on 8767
first (see «Two servers» below), then start it from PowerShell, never through a pipe:

```bash
stop-dr-lab.cmd
start-dr-lab.cmd -NoBrowser              # the same path the operator's shortcut takes
```

If you touched the machine contract (`contract/`), `lab/contract.py`, a route or how screen 24 shows a number:

```bash
.venv-linkml\Scripts\python.exe contract/tools/build.py   # after editing contract/ (PYTHONUTF8=1); then rebuild screen 24
python -B tests/contract_sc11.py                            # expect ALL GOOD
```

If you touched screen 24: run `python design/sozvezdiya-24/src/build.py`, `python -B tests/sem24.py` and
`python -B tests/now24.py`; open http://127.0.0.1:8767/24/ (a history day, e.g. `#date=2025-12-17&inst=NQ&session=RDR`)
in a browser tool at 1600×900 and 1920×1000, evaluate `tests/ui_check24.js` and expect `problems: []` (one known
exception: the toolbar is 2–11 px wider than 1600 px in «История» mode, since before 2026-10-07). Check that
http://127.0.0.1:8767/ still opens /24/ and /22/ opens design 22. If an element changed, update its row in
`spec/ekran-24/`, add an entry to `meaning/13`, and re-shoot (`spec/ekran-24/tools/shots.py`, then `annotate.py`).

Legacy surfaces: design 22 — edit `design/sozvezdiya-22/src`, run its `build.py` (it writes `lab/dist/index.html` and
`sozvezdiya.js`; never build `design/sozvezdiya-21`), evaluate `tests/ui_check21.js` at `/22/`. The classic screen —
`tests/ui_check.js` at `/classic.html`. Never touch their files for screen 24.

## Gotchas already paid for

- **Stale server modules.** Symptom: the page says "Локальный сервер не ответил" or panels are empty after a backend
  change. Cause: the running server imported the old module. Restart it.
- **Two servers on port 8767.** On Windows a second `server.py` can bind the same port, and either may answer (with
  whatever code it loaded); on 2026-10-07 two were listening at once and `stop-dr-lab.cmd` stopped only one. Before
  restarting, stop every listener on 8767 until none is left (`Get-NetTCPConnection -LocalPort 8767 -State Listen`),
  then start once.
- **Do not pipe the launcher** (`start-dr-lab.cmd | tail` in bash, `| Out-String` in PowerShell): the hidden server
  inherits the pipe and the command never returns. Run it directly from PowerShell (`& .\start-dr-lab.cmd -NoBrowser`).
- **CONTRACT_STALE is the contract working.** After an edit of `contract/schema` or `contract/registry` the server
  publishes no statistic until `contract/tools/build.py` runs; after a contract build, a page not rebuilt refuses every
  family («страница собрана с другим реестром контракта»). Build the contract, then screen 24; `lab/contract.py` edits
  also need a server restart (the registry itself is reloaded).
- **A history day's address names no instrument by default.** `#date=…` opens NQ unless `&inst=` is given; a text or
  screenshot of a day must name the instrument (on 2026-10-07 two compared states turned out to be ES and YM).
- **Drawing errors used to look like server errors.** Read the browser console before blaming the server.
- **TradingView must be started with the debugging port 9222.** A TradingView opened from its normal icon has no
  port; the launcher restarts it through `tradingview-mcp` (`node <TV_MCP_DIR>/src/cli/index.js launch`).
- **Readiness of a switched chart.** After `setSymbol`, `chart.symbol()` changes before the bars do; old bars of the
  previous symbol can be read as the new one. `tv_fetch.mjs` waits for the series' own `symbolInfo()` to match,
  `isLoading()` false and a stable bar count. Keep that logic.
- **Prefer reading an existing pane.** If the operator's layout has a pane of the future on 5 (or 1) minutes, bars
  are read from it without switching anything, and the live data refresh every minute. Otherwise the active chart
  is switched for 2–4 s and restored, and the cadence drops to 5 minutes. He currently has NQ 5m and NQ 1m panes.
- **PowerShell 5.1 and Cyrillic.** `.ps1` files with Russian text must be saved as UTF-8 **with BOM** and CRLF.
- **Python.** The operator's Python with numpy/pandas is `%LOCALAPPDATA%\Python\bin\python.exe` (3.14);
  `C:\Python313` has no numpy. The launcher probes candidates. LinkML lives only in `.venv-linkml`
  (`contract/setup-linkml.ps1`); set `PYTHONUTF8=1` in a cp1251 console.
- **Stale page after an update.** The server sends `Cache-Control: no-cache` for static files; keep it.
- **Disk C: can fill up.** On 2026-09-30 it reached 0 bytes free and a study failed while writing its per-state
  records. Keep such records compressed and small (`.json.gz`). The earlier big ones were moved, not deleted, to
  `D:\dr-idr-runtime-archive\2026-09-30`; `studies/m7_claims.py` rebuilds its cache if it is missing. Never touch
  `boxes_*`, `market_*` or `live/`: the screens read them.
- **Label collisions on the chart.** New text on the chart is a visual change: the operator's rule is no new labels
  over the chart unasked (`meaning/13`); design 22 and the classic screen lay labels out with a minimum gap.

## Relation to G3

The market tape and the research standards come from the G3 repository (`FARTOFALOS/g3-market-research`, checked out
next to this one). `lab/build_market.py` reads `../g3-market-research/data/market/<NQ|ES|YM>` unless `DR_IDR_MARKET`
points elsewhere. Research conclusions about DR that follow the G3 standard (declared before counting, honest
baseline, epochs) belong to G3; this repository keeps the tool and its own studies (`studies/`, `docs/RESEARCH.md`).

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `DR_IDR_MARKET` | `../g3-market-research/data/market` | root of the minute tape (`<inst>/close_ts_utc_ns.npy`, `open.npy`, …) |
| `TV_MCP_DIR` | `%USERPROFILE%\Claude\tradingview-mcp` | local checkout of tradingview-mcp (CLI + CDP connection) |
| `PYTHONUTF8` | unset | set to `1` for `contract/tools/build.py` in a cp1251 console |

Ports: 8767 (DR Lab), 9222 (TradingView debugging).
