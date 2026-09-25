> **Что это (по-русски).** Независимый свод правил DR/IDR, собранный вторым проверяющим агентом 2026-09-25 только по
> открытым источникам (опубликованный Pine-код автора DR/IDR V1.5, его ответы и треды, сайты академии, сторонние
> скрипты и описания, 9 изображений) и по словам самого автора в субтитрах. Наша лента и исследования G3 не
> использовались. Главное: определения 2022 года (сессии, DR по фитилям, IDR по телам, шаг STD 0,5 IDR, подтверждение
> закрытием M5) подтверждены кодом; модели после 2022 года и почти все числа есть только в роликах автора; единственный
> независимый публичный тест (TFO) дал 71,7% вместо 88%. Рабочий документ стратегии — `docs/STRATEGY.md`; проверка
> выписок из роликов — `docs/DR_RULES_CROSSCHECK.md`. Файл на английском, как и остальные документы для агентов.

# DR/IDR (TheMas7er / M7DR) — independent rulebook from public sources + the author's own words

Verifier: independent agent, 2026-09-25. No market data or project research was used (`g3-market-research`, `dr-idr` untouched). No trades, no logins, no downloads, no forms.
Scope: public web pages (read, and images looked at where noted) + the raw auto-caption transcripts of 156 of the author's videos/streams (quoted by YouTube id). Extractions A and B were NOT used as evidence for this file; they are checked separately in `docs/DR_RULES_CROSSCHECK.md`.

## 0. How to read this file

Tags (one per rule):
- **WEB-EXPLICIT** — a public web source states it (or the author's published Pine code implements it).
- **WEB-INFERRED** — follows from public sources (e.g. code behaviour, third-party summaries of the author) but is not stated in those words.
- **TRANSCRIPT-ONLY** — nothing public on the web beyond the author's videos; source = video id(s).
- **CONFLICT** — sources disagree with each other, or the author changed the rule over time. The conflict is described and an operational default is proposed (marked PROPOSED DEFAULT; that is my suggestion, not the author's rule).

Evidence weight, highest first: (1) the author's own published Pine code (DR/IDR V1.5); (2) the author's own words (videos, X thread, TradingView replies, m7dr.com); (3) third-party implementations and summaries; (4) search-engine snippets of pages that could not be opened.
Important: almost all statistics below are **author-reported** from his private databases (DRlens 2023, QuantX 2024-26). Only one independent public backtest was found (TFO, §12). Numbers are therefore claims, not verified facts.

### 0.1 Web sources used (keys used below)

| Key | Source | What was used | Access |
|---|---|---|---|
| W1 | TradingView "DR/IDR V1" by TheMas7er — https://www.tradingview.com/script/upzvFFch-DR-IDR-V1/ | description, release notes, full Pine v5 source ("DR/IDR V1.5", 367 lines), showcase chart image | read; code tab read in the browser |
| W2 | Comments under W1 (same URL) | author replies (Nov 2022-Jan 2023) | read |
| W3 | "TheMas7er scalp (US equity) 5min [promuckaj]" — https://www.tradingview.com/script/t81B3CEe-TheMas7er-scalp-US-equity-5min-promuckaj/ | description, release notes, Pine source (IDR logic) | read |
| W4 | "DR/IDR Case Study [TFO]" — https://www.tradingview.com/script/jU17SmIf-DR-IDR-Case-Study-TFO/ | independent backtest code + chart image with stats | read |
| W5 | useThinkScript "Daily Range - Intradaily Range (DR/IDR) for ThinkOrSwim" — https://usethinkscript.com/threads/daily-range-intradaily-range-dr-idr-for-thinkorswim.13646/ | port of the author's Pine (IDR/DR lines of code) | read (via fetch) |
| W6 | LuxAlgo Library "Defining Range" — https://www.luxalgo.com/library/concept/defining-range/ | formulas, windows, usage text | read |
| W7 | xsparro.co DR/IDR — https://www.xsparro.co/dr-idr/ | only search-engine snippets (site reset the connection) | NOT opened |
| W8 | m7dr.com (academy home) — https://m7dr.com/ | framework, tools, instruments, "wick or body close" wording | read |
| W9 | academy.themas7er.com memberships — https://academy.themas7er.com/plans/memberships/ | tool list (QuantX, DRIVE 2.1, indicator suite) | read |
| W10 | Author's X thread, 8 Dec 2022 (Thread Reader) — https://threadreaderapp.com/thread/1600845103207256068.html | early-confirmation → opposite-IDR entry example; follow-up thread (both sides / 2R per session) shown on same page | read |
| W11 | Rattibha, "DR IDR Advance tips from @IamMas7er" (Faysel, 14 Dec 2022) — https://en.rattibha.com/thread/1603001778278203399 | third-party summary of the author's Part-2 video | read |
| W12 | Rattibha, "High probability Dr model I use to trade" (@theAplustrades) — https://en.rattibha.com/thread/1614697072707633152 ; image https://pbs.twimg.com/media/FmiGbFxXwAE6LNJ.png | third-party model thread | read; image looked at |
| W13 | Scribd "DR/IDR Trading Strategy Guide" ("DR/IDR Playbook", third party) — https://www.scribd.com/document/634285160/Untitled | definitions, 4 setup types, stops, trailing | preview text layers read; first-page diagram looked at |
| W14 | "TICK Grid (TheMas7er)" by bmistiaen — https://www.tradingview.com/script/9ctSOWp2-TICK-Grid-TheMas7er/ | TICK levels in code | read |
| W15 | Author's YouTube pages (descriptions, publish dates) and thumbnails, e.g. https://www.youtube.com/watch?v=Uxwr4CVhGhg ; https://i.ytimg.com/vi/nMXrQxyJ46Q/maxresdefault.jpg ; …/IQUFS0SnV2s/… ; …/MA9evuOGL7c/… ; …/KKzy5uJyMmw/… | dates, titles, thumbnails | read / looked at |
| W16 | Trustpilot m7dr.com — https://www.trustpilot.com/review/m7dr.com | critiques (4 reviews) | read (via fetch) |
| W17 | MQL5 "DR IDR Range Indicator" — https://www.mql5.com/en/market/product/92577 | success-rate definition, neutral-day caveat | read (via fetch) |
| W18 | FX Replay "DR/IDR by FX Replay" — https://fxreplay.com/indicators/dr-idr-by-fx-replay-e7f21 | a divergent re-definition | read (via fetch) |
| W19 | "DR IDR Trading Areas [CHE]" — https://www.tradingview.com/script/5ShRtbIu/ | derivative indicator (averages) | read |
| W20 | Search-engine snippets only: author tweet renaming the retirement setup "SHL/GDL" (Trendsmap, https://www.trendsmap.com/twitter/tweet/1600836542527770624, connection refused); author tweet "DR/IDR rule has simply less probability on news days" (https://x.com/IamMas7er/status/1601667934396755968, now 404) | titles/snippets | NOT opened |
| W21 | Patreon https://www.patreon.com/themas7er ; X @M7_DR_ACADEMY https://x.com/M7_DR_ACADEMY | only public metadata (posts paywalled / need login) | partly |
| W22 | Rattibha TRSTN thread https://en.rattibha.com/thread/1602783509969440768 | speculative third-party theory; only used for history (ADR released later) | read |
| — | glasp.co summaries (Cloudflare bot check, not bypassed); Scribd 712659513 (preview empty); Reddit (no hits); @IamMas7er timeline (login) | — | not usable |

Images looked at (one line each):
- W1 showcase chart: ES Mar-2022 5-min, grey IDR box 09:30-10:30, solid DR lines, dashed red IDR lines, dotted IDR mid, SD labels 1.5…4 on the left; after 10:30 price closes above the IDR (early indication long), closes below the DR low ~14:00, then closes above the DR high before 16:00 — the showcase day is a false session (a 2023 commenter pointed this out).
- W4 chart: ES Mar-2023 5-min with labels "Close Through DRH/DRL", "DRL Held", "DRH Not Held" and a table "DR Success Rate 71.73%, Total Sessions 237".
- W12 image: MES Sep-2022 5-min, 13-14 Jul 2022; ODR and RDR boxes shaded; after an RDR long confirmation a long on the retest of the DR high (HL/BOS marks) with the target at the 0.5 SD level (label "0.5 (3774.50)").
- W13 page-1 diagram (M7 logo): a 09:30-10:30 box; captions say a 5-min close above the DR confirms with 88% that the DR low is the low of the day; a close above the IDR is an early indication; mirror for shorts.
- W15 thumbnail nMXrQxyJ46Q ("Positive vs Negative Retracements", Apr 2025): long confirmation; green "+" zone above the dashed IDR-high line (covering the DR-high area), red "−" zone from the IDR high downward through the range.
- W15 thumbnail IQUFS0SnV2s ("85% probability setup — last hour of the day"): green box, long confirmation, deep pullback to the lower part of the range, then rally.
- W15 thumbnail MA9evuOGL7c: staircase ADR→ODR→RDR, each box higher and larger, labelled "upside expansion model"; an arrow from RDR down through the ODR low labelled "broken".
- W15 thumbnail KKzy5uJyMmw: three boxes ADR < ODR < RDR growing in size, an X between ODR and RDR, "DR models — when broken?".
- m7dr.com hero image: marketing graphic only (no data).

---

## 1. Definitions

**D1 Timeframe.** All DR/IDR levels and all confirmations are computed on 5-minute candles. If a chart is below 5 min, the author's script pulls 5-min OHLC.
Sources: W1 ("applied in the 5 Min. Timeframe"; Pine `request.security(…'5'…)`), W3, q1s2INPzN6M ("the only timeframe that is relevant for DR levels and confirmations"). **WEB-EXPLICIT.**
Implementation caveat (WEB-INFERRED from W1 code): the Pine uses `lookahead_on` when pulling 5-min data onto a lower-timeframe chart, which leaks the 5-min bar's final values into earlier sub-bars; do not reuse that code for backtests on sub-5-min charts.

**D2 Clock and DST.** All times are New York local time (America/New_York); DST is handled by the timezone, not by the user. The author says the default times must not be changed whatever the user's own timezone. The same NY clock is applied to FX, metals, energy and crypto.
Sources: W1 (Pine `TIMEZONE = 'America/New_York'`; 26 Nov 2022 release note fixing DST), W2 (author: time settings "have to stay as they are"), W4 (TFO also NY time), all transcripts. **WEB-EXPLICIT.**
Crypto: the Pine extends Friday SD lines to Monday only for non-crypto symbols (crypto trades weekends). The author trades crypto sessions on Saturdays too (YT2Iv-b4FSg). **TRANSCRIPT-ONLY** for the weekend-session rule.

**D3 Sessions (formation hour → validity window).**

| Session | Formation (12 × 5-min bars) | Validity ("lines time") | Notes |
|---|---|---|---|
| ADR (after-session / after-market DR) | 19:30-20:30 | 20:30-02:00 | released Dec 2022 (W1 release note 11 Dec 2022) |
| ODR (overnight DR) | 03:00-04:00 | 04:00-08:30 | |
| RDR (regular DR) | 09:30-10:30 | 10:30-16:00 | the original 2022 rule was RDR-only |

The first bar opens at 09:30 (03:00, 19:30); the last bar opens at 10:25 (03:55, 20:25) because TradingView stamps bars by their open.
Sources: W1 Pine defaults (`0930-1030`/`1030-1600`, `1930-2030`/`2030-0200`, `0300-0400`/`0400-0830`); W3 release note (author confirmed 10:25 / 03:55 as the last bars); W6; q1s2INPzN6M; ZhOruqHWrVE/rpfs35CXZfo ("The RDR goes from 10:30 to 4:00… ADR 20:30 till 2… ODR 4 to 8:30"). **WEB-EXPLICIT.**
Naming noise on the web: LuxAlgo calls ADR "afternoon" (W6); the Scribd playbook and MQL5 sellers call ADR "Asian" and ODR "Outside" (W13, W17). The author's terms are after-session/after-market, overnight, regular.
Gaps between windows: 02:00-03:00 and 08:30-09:30 are "transition time windows" (preparation, not trading) and 16:00-19:30 has no session (AmAwkBpcv5E, wO7rYmSE9vQ). **TRANSCRIPT-ONLY.**
CONFLICT (2022 only): Part 2 (1B69Y1GZ1t4) said the RDR rule "continues to be valid" into the overnight session after 16:00; every later source uses the per-session windows above. PROPOSED DEFAULT: per-session windows.

**D4 DR (Defining Range).** DR high = highest high, DR low = lowest low of the 12 formation bars (wicks included).
Sources: W1 Pine (`rdrhigh := math.max(high_value, rdrhigh)`), W3, W5, W6, W13, Uxwr4CVhGhg. **WEB-EXPLICIT.**

**D5 IDR (Implied Defining Range).** CONFLICT between the author's code and his later wording.
- Code / 2022 wording: IDR high = max over the 12 bars of max(open, close); IDR low = min of min(open, close) — i.e. candle **bodies**, opens included. Sources: W1 Pine V1.5 (`ridrhigh := math.max(open_value, close_value, ridrhigh)`), W3 Pine (same body logic), W5 thinkScript port, W6 formula, W13 ("body close highs and lows"), Uxwr4CVhGhg ("highest body and the lowest body"), q1s2INPzN6M ("highest and lowest body close or open"). **WEB-EXPLICIT.**
- 2024-2026 wording: IDR high = "highest close on a 5-minute timeframe" (h47hEvyA45A, 2024), Fibonacci "applied to the lowest and highest 5-minute close" (nMXrQxyJ46Q, 2025), box size "lowest to highest 5-minute closes" (tb4xMGybw28, CzVFHQEyIjk), IDR high = "highest closing price of the first hour" (sAr1xVrR1Ic, Dec 2025). **TRANSCRIPT-ONLY.**
- The two definitions differ only when an **open** lies outside all closes of the hour: in practice the first bar's open (session open) or an open after a gap between one close and the next open (a volume imbalance). The QuantX formula is not published.
- PROPOSED DEFAULT: compute both; use bodies (the only published code) for levels, and log how often closes-only differs. Treat any statistic quoted from 2024-26 QuantX as possibly closes-based.

**D6 Mid lines.** IDR mid = (IDR high + IDR low)/2 (drawn by default in V1.5); DR mid = (DR high + DR low)/2 (option, default off).
Sources: W1 Pine (`middleidrline` default true, `middledrline` default false). **WEB-EXPLICIT.**
Which mid the author means by "ADR mid", "ODR mid", "previous session mid", "the 50%" is never stated. The 2026 seven-level list names only the "IDR mid" (wO7rYmSE9vQ); the 2022 range-expansion text says "midpoint of the DR levels" (q1s2INPzN6M). **CONFLICT/AMBIGUOUS.** PROPOSED DEFAULT: IDR mid (the only mid on the author's default chart); test DR mid as a variant.

**D7 Opening and closing price of a box.** Opening price = open of the first formation bar (09:30 bar); closing price = close of the last formation bar (10:25 bar, closing 10:30).
Sources: W1 Pine (`sessionOpen := open_value` on the first bar; box colour uses the current close vs `sessionOpen`); 1B69Y1GZ1t4 ("open price at 9.30… close price at 10.30"). **WEB-EXPLICIT.**

**D8 The seven box levels (2026).** DR high, DR low, IDR high, IDR low, IDR mid, opening price, closing price stay relevant for the whole session, before and after confirmation.
Source: wO7rYmSE9vQ. W1 draws all of them except the closing price. **TRANSCRIPT-ONLY** (list); levels WEB-EXPLICIT.

**D9 Standard-deviation (SD) levels.** Unit R = IDR high − IDR low. Levels step by 0.5·R: upward from the IDR high (IDR high + 0.5R, +1.0R, …), downward from the IDR low (IDR low − 0.5R, −1.0R, …). They are fixed multiples, not statistical deviations.
Sources: W1 Pine (`stdStep = |IDRhigh − IDRlow| × 0.5`; positive levels from IDR high, negative from IDR low; labels ±0.5, ±1…), W11 (Fib from IDR low to IDR high, 0.5 steps), W6 (formula; "fixed multiples of the range"), 1B69Y1GZ1t4. **WEB-EXPLICIT.**
- Which session's SDs: the free V1.5 draws SD lines **only from the RDR IDR**, from 10:30 until 08:30 next day (Friday → Monday 08:30 for non-crypto) (W1 Pine). QuantX statistics and all 2024-26 targets use each session's **own** IDR (e.g. ODR targets in SD of the ODR) (dfp2aAKt-Ss, HH2VLbhKNOQ). Users asked for ADR/ODR SDs in W2. **CONFLICT (tool vs method)**; PROPOSED DEFAULT: SD of the session being traded.
- Sign in statistics: extension targets are quoted as positive magnitudes in the confirmation direction ("1.2 SD" for longs and shorts alike) (jPvvCww8aP8, laH3FuECnVg). The Pine labels levels below the IDR low as negative. **WEB-EXPLICIT (labels) / TRANSCRIPT-ONLY (stat convention).**
- LuxAlgo also says the "DR's height" is projected and that some implementations use DR height or anchor at DR edges (W6) — that disagrees with the author's code. **CONFLICT (third party).**

**D10 Confirmation.** After the formation hour, the first 5-minute candle that **closes** above the DR high confirms long; the first close below the DR low confirms short. Wicks do not confirm. The session direction for statistics is the first confirmation.
Sources: W1 rules 1-2 ("closes above the DR high after 10.30… This is called confirmation"), W3 ("really closing… not just wicks"), W10, Uxwr4CVhGhg, wO7rYmSE9vQ, C1wPLsRy7us/pxL9XxVE-Ig (DRlens uses the first confirmation). **WEB-EXPLICIT.**
CONFLICTS:
- LuxAlgo (W6) says a close beyond the **IDR** confirms the bias. That is the author's early indication, not confirmation.
- m7dr.com (W8) says "a confirmation by a wick or a body close" sets the direction. In the streams the author does track a "first wick" through the DR (captioned "first week"/"weak confirmation", pxL9XxVE-Ig) to choose data time-windows, but trades and DR-true statistics use the close. PROPOSED DEFAULT: close-based confirmation; record the first-wick time separately.
- 2022 wording "closing (at least 5 min timeframe)" allows closes on higher timeframes too (Uxwr4CVhGhg). Later material is 5-min only.

**D11 Early indication.** A 5-minute close beyond the IDR (still inside the DR) after the formation hour is an early indication for that side (the opposite DR edge likely holds).
Sources: W1 rule 3, W3, W10 (author calls it "early confirmation"), W13 diagram, Uxwr4CVhGhg. **WEB-EXPLICIT.**
The author also uses "early" for (a) box colour and (b) a confirmation within the first 30 minutes after the box (ZhOruqHWrVE, _4otRSUDFTg). **TRANSCRIPT-ONLY**; three meanings — name them separately in code.
2026 early sign: the first candle after the box wicks above the DR high and closes above the IDR high (SLvkWYx189w/GMG02VI2lRs group). **TRANSCRIPT-ONLY.**

**D12 Box colour.** Green box: closing price > opening price; red: closing price < opening price.
Sources: W1 Pine option "Box color based on open and close" (default off; `boxUp = close > sessionOpen`), W3 v1.6 option, 1B69Y1GZ1t4 (open-vs-close "incline" → lean 60/40 long), W11 tip 1. **WEB-EXPLICIT.**
- Probability that the confirmation follows the box colour: "not 80%… 60-65%" (IT4eQNiqHfU/ZhOruqHWrVE, 2022-23) vs "roughly 70%" (RX57XC74DIo 2025, wO7rYmSE9vQ 2026, many 2026 videos). **CONFLICT (number changed); TRANSCRIPT-ONLY.**
- Equal open and close: the Pine paints it red (strict `>`); 2024-25 videos call it a gray (neutral) box (xe3dy8hERgU, s_VI7Rq7mi4, oOwwZ2kaBsA). **CONFLICT (minor).** PROPOSED DEFAULT: neutral.
- Box colour is a starting probability, not a trade signal (wO7rYmSE9vQ). **TRANSCRIPT-ONLY.**

**D13 DR true / false / unconfirmed.**
- Operational definition (2023+): after the first confirmation, the session is **true** if no 5-minute candle closes beyond the opposite DR edge until the session's end (16:00 / 08:30 / 02:00); **false** if one does. Sessions without any confirmation are unconfirmed.
  Sources: C1wPLsRy7us (Mage: "price never closes below the opposite DR for the rest of the session"), jPvvCww8aP8, W17 (MQL5 defines failure the same way), W10 follow-up (both sides → take the loss). **WEB-EXPLICIT (W17, W10) / TRANSCRIPT.**
- CONFLICT with the original wording: the 2022 video and the TradingView description phrase the rule as "the DR low will be… the low of the trading session" and a stop "will not be reached" (Uxwr4CVhGhg, W1) — a **wick** statement. TFO's default test (W4) uses exactly that wick criterion. PROPOSED DEFAULT: close-based for the rule; report the wick-based rate too.
- Unconfirmed sessions: DRlens showed 93.9% of days confirmed (YM ADR, Mondays view, C1wPLsRy7us). Whether QuantX "DR true %" counts unconfirmed sessions is not stated. An MQL5 seller warns that counting neutral days as true inflates the rate (W17). **OPEN.**

**D14 Headline DR-true rates (all author-reported unless noted).**

| Claim | Conditions | Source | Tag |
|---|---|---|---|
| 88% | ES/YM/NQ RDR, 12 years, **excluding** high-impact news days (CPI, FOMC, NFP…) | Uxwr4CVhGhg; video titles "88 % probability" (W15); W13 diagram | WEB-EXPLICIT (title/diagram) |
| >80% | third party (Dane Trades) 3-year test, news **not** excluded | 1B69Y1GZ1t4 | TRANSCRIPT-ONLY |
| 80% | "all major Forex pairs, BTC, ETH and US equity indices" | W1 description | WEB-EXPLICIT |
| ~85% FX; 75-80% BTC | author replies Dec 2022 | W2 | WEB-EXPLICIT |
| ~82% | DRlens 20y, YM ADR, Mondays, no news filter | C1wPLsRy7us | TRANSCRIPT-ONLY |
| "roughly 80%" | generic 2025-26 statement | wO7rYmSE9vQ, bB0Gmo16YR4 | TRANSCRIPT-ONLY |
| 64%…95% | per instrument/session/weekday/confirmation-window keys (QuantX) | 2024-26 videos | TRANSCRIPT-ONLY |
| **71.73%** | **independent**: TFO script, ES RDR, 237 sessions (early 2023 chart), **wick** criterion, news included | W4 image | WEB-EXPLICIT (independent) |

CONFLICT: the headline has drifted from 88% (news-filtered, 2022) to "roughly 80%" (unfiltered, 2025-26); the only independent number is lower (71.7%, stricter wick test, small sample). PROPOSED DEFAULT: plan with ≤80% and re-measure.

**D15 Retracement (after confirmation) — definition and sign convention. CONFLICT (era-dependent), resolved:**
- Magnitude (both eras): measured from the confirmation-side IDR edge in units of the IDR width. For a long: (IDR high − lowest price after confirmation) / (IDR high − IDR low). Sources: C1wPLsRy7us (Mage's formula), pxL9XxVE-Ig. **TRANSCRIPT-ONLY** (web has no formula).
- **DRlens convention (Jan 2023):** positive = price came back **into** the IDR (1.0 = opposite IDR edge); negative = it never re-entered the IDR (stayed beyond the confirmation-side IDR edge; −0.5 = the 0.5 SD level). Sources: C1wPLsRy7us/4Iu8qwJOJ6k (Mage: "a positive retracement means that price actually came back into IDR… negative… never comes back into IDR"), HdY_wCZzZy0 (author: "negative is above the IDR and positive is below… we're going to change that"). Still used in 2023 academy clips (Y3tZGeA4nE4: a short "shouldn't go above 0.5 anymore").
- **QuantX convention (2024-2026):** 0 = confirmation-side IDR edge; **positive = outside the IDR** toward the extension (for a long, above the IDR high; +0.1 may be inside the DR but not the IDR; +0.2 may not even re-enter the DR); **negative = into the IDR**; −1 = opposite IDR edge; below −1 = beyond the opposite IDR edge but still inside the DR until the opposite DR edge. Sources: nMXrQxyJ46Q (explicit: "A retracement below the IDR high would be classified as a negative retracement"), KDob92SRItY (2024, RTY long: "not going below the minus 0.2 retracement"), dfp2aAKt-Ss, fDWbg2f3lRM (retirement area "−0.7 to −1.0"), sAr1xVrR1Ic. Web image: W15 thumbnail nMXrQxyJ46Q (green + above IDR high, red − below). **WEB-EXPLICIT (thumbnail) + TRANSCRIPT.**
- Third meaning (2024 only): "positive retracement" = any retracement that does not break the opposite DR (BS76JMEwHSw, the 94.5% example). **CONFLICT (terminology).**
- PROPOSED DEFAULT for an agent: store retracement as the QuantX-sign value r = (price − confirmation-side IDR edge)/IDR width, signed so that negative = toward/into the IDR; convert any DRlens-era number by multiplying by −1.

**D16 Max retracement / time; extension; percentiles.**
- Max retracement = the deepest point after the confirmation until session end; its timestamp = max-retracement time (qxh2fHQLHlM, 2026). DRlens (2023) also had "retracement before the session high/low" and "retracement after 0.5 SD" (C1wPLsRy7us). **TRANSCRIPT-ONLY.**
- Max extension = the furthest move beyond the confirmation-side IDR edge during the session, in SD units. **TRANSCRIPT-ONLY.**
- Percentile language (2025): the 70th percentile of max retracement = 70% of sessions' max retracements were no deeper than that level; the 70th percentile of extension = level reached by 70% of sessions (dfp2aAKt-Ss, laH3FuECnVg). One 2024 clip says "70% of retracements reach the −0.3 area" (xe3dy8hERgU), which reads the other way. **CONFLICT/AMBIGUOUS wording**; use the 2025 definition.
- "M7 retracement / M7 retracement time" (2026) is a proprietary calculation that is not disclosed (rOSWBtapz-Q, My_yJfguN9I). **TRANSCRIPT-ONLY; not reproducible.**

**D17 Retracement into DR / into IDR (statistics).** "Into DR" = after confirmation price trades back to at least the confirmation-side DR edge; "into IDR" = back past the confirmation-side IDR edge. Typical quoted pairs: 80-90% into DR, 66-80% into IDR (e.g. 87% into DR, DRlens YM ADR Mondays; 86.3%/70.7% NQ Fri RDR short). Sources: C1wPLsRy7us, jPvvCww8aP8, nMXrQxyJ46Q. **TRANSCRIPT-ONLY.**

**D18 "Outside DR" (DRlens 2023).** % of confirmed sessions whose highest close (long) among the last three 5-min candles of the session is beyond the DR in the confirmation direction (62% all days; 65.5% Monday longs; YM ADR view). The author then read it as a conditional probability ("at 3:30 with price at mid-IDR, 62% to close above the DR high") — the metric as defined is not conditional on a retracement, so that reading is not supported by the definition. Source: C1wPLsRy7us. **TRANSCRIPT-ONLY; caution.**

**D19 Volume imbalance (VIB, "whip").** Consecutive candles whose bodies do not touch (close of one ≠ open of the next) while wicks may overlap. Visible on futures feeds, not on spot FX/CFD feeds. "Open" VIB = not yet traded into (a magnet); "rebalanced" once price returns. Rule of thumb for "filled": about three body closes inside it (wicks do not count).
Sources: transcripts (x9qwawK5v5o, _4otRSUDFTg, cCKyP7QUm9o, 2024-26 videos); W8 says DRIB marks volume and gap imbalances as "price magnets or no trespass areas". **TRANSCRIPT-ONLY** (definition) / **WEB-EXPLICIT** (purpose).

**D20 Gap imbalance (GIB, "gip").** Daily GIB: 17:00 close vs 18:00 reopen; weekly GIB: Friday 17:00 close vs Sunday 18:00 open; intraday GIB: a candle closes at its high (low) and the next candle opens above (below) that close. A gap counts as closed once price trades back to the prior close (a wick is enough). GIBs act as barriers or targets. Sources: x9qwawK5v5o, VSjW7C-zkJw, DFiZQEg7oxI, 2024-26 videos (e.g. 0VEq--M8Do8, AmAwkBpcv5E). **TRANSCRIPT-ONLY.**

**D21 Rejection.** Failure to close through a level: wicks through and back, or a close through followed immediately by a larger-body close back (engulf); alternating closes on both sides ("circling") is not a rejection. Source: DLRENiRX-MA, VSjW7C-zkJw, _4otRSUDFTg. **TRANSCRIPT-ONLY.**

**D22 Previous DR levels.** Each earlier session's DR..IDR zones (high side and low side) are levels; 2026 practice extends them at least 3 weeks back and treats overlapping (darker) zones as stronger. Earlier (2022) only the previous RDR levels (and its SDs until 08:30 next day) were carried. Sources: wO7rYmSE9vQ, AmAwkBpcv5E (2026); ZhOruqHWrVE, DLRENiRX-MA (2022); W1 Pine extends RDR SD lines to next 08:30. **TRANSCRIPT-ONLY** (3-week rule) / **WEB-INFERRED** (RDR carry-over).

---

## 2. Daily models (relationship between ADR → ODR → RDR)

General: compare each session with the previous one (ADR vs the previous day's RDR, ODR vs ADR, RDR vs ODR). "Box size" = IDR width (2025-26: lowest-to-highest 5-min close). A broken model is dropped for the rest of the cycle ("no second-guessing"). Sources: wO7rYmSE9vQ, AmAwkBpcv5E, KKzy5uJyMmw; thumbnails W15 (MA9evuOGL7c, KKzy5uJyMmw). **TRANSCRIPT-ONLY** (rules), **WEB-EXPLICIT** (diagrams).

**M1 Upside (expansion) model.** CONFLICT/evolution of wording:
- 2022 (q1s2INPzN6M): each session respected the previous DR highs, made higher-low and higher-high DR levels, and never closed below previously formed DR lows.
- 2022 streams (VSjW7C-zkJw, DFiZQEg7oxI, ZhOruqHWrVE): the next session must not close below the previous session's 50% midpoint and should close above its highs.
- 2024 (MA9evuOGL7c): every session takes out the previous session's high while respecting its levels/lows.
- 2026 canonical (wO7rYmSE9vQ, WD08zKWYEr0, s94XoNkrVsY): **intact** while each session respects the previous session's low (no 5-min close below it) and closes higher; **strong** if it also respects the previous session mid, boxes are green and each box is larger (then +1 SD is the minimum target); **weakened** by a violation of the previous session mid; **broken** by a 5-min close below the previous session low — including an RDR that opens below the ODR low or whose first candle breaks it.
- Image: MA9evuOGL7c thumbnail (staircase; break below ODR low = broken).
- PROPOSED DEFAULT: the 2026 version; "respect" = no 5-min close beyond (wick = warning).

**M2 Downside (expansion) model.** Mirror of M1: each session does not violate the previous session high; strongest with red boxes, respected previous mid and expanding boxes; broken by a 5-min close above the previous session high (e.g. RDR above ODR high; ODR above ADR high); previous mid violation weakens it. Sources: q1s2INPzN6M, MA9evuOGL7c, KKzy5uJyMmw, bB0Gmo16YR4, 3RW8xnl2ttE. **TRANSCRIPT-ONLY.**

**M3 Range expansion model.** CONFLICT/evolution:
- 2022 (q1s2INPzN6M): each DR extends the previous range on both sides while the DR midpoint stays inside the previous session's IDR; a falling midpoint = expansion with a downward tilt; price usually closes near the mean of the total range.
- 2022-23 streams: used both for a one-directional expansion ("range expansion to the upside") and for a two-sided choppy day ("trumpet", both directions ~80% of the time) (cCKyP7QUm9o, ZhOruqHWrVE).
- 2025-26: **all three boxes larger than the previous box** (even by 1-2 ticks) = range expansion; typical target +/-1 SD; it can expand in one direction only. Excluded when the ODR box is smaller than the ADR box or the RDR box is not larger than the ODR box. Can be confirmed before 10:30 if the forming RDR (closes so far) is already larger ("it can only get bigger"). Sources: RX57XC74DIo, 5l-4QzuLEE4, 3RW8xnl2ttE, wO7rYmSE9vQ, l5DwIIH0rJ8.
- PROPOSED DEFAULT: the 2025-26 size-based definition.

**M4 Trumpet.** Two-sided expansion: in 2026, possible when range expansion holds **and** the ODR has already violated both sides of the ADR; also after the ADR mid is broken (latest 2026 videos). Target 1 SD, then price tends to return to the middle; once both sides are played and +1 SD is reached, the session is "done". Sources: wO7rYmSE9vQ, 2EoZdoMcdI0 group, qxh2fHQLHlM/dDyQllTI96A. Earlier "trumpet" = range expansion itself ("Trompete kostet Geld", ZhOruqHWrVE). **CONFLICT (terminology); TRANSCRIPT-ONLY.**

**M5 Range contraction model.** CONFLICT/evolution:
- 2022 streams: the ODR inside a bigger ADR (cCKyP7QUm9o), or any session inside the previous one (FOlhMAotAEc = x9qwawK5v5o); "rare, once or twice every two months" (DFiZQEg7oxI).
- 2024-26 canonical: the **ADR forms inside the previous day's RDR** (MA9evuOGL7c, KKzy5uJyMmw, sAr1xVrR1Ic, rOSWBtapz-Q). Price is squeezed in one direction (often to the previous RDR's IDR/DR levels, sometimes the previous RDR extreme), then makes an "explosive" move the other way. Once the previous RDR high (or low) has been taken, the squeeze in that direction is assumed done and further trades that way are lower probability; a confirmation toward the untouched side targets the previous RDR's opposite levels. Excluded if the ADR is outside the previous RDR (RX57XC74DIo). If price sits right at a crucial previous-RDR level, trade one bullet or none (sAr1xVrR1Ic).
- PROPOSED DEFAULT: the 2024-26 definition.

**M6 Other formations (2022-23).** Reversal model: small ADR, then a big ODR/RDR expansion taking it out → possible swing reversal (cCKyP7QUm9o). Session inside a big previous session → correction/range (cCKyP7QUm9o, "99%"). **TRANSCRIPT-ONLY.**

**M7 Model exclusion by opening position (2025).** A session opening below the previous session's low excludes the upside model; opening above the previous high excludes the downside model; opening inside keeps all three and makes the previous session mid decisive. The ODR taking out both ADR sides excludes both directional models. Sources: 5l-4QzuLEE4, BS76JMEwHSw, KKzy5uJyMmw. **TRANSCRIPT-ONLY.**

**M8 Counter-model confirmations.** When a directional model is intact and the session confirms the other way, trade it only with targets capped at the structural barrier (e.g. downside model + long confirmation → target at most the ADR mid/ADR high; "the higher your target the lower the probability"), or skip it (PXTJrcRPFT8 "confirmation to avoid"). Sources: BeU96RIiUzE group, q-L5TEIZGvY, PXTJrcRPFT8. **TRANSCRIPT-ONLY.**

**M9 Third-party variants.** A+ (W12) relabels models ("bullish range expansion" for a bearish case, etc.) and targets 0.5 SD; FX Replay (W18) redefines DR/IDR as "Day Range / Initial Day Range" with London 02:00-05:00 and NY 08:00-11:00 — not the author's method. **CONFLICT (third party).**

---

## 3. Time rules

**T1 No setups before the DR hour ends for beginners.** Wait for the box and for confirmation; "before 10:30, don't take a trade" was the first-video rule for beginners. Pre-confirmation trades are for advanced traders using the models (§4 E6). Sources: cCKyP7QUm9o, VSjW7C-zkJw, W11 tip 3 (IDR levels "after 10:30"). **WEB-INFERRED.**

**T2 Early vs late confirmation.** A confirmation within the first 30 minutes after the box is a sign of strength; "the later the confirmation, the less likely price keeps expanding". Statistics must be read per confirmation window (DRlens 30-min buckets; QuantX 15-min or 30-min) and do not transfer across windows. Sources: ZhOruqHWrVE, _4otRSUDFTg, 9ASmoYOuCCg, jPvvCww8aP8, KDob92SRItY. **TRANSCRIPT-ONLY.**

**T3 Last hour.** Normally no new trade in the last hour of a session; the retirement setup is the stated exception ("normally one hour there's enough time"). Examples of "too late": ODR after ~08:00, ADR after ~01:00, RDR after ~12:00-13:00 in some backtests. Sources: ZhOruqHWrVE/rpfs35CXZfo, gejIU96PFKY, VSjW7C-zkJw/IQUFS0SnV2s. **CONFLICT (inconsistent cut-offs); TRANSCRIPT-ONLY.** PROPOSED DEFAULT: no new entries in the last 60 minutes; a data-driven cut-off (T5) overrides.

**T4 Session end.** CONFLICT: 2022-23 streams either exit at the session end or keep the trade with the stop at break-even into the next session (VSjW7C-zkJw, _4otRSUDFTg); 2025-26 time-and-price rules close everything at the session end because targets are filtered for the session (last ODR candle 08:25, last RDR candle 15:55; "close everything at 16:00") (dfp2aAKt-Ss, laH3FuECnVg, 9ASmoYOuCCg). Management across sessions is allowed with stops at BE or tighter (MA9evuOGL7c, Z00VwN92Umo). PROPOSED DEFAULT: flat at session end unless the stop is at break-even or better.

**T5 Time-and-price entry window (QuantX, 2024-26).** From the start of the first mode (from the left) of the max-retracement-time distribution until the median time of max retracement (50% of max retracements done); some keys use the 70th-percentile time as the cut-off; no entries after the cut-off. Sources: dfp2aAKt-Ss, laH3FuECnVg, jPvvCww8aP8 ("no entries should be taken after"), xe3dy8hERgU, mbZRNw5n61o. **TRANSCRIPT-ONLY.**

**T6 Time filter on DR-true (2026).** In some keys the DR-true rate depends strongly on when the max retracement happened: CL Fri RDR long 10:30-11:00, 213 sessions: 95% true if the max retracement came before 12:00, 61% if after; ETH Tue RDR short: 83% if before 11:45, 54% after. Each candle that passes without a new extreme raises the probability that the extreme is in. Sources: qxh2fHQLHlM, 9ASmoYOuCCg. **TRANSCRIPT-ONLY.**

**T7 10:00 reversal window (2026).** Session reversals often happen around 10:00 ±~10 minutes, but only count when price is at a key level with stacked confluence; "a candle in the middle of nowhere" is no signal. Sources: 3RW8xnl2ttE, dDyQllTI96A, hAhyuQj2p9o. **TRANSCRIPT-ONLY.**

**T8 Transition windows are preparation time (2026).** 02:00-03:00 and 08:30-09:30: mark the working range, previous DR levels, GIBs/VIBs and model status; no trading. Sources: AmAwkBpcv5E, wO7rYmSE9vQ. **TRANSCRIPT-ONLY.**

**T9 ADR shortcut.** If one can only trade the ADR, end its validity at 01:00 instead of 02:00 (a few points higher DR-true simply because there is less time to fail). Source: C1wPLsRy7us / QAC__ieFwRk. **TRANSCRIPT-ONLY.** Note: this changes the definition, not the edge.

**T10 News and holidays.** High-impact equity news days (CPI, FOMC, NFP, PPI; US midterm elections) are excluded from the 88% claim and should not be traded (beginners at least wait for confirmation on CPI); be flat about one hour before a high-impact release; FOMC has two phases (decision, then the press conference ~30 min later); in heavy US-news weeks trade commodities (e.g. crude) instead of equity indices; do not trade US bank holidays. News lists differ by instrument (FX reacts to other releases).
Sources: Uxwr4CVhGhg, W3 (news exclusion stated), W6 ("event-day filter"), W20 snippet (author: less probability on news days), x9qwawK5v5o, VSjW7C-zkJw, cCKyP7QUm9o, qFWSUv-nabs, w-H2JpiTsDE. **WEB-EXPLICIT** (exclusion) / TRANSCRIPT (details).

**T11 Kill zones/lunch are irrelevant.** "Algos don't have lunch." Source: _4otRSUDFTg. **TRANSCRIPT-ONLY.**

---

## 4. Entry setups (always in the confirmation direction unless marked advanced)

**E0 Gate.** No trade against the confirmation (except the advanced cases E6-E8); after a confirmation, entries only after a retracement to a pre-defined level/zone and a rejection, or at a pre-defined limit. If the planned target is reached before any retracement into the entry zones, there is no trade ("don't chase"). Sources: W10, W11 tips 3/6, W13, dfp2aAKt-Ss, hAhyuQj2p9o. **WEB-EXPLICIT (gate) / TRANSCRIPT (no-chase).**

**E1 Level-rejection entry (the basic DR trade).** After confirmation, wait for a pullback to the confirmation-side DR edge, IDR edge, IDR mid, opening or closing price, an SD level, previous-session levels or a VIB/GIB; enter on a rejection (at the close of the rejection candle or the next open), latest by about the third rejection. Sources: W11 (tips 3 and 6: IDR high, low and mid are entry points after confirmation), W13 setup 1, W12 image (long at DR-high retest), 1B69Y1GZ1t4, cCKyP7QUm9o. **WEB-EXPLICIT.**

**E2 0.5 SD retest.** A pullback to the 0.5 SD level beyond the confirmation-side IDR edge, then continuation (target new extreme / 1.5 SD). Sources: 1B69Y1GZ1t4, W13 setup 2. **WEB-EXPLICIT (third party) / TRANSCRIPT.** Note: W13 describes it confusingly (as if 0.5 lay inside the range).

**E3 Retirement setup ("SHL/GDL").** The author's own name is **retirement setup** (not "retracement setup"): 260 mentions in 64 transcripts, zero of "retracement setup"; "that's why I call it the retirement setup" (VdY8tYYd9m0); he later nicknamed it SHL ("superman holds the line", long) / GDL ("gandalf holds the line", short) (W20 snippet); third-party playbooks use the same name (W13). **WEB-EXPLICIT (name).**
- Trigger: after a confirmation, price retraces to the **opposite side of the range** — wording varies: "returning to the other side of the DR, preferably below the 75% retracement of IDR low to high" (x9qwawK5v5o, FOlhMAotAEc); "price returns in the area of the opposite IDR levels" (gejIU96PFKY); "retirement setup area starting from −0.7", "from −0.7 to −1.0" in QuantX sign (sAr1xVrR1Ic, fDWbg2f3lRM); DRive tested a 75%-of-IDR trigger (C1wPLsRy7us). In both conventions this is the deepest ~25-30% of the IDR plus the strip between the opposite IDR and DR edges. Third party: "retrace about 80 percent or more to the opposite side of the IDR" (search-engine snippet only; the page behind it was not opened); "retraces back to opposite DR/IDR" (W13). **CONFLICT (depth 70-80%); PROPOSED DEFAULT: zone = −0.7 … opposite DR edge (QuantX sign).**
- Entry: "blind" at the zone (x9qwawK5v5o, _4otRSUDFTg) or on the first rejection there (W13, 2024-26 videos). **CONFLICT; PROPOSED DEFAULT: first 5-min rejection close inside the zone.**
- Stop: 2 ticks beyond the opposite DR edge (gejIU96PFKY, MA9evuOGL7c; W10 for the IDR-low variant; W13 "few points under/above DR"); the author personally often used tighter stops beyond the IDR or a VIB and re-entered. **WEB-EXPLICIT.**
- Target: the confirmation-side DR/IDR edge (partial), a new session extreme, or the next SD level; ≥3R in 2024+ (gejIU96PFKY, MA9evuOGL7c, hhOoJy17Flk). **TRANSCRIPT-ONLY.**
- Timing: needs about an hour left; the "last hour" version is shown as an exception (IQUFS0SnV2s thumbnail W15; VSjW7C-zkJw). **CONFLICT with T3.**
- Pre-confirmation variant (author X thread, W10): after an early indication (close above IDR high), a pullback to the IDR low is the long trigger, stop 2 ticks below the DR low, target IDR high or a new high. **WEB-EXPLICIT.**
- Statistics (author): 1,179 retirement setups in 4 years across ADR/ODR/RDR, 957-965 "working out", 182 stopped (x9qwawK5v5o) — the numbers do not add up (957+182 = 1,139) and the success definition is not given; "182 times the DR got stopped out" suggests success = the opposite DR held, i.e. a stop-survival rate (~81%), not a target-hit rate. DRive's own backtest of a 75%-of-IDR trigger gave 43.33% (26 W / 34 L / 7 neutral, target "standard deviation null", 219 sessions) and 35% for RDR only with the DR as target (5 W / 9 L / 4 N) (C1wPLsRy7us; QAC__ieFwRk captions say 290 sessions). **CONFLICT: survival ~81-85% vs target-hit 35-43%.** Plan with the lower number.

**E4 Time-and-price (QuantX) procedure (2024-26) — the most mechanical rule set.**
1. Key = instrument + session + weekday + confirmation direction + confirmation window (15/30 min). Nothing transfers across windows.
2. Read DR-true % for the key; then filter to DR-true sessions ("assume the session holds true").
3. Entry window = first mode of the max-retracement-time distribution → median (sometimes 70th-percentile) time of max retracement; no entries after.
4. Read P(retrace into DR) and P(retrace into IDR).
5. From the max-retracement distribution (0.1-SD buckets, cross-filtered to the entry window) choose 1-2 zones covering the median/70th percentile; note cut-offs and empty ranges ("no max retracement between X and Y") for stop placement.
6. Target = the 70th-percentile extension (or the dense bucket just before it); the mode/median are more aggressive; cross-filter by the chosen zone; targets may depend on entry time (e.g. before/after the median time).
7. Execution: limit 1 tick inside the zone's near edge; stop 1-3 ticks beyond the zone's far edge; the second bullet in the second zone with the same logic; max two bullets.
8. If the target is hit before a zone is reached: no trade. Close at session end if not hit.
9. After the median time, one may assume the max retracement is in (stop to BE or just beyond the extreme).
Sources: dfp2aAKt-Ss, laH3FuECnVg, jPvvCww8aP8, HH2VLbhKNOQ, xe3dy8hERgU, Z_TzecGFRXo, mbZRNw5n61o. W8 describes QuantX as distributions, mode, median to find "time-based and price-based entries". **TRANSCRIPT-ONLY (procedure) / WEB-EXPLICIT (tool purpose).**
2023 precursor (DRlens + DRive): enter when the retracement-time mode window has closed, stop beyond the retracement low, target the **mode** (not median) of the extension distribution, only if ≥3R, BE at +2R (6ijtg_2TACk, Y3tZGeA4nE4). **CONFLICT (mode vs 70th percentile target).**

**E5 Two-bullet structure.** Bullet 1 in the upper zone (IDR edge, IDR mid, opening/closing price, clusters) with the stop placed so that it covers the start of the retirement area (standard: at −0.7, KKzy5uJyMmw); bullet 2 in the retirement area. Maximum two trades per session, "no exceptions" (2EoZdoMcdI0). Sources: MA9evuOGL7c, hhOoJy17Flk, wzZi22NDxXU, 2EoZdoMcdI0; W10 follow-up (max 2R per session). **WEB-EXPLICIT (2R) / TRANSCRIPT (bullets).**

**E6 Advanced pre-confirmation / pre-box entries.** Allowed only with strong model context and stacked confluence (e.g. range expansion confirmed before 10:30, ODR low as the "line in the sand" for an upside model, 10:00 window at a key level, ODR-open entries when market state and models align); accept being stopped if the confirmation goes the other way. Sources: XsdKPKyGhJY, hAhyuQj2p9o, BtgOtpFIeHo, GMG02VI2lRs, ZhOruqHWrVE, DFiZQEg7oxI. **TRANSCRIPT-ONLY.**

**E7 Counter-trend inside the range (advanced).** Only toward a data-based retracement target with room (big DR) and rejections; targets stay inside the range. Sources: pxL9XxVE-Ig, VSjW7C-zkJw, 1B69Y1GZ1t4 (tip 5). **WEB-INFERRED** (W11 tip 5).

**E8 False-day breakout (advanced).** After a confirmation, wait for the opposite-side 5-min close (session false), then enter with the next candle toward the false-day statistics. Source: pxL9XxVE-Ig. **TRANSCRIPT-ONLY.**

**E9 Order mechanics.** 2022: market orders only (ZhOruqHWrVE) — but a limit order at a DRlens level in pxL9XxVE-Ig; 2024-26: limit orders at pre-defined zones and "limit re-entry" are standard. **CONFLICT; PROPOSED DEFAULT: limits at pre-computed zone edges.**

---

## 5. Stops

**S1 Baseline stop: 2 ticks beyond the opposite DR edge** (the "statistical" stop: it only fails on a false session or a wick beyond). Sources: W10, W11 tip 3, W13, 1B69Y1GZ1t4, gejIU96PFKY. **WEB-EXPLICIT.** Futures ticks; add the spread for CFD/prop feeds (x9qwawK5v5o).

**S2 Tighter structural stops.** 2-3 ticks beyond the IDR edge, the IDR mid, a VIB, the opening or closing price, the previous session mid; with a big DR-IDR gap use 3 ticks beyond the IDR edge; in T&P 1-3 ticks beyond the zone. Sources: KDob92SRItY, ujgFcJH7mLU, dfp2aAKt-Ss, l5DwIIH0rJ8 group. **TRANSCRIPT-ONLY.**

**S3 Philosophy.** Stops "close out scenarios"; place them where the scenario is invalid, beyond significant levels, not at equal highs/lows (retail stops get swept). Sources: 2T4qSRRBimY/VSjW7C-zkJw, IT4eQNiqHfU. **TRANSCRIPT-ONLY.**

**S4 Stop-survival statistics (author).** "84.5-85%" not stopped with a stop beyond the opposite DR (ES, _4otRSUDFTg); "<15%" close beyond (RDR, VSjW7C-zkJw); "<12%" (x9qwawK5v5o); "~80%" (2025-26); GBPUSD Wed ODR short confirmation 04:00-04:30: only 4 of 73 retracements went beyond the DR → 94.5% (BS76JMEwHSw). **TRANSCRIPT-ONLY.** These are close-based rates; a wick can still take a 2-tick stop.

---

## 6. Targets

**TG1 0.5 SD = "low-hanging fruit".** Once price leaves one side of the DR it reaches the 0.5 SD level "with extremely high probability". Sources: W11 tip 4, W13 (".5 has the highest chance of getting hit"), W12 image, 1B69Y1GZ1t4, q1s2INPzN6M. **WEB-EXPLICIT.** If 0.5 SD is already reached by the confirmation move, the next target is 1 SD (x9qwawK5v5o).

**TG2 1 SD in expansion/range-expansion models** ("typically the minimum target" in expansion models, 2026). Sources: wO7rYmSE9vQ, Z00VwN92Umo, RX57XC74DIo. **TRANSCRIPT-ONLY.**

**TG3 Data targets.** QuantX: 70th-percentile extension (safer) or the densest bucket; 2023 DRlens: the mode of the extension histogram, not the median; per-weekday mean SD (e.g. Tuesday RDR 0.6 rather than 0.5, VdY8tYYd9m0). **CONFLICT (mode vs 70th pct); TRANSCRIPT-ONLY.**

**TG4 Structural targets.** New session extreme, previous session highs/lows/mids, open VIBs, daily/weekly GIBs, previous RDR levels in a contraction model. Sources: wO7rYmSE9vQ, MA9evuOGL7c, KKzy5uJyMmw. W13 recommends "previous low or high". **WEB-EXPLICIT (W13) / TRANSCRIPT.**

**TG5 Minimum reward.** ≥2R (2022 streams) → ≥3R (2023 academy onward). **CONFLICT (evolution); PROPOSED DEFAULT 3R.** Sources: ZhOruqHWrVE, 6ijtg_2TACk, KDob92SRItY.

---

## 7. Management

**MG1 Break-even.** CONFLICT: +1R → BE (streams, _4otRSUDFTg); +1R → reduce risk to ~0.5R (ZhOruqHWrVE); +2R → BE (2023 academy, 6ijtg_2TACk); W13 (third party): BE once 1R is held (not on a wick). PROPOSED DEFAULT: BE after a 5-min close at ≥+1R, or per backtest.

**MG2 Partials.** Common: 50% at 0.5 SD or at the confirmation-side DR edge (retirement), rest at 1 SD/new extreme. Sources: ZhOruqHWrVE, VSjW7C-zkJw. **TRANSCRIPT-ONLY.**

**MG3 Trailing.** By structure: 3 ticks beyond a broken-and-retested previous-DR-level cluster, beyond newly created open VIBs, or by SD levels; never on emotion. Sources: wO7rYmSE9vQ, 8RKujaIq4Hw, W13 (trail by SD on 15-min closes, third party). **WEB-INFERRED.**

**MG4 No manual exits (2023 academy rule).** Exit only by stop or target; stops move only by rules. Source: Y3tZGeA4nE4. Conflicts with discretionary session-end exits (T4). **TRANSCRIPT-ONLY.**

---

## 8. Risk

**R1 Fixed-fraction R.** Size = fixed % of equity / stop distance; the author ~1% per R, beginners 0.1-0.5%; never fixed contracts. Sources: VSjW7C-zkJw, DLRENiRX-MA. **TRANSCRIPT-ONLY.**

**R2 Per-session loss limit.** Max 2R lost per session (then stop for that session); normally ≤3R per day. Sources: W10 follow-up thread ("don't risk more than 2 R per session"), x9qwawK5v5o, 2EoZdoMcdI0 ("two trades maximum, no exceptions"). **WEB-EXPLICIT.**

**R3 A false session is a normal loss.** "Take a loss and go next"; do not build solutions for the ~20%. Source: W10 follow-up. **WEB-EXPLICIT.**

**R4 Weak keys → smaller exposure.** Keys with low DR-true (e.g. <70%) → one bullet or reduced risk; conflicting context → 0.5R second bullet. Sources: X8P4pPZJmGs, J054OlJm8jE. **TRANSCRIPT-ONLY.**

---

## 9. No-trade filters (union; each TRANSCRIPT-ONLY unless noted)

1. High-impact news days for that instrument, US bank holidays, holiday half-days (WEB-EXPLICIT for news: W3, W6).
2. No confirmation (beginner rule) — except E6.
3. Target already reached before any retracement into the zones.
4. RR < 3 (2023+).
5. After −2R in the session / two trades used.
6. Entry-window cut-off passed (T5) or last hour (T3).
7. Confirmation against an intact model with a barrier just ahead (PXTJrcRPFT8).
8. Trumpet already played out / squeeze already done in that direction / +1 SD already reached in range expansion.
9. All three boxes clustered in one area (consolidation) or price oscillating between ADR mid and ODR mid (6O8fDaRNTMA).
10. Price "circling" a DR line without clean rejections; price in the middle of the range with no level.

---

## 10. Tools

| Tool | What it is | Evidence | Tag |
|---|---|---|---|
| DR/IDR V1 (V1.5) Pine, free | DR/IDR boxes, mids, opening line, RDR SD lines (static 10+10 by default), box colour option, ADR/ODR/RDR; 367 lines; last update 15 Jan 2023 | W1 | WEB-EXPLICIT |
| TICK Grid (TheMas7er) | NYSE TICK pane, thresholds ±600 and ±800, zero line; author uses it on the 1-min chart during RTH for US indices | W14; cCKyP7QUm9o | WEB-EXPLICIT |
| DRlens (Jan 2023) | web statistics dashboard (developer "Mage"): 20y futures data, filters by weekday/month/week-of-month, DR true/false, confirmation direction and 30-min window; histograms of extension/retracement; DRlens sign convention (D15) | C1wPLsRy7us, 4Iu8qwJOJ6k, pxL9XxVE-Ig | TRANSCRIPT-ONLY |
| DRive 1.0 (Jan 2023) → M7 DRIVE 2.1 | academy Pine: setup backtester (trigger = % IDR retracement, target DR/SD), DRlens lines on chart, alerts; 2.1 = "statistical script": retracement/extension areas, median times, clusters ("TDRC"), win-rate statistics | QAC__ieFwRk; W8, W9 | WEB-EXPLICIT (2.1 description) |
| M7 QuantX (2024+) | database, "120 million data points", 18-20 years; distributions, mode, median, percentiles; filters asset/session/weekday/direction/confirmation window/box colour/DR-true | W8, W9; xe3dy8hERgU | WEB-EXPLICIT |
| DRIB | indicator for volume and gap imbalances | W8 | WEB-EXPLICIT |
| Indicator suite | M7 Weekly DR, M7 MTF, M7 Daily Box, M7 Weekly Box, M7 DIB / M7 DDR (the page lists DIB on one tier and DDR on others) | W8, W9 | WEB-EXPLICIT (names only; no public definitions) |
| DR Frame | academy trading framework, "27 systematic and pragmatic steps"; streams mention "frame one/two/three" rule sets | W8; eO78N2DsPwM, lgKYeW5WpXI | WEB-EXPLICIT |
| M7 Metrics | journal (trading + lifestyle metrics, playbook heatmaps, backtest import); "free" per 2024+ video descriptions | W8, W15 descriptions; Igp-obEjrN4 | WEB-EXPLICIT |
| M7 LIVE / MIND | webinars (8 or 12 per month — the pages disagree) / 12-week mindset workshop | W8, W9 | WEB-EXPLICIT |

Weekly DR, "weekly sequencing", the five VIB types, "special volume imbalance", "M7 retracement" and "VFP" are academy-only; no public definitions exist. **OPEN.**

---

## 11. Instruments

- Original claim: ES, YM, NQ RDR only (RTY "should work") (Uxwr4CVhGhg). TradingView: all major FX pairs, BTC, ETH, US indices (W1). m7dr.com data list: E-mini S&P, Nasdaq, Dow, Russell, DAX futures, EUR/USD, GBP/USD, EUR/JPY, Bitcoin, crude oil, gold (W8). Videos add USDJPY, EURAUD, AUDUSD, 6E/6B/6A, silver, platinum, ETH. **WEB-EXPLICIT (lists).**
- FX: analyse on the currency futures (6E, 6B, 6A…), because spot/CFD feeds differ and show no VIBs; execute on the broker feed (tAx-lXJt4l0, wzZi22NDxXU). **TRANSCRIPT-ONLY.**
- Equity index choice: 2022-23 "ES is the cleanest; stay away from NQ/YM if new; trade one index" (cCKyP7QUm9o) vs 2025 intermarket use of silver/platinum/gold leaders (JL_KDGxsGiQ). **CONFLICT (evolution).**
- Per-instrument DR-true examples (author): gold ADR 73% / ODR 82% / RDR 95% over 1,981 sessions (KDob92SRItY); EURUSD ODR ~80%, RDR ~83% (DRive, C1wPLsRy7us); USDJPY 84% (DFiZQEg7oxI); BTC ~75-80% (W2). **Mostly TRANSCRIPT-ONLY.**

---

## 12. Independent evidence and critiques (web)

- **TFO backtest script (W4):** ES RDR 09:30-10:30, session to 16:00, success = the opposite DR extreme never traded through (default "Wick"; a "Close" option exists); news days not removed. Chart shows 71.73% over 237 sessions. The author (TFO) notes the sample is small and that part of the claimed 88% comes from excluding news days. Only independent number found; it tests the wick version of the rule. **WEB-EXPLICIT.**
- **Showcase chart of W1 is a false session** (image; a 2023 commenter noticed). **WEB-EXPLICIT (image).**
- **TradingView comments (W2):** one user reports a 2-3 hour FX backtest as "useless"; the author replies FX ~85% and that "DR/IDR in the first place has nothing to do with entries or exits"; others report it works. Anecdotal. **WEB-EXPLICIT.**
- **MQL5 (W17):** a seller notes the free version counts neutral (unconfirmed) days as true, inflating the rate. **WEB-EXPLICIT.**
- **Trustpilot (W16, 4 reviews, 2024-25, TrustScore 2.6):** complaints of low win rates/low frequency, rules and frameworks that "constantly change", explanations in hindsight, no refunds. Small sample, unverified. **WEB-EXPLICIT.**
- **Author's own numbers show low win rates for mechanical versions:** DRive 43%/35% (E3); CL Wed ODR long T&P backtest 67 trades, 34.33% win rate, +86.46R, 13 consecutive losses Feb-Aug 2022 (Igp-obEjrN4); student 56 trades, 39% win rate, avg win 5.2R (lgKYeW5WpXI). These are consistent with "high DR-true, low target-hit". **TRANSCRIPT-ONLY.**
- **Backtest vs live:** the author says a backtest week gave ~45-49R while his real week was ~15R (x9qwawK5v5o). **TRANSCRIPT-ONLY.**
- **Web summaries mostly repeat the 2022 rules and the Pine code** (W3, W5, W6, W11, W13). They add no independent statistics and sometimes distort (W6 IDR confirmation, W13 0.5 SD placement, W18 new definitions).

---

## 13. What an autonomous agent still cannot get from public sources

1. The exact IDR formula used by QuantX (bodies vs closes), and whether QuantX DR-true % excludes unconfirmed sessions or news days.
2. Which "mid" (IDR or DR) the model rules use.
3. The per-key statistics themselves (QuantX is paywalled); every number here is a screenshot-level claim from videos.
4. The success definition behind 1,179/957-965/182 and behind "80%" in 2025-26 (close-based; which session end; first confirmation only?).
5. Weekly DR, M7 retracement, DIB/DDR, special VIB types — undisclosed.
6. Precise thresholds for "inside", "respect", "violate" (close vs wick) in some model statements (the 2025 rule says a 5-min close breaks a model, a wick is a hint).
