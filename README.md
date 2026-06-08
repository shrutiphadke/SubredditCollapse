# Subreddit Death Trajectory — Feature Explorer

An interactive dashboard for inspecting how subreddit features evolve across the
community lifespan, grouped by empirically-derived **death trajectory type**.
Built for social-psychology collaborators to explore aggregated patterns without
touching the raw 160 MB dataset.

## What it shows

For any of the **35 features** (engagement, moderation, network structure, LIWC
language measures), the dashboard plots the **mean trajectory** across 100 lifespan
buckets, with filters for:

- **Trajectory type** (7 types: rise_fall, Growth_stability_abrupt_death, etc.) — toggle on/off.
  Each type shows a small **sparkline of its canonical shape** so the trajectory the name refers
  to is always visible while selecting. The shape is the type's mean activity (comments + posts)
  trajectory, per-subreddit min–max normalized, averaged, and lightly smoothed.
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


| `data.json` | Pre-aggregated sufficient statistics (aggregate view) |
| `top_subs.json` | Per-bucket trajectories for the top-10 subreddits per type (individual view) |
| `prepare_data.py` | Regenerates `data.json` and `top_subs.json` from the raw CSV |
