#!/usr/bin/env python3
"""Read every year folder into one frame, and refuse rows that break the schema.

    python3 examples/load.py        # validate, print counts per year and metric

**Why a validator and not a pipeline.** This repo is updated by hand whenever a new data
point turns up: a creator posts an AdSense screenshot, or a publisher reissues its niche
table. A typo in a hand-typed row is the most likely failure, and it fails silently: an RPM
typed into the CPM column still plots. So every chart script loads through here, and a bad
row stops the chart instead of bending it.
"""
import pathlib
import sys

import pandas as pd

REPO = pathlib.Path(__file__).resolve().parents[1]

BENCH = ["year", "as_of", "metric", "niche", "geo", "low", "high", "point", "currency",
         "unit", "basis", "publisher", "source_url", "locator", "notes"]
CREATOR = ["year", "as_of", "creator", "metric", "niche", "geo", "low", "high", "point",
           "currency", "unit", "period", "views", "revenue", "basis", "publisher",
           "source_url", "locator", "notes"]
METRICS = {"rpm", "cpm", "cpv_brand", "shorts_rpm", "impressions_ctr"}
BASES = {"maintainer_estimate", "creator_report", "open_source", "platform_report"}


def _read(name, cols):
    frames = []
    for f in sorted(REPO.glob(f"[0-9][0-9][0-9][0-9]/{name}")):
        df = pd.read_csv(f, dtype={"as_of": str})
        missing = [c for c in cols if c not in df.columns]
        assert not missing, f"{f.relative_to(REPO)} is missing columns {missing}"
        df["file"] = str(f.relative_to(REPO))
        frames.append(df[cols + ["file"]])
    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=cols)
    bad = out[~out.metric.isin(METRICS)]
    assert bad.empty, f"unknown metric: {bad[['file', 'metric']].drop_duplicates().values.tolist()}"
    bad = out[~out.basis.isin(BASES)]
    assert bad.empty, f"unknown basis: {bad[['file', 'basis']].drop_duplicates().values.tolist()}"
    nothing = out[out[["low", "high", "point"]].isna().all(axis=1)]
    assert nothing.empty, f"rows with no value: {nothing[['file', 'niche']].values.tolist()}"
    inverted = out[out.low > out.high]
    assert inverted.empty, f"low > high: {inverted[['file', 'niche']].values.tolist()}"
    # A range is carried by its midpoint and a point by itself, so both can share one axis.
    out["mid"] = out.point.where(out.point.notna(), (out.low + out.high) / 2)
    return out


def benchmarks():
    return _read("benchmarks.csv", BENCH)


def creators():
    return _read("creators.csv", CREATOR)


def macro():
    return pd.read_csv(REPO / "macro" / "macro.csv")


def main():
    b, c = benchmarks(), creators()
    print(f"  benchmarks {len(b)} rows, {b.publisher.nunique()} publishers")
    print(b.pivot_table(index="year", columns="metric", values="niche", aggfunc="count",
                        fill_value=0).to_string())
    print(f"\n  creators {len(c)} rows, {c.creator.nunique()} creators")
    if len(c):
        print(c.groupby("year").size().to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())


# One colour per niche, shared by every chart, so a niche reads the same across plates.
# Ordered roughly by pay so neighbours on the ladder are not neighbours in hue.
NICHE_COLOUR = {
    "finance": "#1f5c4c", "business": "#5b6fb0", "tech": "#c0503e", "health": "#8a5aa8",
    "education": "#c08a3e", "travel": "#3a8fb7", "beauty": "#d46a9f", "lifestyle": "#7a8f3a",
    "food": "#a0522d", "gaming": "#4a4a8a", "entertainment": "#6b6b6b", "all": "#aca89a",
}
