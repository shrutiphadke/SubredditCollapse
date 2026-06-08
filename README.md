# Subreddit Death Trajectory — Feature Explorer

An interactive dashboard for inspecting how subreddit features evolve across the
community lifespan, grouped by empirically-derived **death trajectory type**.
Built for social-psychology collaborators to explore aggregated patterns without
touching the raw 160 MB dataset.

## What it shows

For any of the **35 features** (engagement, moderation, network structure, LIWC
language measures), the dashboard plots the **mean trajectory** across 100 lifespan
buckets, with filters for:

- **Trajectory type** (7 types: rise_fall, Growth_stability_abrupt_death, etc.) — toggle on/off
- **Time alignment** — absolute lifespan (bucket 0–99) or aligned to the death bucket
  (0 = death, negative = buckets before death)
- **Moderation** — all communities / known mods only / unknown mods only
- **Uncertainty band** — ±2 SE of the mean, ±1 SD across communities, or none
- **Cluster detail** — split each type into its constituent sub-clusters (50 total)

There are also **two view modes** (top-left toggle):

- **Aggregate** — pooled mean trajectories across all selected communities (the default).
- **Top 10 subs** — individual feature trajectories for the 10 best-documented subreddits
  within a chosen trajectory type, ranked by count of non-missing feature values (tie-broken
  by total contributors), with the type's pooled mean overlaid as a bold reference line.

Hover any point for the exact mean and the number of communities contributing.

## How it works (and why it's fast)

The raw file is `4,032 subreddits × 100 buckets × 35 features`. Rather than ship that,
`prepare_data.py` pre-aggregates the data into **sufficient statistics** — count, sum,
and sum-of-squares of each feature, per (cluster × moderation × bucket × alignment).

The browser recombines these on the fly. Because sums and sums-of-squares are additive,
**any filter combination yields the exact pooled mean and a valid standard-deviation /
standard-error band** — identical to what you'd get computing over the raw rows. The
shipped `data.json` is ~11 MB (4.3 MB gzipped), so it loads quickly and runs entirely
client-side.

## Deploy to GitHub Pages

1. Create a repository (or use an existing one).
2. Commit `index.html`, `data.json`, and `top_subs.json` to the repo root (or a `/docs` folder).
3. In **Settings → Pages**, set the source to your branch and the folder
   (root or `/docs`).
4. Visit `https://<user>.github.io/<repo>/`.

That's it — no build step, no server. The dashboard is a single static HTML file
plus the data JSON.

> **Tip:** GitHub Pages serves `.gz` files but most setups don't auto-negotiate them.
> The plain `data.json` works everywhere. If you want the smaller transfer, configure
> your host to serve `data.json.gz` with `Content-Encoding: gzip`, or just keep `data.json`.

## Regenerating the data

If the underlying CSV changes, re-run:

```bash
pip install pandas
python prepare_data.py path/to/final_aggregated_data.csv
```

This writes a fresh `data.json` next to `index.html`.

## Files

| File | Purpose |
|------|---------|
| `index.html` | The dashboard (open directly or via Pages) |
| `data.json` | Pre-aggregated sufficient statistics (aggregate view) |
| `top_subs.json` | Per-bucket trajectories for the top-10 subreddits per type (individual view) |
| `prepare_data.py` | Regenerates `data.json` and `top_subs.json` from the raw CSV |
