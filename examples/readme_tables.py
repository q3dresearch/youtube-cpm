#!/usr/bin/env python3
"""Rewrite the tables at the top of the README from the CSVs.

    python3 examples/readme_tables.py

The README's numbers are the first thing a reader sees, and the first thing to go stale
when a row is added by hand. So they are never typed. This fills everything between the
`<!-- tables:start -->` and `<!-- tables:end -->` markers and leaves the rest of the README
alone. Run it after adding any row.
"""
import pathlib
import re
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import load  # noqa: E402

README = load.REPO / "README.md"


def money(v):
    return f"${v:,.0f}" if v == int(v) else f"${v:,.2f}"


def rng(lo, hi):
    return money(lo) if lo == hi else f"{money(lo)} – {money(hi)}"


def main():
    b, c, m = load.benchmarks(), load.creators(), load.macro()
    idx = b[(b.basis == "maintainer_estimate") & (b.metric == "rpm")]
    latest = int(idx.year.max())
    out = []

    # 1 — the ladder, latest year
    now = idx[idx.year == latest].sort_values("mid", ascending=False)
    cr = c[c.metric == "rpm"]
    out += [f"### RPM by niche, {latest}", "",
            "What a creator keeps per 1,000 views, mostly US audience. This is our own estimate; "
            "see [how it is made](#where-the-numbers-come-from).", "",
            "| niche | RPM | evidence | creators' own reports, all years |",
            "| --- | ---: | --- | ---: |"]
    for r in now.itertuples():
        n = (cr.niche == r.niche).sum()
        out.append(f"| **{r.niche.replace('_', ' ')}** | **{rng(r.low, r.high)}** | "
                   f"{r.locator.replace('triangulated against ', '')} | {n or '—'} |")
    out.append("")

    # 2 — every year, midpoints, blank where there is no evidence
    piv = idx.pivot_table(index="niche", columns="year", values="mid")
    piv = piv.loc[piv[latest].dropna().sort_values(ascending=False).index.tolist() +
                  [n for n in piv.index if pd.isna(piv.loc[n, latest])]]
    yrs = [int(y) for y in piv.columns]
    out += ["### The same index, every year", "",
            "Midpoint of the range, $ per 1,000 views. **—** means there was no evidence we "
            "could use that year, not a low rate.", "",
            "| niche | " + " | ".join(map(str, yrs)) + " |",
            "| --- | " + " | ".join("---:" for _ in yrs) + " |"]
    for n, row in piv.iterrows():
        out.append(f"| {n.replace('_', ' ')} | " + " | ".join(
            "—" if pd.isna(v) else money(v) for v in row) + " |")
    out.append("")

    # 3 — the platform, first-party only
    rev = m[(m.series == "yt_ad_revenue") & (m.period == "FY")].set_index("year").value
    q = m[(m.series == "yt_ad_revenue") & m.period.str.startswith("Q")]
    q = q.assign(y=q.year.astype(int)).pivot_table(index="y", columns="period", values="value")
    shorts = m[(m.series == "shorts_daily_views") & (m.unit == "billions_per_day")].groupby("year").value.max()
    ypp = m[(m.series == "ypp_channels") & (m.unit == "count")]
    ypp = ypp.assign(y=ypp.period.str[:4].astype(int)).groupby("y").value.max()
    out += ["### The platform, from YouTube and Alphabet only", "",
            "| year | YouTube ad revenue | Q1 vs the Q4 before | Shorts daily views | partner channels |",
            "| ---: | ---: | ---: | ---: | ---: |"]
    for y in sorted(set(int(v) for v in rev.index) | set(int(v) for v in q.index)):
        drop = ""
        if y in q.index and y - 1 in q.index and pd.notna(q.loc[y].get("Q1")) and pd.notna(q.loc[y - 1].get("Q4")):
            drop = f"{q.loc[y, 'Q1'] / q.loc[y - 1, 'Q4'] - 1:+.0%}"
        r = f"${rev[y]:.1f}B" if y in rev.index else "—"
        sv = f"{shorts[y]:.0f}B+" if y in shorts.index else ""
        yp = f"{ypp[y]/1e6:.0f}M+" if y in ypp.index else ""
        out.append(f"| {y} | {r} | {drop} | {sv} | {yp} |")
    out.append("")

    # 4 — creators, newest first
    # one line per creator: their latest long-form RPM, so no single channel fills the table
    show = (c[c.metric == "rpm"].sort_values(["year", "as_of"], ascending=False)
            .drop_duplicates("creator"))
    out += ["### Creators' own disclosures", "",
            f"{len(c)} rows from {c.creator.nunique()} creators, each linked to the creator's own "
            f"post. Below is each creator's latest RPM; every row (CPM, CTR, Shorts, earlier "
            f"years) is in `data/<year>/creators.csv`.", "",
            "| year | creator | niche | metric | value | period | source |",
            "| ---: | --- | --- | --- | ---: | --- | --- |"]
    for r in show.itertuples():
        v = r.point if r.point == r.point else (r.low + r.high) / 2 if r.low == r.low else r.high
        val = money(v) if r.point == r.point else rng(r.low if r.low == r.low else r.high, r.high)
        out.append(f"| {r.year} | {r.creator} | {r.niche} | {r.metric} | {val} | {r.period} | "
                   f"[link]({r.source_url}) |")
    out.append("")

    text = README.read_text()
    new = re.sub(r"(<!-- tables:start -->\n).*?(<!-- tables:end -->)",
                 lambda mm: mm.group(1) + "\n".join(out) + "\n" + mm.group(2), text, flags=re.S)
    assert new != text or "<!-- tables:start -->" in text, "README has no tables markers"
    README.write_text(new)
    print(f"  README tables: {len(now)} niches in {latest}, {len(yrs)} years, {len(c)} creator rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
