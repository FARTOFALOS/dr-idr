# DR IDR — entry for agents

**State of this file: 11.11.2026, after the repository cleanup.** Everything here is current. What used to be layered
history in this file (TP-1.4, the table time × SD, the 15–21.10 integration updates, the 07.10 baseline) is in the
decision chain [`meaning/07-cepochka-reshenij.md`](meaning/07-cepochka-reshenij.md), in `docs/DECISIONS.md` and in the
commit `3847a70` (the last `main` before the cleanup: old designs 1–21, the 29.09–15.10 lenses and studies, the
superseded docs). Links to removed files point there. Do not bring removed material back as a current base.

## Screen 23.5 · 2026-11-10: TP-2.0 (operator accepted; supersedes TP-1.4 where they differ)

**Start here.** The meaning and the engineer's map: [meaning/25-tp-2-0-specifikaciya.md](meaning/25-tp-2-0-specifikaciya.md)
(§2 ontology, §3 parameters, §4 every number with its set and denominator, §5 facets, §6 the exact screen words, §13 how
it is implemented, §14 where each piece lives and the rules not to break). Changes against the 1.4 section below:
- an amber number (bunch, window, place of R, «вне мест», «без отката до вершины») is a share of the WHOLE family N —
  `EST:TP-MASS-R` on the family of the screen; the share inside a window is shown only in the inspector;
- a bunch or place exists only with at least max(4, ceil(0.05 N)) sessions, N of the whole family (`tp-bands-4`, clock
  `tp-2.0`; server `tp11`, contract reference and page alike);
- a blue place reads «X1 · дошли P %» at rest (reach from its near edge); the price column marks the levels 70 % and
  50 % of the window reached; «кончили здесь» only in the inspector;
- the window on screen: a pinned one, else the window of today's deepest point after the confirmation (within the
  block), else W1; a window without sessions is never on screen;
- the panel's first row: how the DR ended for the family's sessions that by this clock had gone as deep
  (`EST:TP-DR-AT-DEPTH` on `CS:TP-DEPTH-AT-CUT-1`);
- T and T_W are named in the contract as what they are: `CS:TP-TRUE-1`, `CS:TP-WINDOW-1` (OUTCOME_SUBGROUP, C1 only;
  the base estimands speak there through their C1 twins `CF:TP-…`, `contract/registry/45-claims-tp.yaml`). The
  accepted registry has 55 estimands (53 of SC-1.1 + 2 of TP-2.0).

## Screen 23.5: its layers and where each is described

| Layer (how to open) | Status | Described in | Code | Check |
|---|---|---|---|---|
| The confirmation family, TP-2.0 (default) | **current base** | [meaning/25](meaning/25-tp-2-0-specifikaciya.md), [docs/DR-LAB-23-5-TP](docs/DR-LAB-23-5-TP.md) | `tp235.js`, `lab/tp11.py`, `lab/contract.py::ref_tp_*` | `tests/tp235_page.mjs`, `tests/contract_sc11.py` |
| Stops and true sessions | current | [meaning/24](meaning/24-stopy-true-sessiy.md) | — | — |
| The table time × SD of 27.10 (`#tp=0`, `#cells=1`) | kept view, not the base | [meaning/22](meaning/22-time-price-constellation-reset.md), [docs/DR-LAB-23-5-MATRIX](docs/DR-LAB-23-5-MATRIX.md) | `matrix235.js` | `tests/matrix235_page.mjs` |
| «Съёмы лоу» (Слои ▾, off by default) | candidate | [docs/DR-LAB-23-5-SWEEPS](docs/DR-LAB-23-5-SWEEPS.md) | `sweeps235.js`, `lab/sweeps235_ref.py` | `tests/sweeps235.py`, `tests/sweeps235_page.mjs` |
| «Продолжения», «Откаты до обновления» (⚙ → Испытание кандидатов) | candidates, off by default | [integration/README](integration/README.md), [spec/ekran-24/15-otkaty](spec/ekran-24/15-otkaty.md) | `continuations.js`, `pullbacks.js`, `lab/continuations24.py`, `lab/pullbacks24.py` | `tests/continuations24.py`, `tests/pullbacks24.py` |
| time × SD route (`/api/integration/time-sd`) | superseded 26.10, route kept | [docs/DR-LAB-23-5-TIME-SD](docs/DR-LAB-23-5-TIME-SD.md) | `time_sd235.js`, `lab/time_sd235.py` | `tests/time_sd235.py` |
| The STD grid | current (operator 11.11) | below | `app.js::gridSide` | — |

- **R on 23.5** is the pullback before the session's extreme (operator 29.10): every family request carries `:rpre`
  (`OUT:R-BEFORE-X-1`, reference `lab/contract.py::ref_before_extreme_R`). NOW-1.0 stays on the final R.
- **The STD grid** (operator 11.11): from the end of the box hour the STD levels stand on the side of the box colour
  (green up, red down; a flat box keeps both sides); the confirmation only settles the side, a break moves it to the
  break's side. The DR / IDR lines keep their own colour until the confirmation. The TradingView script «90» draws the
  same grid (his Fibonacci template −10 … 10) by the same rule.
- Do not use: the whole-family cohort as the base, a table cell as a place, tops of the last 15 minutes as places,
  bunch × band places of X, the capsule «вершина», the stop test C13 (excluded by the operator on 03.11).

## What this is, in one paragraph

**DR Lab** replicates the DR/IDR method (defining range and implied defining range of TheMas7er / M7DR: a one-hour
window, its wick range DR and body range IDR, a confirmation by an M5 close outside DR) on our own 20-year minute tape
of **NQ, ES and YM (2006–2025)**, and shows it live next to the operator's TradingView. **The main screen is 23.5**
(`http://127.0.0.1:8735/23-5/` from the shortcut «DR Lab 23.5»; the root of `:8767` opens `/23-5/` too): today's
session on M5 candles with the author's DR / IDR / STD lines and, from the family of similar historical sessions fixed
at today's confirmation, the author's Time & Price read on the sessions whose DR held (TP-2.0, above). **Screen 24**
«Границы хода» stays at `/24/` as it works (the operator's decision of 19.10: «keep 24 as it works»); 23.5 grew out of
it and shares its server, contract and drawing. Every number on both is a passport of an estimand of the machine
contract DR-LAB-SC-1.1, checked against a reference before it is shown. Any date of 2006–2025 opens as if it were
today («История»). **Legacy surfaces** still served but outside the contract: design 22 (`/22/`), the classic screen
(`/classic.html`), design 23 (`/sem-v1/`), the research dashboard (`/api/query`, `/api/scene`); do not develop them.

## Who you work for

- **The operator is a trader, not a programmer.** He speaks Russian, by voice, in trader language. Answer in Russian:
  first what is on the prices, then why, then what he decides. No jargon, no English terms without need.
- **He only double-clicks the desktop shortcuts** «DR Lab 23.5» (`start-dr-lab-23-5.cmd`, his daily screen) and «DR Lab» (`start-dr-lab.cmd`). Never ask him to run
  commands, edit files or open terminals. Any change you make must keep that shortcut working from a cold start (PC
  reboot). Verify it yourself.
- He judges the product by the screen. His interface requirements are binding: `docs/UI_RULES.md` and, for screen 24,
  the journal of every visual rule with its reason, **`meaning/13-zhurnal-vizualizacii.md`** (written for screen 24; 23.5 keeps that drawing) (read it before any visual
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
2. **DR-LAB-SC-1.1** — `spec/DR-LAB-Semantic-Contract-1.1-(patched).md`, accepted on 2026-10-07. Its machine form is
   **`contract/`** (start at `contract/README.md`), enforced by `lab/contract.py` and by the pages. The text is the
   source of truth; where `contract/` disagrees with it, `contract/` is the defect. Do not edit the contract text (it is
   pinned by SHA-256); a new edition is the operator's. The accepted registry has 55 estimands (53 of SC-1.1 + 2 of
   TP-2.0); the separate proposed registry of candidates is `integration/candidates/`.
3. **TP-2.0** for screen 23.5 — [meaning/25](meaning/25-tp-2-0-specifikaciya.md), on the core
   [meaning/23](meaning/23-tp-smyslovoe-yadro.md) (DR-LAB-TP-1.4) where 25 does not change it.
4. **DR-LAB-SWPC-1.1** — `spec/DR-LAB-SWPC-1.1.md`, the visual implementation target of screen 24.
5. **The profile definitions SC-1.1 formalises:** DR-LAB-SEM-1.0 (`meaning/lens/2026-10-01-spec-v1/`), zone-map-3
   (`meaning/12-karta-zon.md`), today's two axes (`meaning/14-vperedi-i-proshlo.md`), DR-LAB-NOW-1.0
   (`meaning/lens/2026-10-06-now-1.0/`, `meaning/15-sloj-seichas.md`). Summaries: `meaning/10-dizajn-24.md`,
   `spec/ekran-24/` (every element of screen 24).

## Read in this order

0. `meaning/README.md` — the semantic layer (Russian, no code).
1. This file.
2. `meaning/25-tp-2-0-specifikaciya.md` — the current base of 23.5, with the engineer's map (§13–§14).
3. `contract/README.md` — the machine contract: what it enforces, how to change it without breaking the pages.
4. `docs/ARCHITECTURE.md` — the stack, processes, data flow, API, the contract gate.
5. `docs/UI_RULES.md` and `meaning/13-zhurnal-vizualizacii.md` — the operator's interface requirements.
6. `docs/STRATEGY.md` — the DR/IDR method itself (Russian); `docs/DR_RULES_WEB.md`, `docs/DR_RULES_CROSSCHECK.md` — its
   cross-checks; `docs/RESEARCH.md` — what is measured and what is not.

## Map

```
start-dr-lab-23-5.cmd/.ps1  shortcut «DR Lab 23.5» (the daily screen): TradingView (9222) -> server :8735 -> /23-5/
start-dr-lab-23-5-kletki.cmd  the same with the layer «Клетки» (#cells=1)
start-dr-lab.cmd/.ps1      shortcut «DR Lab»: server :8767 (--integration), / opens /23-5/; start-dr-lab-24.cmd opens /24/
start-dr-lab-integration.* the isolated candidate stand :8773 (15.10); stop-*.cmd/.ps1 stop the matching server
contract/                  DR-LAB-SC-1.1 in machine form: LinkML schema, registry (+ 35-tp-2.yaml, 45-claims-tp.yaml),
                           build tool and products; start at contract/README.md (.venv-linkml/ is git-ignored)
lab/
  server.py                local HTTP server (stdlib): static pages of dist/ + JSON API
  contract.py              the SC-1.1 gate: reference definitions, re-derivation at publication, envelopes, stale state
  scene24.py, zonemap24.py, tp11.py   families, R / X, DR outcome, zone and table maps, TP-2.0 bands and windows
  cluster24.py             main-cluster-1 (meaning/11), read by scene24, not on screen
  now24.py, pre24.py, arrive24.py, continuity*.py, continuations24.py, pullbacks24.py, time_sd235.py   layers and candidates
  integration24.py, integration_audit.py, revisions24.py, runtime_identity.py   candidate trials, audit, versions
  scene21.py               today's trading day from TradingView (used by 24 and 23.5) and design 22's legacy data
  live.py, tv_fetch.mjs, tv_passive.mjs   live candles from TradingView Desktop over CDP (never written to history)
  build_market.py, build_boxes.py   the history base from the G3 tape (once); engine_market.py, engine.py: legacy, demo
  dr_voice.py, dr_speak.ps1 the spoken reading of the screen
  q1/                      the Q1 historical pilot of 12.10 (own server, kept with its checks)
  dist/                    built pages: 23-5/ and 24/ (built from design/), legacy index.html, classic.html, sem-v1/
  .runtime/                git-ignored: history, live candles, logs, NOW validation — market data, never committed
design/sozvezdiya-23-5/src the source of 23.5 (build.py -> lab/dist/23-5); design/sozvezdiya-24/src the source of 24
design/sozvezdiya-22, -23  sources of the legacy pages /22/ and /sem-v1/
meaning/                   the semantic layer (Russian): README, numbered documents, the lenses that are still sources
spec/                      SC-1.0/1.1, SWPC-1.1, INTEGRATION-1.0, the deep-research inputs; ekran-24/ and ekran-23-5/:
                           screens element by element with screenshots
docs/                      architecture, decisions, UI rules, the method, research, the 23.5 layer documents
integration/               the 15.10 integration: candidate registry (candidates/), the preserved Trace/FOM reference
                           (reference/), scripts and receipts
studies/                   the studies that code or current documents still use (aggregates only)
tests/                     checks (below)
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
   not print disclaimers (operator's decision), so the discipline lives in the code. On screens 23.5 and 24 a number exists only
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

Market data lives only on the operator's computer, so the data checks run there (his working copy
`C:\Users\Admin\Claude\dr-idr`).

```bash
python -B tests/smoke.py                 # offline: history, the screens' data, the contract state, JS syntax
python -B tests/contract_sc11.py         # the contract: expect ALL GOOD
```

- **23.5:** `python design/sozvezdiya-23-5/src/build.py`; then with a server on the history
  (`start-dr-lab-23-5.cmd -NoBrowser -HistoryOnly`) `node tests/tp235_page.mjs http://127.0.0.1:8735/23-5/` and the
  layer checks of the table above. Open a history day (`#date=2025-12-17&inst=NQ&session=RDR`) and a live day in a
  browser tool; read the console. Never press «⟳ Обновить».
- **Screen 24:** `python design/sozvezdiya-24/src/build.py`, `python -B tests/sem24.py`, `python -B tests/now24.py`,
  `tests/ui_check24.js` in the page at `/24/` (1600×900 and 1920×1000, expect `problems: []`).
- **The contract** (`contract/`, `lab/contract.py`, a route): `.venv-linkml\Scripts\python.exe contract/tools/build.py`
  (`PYTHONUTF8=1`), then rebuild both pages, then `tests/contract_sc11.py`, `tests/swpc11.py`.
- **Server or `lab/*.py` touched:** restart the server (it caches modules): `stop-dr-lab-23-5.cmd`, then
  `start-dr-lab-23-5.cmd -NoBrowser`; the same for `:8767` with `stop-dr-lab.cmd` / `start-dr-lab.cmd`. Run them from
  PowerShell directly, never through a pipe.
- Links between documents: `python -B tests/semantic_links.py`.

## Repository rules

- **`main` is the line.** Work on a branch, push to `main` only on the operator's word. Every commit carries the chain
  of decisions (what changed in meaning, who decided, on what basis, what stays open); the same node goes into
  `meaning/07-cepochka-reshenij.md`.
- **Pull requests #15–#18 and #26–#28 are superseded by `main`** (decision of 11.11): close them, never merge them; their
  branches stay as history. #29 (the agent trading stack for NinjaTrader) is a separate open draft. A new PR is opened
  only for a change the operator wants to review before it lands.
- Keep the repository clean: a document or study that no code and no current document needs does not stay in `main`.
  A superseded document is removed (it remains in git history), not kept with a «HISTORICAL» banner.

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
