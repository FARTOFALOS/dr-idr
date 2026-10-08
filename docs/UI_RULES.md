# UI rules — the operator's requirements (binding)

These rules came from the operator over many iterations on 2026-09-24. They are requirements, not suggestions. When a
rule and a new idea conflict, keep the rule and ask the operator. Each rule says why, so you can apply it to cases it
does not name.

For screen 24, **DR-LAB-SWPC-1.1** (`spec/DR-LAB-SWPC-1.1.md`) is the operator-authorized contract of how the
accepted semantics are presented, implemented on 2026-10-07 (`meaning/13` № 49–51, passports `spec/ekran-24/12-swpc.md`).
It does not cancel these rules or `meaning/13-zhurnal-vizualizacii.md`; it traces them into PresentationBindings and
adds only its declared `NEW_SWPC` obligations. Human perceptual claims remain unverified until the operator runs
H01–H12 (`meaning/16-priyomka-swpc.md`).

On 2026-09-28 the working screen became «Созвездия» (design 21; since 2026-09-29 design 22, `design/README.md` has the remarks round by round);
the previous screen stays at `/classic.html` and these rules still describe it. For the new screen the operator's
later decisions replace some of them (live chat, 2026-09-28):

- **Replaced:** 3 (the six history charts sit in a handle at the bottom and open over the chart on hover, a click pins
  them); 8 (DR solid, IDR dashed, mid dotted, STD thin solid lines, the side in play brighter; past sessions' DR / IDR
  the same, dimmer, named at the right end — he wanted the kinds of lines told apart, not all dash-dot); 13 and 14
  (colours by role, not by rank: continuation and pullback, before a confirmation «Верх» / «Низ»; every colour,
  brightness and line style is in «⚙ Настройки»); 16 and 17 (a price band or a time window may run across the chart,
  the hovered window runs down to the time axis; details go to the tooltip and the panel instead of a card); 21
  (layers in «Слои», all on).
- **New, for the right panel:** percentages only, never session counts; no line that repeats what the chart shows at a
  glance; every line is a link — hovering it lights on the chart the level, the place, its densest spot and its time,
  a click pins it.
- **Kept:** 1, 2, 4–7, 9–12 (the confirmation and the DR-break pills), 15, 18–20 in spirit, 22, 23 (refresh after every
  M5 close while a session runs; every 5 minutes when the TradingView chart has to be switched).

Check the new screen with `tests/ui_check21.js`; `tests/ui_check.js` is for `/classic.html`.

Design 22 (2026-09-29, a proposal, `meaning/04-dizajn-22.md`) keeps all of the above and removes the hint texts that
had crept into 21 against rule 4 («наведите, чтобы раскрыть», «клик — закрепить», the long replay caption). Its new
presentation choices (no percentage without a matched price, a place's share on its band, the fan as slices) change
no binding rule; they become rules only when the operator accepts them.

Design 24 (2026-10-01 by the operator's order; **the working screen since 2026-10-01 night, the main line on `main`
since 2026-10-07**; `design/sozvezdiya-24/README.md`, every element: `spec/ekran-24/`, every visual rule with its reason:
`meaning/13-zhurnal-vizualizacii.md`, which is binding for 24 together with this file)
follows the specification DR-LAB-SEM-1.0 §15. It **replaces** for itself: the mandatory places, first touches as the
source of the stars, the row of six history windows (one details area instead) and the old reading of the bracket
percentages (a bracket only on a selected band, carrying the band's share). It **keeps** locality, the candles as the
main object, one screen, no text on text, no explanatory paragraphs, percentages and not counts in the right panel,
every panel line a link, replay, one active pick (one selected area). Design 22, kept at `/22/`, and the rules
above for it are not changed by it.
Since 2026-10-01 night (the operator's choice of the look «Окна времени») design 24 also **replaces** for itself: the R / X
switch (both on screen together), the floating tooltip (an inspector in a fixed place at the bottom right: rule 16-17's
«details go to the panel» taken literally), the one details area (six windows of the family that slide up when the mouse
reaches the bottom edge, a click pins them, as design 22's history row did), the cell outlines of the zones (constellations
drawn from the zones' own points; the exact cells on hover). Its colours: R amber `#EBA06C`, X sky `#72A9EC`.

## Layout

1. **The current session is the product.** The live session chart takes most of the screen. Focus mode (`body.focus`)
   is the default: no sidebar, no page headings, no KPI row; ☰ at the top left of the chart brings the research menu
   back. *Why: the operator trades from this chart; everything else is secondary.*
2. **One screen, no scrolling** on a desktop (≥ 1001 px wide, ≥ 600 px tall). Charts size themselves to their boxes.
3. **Secondary charts are small.** The six history charts sit in one narrow row under the session chart.
4. **No explanatory text on screen.** No "time, price, probability" titles, no "описание истории, не прогноз",
   no data badges, no hints like "нажмите на столбец". The meaning lives in `docs/SEMANTICS.md` and in the card that
   opens on click. *Why: every line of text costs chart space and attention.*

## Text

5. **Text never overlaps text.** Before shipping any visual change, evaluate `tests/ui_check.js` in the page; it must
   return no problems. New chart labels go through the right-side label layout in `drawLive` or get their own
   collision check.
6. **No duplicates.** What the side column or the card already says is not printed again on the chart.
7. **TradingView typography.** Font stack `-apple-system, BlinkMacSystemFont, "Trebuchet MS", Roboto, Ubuntu,
   sans-serif` everywhere (read from the operator's TradingView). Time axis 14 px, colour `#D1D4DC`; chart labels
   13 px; side column 13–14 px. No condensed, no monospaced fonts. Text must not be dim.

## Lines and markers on the session chart

8. **DR**: solid, light `#f8fafc`, 1.8 px. **IDR**: dashed `9 4`, light `#f1f5f9`, 1.7 px. **STD levels** (0.5 IDR
   steps from the IDR edges, as in the Pine script) and **mid**: white dash-dot `10 4 2 4`. **Open**: green. No
   dotted lines ("кругляшки").
9. **The 0.1 … 0.9 grid of the IDR** is drawn only inside the DR formation window (time) as thin light lines, labels
   left of the window, counted from the IDR edge on the confirmation side. *Why: it shows at a glance where the DR was
   formed without cluttering the rest of the day.*
10. **No background grid.** Only lines that mean something.
11. **The current-minute line is faint**: thin, low-opacity dash-dot. In replay it reads "момент HH:MM".
12. **Confirmation** is a small pill at the close of the confirming M5 candle with the time inside (green up, red
    down). **DR break** is a dark-red pill at the close of the breaking candle. No arrows with long captions.

## Colour

13. **Probability colours**: green = most likely, yellow = middle, red = least likely. Zones in the side column are
    coloured by rank (equal displayed percentages share a colour); cluster cells by their density.
14. **Guide labels** (boundary time and prices of a hovered cluster) are green `#4ade80` on dark pills so they never
    merge with the white level labels.

## Interaction

15. **One active pick at a time** across the bottom charts (bars, heatmap cells) and the side zones. A new click
    replaces the previous pick; clicking the active one clears it. Other bars never become unclickable.
16. **Every pick is shown on the session chart as time × price cells** (0.1 IDR × 15 min, or the zone's 0.2 IDR ×
    30 min rectangle). Never a band across the whole height or width.
17. **Clusters on the chart are clickable.** A click pins a card left of the cluster: what it is, %, time, prices,
    IDR range, how many similar sessions. While a card is pinned, cluster hover shows guides only (no tooltip on top of
    the card). × , a click on the same cluster or on empty chart closes it.
18. **Guides**: hovering or pinning a cluster draws thin guides down to the time axis and right to the price scale,
    with the boundary times and prices; labels they would cover step aside while shown.
19. **Replay by candle**: a click on a candle shows the screen as it was at that candle's close (all candles stay
    visible); a click on another candle moves there; a click on the same candle returns to live.
20. **Side zone rows** are one line each: colour dot, time window, price range, percent; clickable (rule 15).
21. **Layers**: "Кластеры отката" on, "Кластеры экстремума" off by default, "Веер" on, "Лесенка" on (the operator
    likes the ladder).

## Behaviour

22. **Everything automatic.** Direction and confirmation come from the live candles; the operator never types them.
23. **Live refresh every minute** while the session runs (every 5 minutes only when the TradingView chart has to be
    switched); all numbers are recomputed from the whole history each time.
