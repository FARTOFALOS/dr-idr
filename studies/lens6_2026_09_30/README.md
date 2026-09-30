# Check for semantic lens 6 (2026-09-30, the author's Time & Price reconstructed)

The lens: [`meaning/lens/2026-09-30-linza-6.md`](../../meaning/lens/2026-09-30-linza-6.md); the answer:
[`meaning/lens/2026-09-30-otvet-6.md`](../../meaning/lens/2026-09-30-otvet-6.md) (sections B2 and C2 use this check).

The lens asked for the author's statistical object to be reconstructed from his sources before anything is built.
The reconstruction came from the subtitles and the public QuantX snapshot. This check only tests it: one key the author
published is recomputed on our tape with his own definitions, to see whether his numbers come out.

Read-only over the session table of `studies/m7_claims.py` (`instances`, cached as the git-ignored
`lab/.runtime/study_m7_nq.pkl`). Aggregates only; the two example sessions are printed without their dates (hard rule 1),
as in lens 4. 2026 stays hidden (the tape ends 2025-12-31).

Run from this folder with the operator's Python: `python -B author_key_nq.py` (set `PYTHONIOENCODING=utf-8` on a
Cyrillic Windows console).

| Script | Question | Output |
|---|---|---|
| `author_key_nq.py` | NQ, Friday, RDR, short, first confirmation in 10:30-11:00 (the author's jPvvCww8aP8): sample size and DR true against his; time of the max retracement (15-min bins, first mode, median); max retracement buckets, median and «70 %» with and without his time filter; max extension, «70 %» reach, reach of 1.0; the same on all sessions (the prefix-honest set); two sessions of the key traced to their buckets; sizes of two other Friday NQ keys he published | `author_key_nq.log` |
