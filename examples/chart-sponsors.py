#!/usr/bin/env python3
"""When a channel needs sponsorships, and when it doesn't, by niche.

    python3 examples/chart-sponsors.py

**Why this plate exists.** "Get sponsors" is given as universal advice. Whether a creator
*needs* one depends on two crossings, both computed from this repo's estimates:

- **ads + sponsor**: the views at which AdSense plus one integration pay for a standard
  edit. Below this, nothing pays for an editor: the video is DIY.
- **ads alone**: the views at which AdSense pays for it without help. Above this, a
  sponsor is profit, not survival, and can be turned down when it hurts the video.

Between the two, the channel depends on sponsors. The right column draws what share of a
video's income one sponsor is. That share does not depend on views: it is
CPV / (CPV + RPM), a property of the niche.

**What it cannot say.** Sponsor rates are $ per 1,000 views of a 60-90 second integration,
as this repo estimates them. Real deals are flat fees negotiated on *expected* views, and a
brand can simply decline a small channel. The creator dots are real published rates.
"""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import load  # noqa: E402
import plate  # noqa: E402
from plate import INK, INK2, MUTED, RULE, GRID, FAINT  # noqa: E402

W = 880
DIY, NEED, FREE = "#d9d6cc", "#c08a3e", "#2f6f5e"


def main():
    b = load.benchmarks()
    y1 = int(b[b.basis == "maintainer_estimate"].year.max())
    cur = b[(b.basis == "maintainer_estimate") & (b.year == y1)]
    rpm = cur[cur.metric == "rpm"].set_index("niche").mid
    cpv = cur[cur.metric == "cpv_brand"].set_index("niche").mid
    tiers = cur[cur.metric == "edit_cost"]
    cost = tiers[tiers.notes.str.contains("tier=standard")].iloc[0].mid
    niches = [n for n in rpm.sort_values(ascending=False).index if n in cpv.index]
    rows = []
    for n in niches:
        rows.append(dict(n=n, rpm=rpm[n], cpv=cpv[n],
                         both=cost / (rpm[n] + cpv[n]) * 1000, alone=cost / rpm[n] * 1000,
                         share=cpv[n] / (cpv[n] + rpm[n])))
    lo_s, hi_s = min(r["share"] for r in rows), max(r["share"] for r in rows)
    fin, ent = rows[0], rows[-1]
    title = (f"One sponsor is {lo_s:.0%}–{hi_s:.0%} of a video's income; {fin['n']} outgrows "
             f"the need at {fin['alone']/1e3:.0f}k views.")
    s = plate.open_svg(W, 10, title,
        subtitle=f"Views per video at which a ${cost:.0f} standard edit is paid by ads + one sponsor, "
                 f"and by ads alone. {y1} estimates.")
    f, y = plate.frame(W, 88,
        who="A creator deciding whether to chase, accept or turn down a sponsorship",
        decide="Whether their typical views make a sponsor necessary, optional, or not yet useful",
        wrong="Brands pay a channel far less per view than the niche rate. Then the amber zone "
              "shifts right, as Jeff Geerling's own rate shows for tech")
    s += f

    P0, P1 = 120, 640
    top = y + 44
    RH = 30
    bot = top + RH * len(rows)
    vx0, vx1 = math.log10(1e3), math.log10(1e7)
    X = lambda v: P0 + (P1 - P0) * (math.log10(min(max(v, 1e3), 1e7)) - vx0) / (vx1 - vx0)
    for v, lab in ((1e3, "1k"), (1e4, "10k"), (1e5, "100k"), (1e6, "1M"), (1e7, "10M")):
        s.append(f'<line x1="{X(v):.1f}" y1="{top-6:.1f}" x2="{X(v):.1f}" y2="{bot:.1f}" stroke="{GRID}"/>')
        s.append(plate.txt(X(v), bot + 16, lab, size=10.5, fill=INK2, anchor="middle", weight="600"))
    s.append(plate.txt((P0 + P1) / 2, bot + 32, "views per video", size=9.5, fill=MUTED,
                       anchor="middle"))
    for i, (lab, col) in enumerate((("nothing covers an editor: DIY", DIY),
                                    ("needs a sponsor", NEED), ("ads alone: sponsor = profit", FREE))):
        kx = P0 + i * 180
        s.append(f'<rect x="{kx}" y="{top-32:.1f}" width="14" height="9" fill="{col}"/>')
        s.append(plate.txt(kx + 19, top - 24, lab, size=9.5, fill=MUTED))

    S0, S1 = 700, W - 40
    s.append(plate.txt(S0, top - 24, "ONE SPONSOR'S SHARE", size=8.5, fill=MUTED, weight="700",
                       spacing="0.9"))
    for i, r in enumerate(rows):
        ry = top + i * RH
        mid = ry + RH / 2
        col = load.NICHE_COLOUR.get(r["n"], INK2)
        s.append(plate.txt(P0 - 10, mid + 4, r["n"], size=11, fill=col, anchor="end", weight="600"))
        segs = ((1e3, r["both"], DIY), (r["both"], r["alone"], NEED), (r["alone"], 1e7, FREE))
        for a, z, c in segs:
            if z > a:
                s.append(f'<rect x="{X(a):.1f}" y="{ry+6:.1f}" width="{X(z)-X(a):.1f}" '
                         f'height="{RH-12}" fill="{c}" fill-opacity="{0.55 if c == DIY else 0.8}"/>')
        s += plate.halo(X(r["both"]) - 4, ry + 4, f"{r['both']/1e3:.0f}k", size=9, fill=INK2,
                        anchor="end", weight="500")
        s += plate.halo(X(r["alone"]) + 4, ry + 4, f"{r['alone']/1e3:.0f}k", size=9, fill=INK2,
                        weight="500")
        s.append(f'<rect x="{S0}" y="{ry+9:.1f}" width="{S1-S0}" height="{RH-18}" fill="{GRID}"/>')
        s.append(f'<rect x="{S0}" y="{ry+9:.1f}" width="{(S1-S0)*r["share"]:.1f}" '
                 f'height="{RH-18}" fill="{NEED}"/>')
        s.append(plate.txt(S0 + (S1 - S0) * r["share"] + 4, mid + 4, f"{r['share']:.0%}", size=9.5,
                           fill=INK2))

    # real published rates on the tech row: where their own CPV puts the crossing
    c = load.creators()
    own = c[(c.metric == "cpv_brand") & c.niche.isin([r["n"] for r in rows])]
    for o in own.itertuples():
        i = [r["n"] for r in rows].index(o.niche)
        r = rows[i]
        v = cost / (r["rpm"] + o.point) * 1000
        ry = top + i * RH + RH / 2
        # a tick on the bar itself, named inside it, so it cannot collide with the row above
        s.append(f'<line x1="{X(v):.1f}" y1="{ry-9:.1f}" x2="{X(v):.1f}" y2="{ry+9:.1f}" '
                 f'stroke="{INK}" stroke-width="2.4"/>')
        s.append(plate.txt(X(v) + 5, ry + 3.5, f"{o.creator.split()[-1]}'s own rate", size=8.5,
                           fill=INK, weight="600"))

    sy = bot + 60
    s += plate.halo(28, sy, "In the amber zone, take the sponsor. Right of it, turn one down when "
                    "it hurts the video.", size=12.5, fill=INK)
    s += plate.wrap(28, sy + 19,
        f"Sponsor rates per view run {min(r['cpv']/r['rpm'] for r in rows):.0f}–"
        f"{max(r['cpv']/r['rpm'] for r in rows):.0f}x the niche's RPM, so one integration outweighs "
        f"the ad income in every niche. That is why the sponsor zone is wide in low-RPM niches: "
        f"gaming and entertainment depend on sponsors across most channel sizes. Q1 cuts ads by "
        f"about 15%, which moves every right-hand edge {1/0.85-1:.0%} further right, so a channel "
        f"near its green edge needs a sponsor in Q1 even if it doesn't the rest of the year.",
        size=10.5, fill=MUTED, chars=128, leading=13)

    H = int(sy + 19 + 4 * 13 + 56)
    s.append(f'<line x1="28" y1="{H-44:.1f}" x2="{W-28}" y2="{H-44:.1f}" stroke="{RULE}"/>')
    s += plate.wrap(28, H - 28,
        f"RPM, sponsor rate per 1,000 views and edit cost: maintainer_estimate rows in data/{y1}/"
        f"benchmarks.csv. Creator marks: creator_report rows (cpv_brand) in data/<year>/creators.csv, "
        f"each linked to the creator's own rate card.",
        size=10, fill=MUTED, chars=134, leading=13)
    s.append("</svg>")
    svg = ("\n".join(s).replace('height="10"', f'height="{H}"')
                       .replace(f'viewBox="0 0 {W} 10"', f'viewBox="0 0 {W} {H}"'))
    out = pathlib.Path(__file__).parent / "charts" / "sponsors.svg"
    out.write_text(plate.stamp(svg), encoding="utf-8")
    print(f"  wrote {out.name}: {title}")
    for r in rows:
        print(f"   {r['n']:<14} both {r['both']:>8.0f}  alone {r['alone']:>8.0f}  share {r['share']:.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
