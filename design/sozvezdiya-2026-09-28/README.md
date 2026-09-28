# Design 20 «Созвездия» — the working variant (mockup, not implemented)

The synthesis of the operator's picks from designs 1–19, refined with him round by round on 2026-09-28. It is the 20th
entry of `design/all-designs/ИСТОРИЯ.html`. **Update this design in place** when he gives new remarks (he said so: «Не надо
21, обновляй 20»); a new number only when he asks for a separate variant. The general state, his remarks round by round and
the open questions are in [`design/README.md`](../README.md); this file is about the code.

**Synthetic data only.** The candles are the two invented days of `design/clusters-2026-09-28` (day A: RDR confirms ↑ 10:55
and holds; day B: confirms ↑ 10:45, «Слом DR ↓ 11:45»); `src/build.py` adds a few body gaps so the VIB layer has something
to show. The similar sessions are simulated in `src/app.js` (deterministic per day, session and minute). No market data,
not the lab's numbers.

## Build, open, check

```bash
cd design/sozvezdiya-2026-09-28/src
python build.py            # -> ../built/index.html (one self-contained page, ~130 kB)
sh shots.sh                # -> ../snap/*.png, look at them before saying "done"
python ../../all-designs/make_history.py   # copies the build into the history as design 20
```

Open `built/index.html` in a browser (it fills the window). States by address: `#conf` (live 13:08, confirmed),
`#wait` (replay 10:40, before confirmation), `#brk` (live 13:08 after «Слом DR ↓ 11:45»); add `&pin=pull:1` (a place by
side `cont|pull|up|dn` and number 1–3), `&slice=14:00` (its 15-minute slice), `&band=pull:max` or `&band=pull:24666` (a
price in the density column, as if hovered), `&strip=1`, `&at=11:35` (replay).
`window.__dr` exposes `st`, `render`, `cur`, `hit`, `V` for checks from the console. A local test server must not use
port 8767: that is the running DR Lab (`lab/server.py`).

## What is on the screen (and which design it came from)

| Element | Where it came from | How it works |
|---|---|---|
| Star field | 18 | every similar session = two dim dots: its continuation extreme and its pullback extreme after the moment (before a confirmation: «Верх» / «Низ») |
| Three places per side | operator, round 4 | pullback: «от верхней границы» (≥ −0,25 IDR from the confirmation edge), «от центра» (−0,25…−0,75), «retirement setup» (< −0,75); continuation: up to the next half-step from price, to the one after, beyond; before a confirmation: Верх «не выше DR / от DR high до +1,0 / выше +1,0», Низ mirrored. Share of a place = sessions whose extreme (after the first 15 minutes) fell in its price band, of all similar sessions; written small, like a background |
| Constellation of a place | 8–9 look | where inside the band the extremes lie densest: the connected region ≥ 38 % of the place's own peak that holds most of its sessions; glow brightness against the side's strongest peak |
| Hover on a constellation | operator, rounds 2 and 4 | the constellation lights, its band shows faintly, the 15-minute slice under the cursor is boxed and runs down to the time axis with its own times and prices; the strip column and the panel row light too; a click pins |
| First 15 minutes | operator, round 2 | not in the places (they would cover the last candle); dim dots, and one share per side in the panel |
| Fan and its median | 1 | 20–80 % of closes from the current position as a faint area; the median dashed 6/4, light grey, as in design 1 (SEMANTICS «веер») |
| Levels | 1 + operator | DR solid, IDR dash, mid dots, open faint, STD hairlines (the side in play brighter); DR/IDR of past sessions (ADR, ODR, RDR 23.09) the same white lines, dimmer; VIB boxes; every line named at its right end |
| Density by price | 3, 10, 13 + operator, round 5 | right of the price scale: longer and brighter where more extremes ended; the three densest bins per side labelled. Hover a bin: along its price band a profile by 5 minutes of when those extremes happened; the densest window (5 minutes, widened to neighbours holding ≥ 60 % of it) is boxed and runs down to the time axis, with its share in the tooltip (`timeCluster`, `bandRole`). The same for the price bars of the six history charts |
| Time strip | 4, 8 | 15-minute columns (continuation up, pullback down), brightness by share; grows on hover with numbers, a click pins |
| Six history charts | 1 | hidden in a handle at the bottom; open over the chart on hover, a click pins |
| Replay of a candle | 1 | a click on a candle: the screen as at its close (prefix honesty: later bars shown dim, never used); ← → step, Esc back |
| TradingView mouse | 5–6, 11–16 | drag = pan (vertical drag turns auto scale off), wheel = zoom at the cursor, price scale drag/wheel = price zoom, time scale drag = time zoom, double click on a scale = reset, Alt+R, buttons − + ↺ |
| Panel | 17–19 + operator | session; the day now (each session's confirmation, DR status, where price is against its DR); «Дальше по похожим» (next STD step and its share, DR holds, the most frequent place per side); «Места» (three per side, linked both ways) |
| Settings | operator, round 3 | «⚙ Настройки»: every colour, brightness, line width and style; kept in this browser (localStorage key `drlab.sozvezdiya.cfg`); «Сбросить» |

## Code map (`src/app.js`, one IIFE, plain canvas 2D)

| Part | Functions | Change here to… |
|---|---|---|
| Constants, settings | `SESS`, `PREV`, `C`, `PAL`, `DEF`, `SCHEMA`, `DASH`, `LAYERS` | add a colour or slider: a key in `DEF` + a row in `SCHEMA`, then read `cfg.<key>` where drawn |
| Day and session | `day`, `sess`, `levels`, `where` | session rules (port of `lab/live.py`: DR from wicks, IDR from bodies, confirmation = first M5 close beyond DR, break = close beyond the opposite DR) |
| Similar sessions (simulated) | `walk`, `simulate`, `overlay`, `role` | the cohort per mode `conf` / `brk` / `wait`; `ov.touch(p)` = share that reached a price; `ov.holds` = DR holds |
| Places and constellations | `zoneDefs`, `zoneOf`, `sliceOf`, `kde`, `blur`, `contour`, `fanOf` | the three price bands per side, the density, the core region, the 15-minute slice, the fan |
| View | `st`, `cur`, `setScene`, `selSession`, `replayAt`, `geom`, `autoRange` | state, scenes, replay, layout (plot, price scale, density column, strip, handle) |
| Drawing | `render` and `draw*` (`drawGlow`, `drawStars`, `drawContours`, `drawMarks`, `drawWindow`, `drawLevels`, `drawPrev`, `drawVib`, `drawFanBand`, `drawTyp` (= the median), `drawProj`, `drawStrip`, `drawTags`, `drawPriceAxis`, `drawTimeAxis`, `drawLegend`, `drawHist`) | the look of each element |
| Interaction | `hit`, `tipHtml`, mouse / wheel / key handlers, `click`, `animStrip`, `placeNav` | what is under the cursor, tooltips, TradingView navigation, the drawers |
| Panel and menus | `toolbar`, `panelHtml`, `panelMarks`, `cfgPanel` | right panel, «Слои», «⚙ Настройки» |

`src/page.html` holds the layout and CSS (toolbar, panel, menus); `src/build.py` inlines the days and `app.js` into
`built/index.html`. Hover state is `st.hover` (or `st.pin`), e.g. `{k:'con', role, id, slice}`, `{k:'col', t0, t1}`,
`{k:'pband', pLo, pHi, list|role}`, `{k:'lvl', id, l}`; every draw function reads `hv()` to light or dim.

## Numbers not defined in `docs/SEMANTICS.md` yet

They are fine in a mockup but need a line there (and the operator's agreement) before any implementation: the place and
its share (price band of the side, after the first 15 minutes), the constellation core (≥ 38 % of the place's peak), the
15-minute slice share, the first-15-minutes share, the densest time window of a price band (5-minute bins, widened to
neighbours holding ≥ 60 % of the peak). Defined already: the fan (median and 20–80 %), touch until the end of
the session, DR holds.
