# Rejected charts, kept so the same mistake is not made twice

| chart | what it fails at |
| --- | --- |
| `niche-index-bands.svg` | One horizontal row per niche with a thin band per year stacked inside it. Time is on the wrong axis: to see whether a niche rose or fell, the eye has to compare ten slivers a few pixels tall instead of following a line. Pale early years were nearly invisible. Replaced by `niche-lines.svg` (time on x, one line per niche) and `niche-quadrant.svg` (which niche to enter). |
| `rpm-vs-cpm.svg` | A single-channel case study. It diagnoses why one kids-skewed channel's RPM fell (CPM up, CTR steady, monetized share down), but no reader can make a decision from one channel. Its one transferable number, that creators keep 0.23–0.51 of CPM as RPM, is carried into the unit-economics plate as a conversion caveat. Script kept as `examples/negative-chart-rpm-vs-cpm.py`. |
