#!/usr/bin/env python3
"""When RPM falls, was it the advertiser, the audience, or the share of views that carry an ad?

    python3 examples/chart-rpm-vs-cpm.py

**Why this plate exists.** Creator threads treat RPM, CPM and CTR as one number going up or
down. They are three different levers:

- **CPM** is what advertisers pay per 1,000 monetized playbacks, set by the ad market.
- **RPM** is what the creator keeps per 1,000 *views*, so it also depends on how many views
  carry an ad at all.
- **Impressions CTR** is how often a thumbnail gets clicked, which is the audience's lever.

The one public source that reports all three for the same channel every year is Brick
Experiment Channel's own year-in-review posts. Plotting the three together shows which lever
moved. The right panel sets every creator in this table who disclosed both RPM and CPM for
the same period against each other, as the share of CPM that survives into RPM.

**What it cannot say.** One channel, kids-skewed, is a case and not a sample. The right
panel mixes periods and niches; it shows the spread, not a trend.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import load  # noqa: E402
import plate  # noqa: E402
from plate import INK, INK2, MUTED, RULE, GRID, FAINT  # noqa: E402

W = 880
CPM, RPM, CTR = "#5b6fb0", "#c0503e", "#2f6f5e"
CH = "Brick Experiment Channel"


def main():
    c = load.creators()
    b = c[(c.creator == CH) & (c.period.str.contains("calendar year"))]
    b = b[~b.period.str.contains("Shorts")]
    get = lambda m: b[b.metric == m].set_index("year").point.sort_index()
    cpm, rpm, ctr = get("cpm"), get("rpm"), get("impressions_ctr")

    # pairs: same creator, same period, both metrics disclosed
    pairs = (c[c.metric.isin(["rpm", "cpm"]) & (c.geo == "unknown")]
             .pivot_table(index=["creator", "period", "niche", "year"], columns="metric",
                          values="point").dropna().reset_index())
    pairs["share"] = pairs.rpm / pairs.cpm

    a, z = 2021, int(cpm.index.max())
    title = (f"CPM up {cpm[z]/cpm[a]-1:.0%}, RPM down {1-rpm[z]/rpm[a]:.0%} ({a}–{z}): "
             f"advertisers didn't cut this pay.")
    s = plate.open_svg(W, 10, title,
        subtitle="One channel's own yearly YouTube Analytics (left), and every creator here who "
                 "disclosed RPM and CPM for the same period (right).")
    f, y = plate.frame(W, 88,
        who="A creator whose RPM just dropped and who is deciding what to change",
        decide="Whether to chase higher-CPM topics, fix thumbnails, or fix which views carry ads",
        wrong="CPM and RPM fall together while CTR holds; then it was the ad market after all")
    s += f

    top, bot = y + 40, y + 250
    L0, L1 = 70, 500
    yrs = list(range(int(rpm.index.min()), int(rpm.index.max()) + 1))
    X = lambda t: L0 + (L1 - L0) * (t - yrs[0]) / (yrs[-1] - yrs[0])
    vmax = 4.5
    Y = lambda v: bot - (bot - top) * v / vmax
    s.append(plate.txt(L0, top - 16, f"{CH.upper()}: $ PER 1,000", size=8.5, fill=MUTED,
                       weight="700", spacing="0.9"))
    for v in range(0, 5):
        s.append(f'<line x1="{L0}" y1="{Y(v):.1f}" x2="{L1}" y2="{Y(v):.1f}" stroke="{GRID}"/>')
        s.append(plate.txt(L0 - 8, Y(v) + 4, f"${v}", size=10, fill=MUTED, anchor="end"))
    # the gap between CPM and RPM is the part of the ad price that never reaches the creator
    both = [t for t in yrs if t in cpm.index and t in rpm.index]
    poly = [(X(t), Y(cpm[t])) for t in both] + [(X(t), Y(rpm[t])) for t in reversed(both)]
    s.append('<polygon points="' + " ".join(f"{p:.1f},{q:.1f}" for p, q in poly) +
             f'" fill="{CPM}" fill-opacity="0.08"/>')
    for ser, col, lab in ((cpm, CPM, "CPM (advertiser price)"), (rpm, RPM, "RPM (creator keeps)")):
        s.append('<polyline fill="none" stroke="%s" stroke-width="2.4" points="%s"/>' % (
            col, " ".join(f"{X(t):.1f},{Y(v):.1f}" for t, v in ser.items())))
        for t, v in ser.items():
            s.append(f'<circle cx="{X(t):.1f}" cy="{Y(v):.1f}" r="3.4" fill="{col}"/>')
        t = ser.index[-1]
        s += plate.halo(X(t) + 8, Y(ser[t]) + 4, lab, size=10.5, fill=col)
    s += plate.halo(X(2019.4), (Y(cpm[2020]) + Y(rpm[2020])) / 2 + 4,
                    "unmonetized views + YouTube's 45%", size=9.5, fill=CPM, weight="500")

    # CTR strip with YouTube's own "half of channels" band behind it
    ct, cb = bot + 34, bot + 104
    CY = lambda v: cb - (cb - ct) * v / 12
    s.append(plate.txt(L0, ct - 8, "IMPRESSIONS CTR (audience lever)", size=8.5, fill=MUTED,
                       weight="700", spacing="0.9"))
    s.append(f'<rect x="{L0}" y="{CY(10):.1f}" width="{L1-L0}" height="{CY(2)-CY(10):.1f}" '
             f'fill="{CTR}" fill-opacity="0.07"/>')
    s.append(plate.txt(L1 - 4, CY(2) - 5, "shaded: YouTube says half of channels sit at 2–10%",
                       size=9, fill=MUTED, anchor="end"))
    s.append('<polyline fill="none" stroke="%s" stroke-width="2" points="%s"/>' % (
        CTR, " ".join(f"{X(t):.1f},{CY(v):.1f}" for t, v in ctr.items())))
    for t, v in ctr.items():
        s.append(f'<circle cx="{X(t):.1f}" cy="{CY(v):.1f}" r="3" fill="{CTR}"/>')
        s.append(plate.txt(X(t), CY(v) - 7, f"{v:g}%", size=9, fill=CTR, anchor="middle"))
    for t in yrs:
        s.append(plate.txt(X(t), cb + 16, t, size=10, fill=MUTED, anchor="middle"))

    # right: share of CPM that reaches RPM, per disclosed pair
    R0, R1 = 590, W - 40
    s.append(plate.txt(R0, top - 16, "RPM ÷ CPM, SAME CREATOR & PERIOD", size=8.5, fill=MUTED,
                       weight="700", spacing="0.9"))
    rows = pairs.sort_values("share", ascending=False).reset_index(drop=True)
    step = min(22, (cb - top) / max(len(rows), 1))
    SX = lambda v: R0 + (R1 - R0 - 70) * v
    s.append(f'<line x1="{SX(0.55):.1f}" y1="{top-4:.1f}" x2="{SX(0.55):.1f}" '
             f'y2="{top + step*len(rows):.1f}" stroke="{FAINT}" stroke-dasharray="3 3"/>')
    s.append(plate.txt(SX(0.55), top + step * len(rows) + 13, "0.55 = every view monetized",
                       size=9, fill=MUTED, anchor="middle"))
    for i, r in rows.iterrows():
        ry = top + i * step + step / 2
        mine = r.creator == CH
        col = RPM if mine else INK2
        s.append(f'<line x1="{SX(0):.1f}" y1="{ry:.1f}" x2="{SX(r.share):.1f}" y2="{ry:.1f}" '
                 f'stroke="{GRID}" stroke-width="6"/>')
        s.append(f'<circle cx="{SX(r.share):.1f}" cy="{ry:.1f}" r="4" fill="{col}"/>')
        lab = f"{'Brick' if mine else r.creator.split(' (')[0]} {int(r.year)} · {r.niche}"
        s.append(plate.txt(SX(r.share) + 8, ry + 3.5, lab, size=9, fill=col))

    sy = cb + 50
    s += plate.halo(28, sy, "Before changing topics for a higher CPM, check how many of your "
                    "views carry an ad at all.", size=12.5, fill=INK)
    s += plate.wrap(28, sy + 19,
        f"The channel's thumbnails kept pulling clicks inside YouTube's normal band, and its "
        "advertisers paid more per playback. What fell was the share of views that earned "
        "anything. The creator blames YouTube Kids views, which carry no personalised ads. On "
        f"the right, disclosed RPM runs from {pairs.share.min():.2f} to {pairs.share.max():.2f} of CPM "
        f"against a ceiling of 0.55: the share of the ad price that becomes pay varies more than 2x between channels.",
        size=10.5, fill=MUTED, chars=128, leading=13)

    H = int(sy + 19 + 4 * 13 + 56)
    s.append(f'<line x1="28" y1="{H-44:.1f}" x2="{W-28}" y2="{H-44:.1f}" stroke="{RULE}"/>')
    s += plate.wrap(28, H - 28,
        "Source: creators' own disclosures, one row each in data/<year>/creators.csv with its link. "
        "The CTR band is from YouTube Help (data/macro/macro.csv). RPM here is YouTube Studio RPM, "
        "per 1,000 views of any kind.",
        size=10, fill=MUTED, chars=134, leading=13)
    s.append("</svg>")
    svg = ("\n".join(s).replace('height="10"', f'height="{H}"')
                       .replace(f'viewBox="0 0 {W} 10"', f'viewBox="0 0 {W} {H}"'))
    out = pathlib.Path(__file__).parent / "charts" / "negative" / "rpm-vs-cpm.svg"
    out.write_text(svg, encoding="utf-8")
    print(f"  wrote {out.name}: {title}")
    print(rows[["creator", "year", "niche", "rpm", "cpm", "share"]].round(2).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
