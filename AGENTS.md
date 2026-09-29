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

## Where the work stands (2026-09-29)

- **Semantic audit and design 22 (2026-09-29).** The operator asked for a deep audit of the whole system and then for
  the next design built on its conclusions, with the repository made readable for a semantic agent without code.
  Results: `meaning/03-dokazatelstva.md` (studies in `studies/audit_2026_09_29/`, all aggregates); design 22 is a
  the working screen since the same evening (`design/sozvezdiya-22/`, `meaning/04-dizajn-22.md`); `/api/cohort` sends
  own DR (`uH`, `uL`) and `wick` per similar session. Stars and places were then switched to first arrivals (hard
  rule 10).

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
                          design/sozvezdiya-21), classic.html + app.js + live.js + styles.css (the previous screen)
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
   minute. Replay must obey the same rule (bars after the replay minute are shown, never used).
7. **Descriptive numbers.** Frequencies are the history of similar sessions, not a forecast, not a trade. The UI does
   not print disclaimers (operator's decision), so the discipline lives in the code and in `docs/RESEARCH.md`: never
   add a number to the screen whose meaning is not defined in `docs/SEMANTICS.md`.
8. **The demo engine stays separate** (`--data demo`) and never mixes with market data.
9. **API contract changes update both sides** (server and `dist/`), and `docs/ARCHITECTURE.md`.
10. **Clusters answer the operator's question, not an agent's.** The operator trades DR/IDR: after the box / the
    confirmation, at this candle, the question is WHERE price of similar sessions CAME and WHEN. A star = a similar session's
    first arrival in a place ahead of the price; a place's percentage = how often price came there. **Never** build
    clusters, percentages or times from a session's final extreme until the close («окончательный экстремум», «самое
    дно/верх дня»): agents invented that on 2026-09-28 without being asked, it piled every cluster up at 15:50–16:00 and
    cost the operator a day of confusion (2026-09-29). Any new number must answer a question the operator asked, in the
    operator's words; if unsure, ask in one plain sentence before building.

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

If you touched the page: edit `design/sozvezdiya-21/src` and run its `build.py` (it writes `lab/dist/index.html` and
`sozvezdiya.js`), open http://127.0.0.1:8767 in a browser tool, wait ~6 s, evaluate `tests/ui_check21.js` and expect
`problems: []`. Check at 1600×900 and 1920×1000 at least. Hover a constellation and every panel line, click a candle
(replay) and «К текущему». The mockup (`design/sozvezdiya-21/built/index.html`) must keep working too. For
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
