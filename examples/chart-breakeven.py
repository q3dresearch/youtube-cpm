#!/usr/bin/env python3
"""Unit economics per video: how many views pay for the video, by niche and by cost tier.

    python3 examples/chart-breakeven.py

**Why this plate exists.** The question a creator actually brings is "I get 30k views a
video. Can I pay an editor?" That needs three numbers crossed: views per video, the niche's
RPM, and what the video costs. On log-log axes, a niche's AdSense income is a straight
diagonal (views x RPM / 1,000). Each cost tier is a horizontal band, and breakeven is where
the diagonal crosses the band.

**The cost tiers** are this repo's own estimates (`edit_cost` and
`production_hours_per_min` in data/2026/benchmarks.csv). **The creator's own time** is
priced at `HOURLY`, an assumption stated on the plate. Change it and rerun: time is the
largest cost for a solo creator, and it is usually left out.

**What it cannot say.** This is AdSense only, over a video's whole life. The attention plate
shows a trending video earns about 89% of that in week one, so this is also roughly a
first-week breakeven. Sponsorships are the next plate.
"""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import load  # noqa: E402
import plate  # noqa: E402
from plate import INK, INK2, MUTED, RULE, GRID, FAINT  # noqa: E402

W = 880
HOURLY = 25            # $ per hour for the creator's own time -- an assumption, not data
MINUTES = 10           # finished length of the video
NICHES = ["finance", "tech", "education", "gaming", "entertainment"]
Q1 = 0.85              # Q1 ad revenue vs Q4, from chart-seasonality


def main():
    b = load.benchmarks()
    y1 = int(b[b.basis == "maintainer_estimate"].year.max())
    cur = b[(b.basis == "maintainer_estimate") & (b.year == y1)]
    rpm = cur[cur.metric == "rpm"].set_index("niche").mid
    tiers = cur[cur.metric == "edit_cost"].copy()
    tiers["tier"] = tiers.notes.str.extract(r"tier=([^;]+)")[0]
    hrs = cur[cur.metric == "production_hours_per_min"].iloc[0]
    own_lo, own_hi = hrs.low * MINUTES * HOURLY, hrs.high * MINUTES * HOURLY
    std = tiers[tiers.tier.str.startswith("standard")].iloc[0]
    std_mid = std.mid

    be = {n: std_mid / rpm[n] * 1000 for n in NICHES if n in rpm}
    top_n, bot_n = NICHES[0], NICHES[-1]
    title = (f"A ${std_mid:.0f} outsourced edit pays for itself at {be[top_n]/1e3:.0f}k views in "
             f"{top_n}, {be[bot_n]/1e3:.0f}k in {bot_n}.")
    s = plate.open_svg(W, 10, title,
        subtitle=f"AdSense per video (diagonals, {y1} RPM index) against what a {MINUTES}-minute "
                 f"video costs (bands). Log–log.")
    f, y = plate.frame(W, 88,
        who="A creator with a known views-per-video deciding what production they can afford",
        decide="Whether to stay DIY, pay an editor, or go premium, given their niche and views",
        wrong="A channel sits right of its niche's crossing and still loses money on ads: its "
              "RPM is below the niche's line")
    s += f

    P0, P1 = 80, W - 175
    top, bot = y + 30, y + 400
    vx0, vx1 = math.log10(1e3), math.log10(1e7)
    vy0, vy1 = math.log10(1), math.log10(1e5)
    X = lambda v: P0 + (P1 - P0) * (math.log10(v) - vx0) / (vx1 - vx0)
    Y = lambda d: bot - (bot - top) * (math.log10(max(d, 1)) - vy0) / (vy1 - vy0)
    for d_ in (1, 10, 100, 1e3, 1e4, 1e5):
        s.append(f'<line x1="{P0}" y1="{Y(d_):.1f}" x2="{P1}" y2="{Y(d_):.1f}" stroke="{GRID}"/>')
        s.append(plate.txt(P0 - 8, Y(d_) + 4, f"${d_:,.0f}", size=10, fill=MUTED, anchor="end"))
    for v, lab in ((1e3, "1k"), (1e4, "10k"), (1e5, "100k"), (1e6, "1M"), (1e7, "10M")):
        s.append(f'<line x1="{X(v):.1f}" y1="{top:.1f}" x2="{X(v):.1f}" y2="{bot:.1f}" stroke="{GRID}"/>')
        s.append(plate.txt(X(v), bot + 18, lab, size=10.5, fill=INK2, anchor="middle", weight="600"))
    s.append(plate.txt((P0 + P1) / 2, bot + 34, "views per video", size=9.5, fill=MUTED,
                       anchor="middle"))
    s.append(plate.txt(P0 - 60, top - 12, "$ per video", size=9.5, fill=MUTED))

    # cost bands
    bands = [(r.low, r.high, r.tier, "#5b6fb0", 0.07) for r in tiers.itertuples() if r.high > 60]
    bands.append((own_lo, own_hi, f"your time, ${HOURLY}/h", "#c0503e", 0.08))
    short = {"basic edit": "basic edit", "standard long-form edit + thumbnail": "standard edit + thumb",
             "premium retention edit": "premium edit"}
    labs = []
    for lo_, hi_, lab, col, op in bands:
        s.append(f'<rect x="{P0}" y="{Y(hi_):.1f}" width="{P1-P0}" height="{Y(lo_)-Y(hi_):.1f}" '
                 f'fill="{col}" fill-opacity="{op}"/>')
        labs.append([(Y(lo_) + Y(hi_)) / 2, short.get(lab, lab), f"${lo_:,.0f}–${hi_:,.0f}", col])
    labs.sort()
    for i in range(1, len(labs)):                  # two lines each, so keep 26px apart
        labs[i][0] = max(labs[i][0], labs[i - 1][0] + 26)
    for ly, lab, rng_, col in labs:
        s.append(plate.txt(P1 + 8, ly, lab, size=9.5, fill=col, weight="600"))
        s.append(plate.txt(P1 + 8, ly + 11, rng_, size=9, fill=MUTED))

    # niche diagonals and their crossing with the standard edit
    for n in NICHES:
        if n not in rpm:
            continue
        col = load.NICHE_COLOUR.get(n, INK2)
        r = rpm[n]
        vs = [1e3, 1e7]
        s.append(f'<line x1="{X(vs[0]):.1f}" y1="{Y(vs[0]*r/1000):.1f}" x2="{X(vs[1]):.1f}" '
                 f'y2="{Y(vs[1]*r/1000):.1f}" stroke="{col}" stroke-width="2.2"/>')
        # Q1: the same niche at 85% -- the January version of the line
        s.append(f'<line x1="{X(vs[0]):.1f}" y1="{Y(vs[0]*r*Q1/1000):.1f}" x2="{X(vs[1]):.1f}" '
                 f'y2="{Y(vs[1]*r*Q1/1000):.1f}" stroke="{col}" stroke-width="1" '
                 f'stroke-dasharray="2 3" stroke-opacity="0.7"/>')
        bx = be[n]
        s.append(f'<circle cx="{X(bx):.1f}" cy="{Y(std_mid):.1f}" r="4.5" fill="{col}" '
                 f'stroke="{plate.SURFACE}" stroke-width="1.4"/>')
        s += plate.halo(X(bx) + 6, Y(std_mid) - 7, f"{bx/1e3:.0f}k", size=9.5, fill=col)
        lx = X(1e3 * 1.2)
        s += plate.halo(lx, Y(1.2e3 * r / 1000) - 6, f"{n} ${r:g}", size=10, fill=col)

    sy = bot + 58
    fin_own = ((own_lo + own_hi) / 2) / rpm[top_n] * 1000
    ent_own = ((own_lo + own_hi) / 2) / rpm[bot_n] * 1000
    s += plate.halo(28, sy, "Pay an editor once your typical video clears your niche's dot; "
                    "until then your time is the cost.", size=12.5, fill=INK)
    s += plate.wrap(28, sy + 19,
        f"The dots are where AdSense alone pays a ${std_mid:.0f} edit. Your own {hrs.low*MINUTES:.0f}–"
        f"{hrs.high*MINUTES:.0f} hours on a {MINUTES}-minute video cost more than the editor at "
        f"${HOURLY}/h: covering them takes {fin_own/1e3:.0f}k views in {top_n} and "
        f"{ent_own/1e6:.1f}M in {bot_n}. Dotted lines are Q1 at {Q1:.0%}, which moves every crossing "
        f"{1/Q1-1:.0%} to the right. Below the crossing, only a sponsor covers the gap (next plate).",
        size=10.5, fill=MUTED, chars=128, leading=13)

    H = int(sy + 19 + 4 * 13 + 56)
    s.append(f'<line x1="28" y1="{H-44:.1f}" x2="{W-28}" y2="{H-44:.1f}" stroke="{RULE}"/>')
    s += plate.wrap(28, H - 28,
        f"RPM, edit tiers and hours per finished minute: maintainer_estimate rows in "
        f"data/{y1}/benchmarks.csv. ${HOURLY}/h and {MINUTES} minutes are assumptions set at the top "
        f"of examples/chart-breakeven.py.",
        size=10, fill=MUTED, chars=134, leading=13)
    s.append("</svg>")
    svg = ("\n".join(s).replace('height="10"', f'height="{H}"')
                       .replace(f'viewBox="0 0 {W} 10"', f'viewBox="0 0 {W} {H}"'))
    out = pathlib.Path(__file__).parent / "charts" / "breakeven.svg"
    out.write_text(plate.stamp(svg), encoding="utf-8")
    print(f"  wrote {out.name}: {title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
