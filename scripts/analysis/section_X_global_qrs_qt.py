"""Section X (EXPLORATORY): QRS duration and QT, THIRD attempt: a combined-lead (global activity) method. Rules fixed BEFORE any code ran:
docs/plan/analysis_plan_changes.md, 2026-11-14 (night, third).
  python -I scripts/analysis/section_X_global_qrs_qt.py --dev       1,100 development recordings (1,000 + F001-F100, ORIGINAL signals, page-layout windows): choose a candidate per parameter
                                                                   (5-fold CV, slope >= 0.8 filter); fit the photo offsets once on ~199 digitised clean pages; writes sectionX_frozen.json
  python -I scripts/analysis/section_X_global_qrs_qt.py --test      ONCE on the new sealed pages G001-G100: (a) original signal in the photo windows, (b) digitised clean page
  python -I scripts/analysis/section_X_global_qrs_qt.py --confirm   ONCE on the user's 40 new phone photos of G001-G020 (straightened, digitised by scripts/analysis/digitise_new_photos.py)
One aligned multi-lead median beat is built from the per-lead median beats of Section T (they share the R anchor); QRS and T end are read on the COMBINED activity of all leads."""
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


V = _load("section_V", "scripts/analysis/section_V_qrs_qt_v2.py")      # baselines (attempt 2), offset-only calibration, statistics
T = V.T
LEADS, LAYOUT, ms2n = T.LEADS, T.LAYOUT, T.ms2n
MIN_LEADS = 6
FR = {"3": 0.03, "5": 0.05, "10": 0.10}
PCT = {"05": 0.05, "10": 0.10, "20": 0.20}
QRS_C = [f"qrs_{n}_{f}" for n in ("abs", "euc") for f in FR]
QT_C = [f"qt_thr{p}" for p in PCT] + ["qt_tan"]
BASE = {"qt": "qt_B_tan", "qrs": "qrs_C1_3"}                          # attempt-2 baselines, run for comparison only
CANDS = {"qt": QT_C, "qrs": QRS_C}
RULE = {"qt": (20, 40, 10), "qrs": (10, 20, 5)}
REF = {"qt": "QT_Int_Global", "qrs": "QRS_Dur_Global"}
SLOPE_MIN, TAIL_TOL, TAIL_MIN_N = 0.8, 20.0, 5


# ------------------------------------------------------------------ the combined-lead measurements
def combined_beats(leads, fs, windows, rpk, tmax):
    beats = {}
    for L in LEADS:
        a, b = windows.get(L, (0, 0))
        if b - a <= 0 or L not in leads:
            continue
        mb, n = T.median_beat(leads[L], fs, a, b, rpk, tmax)
        if mb is not None:
            beats[L] = mb
    return beats


def qrs_global(M, fs, f, norm):
    """M: leads x time (all leads share the R anchor at ms2n(300)). Returns (duration ms, onset index, offset index) or None."""
    r0 = ms2n(T.PRE_MS, fs)
    D = np.gradient(M, axis=1) * fs
    Vv = np.abs(D).sum(0) if norm == "abs" else np.sqrt((D ** 2).sum(0))
    lo, hi = max(1, r0 - ms2n(60, fs)), min(M.shape[1] - 2, r0 + ms2n(60, fs))
    ipk = lo + int(np.argmax(Vv[lo:hi + 1]))
    vmax = Vv[ipk]
    if not np.isfinite(vmax) or vmax < 1e-6:
        return None
    i = ipk
    limit = max(r0 - ms2n(150, fs), 1)
    while i > limit and Vv[i] >= f * vmax:
        i -= 1
    j = ipk
    lim = min(r0 + ms2n(150, fs), M.shape[1] - 2)
    while j < lim and Vv[j] >= f * vmax:
        j += 1
    return (j - i) * 1000.0 / fs, i, j


def qt_global(M, fs, onset):
    """Combined distance from the baseline E(t); T end by the 3 threshold rules and by the tangent rule. Returns dict of QT (ms)."""
    out = {c: np.nan for c in QT_C}
    r0 = ms2n(T.PRE_MS, fs)
    b0, b1 = onset - ms2n(T.BASE_FROM_MS, fs), onset - ms2n(T.BASE_TO_MS, fs)
    if b0 < 0 or b1 <= b0:
        return out
    Y = M - np.median(M[:, b0:b1], axis=1, keepdims=True)
    E = np.sqrt((Y ** 2).sum(0))
    t0, t1 = r0 + ms2n(T.T_START_MS, fs), M.shape[1] - 1
    if t1 - t0 < ms2n(60, fs):
        return out
    tpk = t0 + int(np.argmax(E[t0:t1 + 1]))
    if tpk > t1 - ms2n(20, fs) or E[tpk] <= 0:
        return out
    ms = 1000.0 / fs
    for key, p in PCT.items():
        below = np.flatnonzero(E[tpk:] <= p * E[tpk])
        if len(below):
            out[f"qt_thr{key}"] = (tpk + below[0] - onset) * ms
    dE = np.gradient(E) * fs
    k = tpk + int(np.argmin(dE[tpk:min(tpk + ms2n(200, fs), M.shape[1] - 1) + 1]))
    slope = dE[k] / fs
    w = ms2n(30, fs)
    tail = E[tpk:]
    if slope < 0 and len(tail) > w:
        level = float(np.min(np.convolve(tail, np.ones(w) / w, mode="valid")))
        te = k + (level - E[k]) / slope
        if tpk < te <= M.shape[1] - 1 + ms2n(50, fs):
            out["qt_tan"] = (te - onset) * ms
    return out


def measure_record(leads, fs, windows, rpk):
    res = {c: np.nan for p in CANDS for c in CANDS[p]}
    res.update({BASE["qt"]: np.nan, BASE["qrs"]: np.nan, "rr_ms": np.nan, "n_leads": 0})
    if len(rpk) < 3:
        return res
    rr = float(np.median(np.diff(rpk)) * 1000.0 / fs)
    res["rr_ms"] = rr
    tmax = min(T.TMAX_MS, T.RR_FRAC * rr)
    if tmax < 250:
        return res
    beats = combined_beats(leads, fs, windows, rpk, tmax)
    res["n_leads"] = len(beats)
    base = V.measure_record(leads, fs, windows, rpk)                    # attempt-2 candidates for comparison
    res[BASE["qt"]], res[BASE["qrs"]] = base.get(BASE["qt"], np.nan), base.get(BASE["qrs"], np.nan)
    if len(beats) < MIN_LEADS:
        return res
    M = np.vstack([beats[L] for L in beats])
    for norm in ("abs", "euc"):
        for k, f in FR.items():
            q = qrs_global(M, fs, f, norm)
            if q:
                res[f"qrs_{norm}_{k}"] = q[0]
    q5 = qrs_global(M, fs, 0.05, "abs")
    if q5:
        res.update(qt_global(M, fs, q5[1]))
    return res


# ------------------------------------------------------------------ statistics
def slope_of(meas, ref):
    ok = np.isfinite(meas) & np.isfinite(ref)
    return float(np.polyfit(ref[ok], meas[ok], 1)[0]) if ok.sum() >= 5 else float("nan")


def tails(p, meas, ref):
    out = {}
    specs = [("ref QT >= 450", ref >= 450), ("ref QT <= 350", ref <= 350)] if p == "qt" else [("ref QRS >= 120", ref >= 120)]
    for lab, m in specs:
        ok = m & np.isfinite(meas) & np.isfinite(ref)
        out[lab] = (int(ok.sum()), float((meas[ok] - ref[ok]).mean()) if ok.sum() else float("nan"))
    return out


def tails_ok(tl):
    return all((n < TAIL_MIN_N) or abs(m) <= TAIL_TOL for n, m in tl.values())


def full_row(label, p, meas, ref, check_tails=True):
    has = np.isfinite(ref)
    diff = meas - ref
    ok = np.isfinite(diff)
    s = V.stats(pd.Series(diff[ok]), RULE[p][1])
    share = float(np.isfinite(meas[has]).mean()) if has.any() else 0.0
    slope = slope_of(meas, ref)
    tl = tails(p, meas, ref)
    base_ok = V.meets(p, s, share)
    ok_all = bool(base_ok and slope >= SLOPE_MIN and (tails_ok(tl) if check_tails else True))
    tl_txt = "; ".join(f"{k}: n={n}, mean error {m:+.1f}" + ("" if n >= TAIL_MIN_N else " (too few)") for k, (n, m) in tl.items())
    if s.get("n", 0) < 5:
        return f"| {label} | n/a | | | | | | | | does not meet |", False, s, slope, tl
    return (f"| {label} | {int(np.isfinite(meas).sum())} of {len(meas)} ({100 * share:.0f}%) | {s['median_abs']:.1f} ({s['median_abs_ci'][0]:.1f} to {s['median_abs_ci'][1]:.1f}) | {s['p90_abs']:.1f} | "
            f"{s['bias']:+.1f} ({s['bias_ci'][0]:+.1f} to {s['bias_ci'][1]:+.1f}) | {100 * s['within']:.0f}% | {slope:.2f} | {tl_txt} | **{'meets' if ok_all else 'does not meet'}** |"), ok_all, s, slope, tl


HEAD = ["| Measurement | With a value | Median abs diff (95% CI) | 90th pct | Bias (95% CI) | Within tolerance | Slope on 12SL | Tails | Rule |", "|---|---|---|---|---|---|---|---|---|"]


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
    """Digitised clean pages used ONLY to fit the photo offsets: the 99 earlier held-out pages and F001-F100 (their results were seen in attempt 2, so they are development data now)."""
    x12 = pd.read_csv(ROOT + "data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
    rows = []
    ext = pd.read_csv(R + "extension/results_extension.csv")
    sel = pd.read_csv(R + "extension/selected_100.csv").set_index("record")
    files = {os.path.basename(f)[:-4]: f for f in glob.glob(R + "extension/extension_digitized_12lead/**/*.npz", recursive=True)}
    jobs = [(r.variant_id, files[r.variant_id], int(sel.loc[r.record, "ecg_id"])) for _, r in ext[(ext.axis == "clean") & (ext.record != "21205_lr")].iterrows() if r.variant_id in files]
    fr = pd.read_csv(R + "fresh/selected_fresh_100.csv")
    jobs += [(r.page, R + f"fresh/fresh_digitized_12lead/{r.page}.npz", int(r.ecg_id)) for _, r in fr.iterrows()]
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
    d.to_csv(OUT + "sectionX_dev.csv", index=False)
    print("development measured", len(d), "recordings in", round(time.time() - t0), "s", flush=True)
    rng = np.random.default_rng(47)
    fold = rng.permutation(len(d)) % 5
    frozen, L = {}, ["# Section X development (1,100 development recordings, original signals, page-layout windows)", "",
                     "Offset-only calibration (QT: + b x RR + c; QRS: + c) refitted on the training folds. CV = 5-fold by recording. Eligible = a value for at least 90% AND a cross-validated slope on 12SL of at least 0.8. "
                     "Selection: smallest CV median absolute difference, ties by the share within tolerance. The attempt-2 baselines are shown for comparison and are not eligible choices.", ""]
    for p, name, tol in (("qt", "QT interval", RULE["qt"][1]), ("qrs", "QRS duration", RULE["qrs"][1])):
        ref, rr = d[f"ref_{p}"].values, d["rr_ms"].values
        rows_ = []
        for c in CANDS[p] + [BASE[p]]:
            raw = d[c].values
            share = float(np.isfinite(raw).mean())
            pred = np.full(len(d), np.nan)
            for k in range(5):
                tr, te = fold != k, fold == k
                pred[te] = V.apply_cal(raw[te], rr[te], V.fit_cal(raw[tr], rr[tr], ref[tr], p), p)
            ok = np.isfinite(pred) & np.isfinite(ref)
            diff = (pred - ref)[ok]
            rows_.append(dict(cand=c, share=share, n=int(ok.sum()), cv_median_abs=float(np.median(np.abs(diff))), cv_within=float((np.abs(diff) <= tol).mean()), cv_bias=float(diff.mean()),
                              cv_slope=slope_of(pred, ref), baseline=bool(c == BASE[p])))
        t = pd.DataFrame(rows_)
        elig = t[(t.share >= 0.9) & (t.cv_slope >= SLOPE_MIN) & (~t.baseline)].sort_values(["cv_median_abs", "cv_within"], ascending=[True, False])
        L += [f"## {name}", "", "| Candidate | With a value | n | CV median abs diff (ms) | CV within tolerance | CV bias | CV slope on 12SL | |", "|---|---|---|---|---|---|---|---|"]
        for _, r in t.iterrows():
            L.append(f"| {r.cand} | {100 * r.share:.0f}% | {int(r.n)} | {r.cv_median_abs:.1f} | {100 * r.cv_within:.0f}% | {r.cv_bias:+.1f} | {r.cv_slope:.2f} | {'baseline (attempt 2)' if r.baseline else ''} |")
        if elig.empty:
            frozen[p] = dict(candidate=None, table=t.round(3).to_dict(orient="records"))
            L += ["", "**No candidate is eligible (slope >= 0.8 and 90% with a value). Nothing is frozen for this parameter; the attempt stops here for it.**", ""]
            continue
        ch = elig.iloc[0]
        frozen[p] = dict(candidate=str(ch.cand), orig_cal=V.fit_cal(d[ch.cand].values, rr, ref, p), table=t.round(3).to_dict(orient="records"))
        L += ["", f"**Frozen candidate: {ch.cand}**; original-signal offsets {frozen[p]['orig_cal']}", ""]
    dg = digitised_dev_pages()
    L += [f"## Photo offsets (fitted once on {len(dg)} digitised clean pages: the 99 earlier held-out pages and F001-F100)", ""]
    for p in REF:
        if frozen[p].get("candidate"):
            c = frozen[p]["candidate"]
            cal = V.fit_cal(dg[c].values, dg["rr_ms"].values, dg[f"ref_{p}"].values, p)
            frozen[p]["photo_cal"] = cal
            pred = V.apply_cal(dg[c].values, dg["rr_ms"].values, cal, p)
            diff = pd.Series(pred - dg[f"ref_{p}"].values).dropna()
            frozen[p]["photo_fit_in_sample"] = dict(n=int(len(diff)), median_abs=float(diff.abs().median()), slope=slope_of(pred, dg[f"ref_{p}"].values))
            L.append(f"- {p.upper()}: {c}, photo offsets {cal}; in-sample median abs diff {diff.abs().median():.1f} ms, slope {frozen[p]['photo_fit_in_sample']['slope']:.2f} (for the record only: this fit is NOT a test)")
    frozen["written"] = time.strftime("%Y-%m-%d %H:%M")
    json.dump(frozen, open(OUT + "sectionX_frozen.json", "w"), indent=1)
    open(OUT + "SECTION_X_dev.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
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
    fr = json.load(open(OUT + "sectionX_frozen.json"))
    out_csv = OUT + "sectionX_test_per_page.csv"
    if os.path.exists(out_csv) and "--force" not in sys.argv:
        sys.exit("The test was already run once (rule: run ONCE).")
    sel = pd.read_csv(R + "fresh_g/selected_g_100.csv")
    x12 = pd.read_csv(ROOT + "data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
    tasks = []
    for _, r in sel.iterrows():
        p = R + f"fresh_g/g_digitized_12lead/{r.page}.npz"
        if not os.path.exists(p):
            sys.exit(f"missing digitised page {r.page}")
        tasks.append((r.page, p, r.filename_lr.replace("records100", "records500").replace("_lr", "_hr")))
    with ProcessPoolExecutor(max_workers=8) as ex:
        rows = list(ex.map(test_task, tasks, chunksize=4))
    m = pd.DataFrame(rows).merge(sel[["page", "ecg_id", "record"]], on="page")
    import ast
    ptb = pd.read_csv(ROOT + "data/ptbxl/ptbxl_database.csv").set_index("ecg_id")
    m["af"] = m.ecg_id.map(lambda e: ("AFIB" in ast.literal_eval(ptb.loc[e, "scp_codes"])) or ("AFLT" in ast.literal_eval(ptb.loc[e, "scp_codes"])))
    L = ["# Section X: QRS duration and QT, THIRD attempt, tested ONCE on 100 new sealed pages (EXPLORATORY)", "",
         "Rules fixed before any code ran (`docs/plan/analysis_plan_changes.md`, 2026-11-14 night, third). **Stricter rule** (the assistant's proposal, not approved by the guide), for both (a) and (b): the error rule of attempt 2, at least 90% with a value, "
         f"**slope of the measured value on 12SL >= {SLOPE_MIN}** and **tail checks** (mean error within +-{TAIL_TOL:.0f} ms for a reference QT >= 450, QT <= 350 and QRS >= 120; at least {TAIL_MIN_N} pages needed). Difference = measured minus 12SL (ms).", ""]
    verdicts = {}
    for p, name, tol in (("qt", "QT interval", "median abs diff <= 20 ms, 90% within 40 ms, |bias| <= 10 ms"), ("qrs", "QRS duration", "median abs diff <= 10 ms, 90% within 20 ms, |bias| <= 5 ms")):
        if not fr[p].get("candidate"):
            L += [f"## {name}", "", "No candidate was frozen in development (none passed the slope filter): not tested.", ""]
            verdicts[p] = (False, False)
            continue
        c = fr[p]["candidate"]
        m[f"ref_{p}"] = m.ecg_id.map(x12[REF[p]])
        m[f"{p}_orig"] = V.apply_cal(m[f"orig_{c}"].values, m["orig_rr_ms"].values, fr[p]["orig_cal"], p)
        m[f"{p}_dig"] = V.apply_cal(m[f"dig_{c}"].values, m["dig_rr_ms"].values, fr[p]["photo_cal"], p)
        m[f"{p}_base_dig"] = m[f"dig_{BASE[p]}"]
        ref = m[f"ref_{p}"].values
        ra, va, sa, sla, tla = full_row("(a) original signal in the photo windows", p, m[f"{p}_orig"].values, ref)
        rb, vb, sb, slb, tlb = full_row("(b) digitised clean page", p, m[f"{p}_dig"].values, ref)
        L += [f"## {name} (frozen: {c}; rule: {tol})", ""] + HEAD + [ra, rb, "",
              f"**{name} validated on the new sealed pages: {'YES' if va and vb else 'NO'}** ((a) meets: {va}, (b) meets: {vb}).", ""]
        for lab, sub in (("atrial fibrillation / flutter pages", m[m.af]), ("other pages", m[~m.af])):
            d = (sub[f"{p}_dig"] - sub[f"ref_{p}"]).dropna()
            if len(d) >= 3:
                L.append(f"- (b) {lab}: n = {len(d)}, median abs diff {d.abs().median():.1f} ms, bias {d.mean():+.1f} ms")
        verdicts[p] = (va, vb)
        L.append("")
    m.to_csv(out_csv, index=False)
    L += ["## Limits", "", "- Drawn pages digitised on this computer (not photos); the new phone photos follow separately. 12SL is an algorithm. One digitiser; the digitiser is not fully deterministic.",
          "- Nothing is shown to patients unless the new-page test AND the new-phone-photo confirmation both say YES; QT and QRS duration would also get the atrial-fibrillation guard (hidden when rr_cv > 0.12)."]
    open(OUT + "SECTION_X.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


def run_confirm():
    fr = json.load(open(OUT + "sectionX_frozen.json"))
    out_csv = OUT + "sectionX_confirm_per_photo.csv"
    if os.path.exists(out_csv) and "--force" not in sys.argv:
        sys.exit("The confirmation was already run once (rule: run ONCE).")
    sel = pd.read_csv(R + "fresh_g/selected_g_100.csv").set_index("page")
    x12 = pd.read_csv(ROOT + "data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
    files = sorted(glob.glob(R + "fresh_g/photos_digitized_12lead/*__V2_straighten.npz"))
    if len(files) < 2:
        sys.exit("no digitised new phone photos found in results/fresh_g/photos_digitized_12lead/")
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
    L = ["# Section X confirmation: the frozen third-attempt methods on the user's NEW phone photos (EXPLORATORY)", "",
         "Photos of the pages G001-G020 shown on a screen, 2 per page (straight, angled), straightened by the page finder and digitised like every other run; matched to pages by file-name order. Same rule as the page test, tails only reported (too few photos). "
         "One phone, one screen; the two photos of a page are not independent.", ""]
    for p, name in (("qt", "QT interval"), ("qrs", "QRS duration")):
        if not fr[p].get("candidate"):
            L += [f"## {name}", "", "No candidate was frozen.", ""]
            continue
        c = fr[p]["candidate"]
        d[f"ref_{p}"] = d.ecg_id.map(x12[REF[p]])
        d[p] = V.apply_cal(d[c].values, d["rr_ms"].values, fr[p]["photo_cal"], p)
        L += [f"## {name} (frozen: {c})", ""] + HEAD
        for lab, x in [("V2 straightened, all (primary)", d), ("straight shots", d[d.shot == "straight"]), ("angled shots", d[d.shot == "angled"])]:
            L.append(full_row(lab, p, x[p].values, x[f"ref_{p}"].values, check_tails=False)[0])
        L.append("")
    d.to_csv(out_csv, index=False)
    open(OUT + "SECTION_X_confirm.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
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
