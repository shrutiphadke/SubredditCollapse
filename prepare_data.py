#!/usr/bin/env python3
"""Pre-aggregate the subreddit trajectory CSV into compact sufficient statistics
for the static dashboard. Usage: python prepare_data.py final_aggregated_data.csv"""
import sys, json, gzip, os
import pandas as pd, numpy as np

CSV = sys.argv[1] if len(sys.argv) > 1 else "final_aggregated_data.csv"
OUT = "data.json"  # written to the current working directory, beside index.html

FEATURES = ['total_comments','total_posts','total_no_bot_del_contrib','total_no_bot_del_posts',
 'total_no_bot_del_comments','retained_frac','new_users_frac','avg_post_score','avg_comment_score',
 'avg_comment_reply_latency','avg_post_reply_latency','percent_automod','percent_from_mod',
 'percent_any_mod_mention','density','degree_var','reciprocity','frac_in_2_core','frac_in_max_kcore',
 'posts_with_reply_ratio','comments_with_reply_ratio','gini','toxicity','cogproc','emo_angr',
 'affiliation','emo_pos','emo_neg','you','emo_anx','they','I','we','emo_sad','similarity_score_mean']

REL_MIN = -50  # buckets before death to retain for the death-aligned view

def build(df, align):
    if align == 'abs':
        d, key, idx = df, 'bucket', list(range(100))
    else:
        d = df[(df.rel >= REL_MIN) & (df.rel <= 0)]
        key, idx = 'rel', list(range(REL_MIN, 1))
    pos = {b: i for i, b in enumerate(idx)}
    cells = []
    for (cluster, mod), sub in d.groupby(['cluster', 'has_known_mods']):
        cell = {'cluster': int(cluster), 'Type': sub['Type'].iloc[0], 'mod': bool(mod),
                'n_subs': int(sub['subreddit'].nunique()), 'feats': {}}
        for f in FEATURES:
            vals = sub[[key, f]].dropna()
            if len(vals) == 0:
                cell['feats'][f] = None; continue
            agg = vals.groupby(key)[f].agg(n='count', s='sum', ss=lambda x: float((x**2).sum()))
            n = [0]*len(idx); s = [0.0]*len(idx); ss = [0.0]*len(idx)
            for b, row in agg.iterrows():
                if b in pos:
                    i = pos[b]; n[i] = int(row['n']); s[i] = float(row['s']); ss[i] = float(row['ss'])
            cell['feats'][f] = {'n': n, 's': s, 'ss': ss}
        cells.append(cell)
    return {'idx': idx, 'cells': cells}

def build_top(df):
    """Top 10 subreddits per Type by count of non-missing feature values,
    tie-broken by total contributors. Emits full per-bucket trajectories
    on both alignments for individual-curve inspection."""
    df = df.copy()
    df['_nonna'] = df[FEATURES].notna().sum(axis=1)
    rank = (df.groupby('subreddit')
              .agg(Type=('Type', 'first'), nonna=('_nonna', 'sum'),
                   contrib=('total_no_bot_del_contrib', 'sum'),
                   death=('death_bucket', 'first'))
              .reset_index()
              .sort_values(['nonna', 'contrib'], ascending=False))
    top = rank.groupby('Type').head(10)
    sub = df[df.subreddit.isin(set(top.subreddit))]
    rel_idx = list(range(REL_MIN, 1)); rpos = {b: i for i, b in enumerate(rel_idx)}
    out = {}
    for T, grp in top.groupby('Type'):
        arr = []
        for _, row in grp.iterrows():
            s = sub[sub.subreddit == row.subreddit].sort_values('bucket')
            rec = {'name': row.subreddit, 'death': int(row.death),
                   'nonna': int(row.nonna), 'contrib': float(row.contrib),
                   'abs': {}, 'rel': {}}
            for f in FEATURES:
                a = [None]*100
                for b, v in zip(s.bucket, s[f]):
                    a[int(b)] = None if pd.isna(v) else round(float(v), 5)
                rec['abs'][f] = a
                r = [None]*len(rel_idx)
                for rb, v in zip(s.rel, s[f]):
                    if rb in rpos:
                        r[rpos[rb]] = None if pd.isna(v) else round(float(v), 5)
                rec['rel'][f] = r
            arr.append(rec)
        out[T] = arr
    return {'rel_min': REL_MIN, 'features': FEATURES, 'top': out}

def build_shapes(df, npts=40, smooth_w=7):
    """Canonical per-type activity shape: per-subreddit min-max normalized
    activity (comments+posts), averaged across the type, lightly smoothed,
    resampled to `npts`, and emitted as SVG polyline points in a 100x28 box.
    These are inlined as the SHAPES constant in index.html; this writes a
    standalone shapes.json for reference / re-embedding."""
    d = df.copy()
    d['activity'] = d['total_comments'] + d['total_posts']
    out = {}
    for T, g in d.groupby('Type'):
        piv = g.pivot_table(index='subreddit', columns='bucket',
                            values='activity', aggfunc='mean').reindex(columns=range(100))
        mn = piv.min(axis=1); mx = piv.max(axis=1); rng = (mx - mn).replace(0, np.nan)
        normed = piv.sub(mn, axis=0).div(rng, axis=0)
        m = normed.mean(axis=0).rolling(smooth_w, center=True, min_periods=1).mean()
        m = (m - m.min()) / (m.max() - m.min())
        xs = np.linspace(0, 99, npts)
        ys = np.interp(xs, np.arange(100), m.values)
        W, H, pad = 100, 28, 2
        pts = [f"{pad + i/(npts-1)*(W-2*pad):.1f},{(H-pad) - y*(H-2*pad):.1f}"
               for i, y in enumerate(ys)]
        out[T] = " ".join(pts)
    return out

def main():
    df = pd.read_csv(CSV)
    df['rel'] = df['bucket'] - df['death_bucket']
    sub_types = df.groupby('subreddit')['Type'].first()
    out = {
        'features': FEATURES, 'rel_min': REL_MIN,
        'types': sorted(sub_types.unique().tolist()),
        'type_counts': {k: int(v) for k, v in sub_types.value_counts().items()},
        'abs': build(df, 'abs'), 'rel': build(df, 'rel'),
    }
    def rnd(o):
        if isinstance(o, float): return round(o, 5)
        if isinstance(o, list): return [rnd(x) for x in o]
        if isinstance(o, dict): return {k: rnd(v) for k, v in o.items()}
        return o
    js = json.dumps(rnd(out), separators=(',', ':'))
    with open(OUT, 'w') as fp: fp.write(js)
    with gzip.open(OUT + '.gz', 'wt') as fp: fp.write(js)
    print(f"Wrote {OUT}  ({len(js)/1e6:.1f} MB, {os.path.getsize(OUT+'.gz')/1e6:.1f} MB gzipped)")

    tjs = json.dumps(build_top(df), separators=(',', ':'))
    with open('top_subs.json', 'w') as fp: fp.write(tjs)
    print(f"Wrote top_subs.json  ({len(tjs)/1e6:.1f} MB)")

    shapes = build_shapes(df)
    with open('shapes.json', 'w') as fp: fp.write(json.dumps(shapes, separators=(',', ':')))
    print("Wrote shapes.json  (inline these as the SHAPES constant in index.html if data changes)")

if __name__ == '__main__':
    main()
