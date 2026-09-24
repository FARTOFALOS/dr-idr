# Research: what is measured, what is not

The screen shows frequencies of similar historical sessions. This file keeps the discipline the screen does not
print. Numbers below are on the history base (2006–2025, 2026 hidden).

## Measured

**The DR rule on our tape.** Share of sessions where, after the confirmation, no M5 close went beyond the opposite DR
edge until the end of the session ("DR true"):

| Session | NQ | ES | YM |
|---|---:|---:|---:|
| RDR, all confirmations | 82.9 % | 79.5 % | 80.9 % |
| RDR, long confirmation 10:30–11:00 | 78.4 % | 75.7 % | 76.8 % |

The author's "about 80 %" holds on all three indices.

**Intermarket (RDR), `studies/intermarket.py`**, result in `studies/intermarket_rdr.{json,log}`. Declared before
counting, one control added after the first read and marked as such.

- The three indices confirm in the same direction on 78.5 % of days (25.4 % if days were unrelated); the median gap
  between the first and the last confirmation is 25 minutes; all three on the same minute on 17 % of days; NQ is
  alone first most often (25 %), then YM (20 %), ES (11 %). Same-day extension correlates 0.61–0.80.
- At a confirmation, the state of the other two (both agree / half / leading / diverging) looked strong at first:
  "diverging" had DR true 86–91 % vs ~80 %. **It is a timing effect**: diverging confirmations come later
  (median ~12:35 vs ~11:00), less session is left to break the DR. Inside 30-minute confirmation-time strata the
  difference vanishes for all three instruments. ES confirming after NQ and YM agreed: +4.7 pp (z 2.4) inside strata,
  epochs +0.2 / +7.0 / +8.8 — a hint only, not established.

## Not established (read before drawing conclusions from the screen)

1. **What the clock anchor itself adds.** A high DR-true share is partly geometry: after a breakout, breaking the rule
   needs price to travel the whole DR back and close an M5 beyond it, and the later the confirmation, the less time is
   left. The honest line — the same rule on one-hour windows not anchored to 09:30 / 03:00 / 19:30 — is not built yet.
2. **Calibration of the live overlay.** Nobody has checked yet whether "zone 12 %" or "touch 60 %" come true at those
   rates on days outside the matching. Replay (click a candle) lets you eyeball it; a systematic walk-forward check is
   in the backlog.
3. **Money.** Nothing here is a trade: entries, stops, costs and the order of touches (target before stop) are not
   modelled. "Touch before the session end" ignores which came first.

## Backlog (ordered)

1. Honest line for DR true and for the overlay: placebo one-hour windows at unanchored times, same code path.
2. Calibration of the live overlay by replaying history days (walk-forward by year), per instrument and session.
3. Order of touches: target before the opposite DR / before a retracement level, per similar-session cohort.
4. ES and YM at one-minute cadence (5m panes in the operator's TradingView layout) and ODR/ADR live checks at night.
5. Jev (the operator's probabilistic model) as an extra layer on the clusters — only when the operator asks.
6. Consolidate `lab/dist/styles.css` override blocks; keep the look identical.
