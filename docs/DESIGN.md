# Redesign of the DR Lab screen — the chosen variant B′ (not implemented yet)

> **Superseded on 2026-09-28.** After B′ the operator asked for new variants; the working screen is now design 21
> «Созвездия» (`lab/dist/index.html`, source `design/sozvezdiya-21/`, meaning in `docs/SEMANTICS.md`). His remarks
> round by round are in `design/README.md`. This page stays as the record of B′. Since 2026-10-07 the main line is
> screen 24 «Границы хода» (`design/sozvezdiya-24/`, `spec/ekran-24/`).

Status on 2026-09-25: the operator chose this design on an interactive canvas; **the running tool still follows
`docs/UI_RULES.md`**. This file is the target for the implementation. Where it contradicts `docs/UI_RULES.md`, the
newer operator decision recorded here wins once the implementation starts; until then change nothing in the running
tool without asking the operator.

- Canvas (the operator's private Claude artifact, interactive, press Play on an artboard):
  https://claude.ai/artifact/Hyhworqk9xqZtmWqbV4ev2 — row 1 `B′ · Сценарий — выбран`, row 2 the first three variants
  (A «Терминал», B «Сценарий», C «Чистый график») kept for reference.
- Mockup sources, the published artboards and screenshots: `design/redesign-2026-09/` (see its README). The mockup
  draws a **synthetic** day and a **simulated** similar-session cohort; only the look and the behaviour are the target,
  never the numbers.

## How the operator reads the screen (what the design serves)

A session goes through four states, each with its own question: the DR window forms (watch it build); DR formed, no
confirmation yet (which side and when); confirmed — **risk** (will the DR hold; the opposite DR edge), **entry** (where
and when the pullback ends: the red clusters), **target** (how far and when: touch probabilities, the green clusters);
and **replay** — the screen as of any past close, to check the forecast against what happened. Priority on screen:
candles → DR/IDR lines → clusters → numbers → history charts. Numbers belong next to the object they describe (on the
axes and in the one-line inspector), never in a place the eye has to search.

## Why (what the operator disliked)

"Raw" look: text on text, labels overlapping, windows arranged poorly, cluster colours clashing. The cause of the
cluster "mud": low-opacity green / yellow / red on a near-black ground turns olive-brown, and shares hues with the
candles and several lines. Numbers were far from the objects they describe, so the eye had to search.

## What the operator decided (2026-09-24 … 25, live chat)

1. **Candles like TradingView in structure**, not in colour: body/wick proportions, spacing, crisp edges. Body width
   follows TradingView's own formula (below); measured on the operator's chart: 5 px bodies at 6.6 px bar spacing.
2. **The whole trading day on one chart** — evening, ADR, ODR, RDR with their own DR/IDR (as the Pine indicator draws
   them); the session selector picks the session whose forecast is shown and moves the view to it, it never crops the
   chart. **Mouse-wheel zoom** around the cursor and **drag scrolling** over the day are essential.
3. **Everything linked both ways**: a level, zone or number in the side column lights its object on the chart (with its
   prices on the price scale and times on the time axis); an object hovered or clicked on the chart lights its row and
   the matching bars of the history charts. No searching with the eyes.
4. **Variant B «Сценарий» chosen** for how the clusters are drawn (soft areas with iso-lines), with changes:
   - **Continuation (extension / the far extreme) is green**, drawn as a soft cloud with iso-lines;
   - **Pullback (retracement) is red and drawn as triangles**, not squares, so the two kinds never blend where they
     overlap; the triangle points the way of the pullback (down after a long confirmation, up after a short);
   - **percentages much quieter**: small, grey, no frames or pills around them (they took too much space).
5. **From variant C: scrubbing along the bottom.** Moving the mouse along the band above the time axis: over the past it
   shows the screen as of that candle close (the forecast of that moment — the replay without clicking candles); over
   the future it lights all clusters of that 15-minute column. Fast browsing is the point.
6. Candle-click replay stays (click = the screen as of that close, click again = back to live).

## Layout of B′ (1920 × 1000 desktop)

| Area | Content |
|---|---|
| Toolbar, 44 px | ☰ research menu · NQ ES YM · ADR ODR RDR (dot: running / done) · date · layer toggles (Откат, Экстремум, Веер, Лесенка) · LIVE clock, or the yellow «Повтор SESSION · HH:MM · В live» chip · refresh |
| Chart | plot + price scale 132 px on the right; legend top-left (NQ1! · 5 · session, confirmation chip, OHLC of the bar under the crosshair); zoom buttons − + ↺ bottom-right |
| Scrub band, 30 px | above the time axis; extension-time bars up (green), retracement-time bars down (red), future of the moment only |
| Time axis, 28 px | 14 px labels; tags: now (dark), replay moment (yellow), guide times (object colour), crosshair |
| Day strip, 46 px | the whole day 18:00→17:00: session segments with confirmation and result, closes sparkline, the visible window as a frame, now and moment marks; click a segment = go to that session, click elsewhere = centre the view there |
| Side column, 372 px | inspector (one line: what is under the pointer, else the session now) · РИСК (DR holds %, the opposite DR edge as «Слом DR: закрытие M5 ниже/выше …») · ВХОД — откат закончится (zones 1–3) · ЦЕЛЬ — касание до конца сессии (levels with bars, the price line between them) · ЭКСТРЕМУМ · ПРОДОЛЖЕНИЕ (zones 1–3) |
| History row, 168 px | the six charts of the same cohort: path, depth × time, retracement, extension, their times |

## Visual language

- Ground `#0B0D10`, panels `#0F1216`, dividers `#1E232B`; text `#D1D4DC` / `#B2B5BE` (TradingView), font stack of
  `docs/UI_RULES.md` rule 7 unchanged.
- Candles `#089981` / `#F23645`. **Clusters: continuation `#34D399`, pullback `#FF5A5F`. Replay / moment `#F7C948`.**
- Candle body width for bar spacing `S` (lightweight-charts `optimalCandlestickWidth`, 1 px wick):
  `S in [2.5, 4] → 3`; else `w = floor(S · (1 − 0.2·atan(max(4,S) − 4)/(π/2)))`, `min(w, floor(S))`, `max(1, …)`, and
  `w − 1` when `w ≥ 2` is even (so the wick is centred). Pixel-snap the centre; 1 px wick; min body height 1 px.
- DR / IDR / STD / mid / open lines as rule 8; the lines of the non-active sessions at ~35 % opacity; the 0.1…0.9 IDR
  grid only inside the active DR window, its labels on small dark backdrops (they may sit over pre-session candles).
- Level tags live on the price scale, glued to their line (the operator's "0,5 / 1 / 1,5 … слитыми" — our reading; not
  confirmed): name + price; DR filled white, IDR outlined, STD/mid dark; the touch probability of an STD level as a
  quiet grey suffix. Tags never overlap: they stack, and a short tick marks the true price.
- Clusters: continuation = display cells blurred (9 px) into a cloud, clipped to the future of the moment, plus
  marching-squares iso-lines of a kernel density (levels 0.3 / 0.55 / 0.8 of the maximum); pullback = one triangle per
  display cell, size and opacity by density, plus one faint dashed outer iso-line. Zones 1–3 get a small numbered dot
  and a grey share next to them; details only under the pointer.
- Pills (confirmation, DR break) sit just above/below the confirming candle instead of on its close (proposal, rule 12).

## Interaction

- Wheel over the plot: zoom around the cursor (span 40 min … whole day); horizontal wheel or Shift: pan; drag: pan;
  wheel over the price scale: vertical scale; ↺: fit the active session. Batch wheel/mouse events per animation frame.
- Crosshair snapped to bar centres with price and time tags; the legend shows that bar's OHLC.
- One active pick at a time (rule 15). Hover previews, click pins, click again or on empty chart clears.
- Linked objects and what lights up:

| Pointer on | Chart | Side column | History row |
|---|---|---|---|
| zone row / zone mark | zone outline, its cells, guides to both axes with price and time tags | row | bins of its price and time |
| cluster cell (triangle or cloud) | the cell, guides and tags | the zone row it belongs to | its price and time bins |
| level line / tag | line thicker and glowing, tag inverted, others dimmed | the level / touch row | — |
| touch row | a dashed line at that level from the moment to the session end, tag with price and % | row | — |
| history bin / heat cell | its time × price cells (rule 16) | — | the bin |
| scrub band, past | the whole screen as of that close (moment line, later candles dimmed) | facts of that moment | the cohort of that moment |
| scrub band, future | all cells of that 15-minute column, guides | inspector: shares of pullback end and extreme in the column | time bins |
| candle | click: pinned replay | — | — |
| session label / day segment | that session's window lit; click: go there | — | — |

- Both cluster kinds are on by default (change of rule 21: the operator wants to read continuation and pullback
  together).

## Rules of `docs/UI_RULES.md` that change when this is implemented

| Rule | Now | B′ |
|---|---|---|
| 13 | green / yellow / red by probability | colour by kind (continuation green, pullback red), shape by kind (cloud / triangle), rank by number 1–3, density by brightness — **operator decision** |
| 14 | green guide labels | guide tags in the object's colour on the axes — proposal |
| 12 | pill on the candle close | pill beside the candle — proposal |
| 17 | pinned card left of the cluster | the inspector line in the side column replaces the floating card — part of the chosen B |
| 21 | extreme clusters off by default | both on — **operator decision** |
| new | — | whole-day chart, wheel zoom, drag scroll, scrub band, two-way linking — **operator decisions** |

Rules 1–11, 15, 16, 18–20, 22, 23 stay.

## What the implementation needs (not done)

1. **API.** `/api/live` returns one session's bars. B′ needs the whole trading day's M5 bars (evening → now) and the
   DR/IDR, confirmation, DR break and outcome of every session of the day; the overlay stays per active session and
   minute. Keep the prefix-honesty rule (AGENTS.md rule 6) for every minute of the scrub band.
2. **Scrubbing cost.** The band asks for the overlay at many minutes. Snap to M5 closes, cache per (instrument,
   session, minute) on the server and in the page, and prefetch the closes of the visible session after load
   (≈ 0.2–0.5 s each today).
3. **Front end.** Port the geometry of `design/redesign-2026-09/src/engine.js` (`_scene`, `_tagBoxes`, `_bottom`,
   `b2.js`) into `lab/dist/live.js`, replacing the synthetic cohort (`_ov`) with the server's overlay (the field names
   were kept close to `/api/live`: cluster cells, zones, fan, touch, charts). Divs or SVG both work; keep one pixel grid.
4. **Checks.** `tests/ui_check.js` must also cover price tags, zone marks and the inspector line; screenshots at
   1600 × 900 and 1920 × 1000; hover/scrub/replay/zoom by hand as AGENTS.md describes.
5. **Timing.** Change the running tool outside the operator's trading hours or behind a switch; the desktop shortcut
   must keep working from a cold start.

## Open questions for the operator

- What «сделать 0,5 / 1 / 1,5 … слитыми» meant: tags glued to the lines (implemented in the mockup) or solid lines
  instead of dash-dot.
- Rules 12 and 14 above (proposals).
- The screen proposals of `docs/STRATEGY.md` §16.2 (session-model strip, past DR levels, imbalances, entry window,
  signal card, checklist) — a separate session wrote them; fold them into B′ only after the operator decides.
