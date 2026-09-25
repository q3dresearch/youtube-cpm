#!/usr/bin/env python3
"""How long a video earns: attention half-life by category, and what it means for payback.

    python3 examples/chart-attention.py

**Why this plate exists.** Breakeven maths ("a $250 video needs 156k views") hides a second
question: *by when?* If a video's daily views halve every two days, nearly all its ad money
arrives in the first week, and a creator can judge it on day 7. If they halve every month,
the same video is a slow annuity and pays back over a year. The category decides which.

The left panel is the evidence: each category's median daily views, as a share of its first
trending day, over the following days. The right panel reduces each category to its median
half-life, and converts it to the share of views earned in the first 7 days *if* the
decay continued at that rate.

**What it cannot say.** The source only sees videos while they trend (CC0 trending dataset,
US, 2017-18), so this is the half-life of a video that *caught on*. A search-driven evergreen
video never trends and decays far more slowly. That is the condition under which this plate
is wrong, and it says so on its face.
"""
import math
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import attention  # noqa: E402
import plate  # noqa: E402
from plate import INK, INK2, MUTED, RULE, GRID, FAINT  # noqa: E402

W = 880
GROUPS = {"news": "#c0503e", "entertainment": "#6b6b6b", "howto": "#c08a3e", "music": "#1f5c4c"}
MIN_N = 30


def curves():
    """Median daily views relative to the first trending day, per category and day."""
    d = pd.read_csv(attention.RAW)
    d["t"] = pd.to_datetime(d.trending_date, format="%y.%d.%m")
    d = d.sort_values(["video_id", "t"]).drop_duplicates(["video_id", "t"])
    d["daily"] = d.groupby("video_id").views.diff()
    d["gap"] = d.groupby("video_id").t.diff().dt.days
    d = d[(d.gap == 1) & (d.daily > 0)].copy()
    d["k"] = d.groupby("video_id").cumcount()
    first = d[d.k == 0].set_index("video_id").daily
    d["rel"] = d.daily / d.video_id.map(first)
    d["category"] = d.category_id.map(attention.CATEGORY)
    out = {}
    for c in GROUPS:
        g = d[d.category == c].groupby("k").rel.agg(["median", "count"])
        out[c] = g[g["count"] >= MIN_N]["median"]
    return out


def main():
    h = pd.read_csv(attention.REPO / "data" / "attention" / "halflife.csv")
    dec = h.dropna(subset=["half_life_days"])
    med = dec.half_life_days.median()
    by = (dec.groupby("category").half_life_days
          .agg(med="median", q1=lambda s: s.quantile(.25), q3=lambda s: s.quantile(.75), n="count"))
    by = by[by.n >= MIN_N].sort_values("med")
    wk = lambda hl: 1 - 2 ** (-7 / hl)
    fast, slow = by.index[0], by.index[-1]
    title = (f"A trending video's daily views halve every {med:.1f} days: "
             f"{fast} in {by.med[fast]:.1f}, {slow} in {by.med[slow]:.1f}.")
    s = plate.open_svg(W, 10, title,
        subtitle=f"{len(dec):,} US trending videos, 2017–18, CC0. Left: daily views vs first "
                 f"trending day. Right: half-life by category.")
    f, y = plate.frame(W, 88,
        who="A creator deciding when to judge a video, and how to price a sponsor on it",
        decide="Whether a video's income is a one-week event or a slow annuity, and so how "
               "soon it must pay back",
        wrong="A non-music video still gets a quarter of its day-one views after two weeks: "
              "it is search-driven, and this curve does not apply")
    s += f

    # ---- left: the decay itself -------------------------------------------------
    cv = curves()
    top, bot = y + 40, y + 300
    L0, L1 = 70, 410
    K = max(len(c) for c in cv.values()) - 1
    X = lambda k: L0 + (L1 - L0) * k / max(K, 1)
    lo, hi = math.log10(0.02), math.log10(1.3)
    Y = lambda v: bot - (bot - top) * (math.log10(max(v, 0.02)) - lo) / (hi - lo)
    s.append(plate.txt(L0, top - 16, "DAILY VIEWS, SHARE OF FIRST TRENDING DAY", size=8.5,
                       fill=MUTED, weight="700", spacing="0.9"))
    for v, lab in ((1, "100%"), (0.5, "50%"), (0.25, "25%"), (0.1, "10%"), (0.05, "5%")):
        s.append(f'<line x1="{L0}" y1="{Y(v):.1f}" x2="{L1}" y2="{Y(v):.1f}" stroke="{GRID}"/>')
        s.append(plate.txt(L0 - 8, Y(v) + 4, lab, size=10, fill=MUTED, anchor="end"))
    for k in range(0, K + 1, 2):
        s.append(plate.txt(X(k), bot + 18, k, size=10, fill=MUTED, anchor="middle"))
    s.append(plate.txt((L0 + L1) / 2, bot + 34, "days after first trending day", size=9.5,
                       fill=MUTED, anchor="middle"))
    ends = []
    for c, ser in cv.items():
        col = GROUPS[c]
        s.append('<polyline fill="none" stroke="%s" stroke-width="2.4" points="%s"/>' % (
            col, " ".join(f"{X(k):.1f},{Y(v):.1f}" for k, v in ser.items())))
        ends.append([Y(ser.iloc[-1]), c, col, X(ser.index[-1])])
    ends.sort()
    for i in range(1, len(ends)):
        ends[i][0] = max(ends[i][0], ends[i - 1][0] + 13)
    for ly, c, col, lx in ends:
        s += plate.halo(lx + 6, ly + 4, c, size=10.5, fill=col)

    # ---- right: half-life by category, with the first-week share it implies ------
    R0, R1 = 590, W - 60
    s.append(plate.txt(R0, top - 16, "MEDIAN HALF-LIFE, DAYS (middle half as whisker)", size=8.5,
                       fill=MUTED, weight="700", spacing="0.9"))
    HX = lambda v: R0 + (R1 - R0) * min(v, 8) / 8
    step = (bot - top) / len(by)
    for d_ in (0, 2, 4, 6, 8):
        s.append(f'<line x1="{HX(d_):.1f}" y1="{top:.1f}" x2="{HX(d_):.1f}" y2="{bot:.1f}" stroke="{GRID}"/>')
        s.append(plate.txt(HX(d_), bot + 18, d_, size=10, fill=MUTED, anchor="middle"))
    s.append(plate.txt((R0 + R1) / 2, bot + 34, "days for daily views to halve", size=9.5,
                       fill=MUTED, anchor="middle"))
    for i, (c, r) in enumerate(by.iterrows()):
        ry = top + i * step + step / 2
        col = GROUPS.get(c, INK2)
        s.append(f'<line x1="{HX(r.q1):.1f}" y1="{ry:.1f}" x2="{HX(r.q3):.1f}" y2="{ry:.1f}" '
                 f'stroke="{col}" stroke-opacity="0.35" stroke-width="5"/>')
        s.append(f'<circle cx="{HX(r.med):.1f}" cy="{ry:.1f}" r="{2.5 + math.sqrt(r.n) / 6:.1f}" '
                 f'fill="{col}"/>')
        s.append(plate.txt(R0 - 6, ry + 3.5, c.replace("_", " "), size=9.5, fill=INK2, anchor="end"))
        s.append(plate.txt(R1 + 8, ry + 3.5, f"{wk(r.med):.0%}", size=9.5, fill=col))
    s.append(plate.txt(R1 + 8, top - 4, "wk 1", size=8.5, fill=MUTED, weight="700"))

    sy = bot + 64
    s += plate.halo(28, sy, f"Judge a video on day 7, and sell a sponsor on first-week views, "
                    f"not lifetime views.", size=12.5, fill=INK)
    s += plate.wrap(28, sy + 19,
        f"At the median half-life, {wk(med):.0%} of a trending video's views arrive in its first "
        f"week, so its AdSense is a one-week event. Breakeven has to be met in that week, and a "
        f"flat sponsorship fee paid up front is worth more than it looks. Music is the exception "
        f"({wk(by.med[slow]):.0%} in week one): it keeps earning. The long tail comes from search, "
        f"which this data cannot see; a tutorial that never trends is a different asset.",
        size=10.5, fill=MUTED, chars=128, leading=13)

    H = int(sy + 19 + 4 * 13 + 56)
    s.append(f'<line x1="28" y1="{H-44:.1f}" x2="{W-28}" y2="{H-44:.1f}" stroke="{RULE}"/>')
    s += plate.wrap(28, H - 28,
        "Source: Kaggle 'Trending YouTube Video Statistics' (datasnaek), CC0, US file, hash-pinned "
        "in examples/attention.py. Per-video fits in data/attention/halflife.csv. Categories with fewer "
        f"than {MIN_N} fitted videos are left out.",
        size=10, fill=MUTED, chars=134, leading=13)
    s.append("</svg>")
    svg = ("\n".join(s).replace('height="10"', f'height="{H}"')
                       .replace(f'viewBox="0 0 {W} 10"', f'viewBox="0 0 {W} {H}"'))
    out = pathlib.Path(__file__).parent / "charts" / "attention.svg"
    out.write_text(svg, encoding="utf-8")
    print(f"  wrote {out.name}: {title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
