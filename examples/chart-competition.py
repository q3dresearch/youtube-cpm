#!/usr/bin/env python3
"""Shorts inventory against the ad money that has to pay for it.

    python3 examples/chart-competition.py

**Why this plate exists.** An RPM is ad money divided by views. Published niche tables
move the numerator and never mention the denominator, so a reader sees "finance pays
$15-40" and never learns whether the pot is being split between more views each year.

YouTube publishes both halves itself. Alphabet's filings give the ad revenue, and
YouTube's own letters give Shorts daily views and the partner-programme size. Indexed to
the same year, the gap between the revenue line and the views line shows the squeeze
directly. Nothing here comes from a third-party rate table.

**What it cannot say.** Ad revenue includes long-form, Shorts and connected TV, and
YouTube does not split it. So the plate shows a *platform* ratio, not a Shorts RPM. The
Shorts figures are "over X" lower bounds, which means the true gap is at least as wide
as drawn.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import load  # noqa: E402
import plate  # noqa: E402
from plate import INK, INK2, MUTED, RULE, GRID, FAINT  # noqa: E402

W = 880
REV, SHORTS, YPP = "#2f6f5e", "#c0503e", "#5b6fb0"
BASE = 2023


def series():
    m = load.macro()
    rev = m[(m.series == "yt_ad_revenue") & (m.period == "FY")].set_index("year").value
    sv = m[(m.series == "shorts_daily_views") & (m.unit == "billions_per_day")]
    # several statements per year repeat the same "over 200B"; the year's max is the claim
    shorts = sv.groupby("year").value.max()
    yp = m[(m.series == "ypp_channels") & (m.unit == "count")].copy()
    # "Today more than 3 million" was said on 2024-02-06, so it describes the end of 2023
    yp["yr"] = yp.period.str[:4].astype(int) - (yp.period.str[5:7] < "04").astype(int)
    ypp = yp.groupby("yr").value.max()
    return rev, shorts, ypp


def main():
    rev, shorts, ypp = series()
    idx = lambda s, base: {int(y): 100 * v / s[base] for y, v in s.items()}
    R, S = idx(rev, BASE), idx(shorts, BASE)
    # a year with no full-year filing yet has no revenue to set against its views
    S = {k: v for k, v in S.items() if k in R}
    P = {int(y): 100 * v / ypp.loc[2023] for y, v in ypp.items()}
    grow_s = S[max(S)] / 100
    grow_r = R[max(S)] / 100
    title = (f"Shorts views grew {grow_s:.0f}x in two years; the ad money grew "
             f"{(grow_r - 1) * 100:.0f}%.")
    s = plate.open_svg(W, 10, title,
        subtitle="YouTube's own figures, each indexed to 2023 = 100. Log scale, so equal "
                 "slopes mean equal growth rates.")
    f, y = plate.frame(W, 88,
        who="A creator choosing between Shorts and long-form for the next year of uploads",
        decide="Whether Shorts views will ever pay like long-form views, or stay a "
               "discovery tool for the channel",
        wrong="The green line catches the red one: ad revenue growing faster than Shorts "
              "views, so each view's share rises")
    s += f

    PL, PR, top, bot = 84, W - 190, y + 34, y + 330
    years = range(2017, 2027)
    import math
    lo, hi = math.log10(25), math.log10(500)
    X = lambda yr: PL + (PR - PL) * (yr - 2017) / 9
    Y = lambda v: bot - (bot - top) * (math.log10(v) - lo) / (hi - lo)
    for v in (25, 50, 100, 200, 400):
        s.append(f'<line x1="{PL}" y1="{Y(v):.1f}" x2="{PR}" y2="{Y(v):.1f}" stroke="{GRID}"/>')
        s.append(plate.txt(PL - 8, Y(v) + 4, v, size=10, fill=MUTED, anchor="end"))
    for yr in years:
        s.append(plate.txt(X(yr), bot + 18, yr, size=10, fill=MUTED, anchor="middle"))
    s.append(f'<line x1="{PL}" y1="{Y(100):.1f}" x2="{PR}" y2="{Y(100):.1f}" stroke="{FAINT}" '
             f'stroke-dasharray="3 3"/>')

    # the squeeze, drawn as area between the two lines over the years both exist
    both = sorted(set(R) & set(S))
    poly = [(X(t), Y(S[t])) for t in both] + [(X(t), Y(R[t])) for t in reversed(both)]
    s.append('<polygon points="' + " ".join(f"{a:.1f},{b:.1f}" for a, b in poly) +
             f'" fill="{SHORTS}" fill-opacity="0.10"/>')

    def line(d, col, label, dash=""):
        pts = sorted(d.items())
        s.append('<polyline fill="none" stroke="%s" stroke-width="2.4" %s points="%s"/>' % (
            col, f'stroke-dasharray="{dash}"' if dash else "",
            " ".join(f"{X(a):.1f},{Y(b):.1f}" for a, b in pts)))
        for a, b in pts:
            s.append(f'<circle cx="{X(a):.1f}" cy="{Y(b):.1f}" r="3.4" fill="{col}"/>')
        a, b = pts[-1]
        s.extend(plate.halo(X(a) + 10, Y(b) + 4, label, size=11, fill=col))

    line(R, REV, "YouTube ad revenue")
    line(S, SHORTS, "Shorts daily views")
    line(P, YPP, "partner channels (floor)", dash="5 3")

    # inside the wedge, right-aligned to its widest year, clear of both line labels
    last = both[-1]
    gm = (S[last] * R[last]) ** 0.5
    s += plate.halo(X(last) - 10, Y(gm) + 4, "the gap = views diluting the pot",
                    size=10.5, fill=SHORTS, anchor="end", weight="500")

    sy = bot + 50
    s += plate.halo(28, sy, "Treat Shorts as a funnel into long-form. Don't treat it as income.",
                    size=12.5, fill=INK)
    s += plate.wrap(28, sy + 19,
        "Long-form and Shorts share one ad pot and YouTube does not split it, so the shaded gap "
        "is the least that Shorts views have been diluted. The partner line is flat at a "
        "\"3 million\" floor YouTube has repeated since 2024; if it is really growing, the "
        "long-form share is being split too. This advice flips only if a filing shows ad revenue "
        "outgrowing Shorts views.",
        size=10.5, fill=MUTED, chars=128, leading=13)

    H = int(sy + 19 + 4 * 13 + 60)
    s.append(f'<line x1="28" y1="{H-46:.1f}" x2="{W-28}" y2="{H-46:.1f}" stroke="{RULE}"/>')
    s += plate.wrap(28, H - 30,
        "Sources, all first-party: Alphabet 10-K 'YouTube ads' revenue; YouTube CEO letters and "
        "blog posts for Shorts daily views and partner-programme size (\"over\" figures, so lower "
        "bounds). Rows in macro/macro.csv.",
        size=10, fill=MUTED, chars=134, leading=13)
    s.append("</svg>")
    svg = ("\n".join(s).replace('height="10"', f'height="{H}"')
                       .replace(f'viewBox="0 0 {W} 10"', f'viewBox="0 0 {W} {H}"'))
    out = pathlib.Path(__file__).parent / "charts" / "competition.svg"
    out.write_text(svg, encoding="utf-8")
    print(f"  wrote {out.name}: {title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
