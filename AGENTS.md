# DR IDR — entry for agents

You are entering a working trading tool, not a demo. Read this file fully, then the documents it points to, before
changing anything. It is written so that an agent arriving cold (Claude Code, Codex, a designer agent) can work
safely on the first try.

## What this is, in one paragraph

**DR Lab** replicates the DR/IDR method (defining range and implied defining range of TheMas7er / M7DR: a one-hour
window, its wick range DR and body range IDR, a confirmation by an M5 close outside DR) on our own 20-year minute tape
of **NQ, ES and YM (2006–2025)**, and shows it live. The operator opens one desktop shortcut and sees **today's
session on 5-minute candles from his TradingView**, the DR/IDR lines as in the Pine script, and on the future part of
the chart **clusters from similar historical sessions**: where and when the retracement most often ended, how often
each level was touched, the path fan, and how often the DR rule held. It re-matches the whole history **every
minute**. Clicking a candle replays the screen as it was at that candle's close, so the forecast can be checked
against what happened next.

## Who you work for

- **The operator is a trader, not a programmer.** He speaks Russian, by voice, in trader language. Answer in Russian:
  first what is on the prices, then why, then what he decides. No jargon, no English terms without need.
- **He only double-clicks the desktop shortcut "DR Lab".** Never ask him to run commands, edit files or open
  terminals. Any change you make must keep that shortcut working from a cold start (PC reboot). Verify it yourself.
- He judges the product by the screen. His interface requirements are binding: `docs/UI_RULES.md`. They came from
  many iterations; re-read them before any visual change. The working screen is design 22 «Созвездия · смысл числа»
  (since 2026-09-29, the operator's go-ahead; `design/sozvezdiya-22/`); its details still have open questions
  (`meaning/05-otkrytye-voprosy.md`). The redesign B′ of 2026-09-25 (`docs/DESIGN.md`) was superseded by 20/21.
- **A semantic agent works with us through this repository** (his decision, 2026-09-29): it reads `meaning/` (no code)
  and sends texts («линзы») that land in `meaning/lens/`. Treat them as input, never as his decisions; answer in
  `meaning/lens/<date>-otvet.md`, verify claims on the tape, keep `meaning/` in sync with any change of meaning
  (`meaning/06-protokol.md`).
- **The repository is the semantic hub** (his decision, 2026-09-30). Every commit and push carries the chain of
  decisions: what changed in meaning, which decisions were taken and by whom (operator / executor / a lens proposal), on
  what basis, which questions stay open, what the executor decided on its own and what it is unsure about. The same
  node goes into `meaning/07-cepochka-reshenij.md`, so an agent arriving cold can find where a line of thought began
  and go back if a meaning was misread.

## Read in this order

0. `meaning/README.md` — the semantic layer shared with semantic agents (Russian, no code): purpose, events, evidence,
   the current design proposal, open questions, how we work together. Read it first to know what the numbers mean.
1. `AGENTS.md` — this file: map, hard rules, how to verify, gotchas.
2. `docs/ARCHITECTURE.md` — the stack, processes, data flow, file responsibilities, API contract.
3. `docs/SEMANTICS.md` — exact definitions of every object and number (DR, IDR, confirmation, clusters, overlay).
4. `docs/UI_RULES.md` — the operator's interface requirements and the design tokens.
5. `docs/DECISIONS.md` — dated decisions and where they came from.
6. `docs/RESEARCH.md` — what has been measured, what is not established, and the open questions.
7. `docs/STRATEGY.md` — the DR/IDR method itself, formalized from the author's 156 videos and streams (Russian):
   definitions, session models, setups, stops, targets, risk, an algorithm for an autonomous agent, what our tape
   confirms (`studies/m7_claims.py`) and the decisions still open for the operator. `docs/DR_RULES_WEB.md` is an
   independent cross-check of the rules against public sources only.
8. `docs/DESIGN.md` — the redesign of the screen the operator chose (variant B′): target layout, visual language,
   interactions, which UI rules it replaces, what the implementation needs; mockups in `design/redesign-2026-09/`.

## Where the work stands (2026-09-30)

- **Semantic audit and design 22 (2026-09-29).** The operator asked for a deep audit of the whole system and then for
  the next design built on its conclusions, with the repository made readable for a semantic agent without code.
  Results: `meaning/03-dokazatelstva.md` (studies in `studies/audit_2026_09_29/`, all aggregates); design 22 is
  the working screen since the same evening (`design/sozvezdiya-22/`, `meaning/04-dizajn-22.md`); `/api/cohort` sends
  own DR (`uH`, `uL`) and `wick` per similar session. Stars and places were then switched to first arrivals (hard
  rule 10).
- **Lens 4 checks (2026-09-30, `studies/lens4_2026_09_30/`, `meaning/lens/2026-09-30-otvet-4.md`).** Keep rebuilding the
  similar sessions at every M5 (a map frozen at the confirmation has no skill), keep the state matcher (a level-activation
  matcher is not better) and the live minute price (not worse than full M1 alignment, better than closed M5 only). A
  place's cloud height is the first entering bar's depth, not where price came, and the data form no price clusters of
  their own: what to draw instead is the operator's question О11 — do not restyle the clouds before it is answered.

- **Lenses 5 and 6 (2026-09-30, `meaning/lens/`, `meaning/07-cepochka-reshenij.md`).**
  - Lens 5 (cluster spec v0.8): the answer argues that every number is an order of first touches, that a reaction
    detector needs a threshold (`studies/lens5_2026_09_30/`, synthetic) and that a reaction layer is probably
    unnecessary.
  - Lens 6: reconstruct the author's Time & Price literally before transferring anything. The answer:
    - one value per session of the max retracement, its time and the max extension;
    - 0.1 buckets and 15-minute bins; zones picked by eye;
    - the «70 %» line is asymmetric;
    - cross-filters select sessions by their future;
    - M7 retracement stays proprietary.
  - The author's NQ key recomputed on our tape (`studies/lens6_2026_09_30/`) partly reproduces the shape of some of
    his distributions, only after his time filter; the numbers do not match exactly.
  - The author's zones and times are the session's final extreme, the object of hard rule 10. How to transfer them is
    the operator's О13; О12 (reactions) is paused.
  - Lens 7 (independent audit of 5-6): over-strong claims corrected (M7 table only a hypothesis, no global «no
    clusters» / «no path memory», partial replication); the time contract documented (history from its last M5
    close); event «passports» proposed. Found in code: tooltips still saying «окончательный экстремум» and
    similar sessions already inside a pullback place counted as arrivals — both wait for the operator (О15).
  - Lens 8 (the curator's directive, `meaning/lens/2026-09-30-linza-8.md`): one frozen contract for «a new arrival in a
    pullback place while the scenario is alive, then +1.0 before the DR break» (`studies/lens8_2026_09_30/dogovor.md`,
    version 1.1 after an independent blind reading of 21 synthetic paths), and the size of the mismatches already found
    on NQ RDR 2016–2025. Research only; nothing on the screen changed. The operator's three product decisions of the
    directive's §12 are open as О14, О13 and О9, with О15.
  - Lens 9 (the auditor's cluster specification and its patch): the base map's event is «the first new arrival after a
    closed M5 slice», with no chosen target; the lens 8 scenario is a separate module with its own group. The answer fills
    the passports of six screen elements: the star, the contour's price axis and the place row's price show the first
    entering bar's depth, not an arrival. Four requirements of the operator are relayed there (M5 as the minimum step, no
    automatic setup, no own strategy yet, different histories up to the midpoint); they wait for his confirmation, and
    the screen does not change before it (`meaning/lens/2026-09-30-otvet-9.md`, `docs/DECISIONS.md`).
  - Lens 10 (time-first field, patch 2.1: Baseline at the activation M5, Dynamic maps after it) and, at the operator's
    request, the executor's own synthesis of all lenses: **`meaning/08-semantika-klasterov.md`** — the base object is the
    field «which prices the range of every next M5 of the similar sessions reached», first arrival is derived, the map at
    t0 is a snapshot, never rewritten. Read it before touching the clusters. The operator settled О16 and О17 the same
    day (the author's skeleton unchanged; a 15-minute activation family, then M5; `meaning/lens/2026-09-30-linza-11.md`);
    open: the weekday in the key (О18) and the go-ahead to implement.

- **The working screen is «Созвездия» design 22 «смысл числа», on market data** (since 2026-09-29; design 21 from
  2026-09-28 before it). `http://127.0.0.1:8767` opens it (`lab/dist/index.html` + `sozvezdiya.js`, built from
  `design/sozvezdiya-22/src` with its `build.py` — edit there, never the built file; building 21 would overwrite it); the previous screen is
  `/classic.html`. Its data: `lab/scene21.py` (`/api/day`, `/api/cohort`) over a new base of every session
  (`lab/build_boxes.py`, `lab/.runtime/boxes_*`). Every number on it is defined in `docs/SEMANTICS.md` («Экран
  «Созвездия»»); which UI rules it replaces is in `docs/UI_RULES.md`. Start at `design/README.md` for the design story,
  his remarks round by round and what is open.
- **Redesign B′** (`docs/DESIGN.md`) was chosen on 2026-09-25 and then superseded by the rounds above.
- **Strategy formalized, decisions pending.** `docs/STRATEGY.md`: the 12 choices of §15.1 are defaults until the
  operator decides; the screen ideas of §16.2 (session-model strip, past levels, imbalances, entry window, signal card,
  checklist) should be folded into B′ only when he approves them.

## Map

```
start-dr-lab.cmd / .ps1   the operator's shortcut target: TradingView (port 9222) -> history -> server -> page
stop-dr-lab.cmd / .ps1    stop the local server
lab/
  server.py               local HTTP server 127.0.0.1:8767 (stdlib): static page + JSON API
  scene21.py              the working screen's data: the trading day from TradingView, similar sessions at a minute
  build_boxes.py          builds every session box (confirmed or not) with its M5 bars (once; ~20 s per instrument)
  build_market.py         builds the history base from the G3 market tape (once; ~30 s per instrument)
  engine_market.py        history queries over the built base (the research dashboard, API /api/query, /api/scene)
  live.py                 the live session: fetch from TradingView, DR state, overlay from similar sessions, replay
  tv_fetch.mjs            reads M5/M1 bars from TradingView Desktop via Chrome DevTools (tradingview-mcp internals)
  engine.py               synthetic demo engine (python lab/server.py --data demo); never mixed with market data
  dist/                   front end: index.html + sozvezdiya.js (the working screen «Созвездия», built from
                          design/sozvezdiya-22), classic.html + app.js + live.js + styles.css (the previous screen)
  .runtime/               git-ignored: built history, live candles, server logs
studies/                  research scripts with their results (intermarket.py: NQ/ES/YM relations; m7_claims.py: the
                          author's claims and his time-and-price procedure on our tape; audit_2026_09_29/: geometry
                          nulls, the anchor, the screen replayed on 2016-2025)
meaning/                  the semantic layer for agents without code (Russian): start at meaning/README.md; texts of
                          semantic lenses and our answers in meaning/lens/
README.md                 the front page on GitHub: what this is, who reads what, the current design picture
tests/smoke.py            offline checks; run after every change
tests/ui_check21.js       in-page check of the working screen; evaluate it in the browser (ui_check.js: classic.html)
docs/                     everything an agent needs to understand and extend the tool
design/                   mockups on synthetic data, designs 1-22, start at design/README.md; design 22 is also the
                          working screen (built from design/sozvezdiya-22)
```

## Hard rules (do not break; if a task seems to need it, ask the operator first)

1. **Market data is never committed or published.** The tape and everything built from it (`lab/.runtime/`) stay
   local. The repository is public.
2. **2026 stays hidden in the history base.** The build stops at 2025-12-31 ET; `tests/smoke.py` checks it. The 2026
   tape is the forward observation of the G3 research line.
3. **No Volume** anywhere in the method.
4. **Local only.** The server binds 127.0.0.1. Do not expose it, do not deploy it as a web service.
5. **Live candles are displayed, never written into the history base or its statistics.**
6. **Prefix honesty.** At an observed minute the overlay uses only what was known then: DR, confirmation and DR break
   from closed M5 only; the current price from the forming M5; similar sessions measured strictly after the same
   minute. Replay must obey the same rule (bars after the replay minute are shown, never used). **Amended 2026-09-30
   (operator):** the clusters' statistics use closed M5 only. A slice is a closed M5; the similar sessions are taken at
   the same close and measured after it; the live price is only drawn between closes. The working screen still matches
   by the minute price until its change is approved (`meaning/02-sobytiya.md` §2, `meaning/08-semantika-klasterov.md`).
7. **Descriptive numbers.** Frequencies are the history of similar sessions, not a forecast, not a trade. The UI does
   not print disclaimers (operator's decision), so the discipline lives in the code and in `docs/RESEARCH.md`: never
   add a number to the screen whose meaning is not defined in `docs/SEMANTICS.md`.
8. **The demo engine stays separate** (`--data demo`) and never mixes with market data.
9. **API contract changes update both sides** (server and `dist/`), and `docs/ARCHITECTURE.md`.
10. **Clusters answer the operator's question, not an agent's.** The operator trades DR/IDR: after the box / the
    confirmation, at this candle, the question is WHERE price of similar sessions CAME and WHEN. A star = a similar session's
    first arrival in a place ahead of the price; a place's percentage = how often price came there. **Never** build
    clusters, percentages or times from a session's final extreme until the close («окончательный экстремум», «самое
    дно/верх дня»): on 2026-09-28 agents put that object in place of the operator's question without being asked. The object
    itself is real in the author's method (the Time & Price of the maximum retracement, `docs/STRATEGY.md` §6.3), but it
    answers a different question; on the screen it piled every cluster up at 15:50–16:00 and cost the operator a day of
    confusion (2026-09-29). Any new number must answer a question the operator asked, in the
    operator's words; if unsure, ask in one plain sentence before building.
    **Amended 2026-09-30 (operator):** the base object is the path of the author's family per M5. The family is the same
    session, direction and 15-minute confirmation window, counted from the start of the trading window; it is fixed for
    the day. For every next M5 the object says which prices, in each session's own IDR scale, the family's M5 high–low
    ranges reached (`meaning/08-semantika-klasterov.md`). First arrival is a derived number. The ban on the final extreme
    stays. The working screen still shows first arrivals until its change is approved.

## How to verify your change (always, before saying "done")

```bash
python -B tests/smoke.py                 # offline: history, queries, live state, replay, JS syntax
```

Then, if you touched the server or `lab/*.py`: **restart the server** (it caches Python modules; an edited
`live.py` is NOT picked up by a running server):

```bash
stop-dr-lab.cmd                          # or kill the process listening on 8767
start-dr-lab.cmd -NoBrowser              # the same path the operator's shortcut takes
```

If you touched the page: edit `design/sozvezdiya-22/src` and run its `build.py` (never build `design/sozvezdiya-21`:
it would overwrite the working screen) (it writes `lab/dist/index.html` and
`sozvezdiya.js`), open http://127.0.0.1:8767 in a browser tool, wait ~6 s, evaluate `tests/ui_check21.js` and expect
`problems: []`. Check at 1600×900 and 1920×1000 at least. Hover a constellation and every panel line, click a candle
(replay) and «К текущему». The mockup (`design/sozvezdiya-22/built/index.html`) must keep working too. For
`/classic.html` the old check is `tests/ui_check.js`.

## Gotchas already paid for

- **Stale server modules.** Symptom: the page says "Локальный сервер не ответил" or panels are empty after a backend
  change. Cause: the running server imported the old `live.py`. Restart it.
- **Drawing errors used to look like server errors.** `liveFetch` now logs draw errors to the browser console
  (`drawLive`). Read the console before blaming the server.
- **TradingView must be started with the debugging port 9222.** A TradingView opened from its normal icon has no
  port; the launcher restarts it through `tradingview-mcp` (`node <TV_MCP_DIR>/src/cli/index.js launch`).
- **Readiness of a switched chart.** After `setSymbol`, `chart.symbol()` changes before the bars do; old bars of the
  previous symbol can be read as the new one. `tv_fetch.mjs` waits for the series' own `symbolInfo()` to match,
  `isLoading()` false and a stable bar count. Keep that logic.
- **Prefer reading an existing pane.** If the operator's layout has a pane of the future on 5 (or 1) minutes, bars
  are read from it without switching anything, and the live panel refreshes every minute. Otherwise the active chart
  is switched for 2–4 s and restored, and the cadence drops to 5 minutes. He currently has NQ 5m and NQ 1m panes.
- **PowerShell 5.1 and Cyrillic.** `.ps1` files with Russian text must be saved as UTF-8 **with BOM** and CRLF.
- **Python.** The operator's Python with numpy/pandas is `%LOCALAPPDATA%\Python\bin\python.exe` (3.14);
  `C:\Python313` has no numpy. The launcher probes candidates.
- **Stale page after an update.** The server sends `Cache-Control: no-cache` for static files; keep it, or the
  operator's browser may run an old `live.js` after your change.
- **Do not pipe the launcher in bash** (`start-dr-lab.cmd | tail`): the hidden server inherits the pipe and the
  command never returns. Run it directly from PowerShell (`& start-dr-lab.cmd -NoBrowser`).
- **Disk C: can fill up.** On 2026-09-30 it reached 0 bytes free and a study failed while writing its per-state
  records. Keep such records compressed and small (`.json.gz`). The earlier big ones (audit, lens 4, the m7 cache) were
  moved, not deleted, to `D:\dr-idr-runtime-archive\2026-09-30`; `studies/m7_claims.py` rebuilds its cache if it is
  missing. Never touch `boxes_*`, `market_*` or `live/`: the screens read them.
- **Label collisions.** Right-side level labels are laid out with a minimum gap (`labels` in `drawLive`); hover guides
  hide the labels they would cover and restore them after. New text on the chart must go through the same layout or
  be checked with `tests/ui_check.js`.

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

Ports: 8767 (DR Lab), 9222 (TradingView debugging).
