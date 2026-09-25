#!/usr/bin/env python3
"""The January cliff, set against how the ad market was doing that year.

    python3 examples/chart-seasonality.py

**Why this plate exists.** Every creator income thread has someone asking why RPM
halved in January. The usual answer is "Q4 budgets", given as folklore. Alphabet's
quarterly filings measure it: YouTube ad revenue in each Q1 against the Q4 before it.
Those are eight transitions, all first-party.

A single-axis version (eight bars, all negative) would only say "January is bad".
The question a creator actually has is whether this January will be *less* bad because
the market is booming, or worse because it is in a slump. So each transition is plotted
against that Q1's year-on-year growth. If the cliff depended on the market, the dots would
slope. They don't.

**What it cannot say.** This is platform revenue, which is volume times price, not any one
channel's CPM. One creator in this table (Roberto Blake, 2019-12 to 2020-01) saw CPM
*rise* into January. Your channel is one draw from under this line, not the line.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import load  # noqa: E402
import plate  # noqa: E402
from plate import INK, INK2, MUTED, RULE, GRID, FAINT  # noqa: E402

W = 880
LINE, CLIFF, SLUMP = "#2f6f5e", "#c0503e", "#c08a3e"


def quarters():
    m = load.macro()
    q = m[(m.series == "yt_ad_revenue") & m.period.str.startswith("Q")]
    q = q.assign(k=q.year.astype(int) * 4 + q.period.str[1].astype(int) - 1)
    return q.sort_values("k").set_index("k").value


def main():
    q = quarters()
    trans = []
    for k in q.index:
        if k % 4 == 3 and k + 1 in q.index:          # Q4 -> following Q1
            yoy = (q[k + 1] / q[k - 3] - 1) if k - 3 in q.index else None
            trans.append(dict(k=k, yr=k // 4 + 1, drop=q[k + 1] / q[k] - 1, yoy=yoy))
    lo, hi = min(t["drop"] for t in trans), max(t["drop"] for t in trans)
    n = len(trans)
    title = f"YouTube's ad take has fallen {-hi:.0%}–{-lo:.0%} every Q1 for {n} years, boom or slump."
    s = plate.open_svg(W, 10, title,
        subtitle="Alphabet 'YouTube ads' revenue by quarter. Each red drop is a Q4 → next Q1 "
                 "transition, and each one is plotted again on the right.")
    f, y = plate.frame(W, 88,
        who="A creator budgeting next year's income, or a brand timing a sponsorship buy",
        decide="Whether to hold Q4 cash for a January dip, and when sponsorship money goes furthest",
        wrong="A Q1 lands at or above the Q4 before it, or the right-hand dots start to slope "
              "with market growth")
    s += f

    # ---- left: the sawtooth, cliffs in red --------------------------------------
    top, bot = y + 36, y + 300
    L0, L1 = 70, 520
    ks = list(q.index)
    vmax = q.max() * 1.08
    X = lambda k: L0 + (L1 - L0) * (k - ks[0]) / (ks[-1] - ks[0])
    Y = lambda v: bot - (bot - top) * v / vmax
    for v in range(0, int(vmax) + 1, 2):
        s.append(f'<line x1="{L0}" y1="{Y(v):.1f}" x2="{L1}" y2="{Y(v):.1f}" stroke="{GRID}"/>')
        s.append(plate.txt(L0 - 8, Y(v) + 4, f"${v}B", size=10, fill=MUTED, anchor="end"))
    for k in ks:
        if k % 4 == 0:
            s.append(plate.txt(X(k), bot + 18, k // 4, size=10, fill=MUTED, anchor="middle"))
    for a, b in zip(ks, ks[1:]):
        cliff = a % 4 == 3
        s.append(f'<line x1="{X(a):.1f}" y1="{Y(q[a]):.1f}" x2="{X(b):.1f}" y2="{Y(q[b]):.1f}" '
                 f'stroke="{CLIFF if cliff else LINE}" stroke-width="{3 if cliff else 1.8}"/>')
    for k in ks:
        s.append(f'<circle cx="{X(k):.1f}" cy="{Y(q[k]):.1f}" r="2.6" '
                 f'fill="{CLIFF if k % 4 == 0 else LINE}"/>')
    s.append(plate.txt(L0, top - 12, "QUARTERLY YOUTUBE AD REVENUE", size=8.5, fill=MUTED,
                       weight="700", spacing="0.9"))

    # ---- right: the drop against that year's market ------------------------------
    R0, R1 = 600, W - 40
    pts = [t for t in trans if t["yoy"] is not None]
    gx0, gx1 = -0.10, 0.55
    dy0, dy1 = -0.25, 0.02
    GX = lambda g: R0 + (R1 - R0) * (g - gx0) / (gx1 - gx0)
    DY = lambda d: top + (bot - top) * (dy1 - d) / (dy1 - dy0)
    s.append(plate.txt(R0, top - 12, "Q4 → Q1 DROP vs MARKET THAT YEAR", size=8.5, fill=MUTED,
                       weight="700", spacing="0.9"))
    # the band every observed drop sits in
    s.append(f'<rect x="{R0}" y="{DY(hi):.1f}" width="{R1-R0}" height="{DY(lo)-DY(hi):.1f}" '
             f'fill="{CLIFF}" fill-opacity="0.08"/>')
    for d in (0.0, -0.1, -0.2):
        s.append(f'<line x1="{R0}" y1="{DY(d):.1f}" x2="{R1}" y2="{DY(d):.1f}" '
                 f'stroke="{RULE if d == 0 else GRID}"/>')
        s.append(plate.txt(R0 - 6, DY(d) + 4, f"{d:+.0%}".replace("+0%", "0%"), size=10,
                           fill=MUTED, anchor="end"))
    for g in (0.0, 0.25, 0.5):
        s.append(f'<line x1="{GX(g):.1f}" y1="{top:.1f}" x2="{GX(g):.1f}" y2="{bot:.1f}" stroke="{GRID}"/>')
        s.append(plate.txt(GX(g), bot + 18, f"{g:+.0%}", size=10, fill=MUTED, anchor="middle"))
    s.append(plate.txt((R0 + R1) / 2, bot + 34, "that Q1's growth on the year before",
                       size=9.5, fill=MUTED, anchor="middle"))
    s.append(plate.txt(R0 + 4, DY(0) - 6, "no cliff: never observed", size=9.5, fill=MUTED))
    for t in pts:
        col = SLUMP if t["yoy"] < 0 else CLIFF
        s.append(f'<circle cx="{GX(t["yoy"]):.1f}" cy="{DY(t["drop"]):.1f}" r="5" fill="{col}" '
                 f'stroke="{plate.SURFACE}" stroke-width="1.4"/>')
        s.append(plate.txt(GX(t["yoy"]) + 8, DY(t["drop"]) + 4, t["yr"], size=9.5, fill=INK2))

    sy = bot + 66
    s += plate.halo(28, sy, "Budget Q1 income at about 85% of Q4, in any market.",
                    size=12.5, fill=INK)
    slump = [t for t in pts if t["yoy"] < 0]
    boom = max(pts, key=lambda t: t["yoy"])
    s += plate.wrap(28, sy + 19,
        f"The dip does not shrink in a boom or deepen in a slump: {boom['yr']}'s Q1 grew "
        f"{boom['yoy']:.0%} on the year and {slump[0]['yr'] if slump else 'none'}'s "
        f"shrank, and both sit in the same band. So the dip is a calendar effect, not a market "
        f"one. If the drop is price rather than volume, Q1 is when a brand's budget buys the most "
        f"views, and when a creator has the least ad income to fall back on while negotiating.",
        size=10.5, fill=MUTED, chars=128, leading=13)

    H = int(sy + 19 + 4 * 13 + 56)
    s.append(f'<line x1="28" y1="{H-44:.1f}" x2="{W-28}" y2="{H-44:.1f}" stroke="{RULE}"/>')
    s += plate.wrap(28, H - 28,
        "Source: Alphabet Forms 10-Q, 10-K and 8-K earnings exhibits, row 'YouTube ads'. Rows in "
        "macro/macro.csv. Revenue is price times volume; a quarter with more views and flat CPM "
        "would also rise.",
        size=10, fill=MUTED, chars=134, leading=13)
    s.append("</svg>")
    svg = ("\n".join(s).replace('height="10"', f'height="{H}"')
                       .replace(f'viewBox="0 0 {W} 10"', f'viewBox="0 0 {W} {H}"'))
    out = pathlib.Path(__file__).parent / "charts" / "seasonality.svg"
    out.write_text(svg, encoding="utf-8")
    print(f"  wrote {out.name}: {title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
