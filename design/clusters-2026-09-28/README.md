# DR Lab — clusters, three variants (2026-09-28, not implemented)

Interactive mockups on a Claude Design canvas: https://claude.ai/artifact/9NTzLxzdq8qiBRDjpqoDR7 (the operator's
private artifact). They follow the semantics agreed with the operator and the semantic architect on 2026-09-28: the centre
of the screen is the clusters of 20 years of similar sessions (where and when the extreme of the rest of the session
landed), several per kind, each with its share and time window; DR/IDR, STD and the day's structure as context.

**Synthetic data only.** `src/gen_days.py` makes two invented NQ-like days (day A = the redesign day, seed 41; day B =
the same night with an RDR that confirms long and breaks the DR at 11:45). `src/engine.js` simulates the cohorts. No
market data, not the lab's numbers.

| Path | What |
|---|---|
| `built/project/Main.dc.html` | 1 · Кластеры на графике: the numbers next to the clusters, nothing beside the chart |
| `built/project/Summary.dc.html` | 2 · График + сводка: a column with the day, the session and the clusters as rows |
| `built/project/Projections.dc.html` | 3 · Проекции: the same extremes as bars along the price scale and the time axis |
| `src/engine.js` | sessions (the rules of `lab/live.py`), DR break, simulated cohorts (confirmed / before confirmation / after a break), density, clusters, halftone triangles, terraces, chart geometry |
| `src/view.js`, `src/v1.js`, `src/v2.js`, `src/v3.js` | shared view pieces and the three variants |
| `src/build.py` | assembles the artboards and `canvas.json` |
| `src/test.js` | runs `renderVals()` of an artboard in many states, checks every `{{hole}}` and value |
| `src/render.js`, `src/shot.sh`, `src/snaps.sh` | static snapshots for visual review (headless Chrome) into `snap/` |

What the drawing means (the operator's direction of 2026-09-28, the rest is proposal):

- One glyph = one cell of 5 min × 0.1 IDR (operator): the cell's share = k of N similar sessions whose extreme of the rest
  of the session fell there; no smoothing, empty cells stay empty, gaps between glyphs. Triangle = pullback (pointing the
  way of the pullback), dot = continuation; before a confirmation neutral «Верх» / «Низ»; after a DR break the side flips
  and the break stays a mark on its candle.
- Steps (size and brightness) by the cell's count against the densest cell, square-root scale: ≥ 36 % / ≥ 14 % / ≥ 5 %
  and 2+ sessions / single sessions. A cluster = connected step-1 cells; its share = their sessions / N.
- Row 2 of the canvas compares four ways to show strong vs weak places on layout 1: `steps`, `solid` (fill by the number
  of sessions behind a glyph: ≥ 8 solid, 4–7 half, 2–3 outline, 1 a dot; size by share), `units` (15-min × 0.2 IDR blocks
  counted from now, one small glyph = 1 % of the sessions), `mosaic` (the cells as tiles). `_dmode()` selects it.
- The synthetic cohorts are 400–600 sessions (confirmed), 160–240 (after a break), 480–640 (before confirmation).

Rebuild and check:

```bash
cd design/clusters-2026-09-28/src
python gen_days.py A && python gen_days.py B
python build.py
node test.js ../built/project/Main.dc.html
sh snaps.sh            # or: sh snaps.sh hover
```
