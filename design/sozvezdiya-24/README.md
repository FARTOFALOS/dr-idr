# Design 24 «Границы хода» — design 22's screen with the statistics of DR-LAB-SEM-1.0

**The meaning, for agents without code: [`meaning/10-dizajn-24.md`](../../meaning/10-dizajn-24.md)** — where every
percentage comes from, where and why it is fixed, how it is counted, every element on numbered pictures. This page is
about the code. Work on 24 goes on branch `design-24` in its pull request (operator, 2026-10-01).

Design 23 (`design/sozvezdiya-23/`, `/sem-v1/`, `/api/family-v1`) is another agent's first, minimal page of the same
specification, pushed to `main` on 2026-10-01; it is unchanged and runs next to 24. Design 24 is the product version.

A separate version of the DR Lab screen, built 2026-10-01 at the operator's order: **design 22's working screen
(candles, the day's DR / IDR, replay, the right panel, hover / pin, layers, settings) with its statistical layer replaced
end to end by the semantic specification DR-LAB-SEM-1.0** ([`meaning/lens/2026-10-01-spec-v1/`](../../meaning/lens/2026-10-01-spec-v1/README.md)).
**Since 2026-10-01 night design 24 is the working screen** (the operator; on branch `design-24`, not merged into
`main` until he says so): `http://127.0.0.1:8767/` redirects to **`http://127.0.0.1:8767/24/`** (`lab/server.py`), so
the shortcut «DR Lab» opens it, and «DR Lab 24» (`start-dr-lab-24.cmd`, the same launcher with `-Page 24/`) too.
Design 22 is not changed (its files are untouched) and stays at `/22/` (= its built page `/index.html`); «№22 ↗» in
the toolbar opens it on the same session and minute for comparison.

**The full specification of this screen** — every element on annotated screenshots, what it means, how and from what
it is counted, its denominator, the server and page code, how not to read it, the invariants and an audit procedure:
[`../../spec/ekran-24/`](../../spec/ekran-24/README.md). Change an element → update its row there and re-shoot
(`spec/ekran-24/tools/shots.py`, then `annotate.py`).

It runs on market data only (no synthetic mockup): «История» opens **any trading date of 2006–2025 as if it were today**,
its families taken only from earlier sessions, so the screen can be reviewed when the live session has no confirmation.
When the live day has none, the panel offers «Открыть … на истории» (the latest date on which that session confirmed).

**Why each visual rule exists** (the right edge anchored, «↺», the one R/X column, STD on the side in play, ...):
[`meaning/13-zhurnal-vizualizacii.md`](../../meaning/13-zhurnal-vizualizacii.md). Read it before changing the drawing
or the mouse behaviour, and add an entry for every such change.

## Build, open, check

```bash
python design/sozvezdiya-24/src/build.py     # -> lab/dist/24/index.html + d24.js (edit src/, never the built files)
python -B tests/sem24.py                     # the spec's 32 reference checks + integration checks on the session base
python -B tests/smoke.py                     # includes design 24's day, families and JS syntax
```

Then open `http://127.0.0.1:8767/24/` (after a server restart if `lab/scene24.py` or `lab/server.py` changed), evaluate
`tests/ui_check24.js` in the page and expect `problems: []`. Address parameters for reviews and snapshots:
`#date=2025-12-17&session=RDR&at=11:30` (a history day at a slice), `&ev=X` (the event in focus: which zone `&zone=` pins), `&mode=path`, `&view=conf` (the original
snapshot after a break), `&area=-4:-1` (price cells [−0,4; −0,1) SD) or `&area=-4:-1:4:9` (× 15-minute cells 4…8 from the
box end), `&pt=3` (a family session pinned), `&lvl=u2` (a level pinned: drH, drL, idrH, idrL, mid, open, u1…u6, d1…d6),
`&col=12` (an M5 column of «Путь семьи»), `&det=1` (details open), `&scope=all` (the all-weekdays family, an explicit
choice), `&zone=2` (the second zone of the event in focus pinned), `&hov=pcell:X:9` or `&hov=tcell:8` (as if a price band of X or a
15-minute window were hovered, for review snapshots), `&geo=1` (the page writes the geometry of every layer and panel
block into `<script id="geo">`, for `spec/ekran-24/tools/`). `window.__d24` exposes `st`, `cur()`, `passports()`,
`zonesOf()`, `zoneStatus()`, `V` (this frame: `zoneHit`, `hills`, `projCols`, `lk`).

Snapshots for the review: [`shots/`](shots/) (history days of NQ; screenshots of the tool, not the tape — AGENTS.md rule 1).

## The look «Окна времени» (operator, 2026-10-01 evening)

The operator compared three full mockups (canvas «DR Lab · экран 24») and twelve constellation drawings (canvas «DR Lab ·
созвездия») and chose «Окна времени» with «дымка и нити», amber R `#EBA06C`, sky X `#72A9EC`. Only the drawing and the
interaction changed; every number keeps its object, denominator and passport (`meaning/10-dizajn-24.md` §2, §3а).

| Element | What it is | Code |
|---|---|---|
| R and X together | no switch; the toolbar names both; the event under the cursor is «in focus» (`st.ev`) for the panel and the area | `drawPoints`, `toolbar`, `hit` |
| Constellation | a zone of zone-map-3 drawn from its own points: density in screen space (σ 18 px) filled at 0.22 and 0.6 of its peak (blurred), the shortest tree joining its stars (0.5 px), on hover the 0.35 iso-line and the exact cells; dashed when IMPOSSIBLE; a label with the zone's share in a size that follows the share | `kde`, `iso`, `mst`, `cloudsOf`, `drawClouds`, `drawZones` |
| Link | a hovered zone or price band: a ring on the densest spot, a line straight down to the peak 15 minutes (the time cell holding most of its sessions), lit to the time axis | `linkOf`, `drawLink` |
| Price columns | R and X side by side, each its own 100 %; rows of a zone brighter, each zone's densest row larger, a tick for its price extent; the bar is the band's share over the whole horizon, never the zone's | `drawProjRX` |
| Time band | under the chart (a quarter of the height): the zones' capsules over their whole time window with share and status (outer lanes, X above, R below); each zone's hill, the shape of its sessions' times (Gaussian 7 min, height normalised within its event, no number); the columns T_X up and T_R down on one square-root scale; «?» at the right | `drawBand`, `bandHills` |
| Inspector | the fixed block at the bottom right: what is under the cursor (zone, band, 15 minutes, session, level), else what is pinned, else the snapshot; replaces the floating tooltip | `showTip`, `tipHtml`, `zoneTip`, `twoBars` |
| Six windows | slide up when the mouse reaches the bottom edge, a click pins: the passport of the object or the snapshot; R and X as price × time cells with their zones' exact cells; what came first, R or X (100 %); «на уровне или дальше» on today's levels, whole horizon and after the slice; «Путь семьи» with today's closes | `details`, `detBody`, `orderHtml`, `ladderHtml`, `drawHeat`, `drawFilmMini` |
| Panel | the snapshot, the DR outcome, the zones of R and X in one list by time with «сейчас HH:MM», residual and unknown per event, today's facts | `panelHtml`, `zonesHtml` |

Snapshots of this look: `shots/1-okna-vremeni.png` … `6-put-semi.png` (history days of NQ).

## Files

| File | What |
|---|---|
| `lab/zonemap24.py` | The zone map of R and X, `zone-map-3` (meaning/12): one rule (the half-height region of its own apex on the 3 × 3 density), the passport and diagnostics of every zone (shifted grids, resampled sessions, a path-null on held-out sessions), today's status by the reachable set |
| `lab/scene24.py` | The statistical layer: families F and F_break, events R / X per member, DR outcome, order, the M5 path, distributions, snapshot identity, journal of undetermined keys; the history day; integer ticks throughout |
| `lab/server.py` | `/api/d24/day`, `/api/d24/family`, `/api/d24/dates` (design 22's routes unchanged) |
| `src/app.js` | Design 22's `app.js` with the statistical layer replaced (data, points, histograms, «Путь семьи», area, passports, history day) |
| `src/panel.js` | The right panel and the details area (bottom) |
| `src/page.html`, `src/panel.css` | Design 22's page and panel with the new controls |
| `tests/sem24.py`, `tests/ui_check24.js` | Checks: definitions (Python) and the screen (in the page) |

## What changed against design 22, element by element (spec §10.4)

| Design 22 | Design 24 | Object (spec) |
|---|---|---|
| Stars = first touches of three places per side | **Points**: one per family session for the chosen event — R (deepest point against the confirmation) or X (farthest along it), from its own confirmation to the end of its block; at the event's price carried to today's scale and its real clock; a ring = that session broke its DR | §5.1, §10.1 |
| KDE constellations with a 38 % contour, the «best» one bright | **Removed.** Optional «Свечение точек» (off by default): the same soft halo per point, no number, no contour | §7.1 |
| Three places per side with brackets and shares | **Removed.** One **selected area**: a click on the price histogram (a 0,1-SD band; drag for several), a click on the time histogram (a 15-minute window; with a band — band × window), or a rectangle drawn with «▭ Область» / Shift. The bracket right of the block end spans the whole band and carries the band's share; a band × window has its own frame and share | §7.1, §10.3 |
| Density by price right of the scale (first arrivals) | **Price histogram P_E(k)** of the chosen event by 0,1 SD; «▲ / ▼» = the share out of view; «?» = unknown mass | §6, §10.1 |
| Time strip (when places were first reached) | **Time histogram T_E(b)** of the chosen event by 15 minutes from the box end; passed cells dimmer; «?» apart | §6, §10.1 |
| Fan (removed 30.09), six history charts | **One details area** at the bottom: the full passport of what is chosen and one small chart (a session's path; or «на уровне или дальше» / «заходили» as the remaining hours start later) | §10.4 |
| Targets, «дошли хотя бы раз» on levels | **Level details** on hover / pin: «на уровне или дальше» on each session's whole horizon and after the slice, the literal crossing (details), today's fact | §5.4, §8 |
| «DR удержится» + «тенью за DR» | **DR outcome**: held / broken / unknown / no period, 100 % of N, one bar | §5.2 |
| «После касания DR держался …» | Removed | §10.4 |
| — | **«Путь семьи»**: the family's M5 closes per common clock M5, each column its own 100 % (missing M5 = «нет свечи»), one fixed linear colour scale for all columns; the column right of the price scale shows the hovered (or pinned, or the slice's) M5; the range field V in its details | §5.3, §10.2 |
| — | **Switch R / X** changes the points and both histograms together; in «Путь семьи» they are hidden | §10.1, §10.2 |
| After a break: «По слому / Против слома» on the break family | The same family F_break with its own N, no «DR сломан» share inside it, and an explicit switch back to the original snapshot | §9.3 |
| Constellations of 22, then «главный кластер» (meaning/11) | **The zone map** (meaning/12): every zone of the chosen event is its exact region of cells with its share of the family, in the order of time; the rest is the residual; today's status (держится / возможна / невозможна) sets the zone's weight; the family is the weekday one unless «все дни» is clicked | zone-map-3 |
| Kept as in 22 | Candles of the day, DR / IDR / mid / STD / open lines, past sessions' DR / IDR, VI, pills, replay by candle, ← / →, −5м / +5м, wheel zoom, drag, layers, settings, the panel's manner (percentages only, every line a link) | §10, §15 |

## Passports (spec §13.3)

Every percentage shown (panel, tooltips, details) is made by `pp()` with `event_id, family_id, snapshot_id, region_kind,
exact_price_bounds, time_bounds, start_rule, end_rule, N, yes_count, unknown_count, no_event_count, display_scope` and
one sentence in the operator's terms: «такая доля семьи — это событие — в этой области — за этот горизонт» (and «на этой
пятиминутке»). `tests/ui_check24.js` checks that every panel number reproduces its passport, that the page's counts
equal the server's, that R and X with both histograms are one table, that each film column adds up to N, that a window
never exceeds its band, that the tail of X equals «на уровне или дальше» and that moving the slice rewrites nothing.

## Choices the executor made where the specification left room (open for the operator and the auditor)

- **The atom** (operator, 01.10): an existing M5 candle is an observation; only a wholly missing M5 on an event's horizon
  is a hole. The specification's §12 numbers are reproduced exactly (RDR N 25: held 21, broken 4, order 17 / 8, all X
  before all R in 16; ODR N 187: held 133, broken 51, unknown 3, five unknown R).
- **Early closes** are not certified (no calendar): a session whose candles stop early has its events «unknown», never
  «market closed». About 4 % of RDR sessions (holiday half days).
- **The size of the atom's effect** (whole base 2006–2025, of the confirmed sessions): the first confirmation cannot be
  established (journal) for 0–0,1 % of RDR, 0,2–2,1 % of ODR, 3,7–3,8 % of NQ / YM ADR, 1,7 % of ES ADR; R and X are
  unknown for 3,4–3,5 % of RDR, 0,5–3,3 % of ODR, 14,2 % of NQ / YM ADR (whole evening M5 missing, mostly early years),
  3,3 % of ES ADR. A limit of the result, shown as the «?» mass; not a reason for a new study (operator).
- **The side of a level's question** follows §5.4 literally: a level beyond the edge of play (u > 0) asks «по
  направлению» (its whole-horizon share is the tail of X), a level at or behind it asks «против» (the cumulative share of
  R). Named in every passport.
- **«Путь семьи» starts at the box end** (all common clock M5 of the block); columns before a session's own confirmation
  count it and say so in the panel («из них ещё до своего подтверждения»).
- **The film's colour**: alpha = (0,1 + 0,9 × share) × brightness, one brightness for every column (default ×2, «⚙»).
  The scale is linear and fixed; at the default, shares above about 45 % look the same (exact numbers are in the column).
- **The view's price range** includes the middle 90 % of R and X of the family (both, so R / X does not jump); the rest is
  named «▲ / ▼» at the histogram's edge. Calculations never trim.
- **Before a confirmation** the screen shows no family statistics (the old similar-sessions cohort is design 22's).
- **No synthetic mockup**: history days replace it; review pictures are screenshots of history days.
