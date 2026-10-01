# Design 24 «Границы хода» — design 22's screen with the statistics of DR-LAB-SEM-1.0

A separate version of the DR Lab screen, built 2026-10-01 at the operator's order: **design 22's working screen
(candles, the day's DR / IDR, replay, the right panel, hover / pin, layers, settings) with its statistical layer replaced
end to end by the semantic specification DR-LAB-SEM-1.0** ([`meaning/lens/2026-10-01-spec-v1/`](../../meaning/lens/2026-10-01-spec-v1/README.md)).
Design 22 stays the working screen at `http://127.0.0.1:8767/` and is not changed (its files are untouched); design 24
opens next to it at **`http://127.0.0.1:8767/24/`** — the desktop shortcut «DR Lab 24» (`start-dr-lab-24.cmd`, the same
launcher with `-Page 24/`). «№22 ↗» in the toolbar opens design 22 on the same session and minute for comparison.

It runs on market data only (no synthetic mockup): «История» opens **any trading date of 2006–2025 as if it were today**,
its families taken only from earlier sessions, so the screen can be reviewed when the live session has no confirmation.
When the live day has none, the panel offers «Открыть … на истории» (the latest date on which that session confirmed).

## Build, open, check

```bash
python design/sozvezdiya-24/src/build.py     # -> lab/dist/24/index.html + d24.js (edit src/, never the built files)
python -B tests/sem24.py                     # the spec's 32 reference checks + integration checks on the session base
python -B tests/smoke.py                     # includes design 24's day, families and JS syntax
```

Then open `http://127.0.0.1:8767/24/` (after a server restart if `lab/scene24.py` or `lab/server.py` changed), evaluate
`tests/ui_check24.js` in the page and expect `problems: []`. Address parameters for reviews and snapshots:
`#date=2025-12-17&session=RDR&at=11:30` (a history day at a slice), `&ev=X`, `&mode=path`, `&view=conf` (the original
snapshot after a break), `&area=-4:-1` (price cells [−0,4; −0,1) SD) or `&area=-4:-1:4:9` (× 15-minute cells 4…8 from the
box end), `&pt=3` (a family session pinned), `&lvl=u2` (a level pinned: drH, drL, idrH, idrL, mid, open, u1…u6, d1…d6),
`&col=12` (an M5 column of «Путь семьи»), `&det=1` (details open). `window.__d24` exposes `st`, `cur()`, `passports()`.

Snapshots for the review: [`shots/`](shots/) (history days of NQ; screenshots of the tool, not the tape — AGENTS.md rule 1).

## Files

| File | What |
|---|---|
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
