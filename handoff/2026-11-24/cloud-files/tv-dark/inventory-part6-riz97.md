# Part 6/8 RIZ v9.7 MTF (own, 1020 lines, behind_chart=true)
Inputs: bull/bear/t3/2X each colour + separate transparency int; mtf_col #D000FF; mtf_wb 5 px (M) ladder down to 1 px (1m); lbl_max 24 pt (M) ladder to 11 pt (1m); box_col (default black, now #363A45); box font large.
Entities (current effective):
1. RIZ zone box: kind0 bullish tier1/2 white fill α.35 + white border; kind1 bearish same white (direction not visible by colour!); kind2 tier3 breaker / live break preview #787B86 α.30 + opaque border; kind3/4 2X+ (native / MTF) #2962FF α.06 + opaque border. State machine: latent (not drawn) → first body span = active (white) → wick touch kills a side → second span ≥2 bars = BLUE (both sides alive) → body close through live edge = GREY breaker → breaker gone when price returns past broken edge → both edges swept = deleted. Live preview on unclosed candle.
2. MTF magnet line: one horizontal line per magnet side of visible HTF zones, merged within 2 ticks; #D000FF; width 1–5 px by TF rank; SOLID = HTF candle closed, DASHED = provisional; extend right; removed when zone dies.
3. Magnet label: TF list text («1H/4H», «D», «7H») #D000FF 11–24 pt.
4. Nested digits in box («5/15/30») box_col #363A45 large.
5. L1014 MTF 2X label: TF name, HARD-CODED color.black, large.
Recolour = removal + re-creation on last bar.
