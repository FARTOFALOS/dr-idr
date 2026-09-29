# Audit of 2026-09-29 — the studies behind meaning/03-dokazatelstva.md

Read-only over the G3 tape (through `lab/build_market.load_minutes`) and the session base `lab/.runtime/boxes_*`
(`lab/build_boxes.py`). Everything committed here is an aggregate; per-session records are written only to the
git-ignored `lab/.runtime/`. 2026 stays hidden. Instruments are reported separately (they are dependent on the same
day). The questions were fixed before counting; decisions that were added after a first read are marked in each script.

Run from the repository root with the operator's Python (numpy, pandas, scipy): `python -B studies/audit_2026_09_29/<file>.py`.

| Script | Question | Output (committed) |
|---|---|---|
| `geometry_nulls.py` | Do DR true, box colour -> direction, return into DR, +0.5 reached need anything beyond the day's own volatility? Real box + post-box path permuted within 60 minutes (P60), over the whole session (PALL), driftless (P0, a bridge back to the box close, not used in conclusions) or taken from a neighbouring day (NBR) | `geometry_nulls.json`, `.log` |
| `models_vs_colour.py` | Does the day-model effect on the RDR direction survive a neighbouring day's path, and inside one box colour? (models as `lab/scene21.py` computes them) | `.log` |
| `anchor_placebo.py`, `anchor_placebo_fit.py` | DR true of one-hour windows at every start time (fixed 240-minute horizon) against the ratio of the box range to the REALISED range after it; residuals at 03:00, 09:30, 19:30 (a diagnostic, after the fact) | `anchor_placebo.json`, `.log`, `anchor_placebo_fit.log` |
| `anchor_exante.py`, `anchor_exante_robust.py` | The same against an EX-ANTE expected range (20-day median): anchored window minus neighbours ±45 min at equal expected ratio; 5 and 20 strata, logistic model, day-block bootstrap | `anchor_exante.json`, `.log`, `anchor_exante_robust.log` |
| `replay_core.py`, `models_vec.py`, `common.py` | The screen's similar-session rules vectorised (shared code) | — |
| `replay_equivalence.py`, `replay_equivalence_values.py` | Is the vectorised replay identical to the production path `lab/scene21.cohort`? (history days fed to scene21 as if TradingView had delivered them, inside the test process only) | `.log` |
| `screen_replay.py`, `screen_replay_analyze.py` | The working screen (design 21) replayed on every session of 2016-2025 every 15 minutes, cohorts from past years only: calibration (BSS against a constant equal to the realised frequency, session-clustered intervals), the price-matched vs unmatched states, cohort sizes, the two «до DR high» frames, the end-of-session pile-up of extremes vs the arcsine law, the fan's path coverage | `screen_replay.log` (records stay in `lab/.runtime/audit_screen_replay.json`) |
| `empty_interval.py` | Does «пусто» (the widest interval where no similar pullback ended) keep its emptiness on new days? | `.log` |
| `place_core.py` | How many of a place's sessions sit in the drawn core and in the densest spot? | `.log` |

The Russian reading of the results with their status labels is [`../../meaning/03-dokazatelstva.md`](../../meaning/03-dokazatelstva.md).
