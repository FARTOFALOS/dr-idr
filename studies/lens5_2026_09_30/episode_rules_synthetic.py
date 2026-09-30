"""Lens 5 (cluster spec v0.8), synthetic only: what two candidate «reaction» rules return on a driftless random walk.

No market data is read. One unit = the standard deviation of one M5 close-to-close move. Each session is simulated by
the minute (5 steps per M5) so that bar lows exist; closes are every 5th minute. t is the close of bar 0; the horizon
is 66 M5 closes (10:30-16:00).

Rule C, «episode recovery» (first cluster audit, D3): after t the first close below the previous close opens an
episode, its start price a is that previous close; the episode ends at the first later close >= a (recognition);
the base is the lowest low between the start and the recognition bar; no recovery by the horizon = «not recovered».

Rule θ, «reversal by θ»: recognition at the first close that is >= θ above the lowest low since t (the price at t
included); the base is that lowest low. θ = 1, 2.5, 5 units.

For a driftless continuous path the depth of the θ-base below the price at t is exponential with mean θ; the
printout compares the simulated quantiles with that curve and prints the density by 0.25θ bins.
"""
import numpy as np

NS, NB, SUB = 100_000, 66, 5
rng = np.random.default_rng(20260930)


def simulate(kind):
    if kind == "gauss":
        z = rng.standard_normal((NS, NB * SUB))
    else:  # Student t, 4 degrees of freedom, scaled to unit variance
        z = rng.standard_t(4, (NS, NB * SUB)) / np.sqrt(2.0)
    minute = np.concatenate([np.zeros((NS, 1)), np.cumsum(z / np.sqrt(SUB), axis=1)], axis=1)
    close = minute[:, ::SUB]                                   # close[:, 0] = price at t, close[:, k] = bar k
    low = np.empty((NS, NB + 1))
    low[:, 0] = 0.0
    low[:, 1:] = minute[:, 1:].reshape(NS, NB, SUB).min(axis=2)
    low[:, 1:] = np.minimum(low[:, 1:], close[:, :-1])          # a bar's low includes its open
    return close, low


def q(x, ps=(0.1, 0.25, 0.5, 0.75, 0.9)):
    return "  ".join(f"p{int(p * 100)}={np.quantile(x, p):.2f}" for p in ps)


def rule_c(close, low):
    idx = np.arange(NB + 1)
    down = close[:, 1:] < close[:, :-1]
    has = down.any(axis=1)
    k = np.where(has, down.argmax(axis=1) + 1, -1)               # bar whose close opened the episode
    a = close[np.arange(NS), np.maximum(k - 1, 0)]
    rec = (close >= a[:, None]) & (idx[None, :] > k[:, None]) & has[:, None]
    ok = rec.any(axis=1)
    j = np.where(ok, rec.argmax(axis=1), -1)
    lows = np.where((idx[None, :] >= k[:, None]) & (idx[None, :] <= j[:, None]), low, np.inf)
    base = lows.min(axis=1)
    sel = ok
    print(f"  opened: {has.mean():.3f}   recovered by the horizon: {ok.mean():.3f}")
    print(f"  bars from t to the opening close: {q(k[has])}")
    print(f"  bars from opening to recognition: {q((j - k)[sel])}")
    print(f"  depth below the start price a:    {q((a - base)[sel])}")
    print(f"  depth below the price at t:       {q((0.0 - base)[sel])}")
    share_small = np.mean((a - base)[sel] < 1.0)
    share_fast = np.mean((j - k)[sel] <= 3)
    print(f"  recovered episodes shallower than one M5 sd: {share_small:.3f};  recognised within 3 bars: {share_fast:.3f}")
    print(f"  base above the price at t: {np.mean(base[sel] > 0.0):.3f}")


def rule_theta(close, low, theta):
    runlow = np.minimum.accumulate(low, axis=1)
    hit = (close - runlow) >= theta
    hit[:, 0] = False
    ok = hit.any(axis=1)
    n = np.where(ok, hit.argmax(axis=1), -1)
    base = runlow[np.arange(NS), np.maximum(n, 0)]
    depth = (0.0 - base)[ok] / theta
    at_base = (low == base[:, None]) & (np.arange(NB + 1)[None, :] <= n[:, None])
    nb = at_base.argmax(axis=1)
    delay = (n - nb)[ok]
    exp_q = "  ".join(f"p{int(p * 100)}={-np.log(1 - p):.2f}" for p in (0.1, 0.25, 0.5, 0.75, 0.9))
    print(f"  theta={theta}: recognised by the horizon {ok.mean():.3f}")
    print(f"    depth/theta below the price at t: {q(depth)}")
    print(f"    exponential, mean 1:          {exp_q}")
    print(f"    bars from base to recognition: {q(delay)}")
    edges = np.arange(0, 3.01, 0.25)
    h, _ = np.histogram(depth, bins=edges)
    dens = h / ok.sum() / 0.25
    print("    density by 0.25 theta bins from 0 to 3 theta: " + " ".join(f"{d:.2f}" for d in dens))


for kind in ("gauss", "t4"):
    close, low = simulate(kind)
    print(f"== driftless walk, steps {kind}, {NS} sessions x {NB} M5")
    print(" rule C (episode recovery):")
    rule_c(close, low)
    print(" rule theta (reversal by theta from the lowest low since t):")
    for theta in (1.0, 2.5, 5.0):
        rule_theta(close, low, theta)
