# Design 23 · SEM-1.0 prototype

Side-by-side experimental implementation of the proposed DR-LAB-SEM-1.0. It does **not** replace design 22 or change its root screen.

Run the normal local market server and open:

```
python -B lab/server.py --data market
http://127.0.0.1:8767/sem-v1/
```

The prototype adds read-only `/api/family-v1`.

## Deliberate differences from design 22

- Main map: one historical **R** (session-horizon maximum retracement) or **X** (session-horizon maximum extension) per family member, measured from that member's own confirmation to the end of its ADR/ODR/RDR horizon.
- Price and time histograms are projections of the same selected event distribution.
- First-touch KDE is not the main constellation.
- No automatic “best cluster” or forced islands.
- Click a price-histogram bin to select an explicit price zone and see its exact share of original N.
- Separate **Путь семьи** mode shows common-clock M5 close distribution by column; R/X percentages are hidden there.
- DR held/broken remains a separate outcome.
- Existing design 22 stays available at `/`.

This is an operator test surface before semantic acceptance. It does not modify AGENTS.md, UI_RULES.md, meaning/08 or meaning/09.
