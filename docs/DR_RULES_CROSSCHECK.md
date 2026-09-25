> **Что это (по-русски).** Проверка двух выписок правил из субтитров (A — из 10 стримов, B — из 146 роликов) по
> исходным субтитрам и открытым источникам. Итог: выдуманных правил не найдено; исправлены знак отката по эпохам
> (DRlens 2023 и QuantX 2024–26 противоположны), название «retirement setup», цель DRive 43% (край IDR, не +0,5),
> смысл «85–88%» (удержание стопа, не винрейт). Эти поправки внесены в `docs/STRATEGY.md`. Пути к файлам выписок
> ниже — это временная папка сессии, в репозиторий выписки не входят.

# Cross-check of Extraction A (live streams) and Extraction B (regular videos)

Verifier: independent agent, 2026-09-25. Inputs checked: `live_streams_rules.md` (A) and `notes_videos.md` (B). Evidence: the raw transcript file `M7DR_all_transcripts.txt` (156 videos; searched per video id with regular expressions) and the public web sources listed in `docs/DR_RULES_WEB.md` §0.1 (keys W1…W22). No market data, no project research.

Verdicts: **CONFIRMED** (transcript and/or web agree) · **MISQUOTED** (source says something different; correction given) · **UNSUPPORTED** (not found) · **WEB-CONTRADICTED** · **AMBIGUOUS** (source garbled or open to two readings). "Scoped" = correct for the cited period but not valid for the whole 2022-2026 corpus.

## 0. Method and two structural findings

**Method.**
- Qualitative claims: searched the cited video(s) for the key phrase and read ±300-2,500 characters of context.
- Numbers, automated: every numeric token in A (lines citing S01-S10) and in B (bullets under each section header, scoped to the video ids in that header or line) was searched in the cited transcript(s), with normalisation for caption formats (e.g. "4:30 a.m.", "1 p.m.", "0.5 4", "1,900 81").
  - A: 783 tokens; 707 found in the cited stream(s). Nearly all the rest were section numbers, row numbers or time formats; the residual real items were checked by hand (below).
  - B: 136 bullet lines contain numbers; 109 lines had every number found in the cited videos. The other 27 failed only on caption formatting ("9.30", "22.4. 48R", "1,900 81", "1 .4") and were confirmed by hand.
- Numbers-found is not the same as meaning-confirmed. The meanings of all "special attention" items and of every definition/model/stop/target/risk/time rule listed below were read in context.

**Finding 1 — A and B are not independent for 2022-2023.** Many of B's "regular videos" are re-cuts of the same live streams A used (shingle overlap of the auto-captions ≥10%):

| B video | = A stream |
|---|---|
| QAC__ieFwRk (DRive intro), 4Iu8qwJOJ6k (DRlens intro) | S03 C1wPLsRy7us |
| NEsfxtb0b2Q, FOlhMAotAEc | S04 x9qwawK5v5o |
| V2_pvIn_8Cc, psUJaYUnLnw, tB6HCn9rtFE, IQUFS0SnV2s, 2T4qSRRBimY | S05 VSjW7C-zkJw |
| HIgiB0wtDy0, arI5F__5KVc | S06 DFiZQEg7oxI |
| qJ4G2BZVf9Q | S07 cCKyP7QUm9o |
| IT4eQNiqHfU, rpfs35CXZfo, BWBb2Mc5eKA (and gejIU96PFKY by content: same "too late, it's one o'clock" retirement passage) | S08 ZhOruqHWrVE |

So where A and B agree on 2022-23 material they are quoting the same recording. Agreement there is one source, not two.

**Finding 2 — web evidence is thin on everything after 2022.** Public sources confirm the 2022 core (sessions, DR/IDR construction, SD step, confirmation, early indication, box colour option, 0.5 SD target, stops beyond the DR, the retirement setup's name and shape, 2R/session). All models after 2022, the QuantX procedure and nearly all statistics are transcript-only.

---

## 1. Special-attention items

### 1.1 Retracement sign convention — both extractions are right, for different eras

| Era / tool | Convention | Evidence |
|---|---|---|
| DRlens, Jan 2023 | 0 = confirmation-side IDR edge; **positive = back into the IDR** (1 = opposite IDR edge); **negative = never re-entered the IDR** | C1wPLsRy7us / 4Iu8qwJOJ6k (Mage): "a positive retracement means that price actually came back into IDR… if it's negative… it never comes back into IDR". HdY_wCZzZy0 (author): "negative is above the IDR and positive is below… But we're going to change that". Y3tZGeA4nE4 (2023 academy): short example "shouldn't go above 0.5 anymore" (positive = into range). |
| QuantX, 2024-2026 | 0 = confirmation-side IDR edge; **positive = outside the IDR** toward the extension (+0.1 can be inside the DR, +0.2 may not reach the DR); **negative = into the IDR**; −1 = opposite IDR edge; < −1 still inside the DR until the opposite DR edge | nMXrQxyJ46Q (Apr 2025): "A retracement below the IDR high would be classified as a negative retracement and statistically counted as a retracement into the implied defining range." KDob92SRItY (2024, RTY long): "price not going below the minus 0.2 retracement". fDWbg2f3lRM: retirement area "minus 0.7 to minus 1.0". Web: thumbnail of nMXrQxyJ46Q (W15) shows green "+" above the IDR high, red "−" below it. |
| 2024 outlier | "positive retracement" = any retracement that does not go beyond the opposite DR | BS76JMEwHSw (the 94.5% example). |

- **A** (§1.7, §11.1: "negative means it never re-entered the IDR"): **CONFIRMED for DRlens 2023, but scoped.** It must not be applied to 2024-26 numbers. A itself flags "he announced a change" (C12, Q20); the change did happen.
- **B** (lines 113, 128, 165, 182, 191: 2024-26 negative = into the IDR): **CONFIRMED.** B's line 113 ("ambiguity") is resolved by nMXrQxyJ46Q and the thumbnail.
- **Correction for both:** state the era in every stored number. To convert DRlens-era retracements into QuantX sign, multiply by −1.

### 1.2 IDR by bodies vs closes — CONFLICT between the author's code and his later wording
- Author's Pine (W1, "DR/IDR V1.5", Jan 2023): `ridrhigh := math.max(open_value, close_value, ridrhigh)`, `ridrlow := math.min(open_value, close_value, ridrlow)` — **bodies, opens included**. Same in promuckaj's script (W3), the thinkScript port (W5), LuxAlgo (W6), the Scribd playbook (W13). 2022 videos: "highest body and the lowest body" (Uxwr4CVhGhg), "highest and lowest body close or open" (q1s2INPzN6M).
- 2024-26 wording: "IDR high … highest close on a 5minute time frame" (h47hEvyA45A); Fib "applied to the lowest and highest 5-minute close" (nMXrQxyJ46Q); "lowest to highest 5-minute closes" (tb4xMGybw28, CzVFHQEyIjk); "highest closing price of the first hour" (sAr1xVrR1Ic).
- A (§13 Q1, "streams never restate"): **CONFIRMED** (the streams do not define it); now answered by W1 code for 2022-23.
- B (line 190, "OPEN QUESTION: must check Pine source"): **resolved — Pine uses bodies (open and close).** The conflict with the 2024-26 wording remains; the QuantX formula is unpublished.
- The two definitions differ only when an open lies outside all closes of the hour: the first bar's open, or an open after a gap from the previous close (a VIB).

### 1.3 Session and trading-window times — CONFIRMED (web + transcript)
- Formation 19:30-20:30 / 03:00-04:00 / 09:30-10:30 and windows 20:30-02:00 / 04:00-08:30 / 10:30-16:00 NY time. These are the Pine defaults (W1), and the author confirmed the last bars as 10:25 / 03:55 (W3 release note). Transcript: ZhOruqHWrVE (= rpfs35CXZfo) "The RDR goes from 10:30 to 4:00. The ADR goes from 2030 till 2 in the morning. And the ODR timing is from 4 to 8:30."
- A §1.1 and B lines 6, 65: **CONFIRMED.**
- A §1.1 "Daylight saving: never mentioned": **CONFIRMED for the streams**, but the web settles it. The Pine uses America/New_York (DST fixed in the 26 Nov 2022 release) and the author told users not to change the times whatever their timezone (W2). So A's INFERRED "same NY-time sessions for all instruments" is **CONFIRMED by the web**.
- One 2022 statement conflicts: Part 2 says the RDR rule stays valid overnight (1B69Y1GZ1t4). B line 5 records it (Tip 7); A does not. Later material drops it.

### 1.4 Model definitions 2022-2026 — mostly CONFIRMED; both extractions under-mark the evolution
- Upside/downside expansion: 2022 P3 (q1s2INPzN6M) = sessions respect previous DR highs, make higher lows/highs, never close below earlier DR lows. 2022 streams = don't close beyond the previous session's 50%. 2026 (wO7rYmSE9vQ) = each session respects the previous session's low (upside) / has not violated its high (downside); expanding boxes → +1 SD minimum.
  - B lines 6, 70, 104, 117, 156, 238, 285, 292, 321-323: **CONFIRMED.**
  - A §2.1: **CONFIRMED** (2022 only).
- Range expansion: 2022 P3 = each DR extends the previous range on both sides with the midpoint inside the previous IDR. 2022-23 = also used for one-directional expansion and for the two-sided "trumpet" day. 2025-26 = all three boxes larger than the previous (even by 1 tick); 1 SD target; can be one-directional; trumpet only if the ODR also violated both ADR sides.
  - A §2.2 (terminology contradiction C6): **CONFIRMED.**
  - B line 72 ("RANGE EXPANSION = trumpet"): **CONFIRMED for 2023 but superseded** — B's own lines 223, 324, 218 give the 2025-26 distinction. B line 72's "Friday close / Monday continuation" is **UNSUPPORTED** (not found).
- Contraction: 2022 streams = ODR inside a larger ADR (cCKyP7QUm9o) / any session inside the previous one (x9qwawK5v5o); 2024-26 = ADR inside the previous day's RDR (MA9evuOGL7c, sAr1xVrR1Ic, rOSWBtapz-Q).
  - A §2.3 (incl. C7 strict vs loose): **CONFIRMED** for 2022.
  - B lines 73, 106, 116, 161, 232, 266: **CONFIRMED.**
  - Neither extraction states the 2024+ exclusion rule explicitly in its model section. B line 223 has it: "ADR outside the previous RDR excludes contraction" (RX57XC74DIo) — **CONFIRMED.**

### 1.5 Retirement setup — depth and stop

**Name.** The author's term is **"retirement setup"**. It appears 260 times in 64 transcripts; "retracement setup" appears 0 times. He says "that's why I call it the retirement setup" (VdY8tYYd9m0) and self-corrects "the retracement — the retirement setup" (gejIU96PFKY). He later nicknamed it SHL/GDL (W20 snippet of his tweet). Third-party playbooks use the same name (W13).
- **A MISQUOTED** the name: §4.2 calls it the "retracement setup ('retirement setup' in captions)" and treats the caption as a transcription error. The captions are right.

**Depth.**
- "confirmation to one side and then returning to the other side of the DR, preferable below the 75% retracement of IDR low to high" (x9qwawK5v5o = FOlhMAotAEc);
- "as soon price returns in the area of the opposite IDR levels" (gejIU96PFKY);
- 2025-26: "retirement setup area going from minus 0.7 to minus 1.0" (fDWbg2f3lRM); "starting from the minus 0.7 retracement" (sAr1xVrR1Ic);
- DRive trigger example "75% retracement of the IDR" (C1wPLsRy7us).
- A §4.2 and B line 63: **CONFIRMED.** B line 268: **CONFIRMED.**
- The "75% of IDR (2023)" ≈ "−0.7…−1.0 (2025)" equivalence is my inference, consistent with both sign conventions.
- B line 26 "entry anywhere between DR high and IDR low area": **AMBIGUOUS** — the speaker points at the chart ("anywhere between here and here").

**Stop.**
- Beginner/safe: 2 ticks beyond the opposite DR ("stop loss two ticks below the DR low", gejIU96PFKY; W10; W13 "few points under/above DR").
- Personal: tighter, beyond the IDR or a VIB (x9qwawK5v5o, VSjW7C-zkJw).
- A §4.2 and B line 63: **CONFIRMED.**

**Statistics.** "1,179 sessions with retirement setups… 965 working out… 957 times… 182 times the DR got stopped out… ADR, ODR and DR together" (x9qwawK5v5o). A row 24 and §4.2: **CONFIRMED.** Caveats neither extraction states:
1. 957 + 182 = 1,139 and 965 + 182 = 1,147 ≠ 1,179, so 32-40 cases are unaccounted for.
2. "The DR got stopped out" means the tally measures whether the opposite DR held, not whether a target was hit. The DRive test of the same trigger gave 43.33% and 35% (below).

### 1.6 The requested numbers

| Number | Verdict | Exact source and conditions |
|---|---|---|
| 88% | CONFIRMED | Uxwr4CVhGhg (Nov 2022): ES/DJ/NQ RDR, numbers "based on the fact that the model is not used on days with high-impact news"; title "88 % probability" (W15). HdY_wCZzZy0 "the DR rule overall has 88%"; cCKyP7QUm9o "88 days… 12 days". 12-year ES data (VSjW7C-zkJw, _4otRSUDFTg). 2022 wording is a wick claim ("low of the DR is the LOW OF THE DAY"; stop "will not be reached"). |
| 85% | CONFIRMED | VdY8tYYd9m0 "probability below 15… only 15 trades get stopped out"; VSjW7C-zkJw/IQUFS0SnV2s "a trade I'm taking with 85% probability"; _4otRSUDFTg "84.5 .85 probability to not get stopped out" (captions then say "48 days", a slip for 84); W2: author says FX ~85%. |
| 80% | CONFIRMED | W1 description (80%, FX/BTC/ETH/indices); W10 follow-up ("20 times out of 100"); 1B69Y1GZ1t4 (Dane Trades >80%, news not excluded); 2025-26 "roughly an 80% probability that price does not close on the opposite side" (wO7rYmSE9vQ, bB0Gmo16YR4, 8RKujaIq4Hw…). |
| ~70% box colour | CONFIRMED, but it changed | 2022-23: "it's not 80% but… 60 65%" (ZhOruqHWrVE = IT4eQNiqHfU). 2025-26: "roughly 70% probability of a long confirmation" (RX57XC74DIo, wO7rYmSE9vQ, 7UhJjuafb6E…). A (row 38, 60-65%) and B (lines 76, 97, 222) each quote their period correctly. |
| 94.5% | CONFIRMED | BS76JMEwHSw (Top-7, 2024): GBPUSD **Wednesday ODR**, short confirmation 04:00-04:30: "only four out of all 73 retracements went above the DR… approximately 5.5%" → a stop above the DR held 94.5%. B line 124 CONFIRMED; A §5.4 ("not in the live streams") CONFIRMED. |
| 1,179 / 965 / 182 | CONFIRMED (arithmetic flaw) | see 1.5. |
| DRive 43% / 35% | A CONFIRMED; **B MISQUOTED** | C1wPLsRy7us: trigger 75% of IDR, "if we would work with the standard deviation null [= 0], we would have over the last 219 sessions… 26 winners, 34 losers, seven neutral… win rate of 43.33"; RDR only, target = DR: "five winners, nine losers, four neutral… 35%". The QAC__ieFwRk re-cut captions say "290 sessions". B line 42 says "43% WR for 75% IDR retr -> 0.5 STD" — the target was SD 0 (IDR edge), not 0.5 SD. Win rate = W/(W+L), neutrals excluded. |
| 86.46R / 67 trades | CONFIRMED | Igp-obEjrN4: CL Wednesday ODR long, confirmation 04:00-04:30, Jan 2020-Q1 2025, "67 trades… Total profit 86.46R with a win rate of just 34.33%", 13 consecutive losses Feb-Aug 2022, most gains from 04:15 entries. Yearly: 2020 11 trades; 2021 10; 2022 24 (+22.48R); 2023 6; 2024 13; 2025 two days (3 trades) — sums to 67. Author's own backtest in his journal software (M7 Metrics); not independently reproducible. B line 189 CONFIRMED. |

### 1.7 Things stated that the author never said (or said differently)
- A: "retracement setup" as the author's name (§4.2 and throughout) — **MISQUOTED**.
- A §3.1: "At 15:30, with price retraced into the IDR after a confirmation, 62% chance…". The author does say this (C1wPLsRy7us), so **CONFIRMED as a quote**. But the metric as defined (highest close of the last three candles beyond the DR, over all confirmed sessions) is not conditional on a retracement, so the conditional reading is **not supported by the metric's definition**. Same for B line 34 "counted when price had retraced" — **MISQUOTED** (no such condition in the definition).
- B line 42: 43% attributed to a 0.5 SD target — **MISQUOTED** (SD 0).
- B line 72: "Friday close / Monday continuation" — **UNSUPPORTED**.
- B line 58: "'weak confirmation' is a rule-set option" — **AMBIGUOUS**. In pxL9XxVE-Ig the caption "weak confirmation" is the author's **wick confirmation** (the first wick through the DR, used to pick data windows; W8 m7dr.com also speaks of "a confirmation by a wick or a body close"). In JL_KDGxsGiQ (B line 232) "weak confirmation" really means weak (can't close beyond the previous session mid). B conflates the two.
- A §11.1 and §1.7 give the DRlens sign convention as if timeless — **scoped** (see 1.1).
- Nothing else in either extraction was found to be invented. Both are accurate paraphrases. A is notably careful with numbers; B compresses more and occasionally over-interprets.

---

## 2. Extraction A — verdicts by section

| § | Claim (short) | Verdict | Note / correction |
|---|---|---|---|
| 0.1 | Stream legend and dates | CONFIRMED (spot) | Dates are A's inferences; S03 date 15 Jan 2023 stated in-stream. |
| 0.3 | Backtests overstate (45-49R vs ~15R) | CONFIRMED | x9qwawK5v5o. |
| 0.3 | DRlens ES data "from 2005", 20y; part-3 used 12y ES | CONFIRMED | pxL9XxVE-Ig; VSjW7C-zkJw; _4otRSUDFTg. |
| 0.3 | "M7 Metrics" absent from streams | CONFIRMED | 0 hits in the 10 streams. |
| 1.1 | Session formation and trading windows | CONFIRMED | + web W1/W3. |
| 1.1 | ADR 01:00 trick (+7 pts GBP, +4 ES) | CONFIRMED (garbled captions) | C1wPLsRy7us "you just gain 7% success ratio". This changes the definition (less time to fail), not the edge. |
| 1.1 | DST never mentioned; NY clock for all instruments (INFERRED) | CONFIRMED (+ web settles it) | W1 Pine NY timezone, DST fix; W2 author reply. |
| 1.1 | BTC futures only RTH (ADR/ODR "liquidity desert") | CONFIRMED (S06) | Later (2025) the author trades crypto 24/7 incl. Saturday (YT2Iv-b4FSg) — evolution. |
| 1.2 | Close above DR = confirmation, above IDR = early indication | CONFIRMED | + W1 rules 1-3. |
| 1.2 | 5-min working timeframe; 1-min only to refine | CONFIRMED | + W1. |
| 1.2 | Continuous contract; switch the day before the roll; IDR bug on single contracts | CONFIRMED | _4otRSUDFTg; W1 release note 15 Jan 2023 (backtesting older contracts workaround). |
| 1.2 | Decide on ES/SPX, never CFD feeds | CONFIRMED | pxL9XxVE-Ig "manually manipulated data feed". |
| 1.3 | Confirmation = body close; bullish-candle close | CONFIRMED | VSjW7C-zkJw; W3 "not just wicks". |
| 1.3 | Box colour option, 60-65% | CONFIRMED | ZhOruqHWrVE; the number later becomes ~70%. |
| 1.3 | First wick vs confirmation slots | CONFIRMED | pxL9XxVE-Ig (captions "first week"). |
| 1.3 | DRlens direction = first confirmation | CONFIRMED | pxL9XxVE-Ig. |
| 1.3 | Early confirmation 10:30-11:00 = strength | CONFIRMED | ZhOruqHWrVE, _4otRSUDFTg. |
| 1.4 | 88/12 per 100 days | CONFIRMED | cCKyP7QUm9o. |
| 1.4 | Rule = no close beyond opposite DR for the rest of the session (Mage) | CONFIRMED | C1wPLsRy7us. |
| 1.4 | 93.9% confirmed days | CONFIRMED | C1wPLsRy7us (E-mini Dow view). |
| 1.4 | No confirmation → 90% of the time inside the DR/IDR | CONFIRMED | ZhOruqHWrVE. |
| 1.5 | Opening price important; midline usage | CONFIRMED | Which "mid" is meant stays AMBIGUOUS (Pine draws the IDR mid by default). |
| 1.6 | SD in IDR units from the IDR edge | CONFIRMED | + W1 Pine (0.5 × IDR step), W11. |
| 1.6 | RDR SDs carried until 08:30 next day; ODR SDs not carried | CONFIRMED | ZhOruqHWrVE "only… RDR to RDR"; DLRENiRX-MA "draw it out till 8:30 the next morning"; W1 Pine implements exactly this. |
| 1.6 | ~90% precision to the tick | CONFIRMED | _4otRSUDFTg (anecdotal). |
| 1.6 | 0.5 SD low-hanging target / retracement level | CONFIRMED | + W11, W13. |
| 1.7 | DRlens formula and sign | CONFIRMED, **scoped** | Valid for DRlens 2023 only; QuantX 2024-26 uses the opposite sign (§1.1). |
| 1.7 | Metric variants (max retr., before HoS, after 0.5) | CONFIRMED | C1wPLsRy7us. |
| 1.8 | Previous DR levels; horizon = previous day's RDR (INFERRED) | CONFIRMED for 2022 | 2026 practice extends ≥3 weeks back (wO7rYmSE9vQ) — evolution. |
| 1.9 | Gap/GIB/VIB definitions; 3 body fills; 80-85% filled within session | CONFIRMED | x9qwawK5v5o, cCKyP7QUm9o, _4otRSUDFTg. |
| 1.10 | Rejection = inability to close through | CONFIRMED | DLRENiRX-MA. |
| 2.1 | Upside/downside expansion rules (50% of previous session) | CONFIRMED | VSjW7C-zkJw, DFiZQEg7oxI, ZhOruqHWrVE; superseded by 2026 low/high-respect wording. |
| 2.2 | Range expansion vs trumpet terminology clash; 80% both ways | CONFIRMED | cCKyP7QUm9o. |
| 2.3 | Contraction strict vs loose; "once or twice every two months" | CONFIRMED | DFiZQEg7oxI, cCKyP7QUm9o; 2024+ canonical definition differs (ADR inside previous RDR). |
| 2.4 | Reversal model; 99% correction; Friday trend | CONFIRMED | cCKyP7QUm9o, HdY_wCZzZy0. |
| 3.1 | Windows; 1-hour-before-end rule; "too late" table | CONFIRMED | ZhOruqHWrVE, gejIU96PFKY (= S08 content). |
| 3.1 | 62% at 15:30 | CONFIRMED as quote; **interpretation unsupported** | see §1.7. |
| 3.2 | Max-extension median time as time stop | CONFIRMED | HdY_wCZzZy0, pxL9XxVE-Ig. |
| 3.3 | 30-min slots; news rules; FOMC two phases; kill zones irrelevant | CONFIRMED | VSjW7C-zkJw, x9qwawK5v5o, _4otRSUDFTg. |
| 4.1 | Process; trade only with confirmation; entry at candle close | CONFIRMED | |
| 4.1 | Market orders vs limit order (C4) | CONFIRMED | ZhOruqHWrVE vs pxL9XxVE-Ig. |
| 4.2 | Setup name "retracement setup" | **MISQUOTED** | The author's name is "retirement setup" (§1.5). |
| 4.2 | Definitions, depth, stops, targets, 1,179 stats, rarity (C2) | CONFIRMED | Stats arithmetic does not add up; success = DR held (§1.5). |
| 4.3-4.9 | Level entries, DRlens entries, counter-trades, pre-confirmation, false-day entry, engulf, avoid-list | CONFIRMED (spot) | pxL9XxVE-Ig 3.5R/4.6R; cCKyP7QUm9o 2.44/4.5/13R etc. |
| 5.1-5.3 | Stop philosophy; placements; tight vs wide | CONFIRMED | 2T4qSRRBimY = S05 content; _4otRSUDFTg 10R/2.84R/1.5R. |
| 5.4 | 84.5-85%, <20%, <15%, <12%, 84/16; 94.5% not in streams | CONFIRMED | |
| 5.5-5.6 | +1R → BE / reduce to 0.5R; re-entry; 2 losses max | CONFIRMED | ZhOruqHWrVE ("reduced now to 0.5 risk approximately"). |
| 6.1-6.6 | Target hierarchy; partials; min RR 2; 7R/week; session-end handling | CONFIRMED | VdY8tYYd9m0/-lgsKeWGXOM say **6R**/week → 1M in 81 weeks; VSjW7C-zkJw/DLRENiRX-MA say **7R**/week → 1.28M. Both said. At 1% risk, 6R/week × 81 weeks ≈ ×126 (≈1.26M) and 7R ≈ ×280, so the "7R → 1.28M" pairing is arithmetically off. |
| 7.1-7.6 | VI practice; TICK (1-min, RTH, ±600-800); no SMT intraday; algo cues; ICT optional | CONFIRMED | W14 code ±600/±800 defaults. |
| 8.1 | DRlens features and numbers | CONFIRMED | |
| 8.2 | DRive backtester numbers (219 sessions, 43.33%, 35%) | CONFIRMED | Instrument "ES 5-min" not explicit in the passage I read (AMBIGUOUS, minor). |
| 8.3 | Public script v1.3 196 lines | CONFIRMED as spoken | The currently published script is V1.5, 367 lines (W1). |
| 8.4 | Other scripts; M7 Metrics absent | CONFIRMED | |
| 9.1-9.4 | Sizing, 1%/0.3%/0.1-0.5%, <0.01% ruin, -2R/session, -3R/day, win rates, routine | CONFIRMED | DLRENiRX-MA, VSjW7C-zkJw, x9qwawK5v5o, ZhOruqHWrVE. |
| 10 | Per-instrument notes | CONFIRMED | C1wPLsRy7us, DFiZQEg7oxI. |
| 11 | 16 "misunderstood" items | CONFIRMED except item 1 (scoped: DRlens-only sign) | |
| 12 | Contradictions C1-C13 | CONFIRMED | Add: C14 = sign convention flipped in 2024 (not only "announced"). |
| 13 | Open questions | Partly answered by the web | Q1 IDR: Pine uses bodies (conflicts with 2024-26 wording). Q3: the official "early indication" = IDR close (W1 rule 3). Q18 DST: NY timezone in the Pine. Q20: sign flipped by 2024. Q23: 94.5% in BS76JMEwHSw; M7 Metrics = the academy journal (W8). Q2, Q5, Q6 (partly), Q9-Q17, Q19, Q21-Q22 remain open. |

### 2.1 A's number table (§14) — row verdicts

All rows are CONFIRMED against the cited stream unless noted. "Garbled" = captions need repair; the reading is plausible.

| Rows | Verdict |
|---|---|
| 1-2 (88%, 88/12) | CONFIRMED (HdY_wCZzZy0, cCKyP7QUm9o) |
| 3 (84/16) | CONFIRMED; captions read "48 or 84 percent" |
| 4 (<12%), 5 (<15%), 6 (~70%), 7 (<20%) | CONFIRMED |
| 8 (84.5-85%) | CONFIRMED; captions "48 days" = 84 |
| 9-13, 15 (DRlens dashboard) | CONFIRMED (E-mini Dow, ADR, Mondays view); row 12 wording: the source says price comes back "into the DR range" |
| 14 (62% S02) | CONFIRMED |
| 16 (21:20) | CONFIRMED ("920 for the ADR session") |
| 17-23 (DRlens examples) | CONFIRMED where checked (0.4 median, bulk 0.2..−0.1, 05:35/05:45, 0.8); remaining sub-values not individually re-checked but all tokens occur in the cited stream |
| 24 (1,179/957-965/182) | CONFIRMED; arithmetic does not close (see §1.5) |
| 25-26 (DRive) | CONFIRMED (219 sessions in S03; the 290 in QAC__ieFwRk is a caption variant) |
| 27-29 | CONFIRMED |
| 30 (+7/+4) | CONFIRMED, garbled |
| 31 (FX 30-min stats) | CONFIRMED (DFiZQEg7oxI); "with news removed the same 88%" CONFIRMED |
| 32-37 | CONFIRMED |
| 38 (60-65%) | CONFIRMED; superseded by ~70% in 2025-26 |
| 39-47 | CONFIRMED |
| 48 (-2R/session, -3R/day) | CONFIRMED (+ W10 follow-up thread: 2R/session) |
| 49 (~10% max drawdown) | CONFIRMED as a guess (cCKyP7QUm9o: "I would guess around 10%") |
| 50 (7R/81 weeks/1.28M; 60R/quarter) | CONFIRMED; 6R/week variant also said (VdY8tYYd9m0) |
| 51-59 | CONFIRMED (row 58: "10 ticks spread means 2.5 points") |
| 60 (TICK ±600-800) | CONFIRMED (+ W14 code) |
| 61-69 | CONFIRMED |

---

## 3. Extraction B — verdicts by section (line numbers refer to `notes_videos.md`)

| Lines | Claim (short) | Verdict | Note / correction |
|---|---|---|---|
| 4 | P1 rules: RDR 12 bars, wicks; 88% HOD/LOD; IDR bodies; EI; closes not wicks; news excluded | CONFIRMED | Uxwr4CVhGhg; W1, W3. |
| 5 | P2 tips 1-7 (60/40 bias, Fib 0.5 steps, IDR reactions, stop 2 ticks below DR low, 0.5 SD, 88% retrace only to SSL/FVG, rule continues overnight, ODR sets algo until 08:30) | CONFIRMED | 1B69Y1GZ1t4; W11 (third-party summary of the same tips). |
| 6 | P3: ADR times; 8:25 last bar; M5 only; 12y stats; three models | CONFIRMED | q1s2INPzN6M. |
| 9-18 | ES/SPX daily streams (=S06) | CONFIRMED (spot) | |
| 21-24 | Discord: <15% close above DR high; mid-IDR entries + 0.5-0.618 fib; stop options; RR ≥3-5R; 6R/week | CONFIRMED | Captions say "between 0.5 and 0.61". |
| 25 | Tuesday RDR mean 0.6 SD (17 y) | CONFIRMED | VdY8tYYd9m0 (direction "short" not stated in the passage). |
| 26 | Retirement: entry "anywhere between DR high and IDR low"; stop below DR low; 85%+ | CONFIRMED except entry zone **AMBIGUOUS** | Deictic "between here and here". |
| 27-28 | Levels stay relevant for days; algo "radar" | CONFIRMED (spot) | |
| 29 | Crypto 72-86% incl. news; ~75-80% excl. | **AMBIGUOUS** | Captions: "72 and 86 percent so that's not including Newsday… if you take out the really important news it will be still around 75 to 80 percent… even a little bit higher" — which figure is news-filtered is unclear. |
| 30 | Daily/weekly DR not shared (NDA) | not re-checked | W9 confirms "M7 Weekly DR" is an academy tool. |
| 33-38 | DRlens intro | CONFIRMED | Line 34 "counted when price had retraced" **MISQUOTED** (§1.7). Line 35 sign CONFIRMED for DRlens. |
| 39 | DRive imports DRlens data | CONFIRMED | |
| 42 | DRive: 290 sessions, 43% for 75% IDR retr → 0.5 STD; RDR → DR 35% | **MISQUOTED** | Target for 43.33% was SD 0 ("standard deviation null"); 219 sessions in the full live version. 35% (RDR, target DR) CONFIRMED. |
| 43-44 | EURUSD/Gold session quality; ADR 01:00 tip | CONFIRMED | |
| 47-57 | 2023 time-trade workflow; mode target; cumulative reading; stops; GIB/VIB; opening price; never exit manually; seasonality; student results | CONFIRMED | 6ijtg_2TACk (BE once >2R, ≥3R), Y3tZGeA4nE4 (mode 1.1-1.2, never exit manually), lgKYeW5WpXI (56 trades, 39%, avg win 5.2R). |
| 58 | DR Frame 1/2/3; "weak confirmation" option | Frame: CONFIRMED (eO78N2DsPwM; W8: 27-step DR Frame); "weak confirmation": **AMBIGUOUS** (probably "wick confirmation") | |
| 59-60 | Weekly DR box; Mondays ~80% | CONFIRMED (spot) | |
| 63 | Retirement setup canonical (75% of IDR; blind entry; stop 2 ticks beyond opposite DR; target; partial 50%; <15% → 85%) | CONFIRMED | x9qwawK5v5o/FOlhMAotAEc, gejIU96PFKY, VSjW7C-zkJw. |
| 64 | Retirement timing (RDR 12-13 "too late"; last-hour exception; ODR 08:10-08:15; ADR 00:20-01:20) | CONFIRMED | Mostly the same recordings as A's S04/S05/S08. |
| 65-66 | Trade windows; risk rules; min RR 2 → 3 | CONFIRMED | |
| 67-69 | Rejection counting; close-above = candle close; stop philosophy | CONFIRMED | |
| 70 | Upside model (next session not below previous mid, above previous highs; enter pre-confirmation at 50%, stop 2 pts below IDR) | CONFIRMED (spot) | 2022-23 wording. |
| 71-75 | ODR inside ADR → range day; range expansion = trumpet; contraction; reversal; small ADR up / price down = choppy | CONFIRMED; line 72 "Friday close / Monday continuation" **UNSUPPORTED** | Terminology superseded in 2025-26. |
| 76 | Box colour 60-65% | CONFIRMED | |
| 77-83 | VIB behaviour; gap close; Friday trend; FOMC; ES for beginners; backtest > live; big-DR counter-trend | CONFIRMED | |
| 86 | VIB/GIB terms; five VIB types taught in academy | CONFIRMED | QI6U4RjJbRQ "five different types of volume imbalances". |
| 87-88 | VIB definition; GIB daily/weekly/intraday | CONFIRMED | |
| 89-95 | Algo push last 20-30 s; ES vs NQ/YM; midpoint stop 3 ticks; >70% win rate; gears; rejection counts; ODR/RDR alignment | CONFIRMED (spot) | |
| 96-109 | DR BASICS 2024 (green box + long = higher prob.; min 3R; two bullets; stops; targets; seven levels; range expansion; contraction; cross-session management; transition window) | CONFIRMED (spot: 3R minimum in KDob92SRItY; two bullets in wzZi22NDxXU, r33KSmfz5Hc, MA9evuOGL7c) | |
| 110-112 | TICK; futures continuous contracts; gold 73/82/95% over 1,981 sessions; RTY Tue −0.2/70%; EURAUD 3.3 SD | CONFIRMED | KDob92SRItY ("1,900 81 Dr sessions"); 9fgp8Lvvsm8. |
| 113 | Sign convention ambiguity | Resolved | §1.1. |
| 116-130 | Top-7 2024: contraction canonical; upside/downside models; ODR both sides excludes both models; gray box; first-bullet stop covers retirement area; 94.5%; QuantX; T&P procedure; ES Tue RDR 12:15, 1.4-1.5 SD 66%; convention | CONFIRMED | BS76JMEwHSw, MA9evuOGL7c, hhOoJy17Flk, xe3dy8hERgU. Line 127 "70% reach −0.3": the source says "around 70% of retracements reach the minus 0.3 retracement area" — **AMBIGUOUS** wording (conflicts with the later percentile semantics). |
| 133-147 | Late 2024 patterns; USDJPY/CL numbers; 3 ticks beyond IDR with a big DR-IDR gap; scaling; open VIB uses | CONFIRMED (spot) | s_VI7Rq7mi4 "three ticks above the IDR high". |
| 150-168 | Early 2025: 7 steps; ~80/20; −0.7 first-bullet stop; exclusions; low-quality list; contraction 2025; entry types; forex step 0; T&P gold/6E | CONFIRMED | The −0.7 "standard recommendation" is in KKzy5uJyMmw (listed in the section header). |
| 171-186 | Canonical T&P algorithm + four keys (CL Tue ODR S, NQ Fri RDR S 346/85%, 6E Thu RDR L 200/78%, CL Wed ODR L 261/71%) | CONFIRMED | HH2VLbhKNOQ, jPvvCww8aP8, laH3FuECnVg, dfp2aAKt-Ss (all numbers found; "no entries should be taken after", "first mode from the left", "one tick above… three ticks below" verbatim). |
| 189 | CL Wed ODR long backtest | CONFIRMED | §1.6. |
| 190 | IDR wording 2025 = closes; open question | CONFIRMED; the question is now answered by the web (Pine = bodies) | |
| 191-196 | Positive vs negative retracement (2025); CL weekday stats; downside barriers; USDJPY; NQ Wed | CONFIRMED | nMXrQxyJ46Q (+ W15 thumbnail). |
| 199-210 | Mid 2025 model rules and keys | CONFIRMED (numbers found) | |
| 213-219 | ODR/RDR recommendation; low-true keys one bullet; BTC/NQ keys; two windows | CONFIRMED | X8P4pPZJmGs "don't want to place a second bullet". |
| 222-229 | Box colour 70%; exclusions; closing price sensitive; old DR levels; NQ Fri RDR long 190 cases | CONFIRMED | RX57XC74DIo. |
| 232-240 | Contraction details; weak confirmation; NFP → trade CL; intermarket metals; gold RDR false 12.5%; pre-box projection by closes; upside hierarchy | CONFIRMED | w-H2JpiTsDE, JL_KDGxsGiQ, CzVFHQEyIjk. |
| 243-255 | Closes-based range expansion; opening position rules; mega confluence; USDJPY | CONFIRMED | 5l-4QzuLEE4 ("Since the ODR opened below the aftermarket, we can already exclude a DR upside model"). |
| 258-263 | 6E Fri ODR; false sessions max two bullets; old DR levels | CONFIRMED (numbers found) | |
| 266-276 | Dec 2025-Jan 2026 contraction wording; IDR = highest close; retirement from −0.7; previous DR zones; red-box closing price; 20% | CONFIRMED | sAr1xVrR1Ic ("avoid trading… or reduce your risk to maybe one bullet"). |
| 279-289 | Transition windows; working range; model logic; contraction example | CONFIRMED | AmAwkBpcv5E. |
| 292-299 | EP06-07; confirmation to avoid | CONFIRMED | PXTJrcRPFT8. |
| 302-315 | Old levels; pre-box setup; candle-by-candle; 6E Mon; 10 AM window; trumpet done; max retracement def.; CL Fri 213/95/61 | CONFIRMED | 3RW8xnl2ttE ("about 10 minutes of deviation either side"); qxh2fHQLHlM. |
| 318-340 | Canonical 2026 framework and checklist | CONFIRMED | wO7rYmSE9vQ (read in full around steps 3-5). |
| 343-350 | ETH Tue RDR short; three zones two bullets; ADR mid barrier; close at 16:00 | CONFIRMED | 9ASmoYOuCCg; 7UhJjuafb6E/3RW8xnl2ttE "close… at 4:00 p.m.". |
| 353-356 | Gold exclusions; pre-09:30 CL short; contraction trap | CONFIRMED (spot) | |
| 359-370 | Two trades max; ADR mid; broken GIB; early sign (wick above DR high + close above IDR high); 3-step routine; M7 retracement; CL/NQ keys | CONFIRMED | 2EoZdoMcdI0 (early sign; "two trades maximum, no exceptions"), rOSWBtapz-Q, My_yJfguN9I. |

---

## 4. Most important corrections (ranked)

1. **Retracement sign depends on the era.** DRlens (Jan 2023): positive = into the IDR. QuantX (2024-26): negative = into the IDR. Tag every number with its era; A's §1.7/§11.1 statement is valid for DRlens only.
2. **IDR definition conflict.** The author's published Pine V1.5 (W1) uses bodies (max/min of open and close). The 2024-26 videos say closes only. B's open question is answered for the code, not for QuantX. Implement both and log the difference.
3. **The setup is called "retirement setup"** (author's own term, 260 mentions, own tweet "SHL/GDL"). A's renaming to "retracement setup" is a misquote.
4. **DRive 43.33% was for a 0 SD target** (IDR edge), 219 sessions, neutrals excluded — not 0.5 SD (B line 42).
5. **"Success" means two different things.** "85-88%" and "1,179/957/182" measure whether the opposite DR held (stop survival, close-based). DRive 35-43%, the CL backtest 34% win rate and the student's 39% measure target-before-stop. Neither extraction draws this line; an agent must not use 85% as a win rate.
6. **The headline 88% was news-filtered, RDR, 12-year ES, and worded as a wick claim** ("DR low is the low of the day", "stop… will not be reached"). The only independent test (TFO, W4, wick criterion, 237 ES sessions, news included) shows 71.73%. 2025-26 videos use "roughly 80%".
7. **The "Outside DR 62%" metric is unconditional.** A's and B's conditional readings ("when price has retraced to mid-IDR at 15:30") repeat the author's own misreading and are not supported by the metric's definition.
8. **Model definitions changed** (range expansion, trumpet, contraction). Use the 2025-26 versions for an agent; treat 2022-23 statements as history. B line 72 mixes eras; A covers only 2022.
9. **Box colour: 60-65% (2022-23) → ~70% (2025-26).** Pine paints open == close as red; 2024 calls it gray/neutral.
10. **Arithmetic flags:** 1,179 ≠ 957/965 + 182; "7R/week → 1.28M in 81 weeks" does not compute at 1% risk (6R/week ≈ 1.26M does).
11. **Minor:** "weak confirmation" in some captions is "wick confirmation" (B line 58); B line 72 "Friday close / Monday continuation" unsupported; B line 29 crypto numbers garbled; B line 127 "70% reach −0.3" is ambiguous wording.
12. **Independence:** many of B's 2023 sources are re-cuts of A's streams (§0). Agreement on 2022-23 material is one source, not two.

## 5. Open questions no source resolves

1. The exact IDR formula in QuantX (bodies or closes) and in DRIVE 2.1.
2. Whether "ADR mid / ODR mid / previous session mid / 50%" means the IDR mid or the DR mid.
3. Exact DR-true computation in QuantX: close-based beyond the opposite DR edge until 16:00/08:30/02:00? Are unconfirmed sessions and news days excluded? First confirmation only?
4. Precise success definition behind 1,179/957-965/182 (stop, target, trigger depth) and the 32-40 unaccounted cases.
5. Whether 2025-26 SD targets use each session's own IDR in all cases (the free Pine only draws RDR SDs); and how the "pre-box projection" uses closes.
6. Short-side definition of "Outside DR" (presumably the lowest close of the last three candles) and which session's base rate (62%, 65.5%, ~70%) applies.
7. Precise last-entry times per session (the 1-hour rule vs data cut-offs vs the retirement exception) and whether positions are always flat at session end.
8. Thresholds for "inside", "respect", "violate" in models (close vs wick). 2025 says a 5-min close breaks a model and a wick is only a hint; earlier statements are looser.
9. The meaning of the 2024 statement "70% of retracements reach −0.3" versus the 2025 percentile definition.
10. "M7 retracement", weekly DR, DIB/DDR, the five VIB types, "special volume imbalance" and weekly sequencing are undisclosed academy content.
11. Independent replication of any QuantX key (all per-key statistics are author screenshots from videos). The public web contains one small independent test (TFO) and anecdotes.
