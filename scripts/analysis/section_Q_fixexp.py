"""Section Q (EXPLORATORY; rules fixed beforehand in docs/plan/analysis_plan_changes.md 2026-11-10 'Simple-fix experiment'):
do simple preparations (V1 enlarge, V2 straighten, V3 straighten + enlarge) reduce failures on the 60 own-phone photos?
Usage: python -I scripts/analysis/section_Q_fixexp.py <kaggle_output_dir>   (folder with results_fixexp.csv, fixexp_variants.csv, fixexp_digitized_12lead/)
Primary: per variant, bad = no usable heart rate OR wrong (> 5 bpm, cleaned measure) on all 60 photos; exact paired test vs the original (V0), Holm over 3 variants.
Words: 'improves' only if bad falls AND Holm p < 0.05; 'worsens' if bad rises AND Holm p < 0.05; else 'no clear change'."""
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


def holm(ps):
    ps = np.array(ps, float)
    o = np.argsort(ps)
    adj = np.empty_like(ps)
    run = 0
    for r, i in enumerate(o):
        run = max(run, (len(ps) - r) * ps[i])
        adj[i] = min(1.0, run)
    return adj


def md(t):
    h = "| " + " | ".join(map(str, t.columns)) + " |\n|" + "---|" * len(t.columns) + "\n"
    return h + "\n".join("| " + " | ".join(str(z) for z in r) + " |" for r in t.itertuples(index=False))


if __name__ == "__main__":
    O = pd.read_csv(OUT + "sectionO_ownphotos_scored.csv")           # V0: original photos (Section O)
    O["photo"] = O.variant_id
    O["big"] = O.img_w > 3000
    ref = O.set_index("photo").gt_hr_clean.to_dict()
    L0 = pd.read_csv(OUT + "sectionP_own_lights_labels.csv").set_index("variant_id").light.to_dict()
    var = pd.read_csv(RES + "/fixexp_variants.csv")
    r = pd.read_csv(RES + "/results_fixexp.csv").merge(var, on="variant_id")
    assert len(r) == 180, len(r)
    rows = []
    for v in r.itertuples():
        path = f"{RES}/fixexp_digitized_12lead/{v.variant_id}.npz"
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
    d["gt_hr_clean"] = d.photo.map(ref)
    d["none"] = d.dig_hr_clean.isna()
    d["wrong"] = ~d.none & ((d.dig_hr_clean - d.gt_hr_clean).abs() > 5)
    d["bad"] = d.none | d.wrong
    base = O[["photo", "shot", "none", "wrong_c", "big"]].copy()
    base["wrong"] = base.wrong_c & ~base.none
    base["bad"] = base.none | base.wrong
    base["variant"] = "V0_original"
    base["light"] = base.photo.map(L0)
    allv = pd.concat([base[["photo", "variant", "none", "wrong", "bad", "light"]], d[["photo", "variant", "none", "wrong", "bad", "light"]]], ignore_index=True)
    allv = allv.merge(O[["photo", "shot", "big"]], on="photo")
    allv["group"] = np.where((allv.shot == "B_angled") & ~allv.big, "angled + small (15)", "other photos (45)")
    # primary
    b0 = base.set_index("photo").bad
    prim, ps = [], []
    for vn in ("V1_enlarge", "V2_straighten", "V3_straighten_big"):
        x = d[d.variant == vn].set_index("photo").bad.reindex(b0.index)
        worse, better = int((x & ~b0).sum()), int((~x & b0).sum())
        p = binomtest(worse, worse + better, 0.5).pvalue if worse + better else 1.0
        ps.append(p)
        prim.append(dict(variant=vn, bad_original=int(b0.sum()), bad_variant=int(x.sum()), newly_bad=worse, newly_good=better, p_exact=round(p, 4)))
    ph = holm(ps)
    for i, rw in enumerate(prim):
        rw["p_holm"] = round(ph[i], 4)
        rw["verdict"] = ("improves" if (rw["bad_variant"] < rw["bad_original"] and ph[i] < 0.05) else "worsens" if (rw["bad_variant"] > rw["bad_original"] and ph[i] < 0.05) else "no clear change")
    prim = pd.DataFrame(prim)
    sec = allv.groupby(["variant", "group"]).agg(photos=("bad", "size"), no_usable_hr=("none", "sum"), wrong=("wrong", "sum"), bad=("bad", "sum")).reset_index()
    sec["with_output_wrong_rate"] = sec.apply(lambda r_: "n/a", axis=1)
    sec = sec.drop(columns="with_output_wrong_rate")
    lights = allv.groupby(["variant", "light"]).size().unstack(fill_value=0).reindex(columns=["GREEN", "AMBER", "RED"], fill_value=0).reset_index()
    found = d.groupby("variant").page_found.sum().reset_index().rename(columns={"page_found": "page_found_of_60"})
    prim.to_csv(OUT + "sectionQ_primary.csv", index=False)
    sec.to_csv(OUT + "sectionQ_by_group.csv", index=False)
    lights.to_csv(OUT + "sectionQ_lights.csv", index=False)
    allv.to_csv(OUT + "sectionQ_all_variants.csv", index=False)
    Ltxt = ["# Section Q (EXPLORATORY): simple fixes for angled / low-resolution photos of a screen\n",
            "*Generated by `scripts/analysis/section_Q_fixexp.py`. Rules fixed beforehand (docs/plan/analysis_plan_changes.md, 2026-11-10). 60 photos (30 pages x straight/angled), one phone, one screen. V0 = original photos (Section O). 'bad' = no usable heart rate or wrong (> 5 bpm, cleaned).*\n",
            "## Primary: all 60 photos, exact paired test against the original, Holm over 3 variants\n", md(prim) + "\n",
            "## Photos by group (angled + small = the worst case seen in Section O)\n", md(sec) + "\n", "## Traffic lights of the digitised signal\n", md(lights) + "\n",
            "## Page found (V2/V3 rely on finding the page)\n", md(found) + "\n"]
    open(OUT + "SECTION_Q.md", "w", encoding="utf-8").write("\n".join(Ltxt))
    pd.set_option("display.width", 250)
    print(prim.to_string(index=False)); print(); print(sec.to_string(index=False)); print(); print(lights.to_string(index=False)); print(); print(found.to_string(index=False))
