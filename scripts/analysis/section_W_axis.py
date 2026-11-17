"""Section W (EXPLORATORY): frontal QRS AXIS from the digitised limb leads. Rules fixed BEFORE any axis code ran: docs/plan/analysis_plan_changes.md, 2026-11-14 (night, later still).
  python -I scripts/analysis/section_W_axis.py --dev       1,000 unused ORIGINAL recordings (page-layout windows): choose one candidate (nothing is fitted), write sectionW_frozen.json
  python -I scripts/analysis/section_W_axis.py --test      ONCE on the fresh pages F001-F100: (a) original signal in the photo windows, (b) digitised clean page
  python -I scripts/analysis/section_W_axis.py --confirm   ONCE on the 100 own-phone photos (straightened primary)
Reference = 12SL R_AxisFrontal_Global (degrees, wrapped to -180..180). Angles are never rescaled or offset."""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import glob
import importlib.util
import json
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = "D:/Capstone Project/"
R = ROOT + "results/"
OUT = R + "analysis/"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT + path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


U = _load("section_U", "scripts/analysis/section_U_pr_qrs.py")
T = U.T
LEADS, LAYOUT, ms2n = T.LEADS, T.LAYOUT, T.ms2n
ANG = {"I": 0.0, "II": 60.0, "III": 120.0, "aVF": 90.0, "aVL": -30.0, "aVR": -150.0}
DEFS = ("area", "dominant", "sum")
CANDS = [f"axis_{n}_{d}" for n in ("2", "6") for d in DEFS]
RULE = dict(median=10.0, within=0.9, bias=10.0, cat=0.9, share=0.9)
TOL_WITHIN = 30.0


def wrap(a):
    return (np.asarray(a, float) + 180.0) % 360.0 - 180.0


def category(a):
    a = wrap(a)
    return np.where(a < -30, "left", np.where(a > 90, "right", "normal"))


def net_values(mb, fs):
    e = U.edges(mb, fs, 0.05)
    if not e:
        return None
    on, off = e
    b0, b1 = on - ms2n(T.BASE_FROM_MS, fs), on - ms2n(T.BASE_TO_MS, fs)
    if b0 < 0 or b1 <= b0 or off - on < 3:
        return None
    y = mb - np.median(mb[b0:b1])
    seg = y[on:off + 1]
    return dict(area=float(seg.sum() / fs * 1000.0), dominant=float(seg[int(np.argmax(np.abs(seg)))]), sum=float(seg.max() + seg.min()))


def measure_record(leads, fs, windows, rpk):
    res = {c: np.nan for c in CANDS}
    if len(rpk) < 3:
        return res
    rr = float(np.median(np.diff(rpk)) * 1000.0 / fs)
    tmax = min(T.TMAX_MS, T.RR_FRAC * rr)
    if tmax < 250:
        return res
    nets = {}
    for L in ANG:
        a, b = windows.get(L, (0, 0))
        if b - a <= 0 or L not in leads:
            continue
        mb, n = T.median_beat(leads[L], fs, a, b, rpk, tmax)
        if mb is None:
            continue
        v = net_values(mb, fs)
        if v:
            nets[L] = v
    for d in DEFS:
        if "I" in nets and "aVF" in nets:
            res[f"axis_2_{d}"] = float(np.degrees(np.arctan2(nets["aVF"][d], nets["I"][d])))
        if len(nets) >= 4:
            Ls = list(nets)
            A = np.array([[np.cos(np.radians(ANG[L])), np.sin(np.radians(ANG[L]))] for L in Ls])
            bvec = np.array([nets[L][d] for L in Ls])
            xy, *_ = np.linalg.lstsq(A, bvec, rcond=None)
            res[f"axis_6_{d}"] = float(np.degrees(np.arctan2(xy[1], xy[0])))
    return res


def metrics(meas, ref):
    meas, ref = np.asarray(meas, float), np.asarray(ref, float)
    has = np.isfinite(ref)
    share = float(np.isfinite(meas[has]).mean()) if has.any() else 0.0
    ok = np.isfinite(meas) & has
    if ok.sum() < 5:
        return dict(n=int(ok.sum()), share=share)
    e = wrap(meas[ok] - ref[ok])
    ae = np.abs(e)
    rad = np.radians(e)
    return dict(n=int(ok.sum()), share=share, median_abs=float(np.median(ae)), p90_abs=float(np.percentile(ae, 90)), within=float((ae <= TOL_WITHIN).mean()),
                bias=float(np.degrees(np.arctan2(np.sin(rad).mean(), np.cos(rad).mean()))), cat=float((category(meas[ok]) == category(ref[ok])).mean()))


def meets(m):
    return bool(m.get("n", 0) >= 5 and m["median_abs"] <= RULE["median"] and m["within"] >= RULE["within"] and abs(m["bias"]) <= RULE["bias"] and m["cat"] >= RULE["cat"] and m["share"] >= RULE["share"])


def boot_ci(meas, ref, seed=0):
    meas, ref = np.asarray(meas, float), np.asarray(ref, float)
    ok = np.isfinite(meas) & np.isfinite(ref)
    e = np.abs(wrap(meas[ok] - ref[ok]))
    rng = np.random.default_rng(seed)
    b = [np.median(e[rng.choice(len(e), len(e))]) for _ in range(1000)]
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


# ------------------------------------------------------------------ development
def dev_task(a):
    rec, rel500 = a
    orig = T.read_all_leads(rel500)
    fs = 500
    win = {L: (int(LAYOUT[L][0] * fs), int(LAYOUT[L][1] * fs) - 1) for L in LEADS}
    row = dict(record=rec)
    row.update(measure_record(orig, fs, win, T.lead2_rpeaks(orig["II"], fs)))
    return row


def run_dev():
    sel = pd.read_csv(R + "fresh/selected_dev_1000.csv")
    x12 = pd.read_csv(ROOT + "data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
    tasks = [(r.record, r.filename_lr.replace("records100", "records500").replace("_lr", "_hr")) for _, r in sel.iterrows()]
    with ProcessPoolExecutor(max_workers=10) as ex:
        rows = list(ex.map(dev_task, tasks, chunksize=8))
    d = pd.DataFrame(rows).merge(sel[["record", "ecg_id"]], on="record")
    d["ref"] = wrap(d.ecg_id.map(x12["R_AxisFrontal_Global"]).values)
    d.to_csv(OUT + "sectionW_dev.csv", index=False)
    rows_ = []
    for c in CANDS:
        m = metrics(d[c].values, d["ref"].values)
        rows_.append(dict(cand=c, **m))
    t = pd.DataFrame(rows_)
    elig = t[t.share >= 0.9].sort_values(["within", "median_abs"], ascending=[False, True])
    ch = elig.iloc[0]
    frozen = dict(candidate=str(ch.cand), table=t.round(4).to_dict(orient="records"))
    json.dump(frozen, open(OUT + "sectionW_frozen.json", "w"), indent=1)
    L = ["# Section W development (1,000 unused original recordings, page-layout windows)", "",
         "Reference = 12SL R_AxisFrontal_Global. Nothing is fitted. Selection rule: among candidates with a value for at least 90%, the largest share within 30 degrees; ties by the smaller median error.", "",
         "| Candidate | With a value | n | Median abs error (deg) | 90th pct | Within 30 deg | Mean error (deg) | Category agreement |", "|---|---|---|---|---|---|---|---|"]
    for _, r in t.iterrows():
        L.append(f"| {r.cand} | {100 * r.share:.0f}% | {int(r.n)} | {r.median_abs:.1f} | {r.p90_abs:.1f} | {100 * r.within:.0f}% | {r.bias:+.1f} | {100 * r['cat']:.0f}% |")
    L += ["", f"**Frozen candidate: {ch.cand}**"]
    open(OUT + "SECTION_W_dev.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


# ------------------------------------------------------------------ test and confirmation
def test_task(a):
    page, npz, rel500 = a
    z = np.load(npz)
    dig = {L: np.asarray(z[L], float) / 1000.0 for L in LEADS}
    win = {L: T.longest_run(np.isfinite(dig[L])) for L in LEADS}
    row = dict(page=page)
    try:
        for k, v in measure_record(dig, 1000, win, T.lead2_rpeaks(dig["II"], 1000)).items():
            row[f"dig_{k}"] = v
    except Exception as e:
        row["error_dig"] = str(e)[:80]
    try:
        orig = T.read_all_leads(rel500)
        win5 = {L: (a_ // 2, b_ // 2) for L, (a_, b_) in win.items()}
        for k, v in measure_record(orig, 500, win5, T.lead2_rpeaks(orig["II"], 500)).items():
            row[f"orig_{k}"] = v
    except Exception as e:
        row["error_orig"] = str(e)[:80]
    return row


def fmt(label, meas, ref):
    m = metrics(meas, ref)
    if m.get("n", 0) < 5:
        return f"| {label} | n/a | n/a | n/a | n/a | n/a | n/a | n/a | does not meet |", False
    lo, hi = boot_ci(meas, ref)
    v = meets(m)
    return (f"| {label} | {int(np.isfinite(np.asarray(meas)).sum())} ({100 * m['share']:.0f}%) | {m['median_abs']:.1f} ({lo:.1f} to {hi:.1f}) | {m['p90_abs']:.1f} | {100 * m['within']:.0f}% | {m['bias']:+.1f} | "
            f"{100 * m['cat']:.0f}% | **{'meets' if v else 'does not meet'}** |"), v


HEAD = ["| Measurement | With a value | Median abs error deg (95% CI) | 90th pct | Within 30 deg | Mean error deg | Category agreement | Rule |", "|---|---|---|---|---|---|---|---|"]


def run_test():
    fr = json.load(open(OUT + "sectionW_frozen.json"))
    out_csv = OUT + "sectionW_test_per_page.csv"
    if os.path.exists(out_csv) and "--force" not in sys.argv:
        sys.exit("The test was already run once (rule: run ONCE).")
    c = fr["candidate"]
    sel = pd.read_csv(R + "fresh/selected_fresh_100.csv")
    x12 = pd.read_csv(ROOT + "data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
    tasks = []
    for _, r in sel.iterrows():
        p = R + f"fresh/fresh_digitized_12lead/{r.page}.npz"
        if not os.path.exists(p):
            sys.exit(f"missing digitised page {r.page}")
        tasks.append((r.page, p, r.filename_lr.replace("records100", "records500").replace("_lr", "_hr")))
    with ProcessPoolExecutor(max_workers=10) as ex:
        rows = list(ex.map(test_task, tasks, chunksize=4))
    m = pd.DataFrame(rows).merge(sel[["page", "ecg_id", "record"]], on="page")
    m["ref"] = wrap(m.ecg_id.map(x12["R_AxisFrontal_Global"]).values)
    m["axis_orig"] = m[f"orig_{c}"]
    m["axis_dig"] = m[f"dig_{c}"]
    m.to_csv(out_csv, index=False)
    ra, va = fmt("(a) original signal in the photo windows", m.axis_orig.values, m.ref.values)
    rb, vb = fmt("(b) digitised clean page", m.axis_dig.values, m.ref.values)
    L = ["# Section W: frontal QRS axis, tested ONCE on 100 fresh pages (EXPLORATORY)", "",
         f"Rules fixed before any axis code ran (`docs/plan/analysis_plan_changes.md`, 2026-11-14 night, later still). Frozen candidate: **{c}**; no calibration. The acceptance rule is the assistant's proposal, **not approved by the guide**: "
         "median absolute circular error <= 10 degrees, at least 90% within 30 degrees, |mean error| <= 10 degrees, at least 90% category agreement (left < -30, normal, right > 90) and at least 90% of pages with a value, for BOTH (a) and (b).", "",
         "Reference = 12SL R_AxisFrontal_Global.", ""] + HEAD + [ra, rb, "",
         f"**Axis validated on the fresh pages: {'YES' if va and vb else 'NO'}** ((a) meets: {va}, (b) meets: {vb}).", ""]
    ok = np.isfinite(m.axis_dig) & np.isfinite(m.axis_orig)
    if ok.sum() >= 5:
        e = np.abs(wrap(m.axis_dig[ok] - m.axis_orig[ok]))
        L.append(f"- What the photo adds (digitised vs the same method on the original): median {np.median(e):.1f} degrees, 90th percentile {np.percentile(e, 90):.1f}.")
    L += ["", "## Limits", "", "- 12SL is an algorithm; drawn pages digitised on this computer (not photos); one digitiser. Paced rhythms and very low voltage give unreliable axes in every program.",
          "- Nothing is shown to patients unless the fresh test AND the phone-photo confirmation both say YES. Never a verdict word, only degrees."]
    open(OUT + "SECTION_W.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


def confirm_task(a):
    key, npz = a
    z = np.load(npz)
    dig = {L: np.asarray(z[L], float) / 1000.0 for L in LEADS}
    win = {L: T.longest_run(np.isfinite(dig[L])) for L in LEADS}
    row = dict(key=key)
    try:
        row.update(measure_record(dig, 1000, win, T.lead2_rpeaks(dig["II"], 1000)))
    except Exception as e:
        row["error"] = str(e)[:80]
    return row


def run_confirm():
    fr = json.load(open(OUT + "sectionW_frozen.json"))
    out_csv = OUT + "sectionW_confirm_per_photo.csv"
    if os.path.exists(out_csv) and "--force" not in sys.argv:
        sys.exit("The confirmation was already run once (rule: run ONCE).")
    c = fr["candidate"]
    x12 = pd.read_csv(ROOT + "data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
    meta, tasks = {}, []
    p_map, q_map = pd.read_csv(R + "ownphotos/pages_mapping.csv"), pd.read_csv(R + "ownphotos2/pages_mapping.csv")
    p_photos = sorted(os.path.basename(f)[:-4] for f in glob.glob(R + "ownphotos/kaggle_out/ownphotos_digitized_12lead/**/*.npz", recursive=True))
    q_photos = sorted(os.path.basename(f).split("__")[0] for f in glob.glob(R + "ownphotos2/confirm_out/confirm_digitized_12lead/**/*__V0_original.npz", recursive=True))
    for sname, photos, pm, v0, v2 in [
            ("P", p_photos, p_map, R + "ownphotos/kaggle_out/ownphotos_digitized_12lead/{p}.npz", R + "ownphotos/fixexp_out/fixexp_digitized_12lead/{p}__V2_straighten.npz"),
            ("Q", q_photos, q_map, R + "ownphotos2/confirm_out/confirm_digitized_12lead/{p}__V0_original.npz", R + "ownphotos2/confirm_out/confirm_digitized_12lead/{p}__V2_straighten.npz")]:
        for k, ph in enumerate(photos):
            page = pm.iloc[k // 2]
            for ver, tmpl in (("V0", v0), ("V2", v2)):
                path = tmpl.format(p=ph)
                if os.path.exists(path):
                    key = f"{sname}|{ph}|{ver}"
                    meta[key] = dict(set=sname, photo=ph, version=ver, page=page["page"], ecg_id=int(page.ecg_id), shot="straight" if k % 2 == 0 else "angled")
                    tasks.append((key, path))
    with ProcessPoolExecutor(max_workers=10) as ex:
        rows = list(ex.map(confirm_task, tasks, chunksize=2))
    d = pd.DataFrame(rows)
    for col in ("set", "photo", "version", "page", "ecg_id", "shot"):
        d[col] = d.key.map(lambda k: meta[k][col])
    d["ref"] = wrap(d.ecg_id.map(x12["R_AxisFrontal_Global"]).values)
    d["axis"] = d[c]
    d.to_csv(out_csv, index=False)
    L = ["# Section W confirmation: the frozen axis method on own-phone photos (EXPLORATORY)", "",
         f"Candidate {c}, no calibration; rules fixed before the run. One phone, one screen; the two photos of a page are not independent.", ""] + HEAD
    for lab, x in [("V2 straightened, all (primary)", d[d.version == "V2"]), ("V0 original, all", d[d.version == "V0"]),
                   ("V2 straight shots", d[(d.version == "V2") & (d.shot == "straight")]), ("V2 angled shots", d[(d.version == "V2") & (d.shot == "angled")])]:
        L.append(fmt(lab, x.axis.values, x.ref.values)[0])
    open(OUT + "SECTION_W_confirm.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    if "--dev" in sys.argv:
        run_dev()
    elif "--test" in sys.argv:
        run_test()
    elif "--confirm" in sys.argv:
        run_confirm()
    else:
        print(__doc__)
