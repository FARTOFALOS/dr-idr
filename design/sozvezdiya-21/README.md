# Design 21 «Созвездия» — the working screen of DR Lab (and its mockup)

One source, two builds (`src/build.py`): `built/index.html` — the mockup on two synthetic days (self-contained); and
`lab/dist/index.html` + `lab/dist/sozvezdiya.js` — **the working screen** (since 2026-09-28): without the synthetic
days the same code takes the trading day from `/api/day` and the similar sessions from `/api/cohort` (`lab/scene21.py`).
Edit only `src/` and rebuild; never edit the built files. The chart is design 20's (`src/app.js`); the panel is
`src/panel21.js` + `src/panel21.css`. History: the second agent proposed a semantic panel; the operator kept only what
earns its place (round 6), then the strategy's targets, time and risk filled the rest (round 7, `design/README.md`).

Rules for the panel (the operator's):

- percentages only, never session counts;
- no line that repeats what the chart shows at a glance;
- every line is a link: hovering it lights on the chart what it says, a click pins it.

What is on it: «Дальше по похожим» (next STD step and the share that reached it; «DR удержится»; where continuation and
pullback end most often; the first 15 minutes; before a confirmation ↑ / ↓ / нет and the shares that reached DR high /
low) and «Места» (three per side: share, the densest price inside, its time window). Links: a step lights its line and
the densest window of first reaching it (`firstTouch`); a place lights its borders, its constellation and its densest
spot (`hotOf`: the densest 0.1 IDR price step, then its densest 5-minute window widened to neighbours ≥ 60 %) down to
the time axis; DR holds and ↑ / ↓ light the DR line. The confirmation-time contours moved to «Слои».

Below «Места»: **Цели** (`targets21`: the next STD steps, the session extreme, past sessions' DR, the nearest open VIB,
with «дошли» and «обычно к»), **Время** (the median and 70 % times of the extremes), **Где сценарий сломан** (DR holds,
retirement −0,75 and DR after touching it, the empty interval `gapOf`). All numbers are defined in `docs/SEMANTICS.md`.

Build and check: `cd src && python build.py`. Mockup: open `built/index.html`; states as in design 20 (`#conf`,
`#wait`, `#brk`, …) plus `&hl=N` = as if the N-th panel line were hovered. Working screen: http://127.0.0.1:8767
(after a server restart if `lab/*.py` changed), `#at=11:40`, `#session=ODR`, `#inst=ES` open a replay; evaluate
`tests/ui_check21.js` in the page.
