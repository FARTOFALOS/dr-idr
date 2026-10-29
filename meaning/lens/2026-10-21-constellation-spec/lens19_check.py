"""Synthetic counterexamples to meanings proposed by lens 19; no market data."""
from fractions import Fraction as F
import json
from pathlib import Path


def literal_ccpb(anchor, bars, theta):
    """Branch-priority witness only, not a complete CCPB reference extractor."""
    armed, low = False, None
    for b in bars:
        if not armed:
            if b['high'] > anchor:
                anchor = b['high']
                continue
            if b['close'] <= anchor-theta:
                armed, low = True, b['low']
        else:
            low = min(low, b['low'])
            if b['close'] > anchor:
                return 'CONFIRMED_PULLBACK'
    return 'KNOWN_UNCONFIRMED_CORRECTION' if armed else 'KNOWN_NO_STRUCTURAL_PULLBACK'


def run():
    bars = [dict(high=F(11, 10), low=F(7, 10), close=F(3, 4)),
            dict(high=F(6, 5), low=F(74, 100), close=F(23, 20))]
    status = literal_ccpb(F(1), bars, F(1, 5))
    # Bar 1 high necessarily precedes its lower final close; bar 2 close is later.
    witnessed = bars[0]['high']-bars[0]['close'] >= F(1, 5) and bars[1]['close'] > bars[0]['high']
    assert status == 'KNOWN_NO_STRUCTURAL_PULLBACK' and witnessed
    # The anchor-bar low might precede or follow its high. With a later low of .74,
    # the actual post-high trough is bounded by [.70, .74], not one known point.
    lo = min(bars[0]['low'], bars[1]['low'])
    hi = min(bars[0]['close'], bars[1]['low'])
    assert (lo, hi) == (F(7, 10), F(74, 100))
    result = {
        'scope': 'synthetic mathematical examples, not market observations',
        'ccpb_new_high_branch': {
            'theta': '1/5 SD', 'initial_anchor': '1 SD',
            'bars': [{k: str(v) for k, v in b.items()} for b in bars],
            'literal_lens19_result': status,
            'high_then_threshold_lower_close_then_higher_close_is_observed': witnessed,
            'post_anchor_trough_bounds': [str(lo), str(hi)],
            'conclusion': 'The pseudocode misses this witnessed correction and close-confirmed return. No detection is not proof of no structural event; trough precision is a separate issue.'
        },
        'uniform_hdr': {
            'density': 'Uniform[0,1]', 'requested_mass': '7/10',
            'finding': 'Every measurable subset of length 7/10 has the same density and mass; the complete density level set is either all support or empty. A selection/tie rule is necessary; coverage alone does not identify a local mode.',
            'conclusion': 'HDR coverage and existence of a separated concentration are different questions.'
        },
        'outcome': 'COUNTEREXAMPLES_CONFIRMED'
    }
    target = Path(__file__).with_name('semantic-counterexamples.json')
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(result['outcome'])


if __name__ == '__main__':
    run()
