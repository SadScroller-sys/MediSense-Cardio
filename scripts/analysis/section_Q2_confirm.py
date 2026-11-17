"""Section Q2 (CONFIRMATION of the straightening fix on 40 NEW photos; rules fixed before the photos existed: docs/plan/analysis_plan_changes.md, 2026-11-11).
Usage: python -I scripts/analysis/section_Q2_confirm.py <kaggle_output_dir>   (folder with results_confirm.csv, confirm_variants.csv, confirm_digitized_12lead/)
Photos are matched to pages by file-name order: 2 photos per page (A straight, B angled), pages Q01...Q20 (the match was checked by eye on all 40 headers).
Primary (one test): V2 (straighten) vs V0 (original) on 40 photos; bad = no usable heart rate OR wrong (> 5 bpm, cleaned measure); exact paired test (McNemar), alpha 0.05.
Words: 'confirmed' only if bad falls AND p < 0.05; otherwise 'not confirmed'. V1 and V3 are secondary and descriptive (no claim)."""
import os
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.stats import binomtest

warnings.filterwarnings("ignore")
RES = sys.argv[1].rstrip("/\\")
ROOT = "D:/Capstone Project/"
OUT = ROOT + "results/analysis/"
sys.path.insert(0, ROOT + "safeguard")
import ecg_traffic_light as T


def hr_clean(sig, fs=1000):
    import neurokit2 as nk
    x = nk.ecg_clean(sig, sampling_rate=fs, method="neurokit")
    p, _ = nk.ecg_peaks(x, sampling_rate=fs)
    return float(np.nanmean(nk.ecg_rate(p, sampling_rate=fs, desired_length=len(sig))))


def md(t):
    h = "| " + " | ".join(map(str, t.columns)) + " |\n|" + "---|" * len(t.columns) + "\n"
    return h + "\n".join("| " + " | ".join(str(z) for z in r) + " |" for r in t.itertuples(index=False))


def wilson(k, n, z=1.96):
    if n == 0:
        return "n/a"
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return f"{k}/{n} ({100 * p:.0f}%, 95% CI {100 * (c - h):.0f}-{100 * (c + h):.0f}%)"


if __name__ == "__main__":
    import wfdb
    var = pd.read_csv(RES + "/confirm_variants.csv")
    r = pd.read_csv(RES + "/results_confirm.csv").merge(var, on="variant_id")
    assert len(r) == 160 and r.photo.nunique() == 40, (len(r), r.photo.nunique())
    stems = sorted(r.photo.unique())
    page = {s: f"Q{i // 2 + 1:02d}" for i, s in enumerate(stems)}
    shot = {s: ("A_straight" if i % 2 == 0 else "B_angled") for i, s in enumerate(stems)}
    big = var.drop_duplicates("photo").set_index("photo")
    ref = {}
    for pg in sorted(set(page.values())):
        rec = wfdb.rdrecord(ROOT + f"results/ownphotos2/source_records/{pg}")
        ref[pg] = hr_clean(rec.p_signal[:, rec.sig_name.index("II")], rec.fs)
    # original photo size (small = 1440x1080) taken from the V0 rows
    v0 = var[var.variant == "V0_original"].set_index("photo")
    rows = []
    for v in r.itertuples():
        path = f"{RES}/confirm_digitized_12lead/{v.variant_id}.npz"
        hr, light = np.nan, "RED"
        if os.path.exists(path):
            z = T.load_npz(path)
            s = np.asarray(z["II"], float)
            s = s[np.isfinite(s)] / 1000.0
            try:
                hr = hr_clean(s) if len(s) > 10 else np.nan
            except Exception:
                hr = np.nan
            light = T.check(z)["light"]
        rows.append(dict(variant_id=v.variant_id, photo=v.photo, variant=v.variant, page_found=v.page_found, dig_hr_clean=hr, light=light))
    d = pd.DataFrame(rows)
    d["page"] = d.photo.map(page)
    d["shot"] = d.photo.map(shot)
    d["small"] = d.photo.map(lambda p: bool(v0.loc[p, "img_w"] < 3000))
    d["gt_hr_clean"] = d.page.map(ref)
    d["none"] = d.dig_hr_clean.isna()
    d["wrong"] = ~d.none & ((d.dig_hr_clean - d.gt_hr_clean).abs() > 5)
    d["bad"] = d.none | d.wrong
    d.to_csv(OUT + "sectionQ2_all_variants.csv", index=False)
    b0 = d[d.variant == "V0_original"].set_index("photo").bad
    prim = []
    for vn in ("V2_straighten", "V1_enlarge", "V3_straighten_big"):
        x = d[d.variant == vn].set_index("photo").bad.reindex(b0.index)
        worse, better = int((x & ~b0).sum()), int((~x & b0).sum())
        p = binomtest(worse, worse + better, 0.5).pvalue if worse + better else 1.0
        verdict = ("confirmed" if (x.sum() < b0.sum() and p < 0.05) else "not confirmed") if vn == "V2_straighten" else "secondary, descriptive"
        prim.append(dict(variant=vn + (" (PRIMARY)" if vn == "V2_straighten" else ""), bad_original=int(b0.sum()), bad_variant=int(x.sum()), newly_bad=worse, newly_good=better, p_exact=round(p, 4), verdict=verdict))
    prim = pd.DataFrame(prim)
    summ = d.groupby("variant").agg(photos=("bad", "size"), no_usable_hr=("none", "sum"), wrong=("wrong", "sum"), bad=("bad", "sum"), page_found=("page_found", "sum")).reset_index()
    by_shot = d.groupby(["variant", "shot"]).agg(photos=("bad", "size"), no_usable_hr=("none", "sum"), wrong=("wrong", "sum"), bad=("bad", "sum")).reset_index()
    by_size = d.assign(size=np.where(d.small, "small (1440x1080)", "large (4096x3072)")).groupby(["variant", "size"]).agg(photos=("bad", "size"), bad=("bad", "sum")).reset_index()
    lights = []
    for vn in ("V0_original", "V2_straighten"):
        x = d[d.variant == vn]
        for lt in ("GREEN", "AMBER", "RED"):
            y = x[x.light == lt]
            lights.append(dict(variant=vn, light=lt, photos=len(y), no_usable_hr=int(y.none.sum()), wrong=int(y.wrong.sum()), bad=wilson(int(y.bad.sum()), len(y))))
    lights = pd.DataFrame(lights)
    # pooled with the first 60 photos (descriptive only)
    Q = pd.read_csv(OUT + "sectionQ_all_variants.csv")
    pooled = []
    for a, b in (("V0_original", "V0_original"), ("V2_straighten", "V2_straighten")):
        n1 = len(Q[Q.variant == a]); k1 = int(Q[Q.variant == a].bad.sum())
        n2 = len(d[d.variant == b]); k2 = int(d[d.variant == b].bad.sum())
        pooled.append(dict(variant=a, first_60=f"{k1}/{n1}", new_40=f"{k2}/{n2}", pooled_100=wilson(k1 + k2, n1 + n2)))
    pooled = pd.DataFrame(pooled)
    prim.to_csv(OUT + "sectionQ2_primary.csv", index=False)
    summ.to_csv(OUT + "sectionQ2_summary.csv", index=False)
    by_shot.to_csv(OUT + "sectionQ2_by_shot.csv", index=False)
    lights.to_csv(OUT + "sectionQ2_lights.csv", index=False)
    Ltxt = ["# Section Q2: confirmation of the straightening fix on 40 NEW photos (20 new pages)\n",
            "*Generated by `scripts/analysis/section_Q2_confirm.py`. Rules fixed before the photos existed (docs/plan/analysis_plan_changes.md, 2026-11-11). Methods unchanged from Section Q. bad = no usable heart rate or wrong (> 5 bpm, cleaned). One phone, one screen, 20 recordings; the two photos of one page are not independent.*\n",
            "## Primary: V2 (straighten) against the original photo, exact paired test\n", md(prim) + "\n", "## All variants\n", md(summ) + "\n",
            "## By shot\n", md(by_shot) + "\n", "## By original photo size\n", md(by_size) + "\n", "## Traffic lights (V0 and V2; the safeguard was not retrained)\n", md(lights) + "\n",
            "## Pooled with the first 60 photos (descriptive only; the first 60 were used to design the fix)\n", md(pooled) + "\n"]
    open(OUT + "SECTION_Q2.md", "w", encoding="utf-8").write("\n".join(Ltxt))
    pd.set_option("display.width", 250)
    for t in (prim, summ, by_shot, by_size, lights, pooled):
        print(t.to_string(index=False)); print()
