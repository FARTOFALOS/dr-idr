# DR Lab screen design — start here (state of 2026-09-29)

If you join the design work, read this page, then open the pages below. Everything in `design/` is a **mockup on
synthetic data**, except that **design 22 «смысл числа» is the working screen of DR Lab on market data since
2026-09-29** (`lab/dist/index.html` is built from `design/sozvezdiya-22/src`; design 21 was the working screen on
2026-09-28). Its meaning, pictures and open questions: `meaning/04-dizajn-22.md` (Russian, no code needed). **Stars,
constellations and place percentages = where and when price of similar sessions CAME after this candle** (operator,
2026-09-29); never the session's final extreme (AGENTS.md hard rule 10).

## Design 24 «Границы хода» (2026-10-01)

A separate version next to the working screen, at the operator's order: design 22's screen with the statistical layer
of the semantic specification DR-LAB-SEM-1.0 (`meaning/lens/2026-10-01-spec-v1/`). It runs on market data at
`http://127.0.0.1:8767/24/` (the shortcut «DR Lab 24»); any date of 2006–2025 opens as if it were today, so it can be
reviewed without a live confirmation. Code, the element-by-element table against design 22, the choices the executor
made and how to check: [`sozvezdiya-24/README.md`](sozvezdiya-24/README.md); snapshots in
[`sozvezdiya-24/shots/`](sozvezdiya-24/shots/). Design 22 is unchanged and stays the working screen.
Since 2026-10-01 evening its clusters are the **zone map** `zone-map-3` (`meaning/12-karta-zon.md`): several price ×
time zones of R / X with their share of the family and today's status; the weekday family by default, all weekdays
only by an explicit click.
Since the same night its look is the variant **«Окна времени»** the operator chose from three mockups (canvas «DR Lab ·
экран 24»), with the constellation look he chose from twelve (canvas «DR Lab · созвездия»: «дымка и нити», amber R, sky
X): R and X on screen together, zones drawn as constellations, the time band under the chart (X up, R down, every zone a
hill), a hovered zone or price band linked to its peak 15 minutes, the inspector at the bottom right instead of a
tooltip, six windows of the family sliding up from the bottom edge. The meaning of every number is unchanged
(`meaning/10-dizajn-24.md` §3а).

## Where we are, in one paragraph

The operator (a trader of the DR/IDR method, RDR and ODR sessions) wants DR Lab, his second screen next to TradingView,
to show for the current session **where and when price went most often in 20 years of similar sessions** («куда вообще
цена доходила по истории чаще всего — кластеры»), on a TradingView-like chart with the DR/IDR/STD levels and the day's
structure. Twenty-one screen designs exist, all numbered in one history page. He picked parts from 1–19, we built 20,
refined it round by round, reworked its right panel as 21 with a second agent, and on 2026-09-28 he made **21
«Созвездия» the working screen** of DR Lab on market data (http://127.0.0.1:8767; the previous screen is
`/classic.html`). On 2026-09-29 design 22 replaced it (round 8). Further remarks go into design 22.

## Open the work

| What | Where |
|---|---|
| All designs 1–22 and 24, numbered, each live inside the page (24 as snapshots: it runs only on the local server) | `design/all-designs/ИСТОРИЯ.html` (open the file in a browser) |
| Design 24: the meaning of its percentages with numbered pictures / the code | `meaning/10-dizajn-24.md` / [`sozvezdiya-24/README.md`](sozvezdiya-24/README.md) |
| Design 22 full screen (the current proposal) | `design/sozvezdiya-22/built/index.html` |
| Design 22 explained with numbered pictures | `meaning/04-dizajn-22.md` |
| Design 20 full screen | `design/sozvezdiya-2026-09-28/built/index.html` |
| Design 21 (20 + the reworked right panel) | `design/sozvezdiya-21/built/index.html` |
| Design 20: what is on screen, code map, build, checks | [`sozvezdiya-2026-09-28/README.md`](sozvezdiya-2026-09-28/README.md) |

## Folder map

```
design/
  README.md                     this page
  all-designs/                  the history: ИСТОРИЯ.html + everything it runs
    make_history.py             rebuilds the page and interactive/ (python make_history.py; --shots re-takes images/)
    interactive/                every design as a runnable page (01-...20-); support.js = Claude Design runtime, git-ignored
    images/                     snapshots of every design and state
    sources/                    sources that exist nowhere else: v1-sglazhennye (8-10), 17-19-svezhiy-vzglyad (page, notes, brief)
  sozvezdiya-2026-09-28/        design 20, the working variant (src/ -> built/index.html; snap/ git-ignored)
  sozvezdiya-21/                design 21 = design 20 + the right panel of round 6 (src/panel21.js, panel21.css); the working screen
  sozvezdiya-22/                design 22 = design 21 changed by the audit of 29.09 (src/app.js, panel.js, panel.css); a proposal
  sozvezdiya-24/                design 24 = design 22's screen + DR-LAB-SEM-1.0 (src/ -> lab/dist/24/; shots/); next to the working screen
  clusters-2026-09-28/          designs 8-16 (canvas artboards, .dc.html) and the synthetic days gen_days.py used by 20
  semantic-2026-09/             designs 5-7, another session's semantic concept (CONCEPT.md, prototype.html)
  redesign-2026-09/             designs 1-4 (24-25.09); B′ (4) was chosen then, spec in docs/DESIGN.md
```

Canvases on claude.ai (the operator's private artifacts): designs 1–4 https://claude.ai/artifact/Hyhworqk9xqZtmWqbV4ev2,
designs 11–16 https://claude.ai/artifact/9NTzLxzdq8qiBRDjpqoDR7. The local pages above are enough to work.

## How the operator works with us

- He writes in Russian, often by voice (the transcription can be garbled: read for intent, ask only if two readings
  lead to different work). Answer in Russian, plainly, short.
- He wants **working** screens, not pictures: every design must be clickable as intended; check interactions yourself
  (build, `shots.sh`, a browser) before you say it works, and say what you did not check.
- He decides the meaning. Do not invent new definitions or taxonomies («не выдумывайте супер новые технологии»); the core is
  «кластеры — где цена бывала чаще всего; уровень — это всего лишь уровень». A number that `docs/SEMANTICS.md` does not
  define must be listed as undefined (see design 20's README).
- He refers to designs by number and gives picks per number; apply them to design 20 in place.
- He asked us to work as two equal agents on the design (see «Two agents» below). Sub-agents otherwise only when he says.
- Commit only when he asks. The repository is public: no market data, no tape-derived files in `design/`.

## His remarks, round by round (28.09), and what was done

**Round 1 — picks from 1–19 → design 20 built.** From 1: DR/IDR stand out from other lines; the fan in the background
of the future with its middle line («как шла цена»); keep the six history charts (at least collapsible); click on a
candle shows the screen as it was at that candle. From 5–6 and 11–16: TradingView navigation (drag to move, wheel,
scales), price scale right, time bottom. From 3, 10, 13: projections of the clusters by price. From 4, 8: the time strip
at the bottom, but taller and opening on hover. From 8–9: densities drawn as natural shapes, not squares. From 18: the
star field of sessions, but not its percentage chips («137 из 519» not needed), not its day boxes with W, not its
background. Also: pure black, no grid; past sessions' levels readable and named at the right edge; VIB with a switch;
hover shows everything; the next candle must not be covered by a blot.

**Round 2 — on 20.** Zoom buttons vanished under the mouse (fixed); density by price to the right of the price scale;
the fan's middle as a line, not candles; percentages must contrast; past DR/IDR as plain white lines like today's;
STD lines informative on hover; the day section must say what the day is now and what we wait for; less bright colours
(no yellow-blue); the six charts should open on hover instead of taking space; the densest levels brighter, not only
longer; remove the «≤15 мин» boxes at the price; update 20 in place and let it open full screen.

**Round 3 — on 20.** A settings button for all colours, brightness and lines (done: «⚙ Настройки», kept in the browser).

**Round 4 — on 20.** Percentages small and background-like, no outline (done). Hovering a constellation
must light the 15-minute square under the cursor and carry it down to its time (done). The fan's middle line exactly as
in design 1 (done: median, dashed). Replace the levels table in the panel by the most sensible menu from all variants
(done: the «Места» list of 17–19, three per side). Always three constellations per side: pullback «от верхней границы,
от центра, либо retirement setup от низа», and three the same way for the continuation (done; the band limits are our
proposal, see below). Prepare the folder so another agent can take over easily (this page).

**Round 5 — on 20.** Hovering a bar of the density by price (e.g. the 11 % one) must show when those extremes happened:
the densest time window of that price band, 5 or 10 minutes or wider, down to the time axis (done: a 5-minute profile
along the band, the densest window boxed with its time and share; also for the price bars of the six charts).

**Round 6 — the right panel (design 21, the second agent's variant, reworked).** The second agent proposed a semantic
panel (day models, squeeze, widths, last-bar events, nearby past levels, an inspector instead of tooltips). The operator
kept only what earns its place: «Дальше по похожим» (next STD step and its share, DR holds, where continuation and
pullback end most often, first 15 minutes) and «Места» (three per side: share, the densest price, its time). His rules
for any text on the panel: **percentages only, never session counts**; **no text that repeats what the chart shows
at a glance** («ADR ↑ 20:45 · DR удержался · цена выше DR — зачем мне это читать?»); **every line is a link**: hovering
it lights on the chart what it talks about (a step: the line and when it was usually reached; a place: its borders,
its constellation and its densest spot with its time down to the axis); the densest bars of the price density must
stand out much more. Done in `design/sozvezdiya-21/` (panel in `src/panel21.js`); it is design 21 in the history.

**Round 7 — the working screen.** The empty lower half of the panel was filled with what the strategy needs for the
decision (after a review of `docs/STRATEGY.md`): **Цели** (targets ahead with the share that reached them and when they
usually did), **Время** (by when half and 70 % of the pullbacks and extremes had ended), **Где сценарий сломан** (DR
holds, the retirement zone and how often DR held after touching it, the empty interval for a stop); the day's models and
the box colour went into the choice of similar sessions before a confirmation, not into text. Then: «make 21 the main
working screen on market data, push to GitHub». Done: `lab/scene21.py` + `lab/build_boxes.py`, `lab/dist/index.html`,
definitions in `docs/SEMANTICS.md`, replaced rules in `docs/UI_RULES.md`, checks in `tests/smoke.py` and
`tests/ui_check21.js`.

**Round 8 — 29.09: the semantic audit and design 22.** The operator asked for a deep audit of the whole system (strategy,
calculations, studies, designs, external sources), then passed on two texts of a semantic agent («линзы»,
`meaning/lens/`), then asked for the next design built on all the semantic conclusions and for the repository to be
readable by a semantic agent without code (GitHub as the intermediary). Done: `meaning/` (the semantic layer),
`studies/audit_2026_09_29/`, design 22 in `design/sozvezdiya-22/`. The same evening the operator made 22 the working
screen and corrected it live: stars and places = first arrivals (on 28.09 agents had put the author's final-extreme object, STRATEGY §6.3, in place of the operator's question), fan back to the filled band, box fill by colour, smaller line names, VI by the ICT rule, wheel zoom anchored at
the session end. What changed and why: `meaning/04-dizajn-22.md`; open decisions: `meaning/05-otkrytye-voprosy.md`.

## Open questions

- **On market data** the places, times and targets are now real; watch whether the band limits, the 38 % core and
  the 15-minute exclusion still read well, and whether the VIB thresholds (NQ 2, ES 0,5, YM 5 points) fit.
- **Band limits of the three places** are ours: pullback −0,25 / −0,75 IDR from the confirmation edge; continuation at
  the next two half-steps from the current price; before a confirmation at DR high/low and ±1,0. Confirm with him.
- **The fan's middle line.** Now the median of all similar sessions (as defined); design 1 used a smaller cohort, so its
  median looked more jagged. If he wants more of that «heartbeat», ask before changing the definition.
- **What goes on the right** is still his open question; now: session, day, «Дальше по похожим», «Места».
- **Colours** are his to set (settings); defaults are muted mint (continuation) and coral (pullback).
- The numbers of design 21 are defined in `docs/SEMANTICS.md` («Экран Созвездия»); those of design 22 in the same file
  («Дизайн 22») and in `meaning/02-sobytiya.md` §3.
- The operator's decisions on design 22: `meaning/05-otkrytye-voprosy.md`.
- **Real data** will change the shapes: everything here is simulated; a session-end pile-up of extremes (15:30–16:00) in
  the mockups may or may not be real.
- **Implementation** (later, with his go-ahead): the API must serve the similar sessions' extremes as points (the star
  field), fan quantiles per 5 minutes, per-minute overlays for replay, whole-day bars and every session's DR.

## Guardrails for design work

- Port **8767 is the running DR Lab** (`lab/server.py`); never start a test server there, pick another port and stop it.
- Designs use the synthetic days of `clusters-2026-09-28/src/gen_days.py` (and `sozvezdiya-2026-09-28/src/build.py` adds
  VIBs); never load the tape or `lab/.runtime/` into a mockup.
- `all-designs/interactive/support.js` is Anthropic's canvas runtime copied for local viewing: git-ignored, never commit.
- Snapshots, browser profiles and `_tmp/` are throw-away; `.gitignore` files cover them.

## Two agents on one design

- Design 20 is two source files (`src/app.js`, `src/page.html`). Before editing, say which part you take (the code map
  in its README splits it: model, places, drawing, interaction, panel); rebuild and re-shoot after each change.
- To try an alternative without touching 20: copy the folder (`design/sozvezdiya-<idea>/`), and add it to the history as
  a new stage and number in `all-designs/make_history.py` (lists `STAGES` and `D`), then `python make_history.py`.
- Record each new round of his remarks above, with what was done and what stayed open.
