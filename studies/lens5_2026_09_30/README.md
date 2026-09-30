# Check for semantic lens 5 (2026-09-30, cluster spec v0.8)

The lens: [`meaning/lens/2026-09-30-linza-5.md`](../../meaning/lens/2026-09-30-linza-5.md); the answer:
[`meaning/lens/2026-09-30-otvet-5.md`](../../meaning/lens/2026-09-30-otvet-5.md).

The lens asked for a semantic critique before any market computation, so nothing here reads the tape. One synthetic
check: what two candidate «reaction» rules return on a driftless random walk.

Run from this folder with the operator's Python: `python -B episode_rules_synthetic.py` (set `PYTHONIOENCODING=utf-8`
on a Cyrillic Windows console).

| Script | Question | Output |
|---|---|---|
| `episode_rules_synthetic.py` | Rule C «episode ends when price recovers its start» (first cluster audit, D3) and rule θ «reversal by θ from the lowest low since t»: where the first episode's base lies, how soon it is recognised, what share never is; Gaussian and Student-t steps | `episode_rules_synthetic.log` |
