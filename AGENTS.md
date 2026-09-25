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
  many iterations; re-read them before any visual change. On 2026-09-25 he chose a redesign (`docs/DESIGN.md`,
  mockups in `design/`): it is the target of the next UI work and records which rules it changes; it is not
  implemented yet.

## Read in this order

1. `AGENTS.md` — this file: map, hard rules, how to verify, gotchas.
2. `docs/ARCHITECTURE.md` — the stack, processes, data flow, file responsibilities, API contract.
3. `docs/SEMANTICS.md` — exact definitions of every object and number (DR, IDR, confirmation, clusters, overlay).
4. `docs/UI_RULES.md` — the operator's interface requirements and the design tokens.
5. `docs/DECISIONS.md` — dated decisions and where they came from.
6. `docs/RESEARCH.md` — what has been measured, what is not established, and the open questions.

## Map

```
start-dr-lab.cmd / .ps1   the operator's shortcut target: TradingView (port 9222) -> history -> server -> page
stop-dr-lab.cmd / .ps1    stop the local server
lab/
  server.py               local HTTP server 127.0.0.1:8767 (stdlib): static page + JSON API
  build_market.py         builds the history base from the G3 market tape (once; ~30 s per instrument)
  engine_market.py        history queries over the built base (the research dashboard, API /api/query, /api/scene)
  live.py                 the live session: fetch from TradingView, DR state, overlay from similar sessions, replay
  tv_fetch.mjs            reads M5/M1 bars from TradingView Desktop via Chrome DevTools (tradingview-mcp internals)
  engine.py               synthetic demo engine (python lab/server.py --data demo); never mixed with market data
  dist/                   front end: index.html, app.js (history dashboard), live.js (live panel), styles.css
  .runtime/               git-ignored: built history, live candles, server logs
studies/                  research scripts with their results (e.g. intermarket.py: NQ/ES/YM relations)
tests/smoke.py            offline checks; run after every change
tests/ui_check.js         in-page check for text overlaps and layout; evaluate it in the browser
docs/                     everything an agent needs to understand and extend the tool
design/                   interactive mockups of the chosen redesign (synthetic data), see docs/DESIGN.md
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

If you touched the page: open http://127.0.0.1:8767 in a browser tool, wait ~6 s for the live panel, evaluate
`tests/ui_check.js` and expect `problems: []`. Check at 1600×900 and 1920×1000 at least. Hover and click a cluster,
click a candle (replay) and click it again (back to live), click a bottom-chart bar twice.

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
