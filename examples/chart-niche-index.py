#!/usr/bin/env python3
"""The niche ladder, every year it can be drawn, with the creators who fall off it.

    python3 examples/chart-niche-index.py

**Why this plate exists.** The niche table is the first thing anyone looks for, so the
README leads with it. As a table it answers "which niche pays most" and stops. Two
questions follow straight away, and a table cannot answer either:

- **Has the ladder held?** A ranking from one year is advice only if the order survives
  across years. So every year's range is drawn on the same row.
- **Does my channel sit on the rung?** Verified creator disclosures are drawn over the
  ranges. A disclosure far from its niche's range shows the niche label is not the whole
  story.

**What it cannot say.** Before 2022 most rungs are missing, because no source for those years
could be republished or triangulated. A missing bar means *no evidence*, not a low rate.
Entertainment's low values lean on one kids-skewed channel's own reports.
"""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import load  # noqa: E402
import plate  # noqa: E402
from plate import INK, INK2, MUTED, RULE, GRID, FAINT  # noqa: E402

W = 880
DOT = "#c0503e"


def year_colour(y, y0, y1):
    # old = pale, new = deep; one hue so years read as order, not category
    t = (y - y0) / max(y1 - y0, 1)
    a, b = (199, 214, 208), (31, 92, 76)
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def main():
    b = load.benchmarks()
    idx = b[(b.basis == "maintainer_estimate") & (b.metric == "rpm")]
    cr = load.creators()
    cr = cr[(cr.metric == "rpm") & (cr.geo.isin(["unknown", "US"]))]
    niches = (idx.groupby("niche").mid.median().sort_values(ascending=False).index.tolist())
    niches = [n for n in niches if n != "all"] + (["all"] if "all" in niches else [])
    y0, y1 = int(idx.year.min()), int(idx.year.max())

    both = idx.pivot_table(index="year", columns="niche", values="mid")
    both = both[["finance", "entertainment"]].dropna() if {"finance", "entertainment"} <= set(both) else None
    if both is not None and len(both):
        r = both.finance / both.entertainment
        title = (f"Finance paid {r.min():.0f}–{r.max():.0f}x entertainment in all {len(r)} years "
                 f"measured; the rungs between swap.")
    else:
        title = "The niche ladder by year"
    s = plate.open_svg(W, 10, title,
        subtitle="Bars: this repo's RPM index (US-heavy, per 1,000 views), one per year. "
                 "Dots: creators' own disclosed RPM.")
    f, y = plate.frame(W, 88,
        who="Someone choosing a niche to start, or a creator checking if their RPM is normal",
        decide="Whether a niche switch would move income more than fixing the channel itself",
        wrong="Two niches swap order between years, or creator dots stop scattering beyond "
              "their niche's bars")
    s += f

    LX, P0, P1 = 28, 150, W - 40
    lo, hi = math.log10(0.3), math.log10(60)
    X = lambda v: P0 + (P1 - P0) * (math.log10(max(v, 0.3)) - lo) / (hi - lo)
    RH = 40
    top = y + 34
    bot = top + RH * len(niches)
    for v in (0.5, 1, 2, 5, 10, 20, 50):
        s.append(f'<line x1="{X(v):.1f}" y1="{top-6:.1f}" x2="{X(v):.1f}" y2="{bot:.1f}" stroke="{GRID}"/>')
        s.append(plate.txt(X(v), bot + 16, f"${v:g}", size=10, fill=MUTED, anchor="middle"))
    s.append(plate.txt(P1, bot + 32, "RPM, $ per 1,000 views (log scale)", size=9.5, fill=MUTED,
                       anchor="end"))

    years = list(range(y0, y1 + 1))
    lane = (RH - 8) / len(years)
    outliers = []
    for i, n in enumerate(niches):
        ry = top + i * RH
        if i:
            s.append(f'<line x1="{LX}" y1="{ry:.1f}" x2="{P1}" y2="{ry:.1f}" stroke="{GRID}"/>')
        s.append(plate.txt(LX, ry + RH / 2 + 4, n.replace("_", " "), size=11, fill=INK2,
                           weight="600" if n != "all" else "normal"))
        rows = idx[idx.niche == n]
        for r in rows.itertuples():
            ly = ry + 4 + (int(r.year) - y0) * lane + lane / 2
            x0, x1 = X(r.low), X(r.high)
            if x1 - x0 < 3:                      # a point estimate still has to be visible
                x0, x1 = x0 - 1.5, x1 + 1.5
            s.append(f'<line x1="{x0:.1f}" y1="{ly:.1f}" x2="{x1:.1f}" y2="{ly:.1f}" '
                     f'stroke="{year_colour(int(r.year), y0, y1)}" stroke-width="{max(lane-0.6, 1.4):.1f}" '
                     f'stroke-linecap="butt"/>')
        span = rows[["low", "high"]]
        for c in cr[cr.niche == n].itertuples():
            v = c.point if c.point == c.point else (c.low + c.high) / 2
            s.append(f'<circle cx="{X(v):.1f}" cy="{ry + RH/2:.1f}" r="3.6" fill="{DOT}" '
                     f'fill-opacity="0.75" stroke="{plate.SURFACE}" stroke-width="1"/>')
            if len(span) and (v > span.high.max() * 2 or v < span.low.min() / 2):
                outliers.append((c.creator, int(c.year), n, v))

    # year key
    ky = bot + 52
    s.append(plate.txt(LX, ky, "YEAR", size=8.5, fill=MUTED, weight="700", spacing="0.9"))
    for j, yr in enumerate(years):
        kx = LX + 44 + j * 52
        s.append(f'<line x1="{kx:.1f}" y1="{ky-4:.1f}" x2="{kx+18:.1f}" y2="{ky-4:.1f}" '
                 f'stroke="{year_colour(yr, y0, y1)}" stroke-width="5"/>')
        s.append(plate.txt(kx + 22, ky, yr, size=9.5, fill=MUTED))
    kx = LX + 44 + len(years) * 52 + 10
    s.append(f'<circle cx="{kx:.1f}" cy="{ky-4:.1f}" r="3.6" fill="{DOT}" fill-opacity="0.75"/>')
    s.append(plate.txt(kx + 8, ky, "creator's own disclosure", size=9.5, fill=MUTED))

    # which pairs of niches change order between years (ties are not a flip)
    import itertools
    pv = idx[idx.niche != "all"].pivot_table(index="year", columns="niche", values="mid")
    flips, tested = set(), 0
    for a, c in itertools.combinations(pv.columns, 2):
        d = (pv[a] - pv[c]).dropna()
        d = d[d != 0]
        if len(d) < 2:
            continue
        tested += 1
        if (d > 0).nunique() > 1:
            flips |= {a, c}
    steady = [n for n in niches if n not in flips and n != "all"]

    sy = ky + 30
    s += plate.halo(28, sy, "Choose between the ends of the ladder by niche; inside the middle, "
                    "fix the channel instead.", size=12.5, fill=INK)
    far = ", ".join(f"{o[0]} ({o[2]}, {o[1]}: ${o[3]:.2f})" for o in outliers[:3])
    s += plate.wrap(28, sy + 19,
        f"Of {tested} niche pairs seen in two or more years, only these swap order: "
        f"{', '.join(sorted(flips)) or 'none'}. Ranking inside that band is noise; the ends are "
        f"not. Disclosures land more than 2x outside their niche's bars: {far or 'none'}. The reasons on record are "
        f"audience country, kids-classified views and video length, and none of them is the "
        f"niche. A missing bar means no evidence that year, not a low rate.",
        size=10.5, fill=MUTED, chars=128, leading=13)

    H = int(sy + 19 + 4 * 13 + 56)
    s.append(f'<line x1="28" y1="{H-44:.1f}" x2="{W-28}" y2="{H-44:.1f}" stroke="{RULE}"/>')
    s += plate.wrap(28, H - 28,
        "Bars: maintainer_estimate rows in <year>/benchmarks.csv, triangulated against sources "
        "whose terms forbid republishing (method in examples/build_index.py). Dots: "
        "creator_report rows in <year>/creators.csv, each linked to the creator's own post.",
        size=10, fill=MUTED, chars=134, leading=13)
    s.append("</svg>")
    svg = ("\n".join(s).replace('height="10"', f'height="{H}"')
                       .replace(f'viewBox="0 0 {W} 10"', f'viewBox="0 0 {W} {H}"'))
    out = pathlib.Path(__file__).parent / "charts" / "niche-index.svg"
    out.write_text(svg, encoding="utf-8")
    print(f"  wrote {out.name}: {title}")
    for o in outliers:
        print("   outlier", o)
    return 0


if __name__ == "__main__":
    sys.exit(main())
