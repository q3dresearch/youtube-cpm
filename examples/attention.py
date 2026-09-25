#!/usr/bin/env python3
"""Attention half-life: how fast a video's daily views fall, fitted per video.

    python3 examples/attention.py          # downloads the source once, writes data/attention/halflife.csv

**Source.** *Trending YouTube Video Statistics* (Kaggle, datasnaek), **CC0: Public Domain**.
It is a daily record of YouTube's US trending list, 2017-11-14 to 2018-06-14: 40,949
snapshots of 6,351 videos, each with its cumulative view count on that day. Kaggle needs
an account to download, so this fetches a byte-identical public mirror and checks its hash.
The 62 MB file is git-ignored. Only the per-video fit is committed.

**Method.** A video's daily views on day *t* are its view count on day *t* minus day
*t-1*, keeping only consecutive-day pairs. For each video with four or more such days,
log(daily views) is regressed on age, and half-life = ln 2 / -slope. A video whose daily
views did not fall gets no half-life (`half_life_days` empty) instead of an infinite one.

**What it cannot say.** A video is seen only while it trends, so this measures the
*viral* part of a video's life. A search-driven evergreen video, which never trends and
decays slowly for years, is invisible here. The figures describe what happens after a
video catches on, not a typical upload.
"""
import hashlib
import pathlib
import sys
import urllib.request

import numpy as np
import pandas as pd

REPO = pathlib.Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "attention" / "raw" / "USvideos.csv"
MIRROR = "https://media.githubusercontent.com/media/kristenauriemma/595Project/main/USvideos.csv"
SHA256 = "09b4eb71295752705e472ebefeac9d2afab4177b7a818af795dea62744a48eb2"
CATEGORY = {1: "film", 2: "autos", 10: "music", 15: "pets", 17: "sports", 19: "travel",
            20: "gaming", 22: "people_blogs", 23: "comedy", 24: "entertainment", 25: "news",
            26: "howto", 27: "education", 28: "science_tech", 29: "nonprofit", 43: "shows"}


def fetch():
    if not RAW.exists():
        RAW.parent.mkdir(parents=True, exist_ok=True)
        print(f"  downloading {MIRROR}")
        urllib.request.urlretrieve(MIRROR, RAW)
    h = hashlib.sha256(RAW.read_bytes()).hexdigest()
    assert h == SHA256, f"USvideos.csv hash {h} is not the pinned CC0 release; refusing to fit"


def main():
    fetch()
    d = pd.read_csv(RAW)
    d["t"] = pd.to_datetime(d.trending_date, format="%y.%d.%m")
    d["pub"] = pd.to_datetime(d.publish_time).dt.tz_localize(None)
    d = d.sort_values(["video_id", "t"]).drop_duplicates(["video_id", "t"])
    d["age"] = (d.t - d.pub).dt.total_seconds() / 86400
    d["daily"] = d.groupby("video_id").views.diff()
    d["gap"] = d.groupby("video_id").t.diff().dt.days
    d = d[(d.gap == 1) & (d.daily > 0)]

    rows = []
    for vid, g in d.groupby("video_id"):
        if len(g) < 4:
            continue
        slope = np.polyfit(g.age, np.log(g.daily), 1)[0]
        rows.append(dict(
            video_id=vid, category=CATEGORY.get(int(g.category_id.iloc[0]), "other"),
            days_observed=len(g), first_age_days=round(g.age.min(), 2),
            first_daily_views=int(g.daily.iloc[0]), last_views=int(g.views.iloc[-1]),
            half_life_days=round(np.log(2) / -slope, 3) if slope < 0 else None))
    out = pd.DataFrame(rows)
    f = REPO / "data" / "attention" / "halflife.csv"
    out.to_csv(f, index=False)
    dec = out.dropna(subset=["half_life_days"])
    print(f"  wrote {f.relative_to(REPO)}: {len(out)} videos, {len(dec)} decaying, "
          f"median half-life {dec.half_life_days.median():.2f} days")
    return 0


if __name__ == "__main__":
    sys.exit(main())
