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
- **No positive edge established for the mechanical entries on NQ/ES/YM** (mean net results negative; for NQ RDR
  time-and-price the intervals include zero, so «loss-making» would overstate it). Retirement setup (touch −0.75, stop 2 ticks beyond the
  opposite DR): every false session passes −0.75, so the DR holds in only 31-40 % of entered sessions; net −0.10…−0.45 R
  per trade, gross negative. Time-and-price, walk-forward by year 2011-2025, parameters from past years only: all
  variants negative (−0.02…−0.50 R); parameters from DR-true sessions only (as the author does) give 67-81 % stops.
  Only hint: NQ RDR 2021-2025, +0.10…+0.12 R with the interval touching zero — one cell after selection, not
  established.

**The semantic audit of 2026-09-29** (`studies/audit_2026_09_29/`; the Russian reading with status labels is
`meaning/03-dokazatelstva.md`). All numbers aggregate; instruments separate; cohorts from past years only.

- **The descriptive regularities are range geometry.** Keeping the real box and replacing what follows by the day's own
  bars permuted within each hour (P60) or by a neighbouring day's path (NBR) reproduces RDR DR true (82.6 / 79.1 / 80.7 %
  vs P60 82.7 / 79.7 / 81.2), box colour -> direction (~71 %), return to the DR edge and +0.5 reached; ODR/ADR keep a
  +1…+3 pp residual. The day-model direction effect (+14…+18 pp) is reproduced by the neighbouring day's path and nearly
  vanishes inside one box colour. The author's public wick claim («DR low will be the low of the session») gives 75 / 70
  / 73 % on RDR.
- **The clock anchor.** Against the REALISED range after the window, DR true of a one-hour window at any start time is
  explained by box range / next-hours range (R² 0.99, ~210 starts); 09:30 is 1.7–2.4 pp below the curve. Against an
  EX-ANTE expected range (20-day median), windows at 03:00 and 09:30 hold 1.9–2.7 pp more often than neighbours within
  ±45 min (day-bootstrap intervals exclude zero), 19:30 +0.6–1.2. Mechanism not established.
- **The working screen on history** (replay identical to `lab/scene21.cohort` on 360/360 sampled cohorts and 72/72
  value sets): DR holds BSS 13.5 % (RDR) / 15.0 % (ODR), pullback places 13.0 / 12.1 %, first confirmation ↑ before a
  confirmation 19.8 / 13.7 %, the panel's first STD target 22 / 19 % with a matched price but −48 / −50 % when the price
  could not be matched (12–13 % of confirmed moments; then DR holds and places also have no skill). After a DR break the
  cohort is below 40 sessions in 90 % of the moments of the first hour after the confirmation. «До DR high» mapped from
  today contradicts «↑» in 9–11 % of waiting moments, never in each session's own DR frame. 28–31 % of the final
  extremes fall in the last 30 minutes (12.7–15.5 % for uniform time; a driftless path predicts 27–36 %). The whole path
  stays inside the 20–80 fan for only 12–13 % of sessions. A place's drawn core holds ~0.3 of its sessions. «Пусто» is
  as empty as its neighbours on new days.

## Not established (read before drawing conclusions from the screen)

1. **Why the anchored windows hold ~2 pp more often at equal expected volatility** (above): through volatility or through
   levels. Permuting bars within the hour does not change RDR DR true, which points to volatility; not tested directly.
2. **How the operator reads the screen**: whether a place's share is taken for its core, the fan for a corridor.
   Only the size of those differences is measured.
3. **Money.** Nothing here is a trade: entries, stops, costs and the order of touches (target before stop) are not
   modelled. "Touch before the session end" ignores which came first.

## Backlog (ordered)

1. ~~Honest line for DR true~~ and ~~calibration of the overlay~~: done 2026-09-29 (above).
2. Design 22 onto market data if the operator approves (`meaning/05-otkrytye-voprosy.md`): own DR and wick per session in
   `/api/cohort`, then the replay of its numbers.
3. After a DR break: a wider similarity condition (confirmation window ±30 min) and its calibration, if the operator wants
   numbers there (О2).
4. Order of touches: target before the opposite DR / before a retracement level, per similar-session cohort.
5. ES and YM at one-minute cadence (5m panes in the operator's TradingView layout) and ODR/ADR live checks at night.
6. Jev (the operator's probabilistic model) as an extra layer on the clusters — only when the operator asks.
6a. From `docs/STRATEGY.md` §14.4: a testable operationalization of the discretionary S1 entry (rejection at stacked
    levels: previous DR levels 3 weeks, VIB/GIB, ADR/ODR mids); a news-day filter; distance control for the
    contraction result; NQ RDR 2021-2025 time-and-price on the hidden 2026 tape only by the operator's decision.
7. Consolidate `lab/dist/styles.css` override blocks; keep the look identical.
