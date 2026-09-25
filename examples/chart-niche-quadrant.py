#!/usr/bin/env python3
"""Which niche to go into: how well it pays, and whether its pay is outgrowing YouTube.

    python3 examples/chart-niche-quadrant.py

**Why this plate exists.** The line chart shows the ladder, but a creator choosing a niche
has two questions, not one: *does it pay well now*, and *is it getting better or worse*. So
this crosses them.

- **y** is the niche's latest RPM (midpoint, with the range as a whisker).
- **x** is its pay growth per year over the recent window, from a log-linear fit.

**The vertical line is not zero.** It is YouTube's own ad-revenue growth over the same
years, from Alphabet's filings. A niche right of it is taking a growing share of the ad
money. A niche left of it is shrinking relative to the platform, even if its RPM rose in
dollars. The horizontal line is the median niche's RPM.

**What it cannot say.** Most niches have two or three years in the window, so x is noisy.
Dot size is the number of years, and small dots should be read as leads, not verdicts.
Niches with a single year in the window cannot have a slope and are set aside on the right.
"""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import load  # noqa: E402
import plate  # noqa: E402
from plate import INK, INK2, MUTED, RULE, GRID, FAINT  # noqa: E402

W = 880
WINDOW = 3          # years back from the latest, inclusive


def main():
    b = load.benchmarks()
    idx = b[(b.basis == "maintainer_estimate") & (b.metric == "rpm") & (b.niche != "all")].copy()
    idx["year"] = idx.year.astype(int)
    y1 = int(idx.year.max())
    y0 = y1 - WINDOW + 1
    win = idx[idx.year >= y0]

    m = load.macro()
    rev = m[(m.series == "yt_ad_revenue") & (m.period == "FY")].set_index("year").value
    rev.index = rev.index.astype(int)
    rv = rev[rev.index >= y0 - 1]
    # the platform's growth per year over the same span the niches are measured on
    plat = (rv.iloc[-1] / rv.iloc[0]) ** (1 / (rv.index[-1] - rv.index[0])) - 1

    pts, lone = [], []
    for n, g in win.groupby("niche"):
        g = g.sort_values("year")
        last = g.iloc[-1]
        if len(g) < 2:
            lone.append(dict(n=n, y=last.mid, lo=last.low, hi=last.high, yr=int(last.year)))
            continue
        slope = np.polyfit(g.year, np.log(g.mid), 1)[0]
        pts.append(dict(n=n, g=math.exp(slope) - 1, y=last.mid, lo=last.low, hi=last.high,
                        k=len(g), yr=int(last.year)))
    ymed = float(np.median([p["y"] for p in pts + lone]))
    go = [p["n"] for p in pts if p["g"] > plat and p["y"] > ymed]

    names = [n.title() if i == 0 else n for i, n in enumerate(go)]
    who = (", ".join(names[:-1]) + " and " + names[-1]) if len(names) > 1 else (names[0] if names else "No niche")
    title = f"{who}: above-median pay, growing faster than YouTube's ad money."
    s = plate.open_svg(W, 10, title,
        subtitle=f"Each niche's latest RPM against its pay growth per year, {y0}–{y1}. "
                 f"Dot size = years of evidence.")
    f, y = plate.frame(W, 88,
        who="Someone choosing which niche to start a channel in, or to move a channel toward",
        decide="Which niche pays well now and is taking a growing share of YouTube's ad money",
        wrong="A niche's next year lands in the opposite column. Small dots are two points "
              "and can flip on one new source")
    s += f

    P0, P1 = 80, W - 170
    top, bot = y + 34, y + 380
    gmin = min(-0.3, min(p["g"] for p in pts) - 0.05)
    gmax = max(0.6, max(p["g"] for p in pts) + 0.05)
    lo, hi = math.log10(1), math.log10(30)
    X = lambda g: P0 + (P1 - P0) * (g - gmin) / (gmax - gmin)
    Y = lambda v: bot - (bot - top) * (math.log10(max(v, 1)) - lo) / (hi - lo)

    # quadrant shading: only the one worth going to is tinted
    s.append(f'<rect x="{X(plat):.1f}" y="{top:.1f}" width="{P1-X(plat):.1f}" '
             f'height="{Y(ymed)-top:.1f}" fill="#2f6f5e" fill-opacity="0.07"/>')
    for v in (1, 2, 5, 10, 20):
        s.append(f'<line x1="{P0}" y1="{Y(v):.1f}" x2="{P1}" y2="{Y(v):.1f}" stroke="{GRID}"/>')
        s.append(plate.txt(P0 - 8, Y(v) + 4, f"${v:g}", size=10, fill=MUTED, anchor="end"))
    g = math.ceil(gmin * 10) / 10
    while g <= gmax:
        s.append(f'<line x1="{X(g):.1f}" y1="{top:.1f}" x2="{X(g):.1f}" y2="{bot:.1f}" stroke="{GRID}"/>')
        s.append(plate.txt(X(g), bot + 18, f"{g:+.0%}".replace("+0%", "0%"), size=10,
                           fill=MUTED, anchor="middle"))
        g = round(g + 0.2, 2)
    s.append(plate.txt((P0 + P1) / 2, bot + 36, "niche RPM growth per year (log-linear fit)",
                       size=9.5, fill=MUTED, anchor="middle"))
    s.append(plate.txt(P0 - 50, top - 12, "RPM, latest year", size=9.5, fill=MUTED))

    # the two dividing lines, both drawn from data
    s.append(f'<line x1="{X(plat):.1f}" y1="{top:.1f}" x2="{X(plat):.1f}" y2="{bot:.1f}" '
             f'stroke="{INK2}" stroke-dasharray="4 3"/>')
    s.append(plate.txt(X(plat) + 5, bot - 6, f"YouTube ad revenue {plat:+.0%}/yr", size=9.5,
                       fill=INK2))
    s.append(f'<line x1="{P0}" y1="{Y(ymed):.1f}" x2="{P1}" y2="{Y(ymed):.1f}" '
             f'stroke="{INK2}" stroke-dasharray="4 3"/>')
    s.append(plate.txt(P0 + 4, Y(ymed) - 5, f"median niche ${ymed:.2f}", size=9.5, fill=INK2))

    corners = ((P1 - 6, top + 14, "end", "GO: pays well, gaining share"),
               (P0 + 6, top + 14, "start", "PAYS WELL, LOSING SHARE"),
               (P1 - 6, bot - 22, "end", "CHEAP, GAINING: an early bet"),
               (P0 + 6, bot - 22, "start", "AVOID"))
    for cx, cy, a, t in corners:
        s.append(plate.txt(cx, cy, t, size=8.5, fill=MUTED, anchor=a, weight="700", spacing="0.9"))

    for p in sorted(pts, key=lambda p: -p["k"]):
        col = load.NICHE_COLOUR.get(p["n"], INK2)
        cx = X(p["g"])
        s.append(f'<line x1="{cx:.1f}" y1="{Y(p["lo"]):.1f}" x2="{cx:.1f}" y2="{Y(p["hi"]):.1f}" '
                 f'stroke="{col}" stroke-opacity="0.45" stroke-width="2"/>')
        r = 3 + 2.2 * p["k"]
        s.append(f'<circle cx="{cx:.1f}" cy="{Y(p["y"]):.1f}" r="{r:.1f}" fill="{col}" '
                 f'stroke="{plate.SURFACE}" stroke-width="1.4"/>')
        s += plate.halo(cx + r + 4, Y(p["y"]) + 4, f"{p['n']} ${p['y']:g}", size=10.5, fill=col)

    # niches with one year in the window: no slope, set aside at their height
    gx = P1 + 34
    s.append(f'<line x1="{gx-14:.1f}" y1="{top:.1f}" x2="{gx-14:.1f}" y2="{bot:.1f}" '
             f'stroke="{RULE}" stroke-dasharray="3 3"/>')
    s.append(plate.txt(gx - 6, top - 12, "NO TREND YET", size=8.5, fill=MUTED, weight="700",
                       spacing="0.9"))
    for p in lone:
        col = load.NICHE_COLOUR.get(p["n"], INK2)
        s.append(f'<line x1="{gx:.1f}" y1="{Y(p["lo"]):.1f}" x2="{gx:.1f}" y2="{Y(p["hi"]):.1f}" '
                 f'stroke="{col}" stroke-opacity="0.45" stroke-width="2"/>')
        s.append(f'<circle cx="{gx:.1f}" cy="{Y(p["y"]):.1f}" r="4" fill="none" stroke="{col}" '
                 f'stroke-width="2"/>')
        s += plate.halo(gx + 9, Y(p["y"]) + 4, f"{p['n']} ${p['y']:g}", size=10.5, fill=col)

    sy = bot + 62
    s += plate.halo(28, sy, "Go top-right; treat the size of the dot as how much to trust it.",
                    size=12.5, fill=INK)
    lefts = [p["n"] for p in pts if p["g"] < plat and p["y"] > ymed]
    s += plate.wrap(28, sy + 19,
        f"Right of the dashed line, a niche's pay is growing faster than YouTube's ad revenue "
        f"({plat:+.0%}/yr), so it is winning a bigger slice of the same pot. "
        f"{', '.join(lefts).capitalize() or 'Nothing'} pay{'s' if len(lefts) == 1 else ''} "
        f"well but {'is' if len(lefts) == 1 else 'are'} growing more slowly than the platform. "
        f"The vertical whiskers are each niche's range: where they cross the median line, "
        f"the quadrant is not settled. Rerun after adding a year, and the dots move.",
        size=10.5, fill=MUTED, chars=128, leading=13)

    H = int(sy + 19 + 4 * 13 + 56)
    s.append(f'<line x1="28" y1="{H-44:.1f}" x2="{W-28}" y2="{H-44:.1f}" stroke="{RULE}"/>')
    s += plate.wrap(28, H - 28,
        "y and x: maintainer_estimate rows in data/<year>/benchmarks.csv. Platform growth: Alphabet "
        f"10-K 'YouTube ads' revenue, {int(rv.index[0])}–{int(rv.index[-1])}, in data/macro/macro.csv.",
        size=10, fill=MUTED, chars=134, leading=13)
    s.append("</svg>")
    svg = ("\n".join(s).replace('height="10"', f'height="{H}"')
                       .replace(f'viewBox="0 0 {W} 10"', f'viewBox="0 0 {W} {H}"'))
    out = pathlib.Path(__file__).parent / "charts" / "niche-quadrant.svg"
    out.write_text(plate.stamp(svg), encoding="utf-8")
    print(f"  wrote {out.name}: {title}")
    for p in pts:
        print(f"   {p['n']:<14} y=${p['y']:<6} g={p['g']:+.0%} k={p['k']}")
    print("   no trend:", [p["n"] for p in lone], f" platform {plat:+.1%}, median ${ymed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
