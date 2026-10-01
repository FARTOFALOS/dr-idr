# Lens 15 · the automatic main cluster of R / X (2026-10-01)

Question of [lens 15](../../meaning/lens/2026-10-01-linza-15.md): under what conditions does a part of one family's
R (or X) points earn the name «automatic main cluster»? The lens proposes to judge a region against the product of the
family's two histograms (price and time): a true price × time cluster is where price and time coincide more often than
the two histograms explain. This study puts that proposal, and two alternatives, through the stability conditions of
DR-LAB-SEM-1.0 §7.2 on the session base, and runs the same pipeline on memoryless paths made of the same candles. The
answer in plain words: [meaning/lens/2026-10-01-otvet-15.md](../../meaning/lens/2026-10-01-otvet-15.md).

Research only: nothing on any screen changed. Outputs are aggregates (family keys, counts, shares, region bounds); no
dates, no paths (AGENTS.md rule 1).

## What was declared before counting

The rules are in the docstring of [`selector.py`](selector.py), frozen before the first run on the tape (sha256
`192444c7cd4693b9567e3d97f200fa12211d145132a1c79748a9fb0f8f0d57de`, 2026-10-01 14:31 MSK); the pipeline was debugged on
synthetic random walks only (`--synthetic`). Later edits of the file: none.

- **Atom, grid, family** — DR-LAB-SEM-1.0 and `lab/scene24.py` unchanged: one known R or X per member of a confirmation
  family (instrument × session × weekday × direction × 15-minute window), measured from its own confirmation to the block
  end; cells 0.1 SD × 15 minutes; R and X apart; unknown events stay in N without a position. The families and events
  equal `scene24._snapshot` (checked on NQ RDR Wed long 11:45 N 25, ODR Wed long 04:00 N 187, RDR Mon long 10:30 N 146,
  ADR Thu short 20:45 N 71). Families with N ≥ 20, history 2006–2025.
- **Candidate regions** — rectangles of whole cells inside the family's possible hours (from its confirmation window to
  the block end).
- **Three definitions of concentration**:
  - **M** «where most»: the 3 × 3-cell window (0.3 SD × 45 min) holding the most events;
  - **J** «beyond the two histograms» (the lens): Kulldorff's space-time permutation scan statistic, expected count =
    band count × window count / n, rectangles up to 1.0 SD × 2 h;
  - **G** «beyond geometry»: the same statistic against memoryless paths of the same members (each member's own
    post-confirmation M5 candles at their own clock places, every candle's direction a fair coin; 100 replicas per
    member).
- **Confirmed** = all of: (1) the first decade (2006–2015) finds the same place as the whole history (IoU ≥ 0.25);
  (2) in the second decade (2016–2025) that first-decade region, fixed, is still a concentration (p < 0.05: M against its
  same-size neighbours, J against permuted time labels, G against the memoryless baseline); (3) three shifted grids
  (+0.05 SD, +5 min, +10 min) find the same place; (4) ≥ 50 % of 200 bootstrap samples of whole sessions find it, and so
  does the family without any one of its sessions; (5) J and G: the region beats chance as the maximum over all regions
  (199 permutations / memoryless families).
- **Data «null»** — the same pipeline on one memoryless replica of every member instead of its real path. What it
  confirms there is the geometry of the candles.

## Files

| File | What |
|---|---|
| `selector.py` | The study (declaration in the docstring): `python -B selector.py --inst NQ --sessions RDR`; `--merge` joins the sessions; `--synthetic` debugs on random walks |
| `report.py` | The tables of the answer: `python -B report.py NQ ES YM` |
| `figure.py` | One family's R and X grid, real against memoryless, with the three main regions: `meaning/img/lens15-*.png` |
| `results_<inst>.json` | Aggregates per family: N, known, the main region of each definition on real and memoryless data, every condition, p-values, the share of N in the first and last 30 minutes |
| `log_<inst>_<session>.txt` | The run logs |

## Results

Families with N ≥ 20: NQ 166, ES 182, YM 168 (79–80 % of each instrument's confirmed sessions). Confirmed main regions,
real / memoryless:

| Event · definition | NQ | ES | YM |
|---|---|---|---|
| R · M | 29 / 37 | 39 / 33 | 28 / 25 |
| R · J | 32 / 30 | 39 / 39 | 31 / 29 |
| R · G | 0 / 0 | 1 / 0 | 0 / 0 |
| X · M | 20 / 21 | 31 / 28 | 21 / 24 |
| X · J | 14 / 24 | 13 / 24 | 13 / 18 |
| X · G | 0 / 0 | 0 / 0 | 0 / 0 |

- Every confirmed M and J region, real or memoryless, begins in the first 30 minutes of the family's possible hours, at
  the confirmation price.
- The shares of R and X in the first and the last 30 minutes are nearly the same on memoryless paths. The one exception
  is X in the first 30 minutes: real sessions are 2–3 points higher on all three instruments (an observation after the
  run, not tested).
- J beats chance as often on memoryless data as on real data (R: 92 / 95, 110 / 111, 90 / 84 families). G beats chance
  in 6–10 families per event and instrument, the same on memoryless data: the 5 % level.
- The one G confirmation: ES RDR Tue short 11:00, N 59, R in −1.0…−0.2 SD × 14:30–15:30, 27 % of N, 5.3 × the
  memoryless expectation. One case in 1032 tests.
- Sensitivity (`power.py`, synthetic, added after the run, 4 families per level): with 150 sessions, G confirms a planted
  cluster holding 30 % of the family 4 of 4 times at the planted place; at 10–20 % it does so 1 time in 8; on a pure
  random walk 0 of 8. J never finds the planted place. The `confirmed_at_planted_place` flag of `power.json` is too
  narrow (lower bound −1.4 SD); read the recorded regions.

`tables.txt` is the printed output of `report.py NQ ES YM`.
