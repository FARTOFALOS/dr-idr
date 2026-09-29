# Checks asked by semantic lens 4 (2026-09-30)

The lens: [`meaning/lens/2026-09-30-linza-4.md`](../../meaning/lens/2026-09-30-linza-4.md); the answer with the plain
reading of these results: [`meaning/lens/2026-09-30-otvet-4.md`](../../meaning/lens/2026-09-30-otvet-4.md).

Read-only over the session base `lab/.runtime/boxes_*` (M5) and the G3 minute tape (`lab/build_market.load_minutes`).
Only aggregates are committed; per-state records go to the git-ignored `lab/.runtime/lens4_*.json`. 2026 stays hidden
(the session base ends 2025-12-31). Test sessions 2016–2025, similar sessions from the years before the test year
(walk-forward), the screen's rules for confirmed states (`lab/scene21.py`, conf mode).

Run from this folder with the operator's Python: `python -B <file>.py`.

| Script | Question | Output (committed) |
|---|---|---|
| `lenscommon.py` | Shared: conf coordinates, the screen's cohort at any M5 close, places ahead of the price, Brier skill with session-clustered bootstrap | — |
| `check_equivalence.py` | Is `lenscommon.Screen.cohort` the same as `audit_2026_09_29/replay_core.cohort` (itself checked against `lab/scene21.cohort`)? | printed: 5213 of 5213 identical |
| `c1_example.py` | Lens check 1 on one historical M5: the place's edge, the true first entry (M1), the bar's high, the star | printed, normalized, no date |
| `c12_stars_fields.py` | Lens checks 1–2: how high above the place's edge the screen's stars sit (the first bar's depth) and how that compares with how deep price went later; fields of first visits and of visits on a plain grid without the three places; stable price modes of the visit field | `c12_stars_fields.log`, `fields.npz` (mean fields) |
| `plot_fields.py` | Pictures of the three fields | `meaning/img/lens4-pole-nq-rdr.png`, `…-nq-odr.png` |
| `c3_frozen_dynamic.py` | Lens check 3: a map frozen at the confirmation against the screen's map rebuilt at every M5 | `c3_frozen_dynamic.log` |
| `c4_level_event.py` | Lens check 4: similar sessions by state (the screen) against similar sessions by a level activation (an M5 close crossing the same half-step in the same direction) | `c4_level_event.log` |
| `c5_minute_alignment.py` | Lens «alignment»: the live screen between two M5 closes (today's price by the minute, history by the M5 close) against minutes on both sides and closed M5 on both sides | `c5_minute_alignment.log` |
