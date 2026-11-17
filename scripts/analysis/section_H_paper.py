"""Section H (EXPLORATORY): the straightening fix and the traffic light on PHOTOS OF PRINTED PAPER (pages H01-H20). Rules fixed BEFORE any page was chosen: docs/plan/analysis_plan_changes.md, 2026-11-14 (night).
  python -I scripts/analysis/section_H_paper.py [set_name]        set_name defaults to H (first phone); H2 = optional second phone. Refuses to run twice per set.
Photos matched to pages by file-name order (2 per page, straight first): the digitised files are named like the photos (sorted).
Primary (one test): V2 (straightened) against V0 (photo as it is) on the 40 photos; bad = no usable heart rate OR wrong (> 5 bpm, cleaned measure; reference = PTB-XL 100 Hz lead II);
exact McNemar, alpha 0.05; 'confirmed on printed paper' only if bad falls AND p < 0.05. Traffic light, PR and axis are descriptive (same frozen methods and rules as before, no retuning)."""
import glob
import os
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.stats import binomtest

warnings.filterwarnings("ignore")
ROOT = "D:/Capstone Project/"
PH = ROOT + "results/paper_h/"
OUT = ROOT + "results/analysis/"
sys.path.insert(0, ROOT + "safeguard")
sys.path.insert(0, ROOT + "demo")
import ecg_traffic_light as T  # noqa: E402
import axis_deg as AXD  # noqa: E402
import pr_interval as PRI  # noqa: E402

SET = sys.argv[1] if len(sys.argv) > 1 else "H"


def hr_clean(sig, fs=1000):
    import neurokit2 as nk
    x = nk.ecg_clean(sig, sampling_rate=fs, method="neurokit")
    p, _ = nk.ecg_peaks(x, sampling_rate=fs)
    return float(np.nanmean(nk.ecg_rate(p, sampling_rate=fs, desired_length=len(sig))))


def wilson(k, n, z=1.96):
    if n == 0:
        return "n/a"
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return f"{k}/{n} ({100 * p:.0f}%, 95% CI {100 * (c - h):.0f}-{100 * (c + h):.0f}%)"


def md(t):
    h = "| " + " | ".join(map(str, t.columns)) + " |\n|" + "---|" * len(t.columns) + "\n"
    return h + "\n".join("| " + " | ".join(str(z) for z in r) + " |" for r in t.itertuples(index=False))


if __name__ == "__main__":
    out_csv = OUT + f"sectionH_{SET}_all.csv"
    if os.path.exists(out_csv) and "--force" not in sys.argv:
        sys.exit("The test was already run once for this set (rule: run ONCE).")
    import wfdb
    sel = pd.read_csv(PH + "selected_h_20.csv")
    x12 = pd.read_csv(ROOT + "data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
    ddir = PH + f"photos_dig_{SET}/"
    stems = sorted({os.path.basename(f).split("__")[0] for f in glob.glob(ddir + "*__V0.npz")})
    assert len(stems) == 40, len(stems)
    page = {s: sel.page[i // 2] for i, s in enumerate(stems)}
    shot = {s: ("straight" if i % 2 == 0 else "angled") for i, s in enumerate(stems)}
    eid = dict(zip(sel.page, sel.ecg_id))
    ref = {}
    for pg in sel.page:
        rec = wfdb.rdrecord(PH + f"source_records/{pg}")
        ref[pg] = hr_clean(rec.p_signal[:, rec.sig_name.index("II")], rec.fs)
    rows = []
    for s in stems:
        for v in ("V0", "V2"):
            z = T.load_npz(ddir + f"{s}__{v}.npz")
            sig = np.asarray(z["II"], float)
            sig = sig[np.isfinite(sig)] / 1000.0
            try:
                hr = hr_clean(sig) if len(sig) > 10 else np.nan
            except Exception:
                hr = np.nan
            chk = T.check(z)
            pr_ms = axis = np.nan
            if v == "V2":
                try:
                    pr_ms = PRI.pr_from_leads(z)
                except Exception:
                    pass
                try:
                    axis = AXD.axis_from_leads(z)
                except Exception:
                    pass
            rr_cv = (chk.get("features") or {}).get("rr_cv", np.nan)
            rows.append(dict(photo=s, page=page[s], shot=shot[s], variant=v, dig_hr=hr, gt_hr=ref[page[s]], light=chk["light"], rr_cv=rr_cv, pr_ms=pr_ms, axis_deg=axis,
                             ref_pr=x12.loc[eid[page[s]], "PR_Int_Global"], ref_axis=x12.loc[eid[page[s]], "R_AxisFrontal_Global"]))
    d = pd.DataFrame(rows)
    d["none"] = d.dig_hr.isna()
    d["wrong"] = ~d.none & ((d.dig_hr - d.gt_hr).abs() > 5)
    d["bad"] = d.none | d.wrong
    d.to_csv(out_csv, index=False)
    b0 = d[d.variant == "V0"].set_index("photo").bad
    b2 = d[d.variant == "V2"].set_index("photo").bad.reindex(b0.index)
    worse, better = int((b2 & ~b0).sum()), int((~b2 & b0).sum())
    p = binomtest(worse, worse + better, 0.5).pvalue if worse + better else 1.0
    verdict = "confirmed on printed paper" if (b2.sum() < b0.sum() and p < 0.05) else "not confirmed"
    prim = pd.DataFrame([dict(bad_original_V0=int(b0.sum()), bad_straightened_V2=int(b2.sum()), newly_bad=worse, newly_good=better, p_exact=round(p, 5), verdict=verdict)])
    summ = d.groupby("variant").agg(photos=("bad", "size"), no_usable_hr=("none", "sum"), wrong=("wrong", "sum"), bad=("bad", "sum")).reset_index()
    by_shot = d.groupby(["variant", "shot"]).agg(photos=("bad", "size"), bad=("bad", "sum")).reset_index()
    lights = []
    for v in ("V0", "V2"):
        x = d[d.variant == v]
        for lt in ("GREEN", "AMBER", "RED"):
            y = x[x.light == lt]
            lights.append(dict(variant=v, light=lt, photos=len(y), no_usable_hr=int(y.none.sum()), wrong=int(y.wrong.sum()), bad=wilson(int(y.bad.sum()), len(y))))
    lights = pd.DataFrame(lights)
    v2 = d[d.variant == "V2"]
    pr = v2[(v2.light == "GREEN") & (v2.rr_cv <= 0.12) & v2.pr_ms.notna() & v2.ref_pr.notna()]
    ax = v2[v2.axis_deg.notna()]
    dpr = (pr.pr_ms - pr.ref_pr)
    dax = ((ax.axis_deg - ax.ref_axis + 180) % 360) - 180
    desc = pd.DataFrame([
        dict(measure="PR interval (V2, GREEN, rr_cv<=0.12)", photos=len(pr), typical_error=f"{dpr.abs().median():.1f} ms" if len(pr) else "n/a", within_40ms=f"{100 * (dpr.abs() <= 40).mean():.0f}%" if len(pr) else "n/a",
             bias=f"{dpr.mean():+.1f} ms" if len(pr) else "n/a"),
        dict(measure="Frontal axis (V2, all with a value)", photos=len(ax), typical_error=f"{dax.abs().median():.1f} deg" if len(ax) else "n/a", within_40ms=f"{100 * (dax.abs() <= 30).mean():.0f}% within 30 deg" if len(ax) else "n/a",
             bias=f"{dax.mean():+.1f} deg" if len(ax) else "n/a")])
    L = [f"# Section H ({SET}): straightening and the traffic light on PHOTOS OF PRINTED PAPER (EXPLORATORY)", "",
         "*Generated by `scripts/analysis/section_H_paper.py`. Rules fixed before any page was chosen (docs/plan/analysis_plan_changes.md, 2026-11-14 night). 20 printed pages, 2 photos each (straight, angled), one phone. "
         "bad = no usable heart rate or wrong (> 5 bpm, cleaned measure). The two photos of a page are not independent. PR and axis are descriptive, with the frozen methods and no retuning.*", "",
         "## Primary: V2 (straightened) against V0 (photo as it is), exact paired test", "", md(prim), "", "## Both variants", "", md(summ), "", "## By shot", "", md(by_shot), "",
         "## Traffic lights (frozen safeguard, not retrained)", "", md(lights), "", "## PR interval and frontal axis on the straightened photos (descriptive)", "", md(desc), ""]
    open(OUT + f"SECTION_H_{SET}.md", "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L))
