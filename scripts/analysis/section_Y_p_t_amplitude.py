"""Section Y (EXPLORATORY): P-wave and T-wave AMPLITUDE in lead II against 12SL. Rules fixed BEFORE any code ran: docs/plan/analysis_plan_changes.md, 2026-11-14 (afternoon).
ST segment, P duration and T duration are NOT attempted (the commercial algorithms do not agree on them; reasons in the plan entry).
  python -I scripts/analysis/section_Y_p_t_amplitude.py --dev       1,100 development recordings (original signals, page-layout windows): choose a candidate per measurand (5-fold CV, offset only, slope >= 0.8);
                                                                    fit photo offsets once on ~199 digitised clean pages; writes sectionY_frozen.json
  python -I scripts/analysis/section_Y_p_t_amplitude.py --test      ONCE on the sealed pages G001-G100: (a) original signal in the photo windows, (b) digitised clean page
  python -I scripts/analysis/section_Y_p_t_amplitude.py --confirm   ONCE on the 40 phone photos of G001-G020 (straightened, digitised by digitise_new_photos.py)
Reads only saved files. Amplitudes in mV (signed). Difference = measured minus 12SL."""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import ast
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


T = _load("section_T", "scripts/analysis/section_T_better_qt.py")
LEADS, LAYOUT, ms2n = T.LEADS, T.LAYOUT, T.ms2n
# ---- constants fixed in the plan entry ----
P_FROM_MS, P_TO_MS = 250, 30           # P window = [QRS onset - 250, QRS onset - 30] ms
BASE_FROM_MS, BASE_TO_MS = 40, 10      # baseline = PR segment
SMOOTH20_MS = 20
SLOPE_MIN, TAIL_MIN_N = 0.8, 5
THREE_P, THREE_T = ("I", "II", "aVF"), ("I", "II", "V5")
CANDS = {"p": ["PA", "PB", "PC"], "t": ["TA", "TB", "TC"]}
REF = {"p": "P_Amp_II", "t": "T_Amp_II"}
RULE = {"p": (0.03, 0.06, 0.015), "t": (0.05, 0.10, 0.03)}                # median abs, 90% within, |bias| (mV)
TAILS = {"p": [("ref P <= 0.05", lambda r: r <= 0.05, 0.03), ("ref P >= 0.20", lambda r: r >= 0.20, 0.03)],
         "t": [("ref T <= -0.10", lambda r: r <= -0.10, 0.05), ("ref T >= 0.50", lambda r: r >= 0.50, 0.05)]}
NAMES = {"p": "P-wave amplitude, lead II", "t": "T-wave amplitude, lead II"}


def lead_amps(mb, fs):
    """From one median beat (R anchor at PRE_MS): P amplitude (PA, PB) and T amplitude (TA, TB), mV, signed, from the PR-segment baseline."""
    out = dict(PA=np.nan, PB=np.nan, TA=np.nan, TB=np.nan)
    f = T.beat_features(mb, fs)
    if not np.isfinite(f["onset"]):
        return out
    r0 = ms2n(T.PRE_MS, fs)
    on = r0 + ms2n(f["onset"], fs)
    b0, b1 = on - ms2n(BASE_FROM_MS, fs), on - ms2n(BASE_TO_MS, fs)
    if b0 < 0 or b1 <= b0:
        return out
    y = mb - np.median(mb[b0:b1])
    p0, p1 = max(0, on - ms2n(P_FROM_MS, fs)), on - ms2n(P_TO_MS, fs)
    if p1 - p0 >= ms2n(60, fs):
        seg = y[p0:p1]
        out["PA"] = float(seg[int(np.argmax(np.abs(seg)))])
        n = max(3, ms2n(SMOOTH20_MS, fs) | 1)
        sm = np.convolve(y, np.ones(n) / n, mode="same")[p0:p1]
        out["PB"] = float(sm[int(np.argmax(np.abs(sm)))])
    t0, t1 = r0 + ms2n(T.T_START_MS, fs), len(mb) - 1
    if t1 - t0 >= ms2n(60, fs):
        tpk = t0 + int(np.argmax(np.abs(y[t0:t1 + 1])))
        if tpk <= t1 - ms2n(20, fs):
            w = ms2n(20, fs)
            out["TA"] = float(y[tpk])
            out["TB"] = float(np.mean(y[max(0, tpk - w):tpk + w + 1]))
    return out


def measure_record(leads, fs, windows, rpk):
    res = {c: np.nan for p in CANDS for c in CANDS[p]}
    res.update(rr_ms=np.nan, rr_cv=np.nan)
    if len(rpk) < 3:
        return res
    rr = np.diff(rpk) * 1000.0 / fs
    res["rr_ms"] = float(np.median(rr))
    res["rr_cv"] = float(np.std(rr) / np.mean(rr))
    tmax = min(T.TMAX_MS, T.RR_FRAC * res["rr_ms"])
    if tmax < 250:
        return res
    per = {}
    for L in set(THREE_P) | set(THREE_T):
        a, b = windows.get(L, (0, 0))
        if b - a <= 0 or L not in leads:
            continue
        mb, n = T.median_beat(leads[L], fs, a, b, rpk, tmax)
        if mb is not None:
            per[L] = lead_amps(mb, fs)
    if "II" in per:
        for k in ("PA", "PB", "TA", "TB"):
            res[k] = per["II"][k]
    v = [per[L]["PA"] for L in THREE_P if L in per and np.isfinite(per[L]["PA"])]
    if len(v) >= 2:
        res["PC"] = float(np.median(v))
    v = [per[L]["TA"] for L in THREE_T if L in per and np.isfinite(per[L]["TA"])]
    if len(v) >= 2:
        res["TC"] = float(np.median(v))
    return res


# ------------------------------------------------------------------ statistics
def slope_of(meas, ref):
    ok = np.isfinite(meas) & np.isfinite(ref)
    return float(np.polyfit(ref[ok], meas[ok], 1)[0]) if ok.sum() >= 5 else float("nan")


def sign_check(meas, ref):
    m = np.isfinite(meas) & np.isfinite(ref) & (np.abs(ref) >= 0.10)
    n = int(m.sum())
    return n, (float((np.sign(meas[m]) == np.sign(ref[m])).mean()) if n else float("nan"))


def row_for(label, p, meas, ref, check_tails=True):
    tm, tw, tb = RULE[p]
    has = np.isfinite(ref)
    diff = meas - ref
    ok = np.isfinite(diff)
    s = T.stats(pd.Series(diff[ok]), tol_within=tw)
    share = float(np.isfinite(meas[has]).mean()) if has.any() else 0.0
    if s.get("n", 0) < 5:
        return f"| {label} | n/a | | | | | | | | does not meet |", False
    slope = slope_of(meas, ref)
    tails, tails_ok = [], True
    for lab, fn, tol in TAILS[p]:
        m = fn(ref) & ok
        n = int(m.sum())
        me = float(diff[m].mean()) if n else float("nan")
        tails.append(f"{lab}: n={n}, mean error {me:+.3f}" + ("" if n >= TAIL_MIN_N else " (too few)"))
        if n >= TAIL_MIN_N and abs(me) > tol:
            tails_ok = False
    sg = ""
    sg_ok = True
    if p == "t":
        n, a = sign_check(meas, ref)
        sg = f"sign agreement {100 * a:.0f}% (n={n})" if n else "sign n/a"
        sg_ok = (n < TAIL_MIN_N) or a >= 0.9
    base = bool(s["n"] >= 5 and s["median_abs"] <= tm and s["within"] >= 0.9 and abs(s["bias"]) <= tb and share >= 0.9)
    allok = bool(base and slope >= SLOPE_MIN and (tails_ok if check_tails else True) and sg_ok)
    return (f"| {label} | {int(np.isfinite(meas).sum())} of {len(meas)} ({100 * share:.0f}%) | {s['median_abs']:.3f} ({s['median_abs_ci'][0]:.3f} to {s['median_abs_ci'][1]:.3f}) | {s['p90_abs']:.3f} | "
            f"{s['bias']:+.3f} ({s['bias_ci'][0]:+.3f} to {s['bias_ci'][1]:+.3f}) | {100 * s['within']:.0f}% | {slope:.2f} | {'; '.join(tails)}{'; ' + sg if sg else ''} | **{'meets' if allok else 'does not meet'}** |"), allok


HEAD = ["| Measurement | With a value | Median abs diff mV (95% CI) | 90th pct | Bias mV (95% CI) | Within tolerance | Slope on 12SL | Tails / sign | Rule |", "|---|---|---|---|---|---|---|---|---|"]


def fit_c(raw, ref):
    ok = np.isfinite(raw) & np.isfinite(ref)
    return float(np.mean(ref[ok] - raw[ok])) if ok.sum() >= 10 else None


# ------------------------------------------------------------------ development
def dev_task(a):
    rec, rel500 = a
    orig = T.read_all_leads(rel500)
    fs = 500
    win = {L: (int(LAYOUT[L][0] * fs), int(LAYOUT[L][1] * fs) - 1) for L in LEADS}
    row = dict(record=rec)
    row.update(measure_record(orig, fs, win, T.lead2_rpeaks(orig["II"], fs)))
    return row


def digitised_dev_pages():
    x12 = pd.read_csv(ROOT + "data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
    ext = pd.read_csv(R + "extension/results_extension.csv")
    sel = pd.read_csv(R + "extension/selected_100.csv").set_index("record")
    files = {os.path.basename(f)[:-4]: f for f in glob.glob(R + "extension/extension_digitized_12lead/**/*.npz", recursive=True)}
    jobs = [(r.variant_id, files[r.variant_id], int(sel.loc[r.record, "ecg_id"])) for _, r in ext[(ext.axis == "clean") & (ext.record != "21205_lr")].iterrows() if r.variant_id in files]
    fr = pd.read_csv(R + "fresh/selected_fresh_100.csv")
    jobs += [(r.page, R + f"fresh/fresh_digitized_12lead/{r.page}.npz", int(r.ecg_id)) for _, r in fr.iterrows()]
    rows = []
    for vid, path, eid in jobs:
        z = np.load(path)
        dig = {L: np.asarray(z[L], float) / 1000.0 for L in LEADS}
        win = {L: T.longest_run(np.isfinite(dig[L])) for L in LEADS}
        row = dict(page=vid, ecg_id=eid)
        row.update(measure_record(dig, 1000, win, T.lead2_rpeaks(dig["II"], 1000)))
        for p in REF:
            row[f"ref_{p}"] = x12.loc[eid, REF[p]]
        rows.append(row)
    return pd.DataFrame(rows)


def run_dev():
    t0 = time.time()
    x12 = pd.read_csv(ROOT + "data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
    s1 = pd.read_csv(R + "fresh/selected_dev_1000.csv")
    s2 = pd.read_csv(R + "fresh/selected_fresh_100.csv")
    sel = pd.concat([s1[["record", "ecg_id", "filename_lr"]], s2[["record", "ecg_id", "filename_lr"]]], ignore_index=True)
    tasks = [(r.record, r.filename_lr.replace("records100", "records500").replace("_lr", "_hr")) for _, r in sel.iterrows()]
    with ProcessPoolExecutor(max_workers=8) as ex:
        rows = list(ex.map(dev_task, tasks, chunksize=8))
    d = pd.DataFrame(rows).merge(sel[["record", "ecg_id"]], on="record")
    for p in REF:
        d[f"ref_{p}"] = d.ecg_id.map(x12[REF[p]])
    d.to_csv(OUT + "sectionY_dev.csv", index=False)
    print("development measured", len(d), "recordings in", round(time.time() - t0), "s", flush=True)
    rng = np.random.default_rng(48)
    fold = rng.permutation(len(d)) % 5
    frozen, L = {}, ["# Section Y development (1,100 development recordings, original signals, page-layout windows)", "",
                     "Offset-only calibration refitted on the training folds. CV = 5-fold by recording. Eligible = a value for at least 90% AND a cross-validated slope on 12SL of at least 0.8. Selection: smallest CV median absolute difference (mV).", ""]
    for p in ("p", "t"):
        ref = d[f"ref_{p}"].values
        rows_ = []
        for c in CANDS[p]:
            raw = d[c].values
            pred = np.full(len(d), np.nan)
            for k in range(5):
                tr, te = fold != k, fold == k
                cc = fit_c(raw[tr], ref[tr])
                pred[te] = raw[te] + (cc if cc is not None else np.nan)
            ok = np.isfinite(pred) & np.isfinite(ref)
            diff = (pred - ref)[ok]
            n_s, a_s = sign_check(pred, ref)
            rows_.append(dict(cand=c, share=float(np.isfinite(raw).mean()), n=int(ok.sum()), cv_median_abs=float(np.median(np.abs(diff))), cv_within=float((np.abs(diff) <= RULE[p][1]).mean()),
                              cv_bias=float(diff.mean()), cv_slope=slope_of(pred, ref), sign=a_s))
        t = pd.DataFrame(rows_)
        elig = t[(t.share >= 0.9) & (t.cv_slope >= SLOPE_MIN)].sort_values("cv_median_abs")
        L += [f"## {NAMES[p]}", "", "| Candidate | With a value | n | CV median abs diff (mV) | CV within tolerance | CV bias | CV slope on 12SL | sign agreement (|ref| >= 0.10) |", "|---|---|---|---|---|---|---|---|"]
        for _, r in t.iterrows():
            L.append(f"| {r.cand} | {100 * r.share:.0f}% | {int(r.n)} | {r.cv_median_abs:.3f} | {100 * r.cv_within:.0f}% | {r.cv_bias:+.3f} | {r.cv_slope:.2f} | {100 * r.sign:.0f}% |")
        if elig.empty:
            frozen[p] = dict(candidate=None, table=t.round(4).to_dict(orient="records"))
            L += ["", "**No candidate is eligible (slope >= 0.8 and 90% with a value). Nothing is frozen for this measurand; it stops here.**", ""]
            continue
        ch = elig.iloc[0]
        frozen[p] = dict(candidate=str(ch.cand), orig_c=fit_c(d[ch.cand].values, ref), table=t.round(4).to_dict(orient="records"))
        L += ["", f"**Frozen candidate: {ch.cand}**; original-signal offset {frozen[p]['orig_c']:+.4f} mV", ""]
    dg = digitised_dev_pages()
    L += [f"## Photo offsets (fitted once on {len(dg)} digitised clean pages: the 99 earlier held-out pages and F001-F100)", ""]
    for p in ("p", "t"):
        if frozen[p].get("candidate"):
            c = frozen[p]["candidate"]
            cc = fit_c(dg[c].values, dg[f"ref_{p}"].values)
            frozen[p]["photo_c"] = cc
            pred = dg[c].values + cc
            diff = pd.Series(pred - dg[f"ref_{p}"].values).dropna()
            frozen[p]["photo_fit_in_sample"] = dict(n=int(len(diff)), median_abs=float(diff.abs().median()), slope=slope_of(pred, dg[f"ref_{p}"].values))
            L.append(f"- {p.upper()}: {c}, photo offset {cc:+.4f} mV; in-sample median abs diff {diff.abs().median():.3f} mV, slope {frozen[p]['photo_fit_in_sample']['slope']:.2f} (for the record only: NOT a test)")
    frozen["written"] = time.strftime("%Y-%m-%d %H:%M")
    json.dump(frozen, open(OUT + "sectionY_frozen.json", "w"), indent=1)
    open(OUT + "SECTION_Y_dev.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
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


def run_test():
    fr = json.load(open(OUT + "sectionY_frozen.json"))
    out_csv = OUT + "sectionY_test_per_page.csv"
    if os.path.exists(out_csv) and "--force" not in sys.argv:
        sys.exit("The test was already run once (rule: run ONCE).")
    sel = pd.read_csv(R + "fresh_g/selected_g_100.csv")
    x12 = pd.read_csv(ROOT + "data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
    tasks = []
    for _, r in sel.iterrows():
        pth = R + f"fresh_g/g_digitized_12lead/{r.page}.npz"
        if not os.path.exists(pth):
            sys.exit(f"missing digitised page {r.page}")
        tasks.append((r.page, pth, r.filename_lr.replace("records100", "records500").replace("_lr", "_hr")))
    with ProcessPoolExecutor(max_workers=8) as ex:
        rows = list(ex.map(test_task, tasks, chunksize=4))
    m = pd.DataFrame(rows).merge(sel[["page", "ecg_id", "record"]], on="page")
    ptb = pd.read_csv(ROOT + "data/ptbxl/ptbxl_database.csv").set_index("ecg_id")
    m["af"] = m.ecg_id.map(lambda e: ("AFIB" in ast.literal_eval(ptb.loc[e, "scp_codes"])) or ("AFLT" in ast.literal_eval(ptb.loc[e, "scp_codes"])))
    L = ["# Section Y: P-wave and T-wave amplitude (lead II), tested ONCE on 100 new sealed pages (EXPLORATORY)", "",
         "Rules fixed before any code ran (`docs/plan/analysis_plan_changes.md`, 2026-11-14 afternoon). Proposal of the assistant, NOT approved by the guide. Difference = measured minus 12SL (mV). "
         "Rule: share with a value >= 90%; slope on 12SL >= 0.8; P: median abs <= 0.03, 90% within 0.06, |bias| <= 0.015, tails (ref P <= 0.05 and >= 0.20) within +-0.03; "
         "T: median abs <= 0.05, 90% within 0.10, |bias| <= 0.03, tails (ref T <= -0.10 and >= 0.50) within +-0.05, sign agreement >= 90% where |ref| >= 0.10. Disclosure: these pages were used before for QRS/QT only.", ""]
    verdicts = {}
    for p in ("p", "t"):
        if not fr[p].get("candidate"):
            L += [f"## {NAMES[p]}", "", "No candidate was frozen in development: not tested.", ""]
            verdicts[p] = (False, False)
            continue
        c = fr[p]["candidate"]
        ref = m.ecg_id.map(x12[REF[p]]).values
        m[f"ref_{p}"] = ref
        m[f"{p}_orig"] = m[f"orig_{c}"] + fr[p]["orig_c"]
        m[f"{p}_dig"] = m[f"dig_{c}"] + fr[p]["photo_c"]
        L += [f"## {NAMES[p]} (frozen: {c})", ""] + HEAD
        ra, oa = row_for("(a) original signal in the photo windows", p, m[f"{p}_orig"].values, ref)
        rb, ob = row_for("(b) digitised clean page", p, m[f"{p}_dig"].values, ref)
        L += [ra, rb, ""]
        verdicts[p] = (oa, ob)
        L += [f"**{NAMES[p]} validated on the new sealed pages: {'YES' if (oa and ob) else 'NO'}** ((a) meets: {oa}, (b) meets: {ob})", ""]
        af = m.af.values
        L += [f"- (b) atrial fibrillation / flutter pages: n = {int(af.sum())}, median abs diff {np.nanmedian(np.abs((m[f'{p}_dig'] - ref)[af])):.3f} mV, bias {np.nanmean((m[f'{p}_dig'] - ref)[af]):+.3f} mV",
              f"- (b) other pages: n = {int((~af).sum())}, median abs diff {np.nanmedian(np.abs((m[f'{p}_dig'] - ref)[~af])):.3f} mV, bias {np.nanmean((m[f'{p}_dig'] - ref)[~af]):+.3f} mV", ""]
    m.to_csv(out_csv, index=False)
    L += ["## Limits", "", "- Drawn pages digitised on this computer (not photos); the phone photos follow separately. 12SL is an algorithm. One digitiser, not fully deterministic. The pages were used before for the QRS/QT test (disclosed in the plan).",
          "- Nothing is shown to patients unless the page test AND the photo confirmation both say YES."]
    open(OUT + "SECTION_Y_test.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


def run_confirm():
    fr = json.load(open(OUT + "sectionY_frozen.json"))
    out_csv = OUT + "sectionY_confirm_per_photo.csv"
    if os.path.exists(out_csv) and "--force" not in sys.argv:
        sys.exit("The confirmation was already run once (rule: run ONCE).")
    sel = pd.read_csv(R + "fresh_g/selected_g_100.csv").set_index("page")
    x12 = pd.read_csv(ROOT + "data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
    files = sorted(glob.glob(R + "fresh_g/photos_digitized_12lead/*__V2_straighten.npz"))
    if len(files) < 2:
        sys.exit("no digitised phone photos found")
    pages = [f"G{i + 1:03d}" for i in range(20)]
    rows = []
    for k, f in enumerate(files):
        page = pages[k // 2]
        z = np.load(f)
        dig = {L: np.asarray(z[L], float) / 1000.0 for L in LEADS}
        win = {L: T.longest_run(np.isfinite(dig[L])) for L in LEADS}
        row = dict(photo=os.path.basename(f).split("__")[0], page=page, shot="straight" if k % 2 == 0 else "angled", ecg_id=int(sel.loc[page, "ecg_id"]))
        row.update(measure_record(dig, 1000, win, T.lead2_rpeaks(dig["II"], 1000)))
        rows.append(row)
    d = pd.DataFrame(rows)
    L = ["# Section Y confirmation: the frozen P and T amplitude methods on the 40 phone photos of G001-G020 (EXPLORATORY)", "",
         "Straightened (V2) photos, matched to pages by file-name order. Same rule as the page test, tails only reported (too few photos). One phone, one screen; the two photos of a page are not independent. "
         "Disclosure: these photos were used before for the QRS/QT confirmation only.", ""]
    for p in ("p", "t"):
        if not fr[p].get("candidate"):
            L += [f"## {NAMES[p]}", "", "No candidate was frozen.", ""]
            continue
        c = fr[p]["candidate"]
        d[f"ref_{p}"] = d.ecg_id.map(x12[REF[p]])
        d[p] = d[c] + fr[p]["photo_c"]
        L += [f"## {NAMES[p]} (frozen: {c})", ""] + HEAD
        for lab, x in [("V2 straightened, all (primary)", d), ("straight shots", d[d.shot == "straight"]), ("angled shots", d[d.shot == "angled"])]:
            L.append(row_for(lab, p, x[p].values, x[f"ref_{p}"].values, check_tails=False)[0])
        L.append("")
    d.to_csv(out_csv, index=False)
    open(OUT + "SECTION_Y_confirm.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
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
