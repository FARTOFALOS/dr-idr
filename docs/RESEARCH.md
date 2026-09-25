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

**The author's claims and his mechanical entries, `studies/m7_claims.py`** (2026-09-25), results in
`studies/m7_claims.{json,log}`; hypotheses and the decision rule written in the script before counting; NQ, ES, YM
reported separately; epochs 2006-12 / 2013-19 / 2020-25. Full reading in Russian: `docs/STRATEGY.md` §14.

- Descriptive claims mostly hold: DR true RDR 83.0 / 79.6 / 81.0 %, ODR ~77-80 %, ADR ~72-76 %; after a confirmation
  price touches the DR edge again in 88-91 % of sessions and the IDR edge in 78-85 %; the box colour agrees with the
  confirmation in 70-71 % of confirmed RDR sessions (63-68 % of all sessions); Wednesday is the weakest RDR day on all
  three; +0.5 IDR is reached in ~80 % (not "almost always"), +1.0 in ~50 %.
- Session models at 10:30: when only the upside model is intact, RDR confirms long in 59-64 %; when only the downside
  model is intact, long in 45-47 % (+13…+19 pp, |z| 5-7, all epochs). "All three boxes growing" (range expansion) holds
  on 66-70 % of days (ordinary intraday volatility) and reaches +1.0 less often, not more. Contraction days (ADR inside
  the previous RDR, 25-27 % of days) reach the other extreme of the previous RDR more often (33-35 % vs 20-21 %), not
  controlled for distance.
- Look-ahead reproduced: "max retracement before 12:00 → DR true 97-98 %, after → 60-66 %" (author's CL example 95/61).
  The honest prefix version (DR still intact at 12:00) adds only ~3 pp.
- **Mechanical entries have no edge after costs on NQ/ES/YM.** Retirement setup (touch −0.75, stop 2 ticks beyond the
  opposite DR): every false session passes −0.75, so the DR holds in only 31-40 % of entered sessions; net −0.10…−0.45 R
  per trade, gross negative. Time-and-price, walk-forward by year 2011-2025, parameters from past years only: all
  variants negative (−0.02…−0.50 R); parameters from DR-true sessions only (as the author does) give 67-81 % stops.
  Only hint: NQ RDR 2021-2025, +0.10…+0.12 R with the interval touching zero — one cell after selection, not
  established.

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
5a. From `docs/STRATEGY.md` §14.4: a testable operationalization of the discretionary S1 entry (rejection at stacked
    levels: previous DR levels 3 weeks, VIB/GIB, ADR/ODR mids); a news-day filter; distance control for the
    contraction result; NQ RDR 2021-2025 time-and-price on the hidden 2026 tape only by the operator's decision.
6. Consolidate `lab/dist/styles.css` override blocks; keep the look identical.
