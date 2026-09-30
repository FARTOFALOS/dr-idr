# Lens 10: the time-first field and the Baseline / Dynamic hierarchy (2026-09-30)

The lens: [`meaning/lens/2026-09-30-linza-10.md`](../../meaning/lens/2026-09-30-linza-10.md) (specification v2.0) and
[`…-linza-10-patch-2-1.md`](../../meaning/lens/2026-09-30-linza-10-patch-2-1.md) (patch 2.1); the answer:
[`meaning/lens/2026-09-30-otvet-10.md`](../../meaning/lens/2026-09-30-otvet-10.md).

The proposed base object: after a closed M5 of today, for the similar sessions, which normalized prices the range of
every next M5 reached (cells price bin × future M5, one vote per session per cell, V = sessions / N). Patch 2.1 adds the
hierarchy: the Baseline map at the activation M5 t0, a Dynamic map at every later closed M5, never rewriting the
Baseline. Synthetic only; the working screen is unchanged.

| File | What |
|---|---|
| `pasport-polya.md` | Step P1: the passport of the field and of the time hierarchy (Russian): t0 and tn, the group, columns, bins, the vote, V and the derived numbers, unknowns, gaps, brightness, what it does not claim, the open fork «clock time or time since activation» |
| `field.py` | The field for one or many sessions: bins, votes, V(k, j), V over a wide area and a window, first reach, session mass of a contour, gap crossings, unknown columns |
| `synthetic_field.py` | Step P2: tests T1-T8 of the specification and five edge cases → `synthetic_field.log` |
| `hierarchy.py` | Patch 2.1 on a toy history: activation t0, the Baseline once, a Dynamic map per later closed M5, each from today's prefix only; the matcher aligned by clock time (the screen now) or by time since activation |
| `synthetic_hierarchy.py` | Tests A-D of the patch and E (the fork) → `synthetic_hierarchy.log` |

The same field on the tape was measured by lens 4 (`studies/lens4_2026_09_30/c12_stars_fields.py`, panel «Где цена
бывала» of `meaning/img/lens4-pole-nq-rdr.png`; bins there are closed on both sides).

Run from this folder: `python -B synthetic_field.py`, `python -B synthetic_hierarchy.py`.
