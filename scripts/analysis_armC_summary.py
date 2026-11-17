"""Arm C summary: no-output, wrong-HR rates with Wilson CI, SNR, exact paired test vs clean page (McNemar exact, Holm)."""
import numpy as np, pandas as pd
from scipy.stats import binomtest
d = pd.read_csv('results/armC/results_armC.csv')
d['none'] = d.dig_hr.isna()
d['wrong5'] = d.diff_bpm.abs() > 5
d['wrong10'] = d.diff_bpm.abs() > 10
d['bad'] = d.none | d.wrong5          # no answer or wrong by >5 bpm
def wilson(k, n, z=1.96):
    p = k/n; c = (p + z*z/(2*n))/(1+z*z/n); h = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))/(1+z*z/n)
    return c-h, c+h
order = list(d.axis.unique())
clean = d[d.axis == order[0]].set_index('record')
rows = []; pv = []
for a in order:
    g = d[d.axis == a].set_index('record')
    n = len(g); k_bad = int(g.bad.sum()); k_none = int(g.none.sum()); k_w5 = int(g.wrong5.sum()); k_w10 = int(g.wrong10.sum())
    lo, hi = wilson(k_bad, n)
    b = int(((~clean.bad) & g.bad.reindex(clean.index)).sum()); c = int((clean.bad & (~g.bad.reindex(clean.index))).sum())
    p = np.nan if a == order[0] else (binomtest(b, b+c, 0.5).pvalue if b+c > 0 else 1.0)
    pv.append(p)
    rows.append(dict(capture=a, n=n, no_output=k_none, wrong_gt5bpm=k_w5, wrong_gt10bpm=k_w10, bad_total=k_bad,
                     bad_pct=round(100*k_bad/n, 1), ci95=f'{100*lo:.0f}-{100*hi:.0f}%',
                     median_snr_db=round(g.snr_aligned_db.median(), 1), worse_than_clean=b, better_than_clean=c, p_exact=p))
o = pd.DataFrame(rows)
m = o.p_exact.notna().sum(); idx = o.p_exact.dropna().sort_values().index; run = 0
for i, ix in enumerate(idx):
    run = max(run, min(1, (m-i)*o.loc[ix, 'p_exact'])); o.loc[ix, 'p_holm'] = run
o['p_exact'] = o.p_exact.round(3); o['p_holm'] = o.p_holm.round(3)
o.to_csv('results/armC/armC_summary.csv', index=False)
print(o.to_string(index=False))
