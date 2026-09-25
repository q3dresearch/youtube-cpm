#!/usr/bin/env python3
"""The niche index over time: one line per niche.

    python3 examples/chart-niche-lines.py

**Why this plate exists.** The README table gives each niche's number for each year. What
it cannot show is whether a niche is climbing, sinking or crossing another. So time goes
on x, pay on y, and every niche is one line in its own colour.

**How gaps are drawn.** A year with no evidence is a gap, not a zero. Consecutive years are
joined by a solid line; years joined across a gap get a dashed line, so a reader can see
where the line is interpolated rather than measured.

**What it cannot say.** Before 2024 only entertainment and tech have more than a year or
two of evidence. A short line is thin evidence, not a flat market.
"""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import load  # noqa: E402
import plate  # noqa: E402
from plate import INK, INK2, MUTED, RULE, GRID  # noqa: E402

W = 880


def main():
    b = load.benchmarks()
    idx = b[(b.basis == "maintainer_estimate") & (b.metric == "rpm")]
    piv = idx.pivot_table(index="year", columns="niche", values="mid")
    piv.index = piv.index.astype(int)
    y0, y1 = int(piv.index.min()), int(piv.index.max())
    latest = piv.loc[y1].dropna().sort_values(ascending=False)

    top_n, bot_n = latest.index[0], latest.index[-1]
    ratio = latest.iloc[0] / latest.iloc[-1]
    title = f"{top_n.title()} pays {ratio:.0f}x {bot_n} in {y1}; the top and bottom never swap."
    s = plate.open_svg(W, 10, title,
        subtitle="This repo's RPM index: midpoint, $ per 1,000 views, mostly US audience. "
                 "Log scale. Dashed = joined across a year with no evidence.")
    f, y = plate.frame(W, 88,
        who="Someone comparing niches before starting, or a creator watching their own",
        decide="Whether a niche's pay is rising, falling or crossing another over time",
        wrong="A creator's own reported RPM for a niche keeps landing far from its line")
    s += f

    P0, P1 = 70, W - 150
    top, bot = y + 30, y + 400
    lo, hi = math.log10(0.4), math.log10(30)
    X = lambda t: P0 + (P1 - P0) * (t - y0) / (y1 - y0)
    Y = lambda v: bot - (bot - top) * (math.log10(v) - lo) / (hi - lo)
    for v in (0.5, 1, 2, 5, 10, 20):
        s.append(f'<line x1="{P0}" y1="{Y(v):.1f}" x2="{P1}" y2="{Y(v):.1f}" stroke="{GRID}"/>')
        s.append(plate.txt(P0 - 8, Y(v) + 4, f"${v:g}", size=10, fill=MUTED, anchor="end"))
    for t in range(y0, y1 + 1):
        s.append(plate.txt(X(t), bot + 18, t, size=10, fill=MUTED, anchor="middle"))

    ends = []
    for n in piv.columns:
        col = load.NICHE_COLOUR.get(n, INK2)
        ser = piv[n].dropna()
        pts = list(ser.items())
        dash = ' stroke-dasharray="4 3"' if n == "all" else ""
        for (ta, va), (tb, vb) in zip(pts, pts[1:]):
            gap = tb - ta > 1
            s.append(f'<line x1="{X(ta):.1f}" y1="{Y(va):.1f}" x2="{X(tb):.1f}" y2="{Y(vb):.1f}" '
                     f'stroke="{col}" stroke-width="{1.4 if gap else 2.4}" '
                     f'{"stroke-dasharray=\"3 4\"" if gap else dash[1:]} stroke-opacity="{0.55 if gap else 1}"/>')
        for t, v in pts:
            s.append(f'<circle cx="{X(t):.1f}" cy="{Y(v):.1f}" r="3.4" fill="{col}" '
                     f'stroke="{plate.SURFACE}" stroke-width="1"/>')
        if n == "all":
            # the all-niche average ends mid-chart, inside other lines; label its first point
            t, v = pts[0]
            s += plate.halo(X(t) + 4, Y(v) - 9, "all niches (average)", size=10, fill=col)
            continue
        t, v = pts[-1]
        ends.append([Y(v), n, col, t, v])

    # direct labels at each line's end; nudge apart so none overlap
    ends.sort()
    for i in range(1, len(ends)):
        if ends[i][0] - ends[i - 1][0] < 13:
            ends[i][0] = ends[i - 1][0] + 13
    for ly, n, col, t, v in ends:
        lx = X(t) + 8 if t == y1 else X(t) + 8
        name = "all niches" if n == "all" else n.replace("_", " ")
        s += plate.halo(max(lx, X(t) + 8), ly + 4, f"{name} ${v:g}" + ("" if t == y1 else f" ({t})"),
                        size=10.5, fill=col)

    sy = bot + 48
    s += plate.halo(28, sy, "Read the order of the lines, not the slopes: two-point slopes "
                    "are noise.", size=12.5, fill=INK)
    s += plate.wrap(28, sy + 19,
        "A line with two points moves as far as its two sources disagree. The order at the top "
        "(finance, then business and tech) and at the bottom (gaming, entertainment) repeats "
        "every year it can be checked; the middle swaps. The quadrant plate turns this into a "
        "choice: which niche pays well and is gaining on YouTube's own ad growth.",
        size=10.5, fill=MUTED, chars=128, leading=13)

    H = int(sy + 19 + 3 * 13 + 56)
    s.append(f'<line x1="28" y1="{H-44:.1f}" x2="{W-28}" y2="{H-44:.1f}" stroke="{RULE}"/>')
    s += plate.wrap(28, H - 28,
        "maintainer_estimate rows in data/<year>/benchmarks.csv: our own ranges, triangulated against "
        "sources whose terms forbid republishing (method in examples/build_index.py).",
        size=10, fill=MUTED, chars=134, leading=13)
    s.append("</svg>")
    svg = ("\n".join(s).replace('height="10"', f'height="{H}"')
                       .replace(f'viewBox="0 0 {W} 10"', f'viewBox="0 0 {W} {H}"'))
    out = pathlib.Path(__file__).parent / "charts" / "niche-lines.svg"
    out.write_text(plate.stamp(svg), encoding="utf-8")
    print(f"  wrote {out.name}: {title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
