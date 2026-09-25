#!/usr/bin/env python3
"""Turn the private triangulation sources into this repo's own niche RPM index.

    python3 examples/build_index.py          # maintainer only: needs triangulation/

**Why the index exists at all.** Nearly every published RPM-by-niche table sits behind terms
that forbid redistribution, so this repository cannot print their numbers. It can print its
own. This script reads those tables from `triangulation/` (git-ignored, never committed),
and writes one `maintainer_estimate` row per niche and year into `<year>/benchmarks.csv`.
Each row states how many independent publishers it was checked against. It never names them
or carries their values.

**The rules, and the trap each one closes:**

- **Two publishers or nothing.** One table is that publisher's number reworded, not an
  estimate. A niche-year with a single publisher is left out.
- **A stale copy counts once.** Several blogs reprint the same figures every year with only
  the year changed (one table carried identical values from 2022 to 2025). A value a
  publisher already gave for that niche in an earlier year is dropped, so a reprint cannot
  pass for a second year of evidence.
- **RPM only.** CPM is the advertiser's price and RPM is the creator's pay. The ratio
  between them varies more than 2x across channels (see chart-rpm-vs-cpm), so converting one
  into the other would invent a number.
- **Verified creator disclosures are one extra vote.** Every public `creator_report` RPM
  for that niche and year is pooled into a single voter called "creator disclosures". They
  are independent of the blogs, but one channel's month is noisy, so all of them together
  get the same single vote as one publisher.
- **A neighbouring year only when a year falls short.** If a niche-year has fewer than two
  voters, voters from the year before and after are allowed in, and `locator` says so. Old
  years are thin (most pre-2022 tables are one-off articles), and a labelled window is
  more honest than leaving the year blank or pretending one source is a consensus.
- **The range is the middle of the sources, not their envelope.** The low end is the median
  of the sources' lows and the high end is the median of their highs, both rounded to $0.50.
  An envelope would let the most extreme publisher set every range.

Rows written by hand (a creator report, an open-licence row) are left untouched. Only
`maintainer_estimate` rows are rewritten.
"""
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import load  # noqa: E402

REPO = load.REPO
TRI = REPO / "triangulation"
MIN_PUBLISHERS = 2


def private_rows():
    frames = [pd.read_csv(f) for f in sorted(TRI.glob("backfill_*.csv"))]
    frames += [pd.read_csv(f) for f in sorted(TRI.glob("[0-9][0-9][0-9][0-9]/benchmarks.csv"))]
    d = pd.concat(frames, ignore_index=True)
    d = d[(d.metric == "rpm") & d.niche.notna() & ~d.niche.isin(["shorts_all", "unknown", "unspecified"])]
    d["lo"] = d.low.fillna(d.point)
    d["hi"] = d.high.fillna(d.point)
    d = d.dropna(subset=["lo", "hi"])
    d["year"] = d.year.astype(int)
    # a stale copy counts once: keep the first year a publisher gave this exact range
    d = d.sort_values("year").drop_duplicates(["publisher", "niche", "lo", "hi"], keep="first")
    c = load.creators()
    c = c[(c.metric == "rpm") & c.niche.notna()].assign(publisher="creator disclosures")
    c["lo"] = c.low.fillna(c.point)
    c["hi"] = c.high.fillna(c.point)
    return pd.concat([d, c[["year", "niche", "publisher", "lo", "hi"]]], ignore_index=True)


def half(v):
    return round(v * 2) / 2


def main():
    if not TRI.exists():
        print("  triangulation/ is not here; only the maintainer can rebuild the index")
        return 1
    d = private_rows()
    # one vote per publisher per niche-year: its own median, so a table with three
    # sub-niche rows for "tech" does not outvote a table with one
    per = d.groupby(["year", "niche", "publisher"]).agg(lo=("lo", "median"), hi=("hi", "median"))
    per = per.reset_index()
    rows = []
    for (year, niche) in sorted(set(zip(per.year, per.niche)) | {
            (y + k, n) for y, n in zip(per.year, per.niche) for k in (-1, 1)}):
        for window, label in ((0, "same year"), (1, f"window {year-1}-{year+1}")):
            v = per[(per.niche == niche) & ((per.year - year).abs() <= window)]
            # the year itself must have a voter, or a window would invent a year
            if (per[(per.niche == niche) & (per.year == year)]).empty:
                break
            used = sorted(set(int(t) for t in v.year))
            v = v.groupby("publisher").agg(lo=("lo", "median"), hi=("hi", "median"))
            if len(v) >= MIN_PUBLISHERS:
                if window:          # name the years actually borrowed, not the ones allowed
                    label = f"pooled {used[0]}-{used[-1]}"
                rows.append(dict(year=year, niche=niche, n=len(v), lo=v.lo.median(),
                                 hi=v.hi.median(), window=label))
                break
    g = pd.DataFrame(rows)
    written = 0
    for year, rows in g.groupby("year"):
        out = pd.DataFrame({
            "year": year, "as_of": "2026-09-25", "metric": "rpm", "niche": rows.niche,
            "geo": "mostly US", "low": rows.lo.map(half), "high": rows.hi.map(half),
            "point": None, "currency": "USD", "unit": "per_1000_views",
            "basis": "maintainer_estimate", "publisher": "q3dresearch/youtube-cpm",
            "source_url": "https://github.com/q3dresearch/youtube-cpm",
            "locator": [f"triangulated against {r.n} voters, {r.window}" for r in rows.itertuples()],
            "notes": "median of sources' lows and highs; sources not named (terms forbid redistribution)",
        })
        f = REPO / str(year) / "benchmarks.csv"
        f.parent.mkdir(exist_ok=True)
        keep = pd.read_csv(f) if f.exists() else pd.DataFrame(columns=load.BENCH)
        keep = keep[keep.basis != "maintainer_estimate"]
        pd.concat([keep, out]).to_csv(f, index=False)
        written += len(out)
        print(f"  {year}: {len(out)} niches  " + ", ".join(
            f"{r.niche} ${half(r.lo):g}-{half(r.hi):g} (n={r.n}{'' if r.window == 'same year' else ', ±1y'})" for r in rows.itertuples()))
    print(f"  wrote {written} maintainer_estimate rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
