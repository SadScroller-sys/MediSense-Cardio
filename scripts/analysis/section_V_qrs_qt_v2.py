"""Section V (EXPLORATORY): QRS duration and QT interval, SECOND attempt on fresh data. Rules fixed BEFORE any code ran: docs/plan/analysis_plan_changes.md, 2026-11-14 (night).
  python -I scripts/analysis/section_V_qrs_qt_v2.py --dev       1,000 unused ORIGINAL recordings (page-layout windows): choose one candidate per parameter by 5-fold cross-validation, then fit the PHOTO calibration
                                                                  once on the digitised clean pages of the earlier 99 held-out recordings; writes sectionV_frozen.json
  python -I scripts/analysis/section_V_qrs_qt_v2.py --test      ONCE on the fresh pages F001-F100: (a) original signal in the photo windows, (b) digitised clean page
  python -I scripts/analysis/section_V_qrs_qt_v2.py --confirm   ONCE on the 100 own-phone photos (straightened primary)
Reuses the beat cutting of Section T and the QRS edge detector of Section U."""
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
from scipy.stats import spearmanr

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
AREA_FRAC = 0.97
FRACS = {"3": 0.03, "5": 0.05, "10": 0.10}
RULE = {"qt": (20, 40, 10), "qrs": (10, 20, 5)}              # median abs diff, 90% within, |bias| (ms): unchanged
REF = {"qt": "QT_Int_Global", "qrs": "QRS_Dur_Global"}
QT_CANDS = [f"qt_{a}_{m}" for a in "BDE" for m in ("tan", "area")]
QRS_CANDS = [f"qrs_{a}_{f}" for a in ("C1", "C2", "B") for f in ("3", "5", "10")]
CANDS = {"qt": QT_CANDS, "qrs": QRS_CANDS}


# ------------------------------------------------------------------ per-lead features and aggregation
def qt_lead(mb, fs):
    """QRS onset (5% slope), T end by tangent and by 97% area, T amplitude; ms relative to the R anchor."""
    f = dict(onset=np.nan, tend_tan=np.nan, tend_area=np.nan, tamp=np.nan)
    e = U.edges(mb, fs, 0.05)
    if not e:
        return f
    r0 = ms2n(T.PRE_MS, fs)
    onset = e[0]
    b0, b1 = onset - ms2n(T.BASE_FROM_MS, fs), onset - ms2n(T.BASE_TO_MS, fs)
    if b0 < 0 or b1 <= b0:
        return f
    y = mb - np.median(mb[b0:b1])
    t0, t1 = r0 + ms2n(T.T_START_MS, fs), len(mb) - 1
    if t1 - t0 < ms2n(60, fs):
        return f
    seg = np.abs(y[t0:t1 + 1])
    tpk = t0 + int(np.argmax(seg))
    if tpk > t1 - ms2n(20, fs):
        return f
    ms = 1000.0 / fs
    f["onset"] = (onset - r0) * ms
    f["tamp"] = float(abs(y[tpk]))
    yy = y * (1.0 if y[tpk] >= 0 else -1.0)
    dd = np.gradient(yy) * fs
    k = tpk + int(np.argmin(dd[tpk:min(tpk + ms2n(T.TAN_SEARCH_MS, fs), len(mb) - 1) + 1]))
    slope = dd[k] / fs
    if slope < 0:
        te = k - yy[k] / slope
        if tpk < te <= len(mb) - 1 + ms2n(50, fs):
            f["tend_tan"] = (te - r0) * ms
    cum = np.cumsum(seg)
    if cum[-1] > 0:
        f["tend_area"] = (t0 + int(np.argmax(cum >= AREA_FRAC * cum[-1])) - r0) * ms
    return f


def measure_record(leads, fs, windows, rpk):
    res = {c: np.nan for p in CANDS for c in CANDS[p]}
    res["rr_ms"] = np.nan
    if len(rpk) < 3:
        return res
    rr = float(np.median(np.diff(rpk)) * 1000.0 / fs)
    res["rr_ms"] = rr
    tmax = min(T.TMAX_MS, T.RR_FRAC * rr)
    if tmax < 250:
        return res
    qt, qrs = {}, {}
    for L in LEADS:
        a, b = windows.get(L, (0, 0))
        if b - a <= 0 or L not in leads:
            continue
        mb, n = T.median_beat(leads[L], fs, a, b, rpk, tmax)
        if mb is None:
            continue
        qt[L] = qt_lead(mb, fs)
        r0 = ms2n(T.PRE_MS, fs)
        ms = 1000.0 / fs
        qrs[L] = {}
        for k, fr in FRACS.items():
            e = U.edges(mb, fs, fr)
            qrs[L][k] = ((e[0] - r0) * ms, (e[1] - r0) * ms) if e else (np.nan, np.nan)
    mn = T.MIN_LEADS
    for m, key in (("tan", "tend_tan"), ("area", "tend_area")):
        vals = {L: f[key] - f["onset"] for L, f in qt.items() if np.isfinite(f[key]) and np.isfinite(f["onset"])}
        if len(vals) >= mn:
            v = np.array(list(vals.values()))
            res[f"qt_B_{m}"] = float(np.median(v))
            s = np.sort(v)
            res[f"qt_D_{m}"] = float(np.mean(s[2:-2])) if len(s) >= 6 else float(np.median(s))
            top = sorted(vals, key=lambda L: -qt[L]["tamp"])[:4]
            res[f"qt_E_{m}"] = float(np.median([vals[L] for L in top]))
    for k in FRACS:
        pairs = [qrs[L][k] for L in qrs if np.isfinite(qrs[L][k][0]) and np.isfinite(qrs[L][k][1])]
        if len(pairs) >= mn:
            on = np.array([p[0] for p in pairs])
            off = np.array([p[1] for p in pairs])
            res[f"qrs_C1_{k}"] = float(np.percentile(off, 90) - np.percentile(on, 10))
            res[f"qrs_C2_{k}"] = float(np.percentile(off, 95) - np.percentile(on, 5))
            res[f"qrs_B_{k}"] = float(np.median(off - on))
    return res


# ------------------------------------------------------------------ calibration (amended 2026-11-14 night: the calibration may NOT rescale the measurement)
def fit_cal(raw, rr, ref, p):
    """QT = raw + b x RR + c ; QRS = raw + c. Fitted by least squares on (reference - raw). The slope on raw is fixed at 1."""
    raw, rr, ref = np.asarray(raw, float), np.asarray(rr, float), np.asarray(ref, float)
    ok = np.isfinite(raw) & np.isfinite(ref) & (np.isfinite(rr) if p == "qt" else True)
    if ok.sum() < 10:
        return None
    y = ref[ok] - raw[ok]
    if p == "qt":
        X = np.column_stack([rr[ok], np.ones(ok.sum())])
        coef, *_ = np.linalg.lstsq(X, y, rcond=None)
        return dict(b=float(coef[0]), c=float(coef[1]))
    return dict(c=float(np.mean(y)))


def apply_cal(raw, rr, cal, p):
    raw = np.asarray(raw, float)
    if cal is None:
        return raw * np.nan
    if p == "qt":
        return raw + cal["b"] * np.asarray(rr, float) + cal["c"]
    return raw + cal["c"]


def stats(diff, tol):
    return T.stats(diff, tol_within=tol)


def meets(p, s, share):
    tm, tw, tb = RULE[p]
    return bool(s.get("n", 0) >= 5 and s["median_abs"] <= tm and s["within"] >= 0.9 and abs(s["bias"]) <= tb and share >= 0.9)


# ------------------------------------------------------------------ development
def dev_task(a):
    rec, rel500 = a
    orig = T.read_all_leads(rel500)
    fs = 500
    win = {L: (int(LAYOUT[L][0] * fs), int(LAYOUT[L][1] * fs) - 1) for L in LEADS}
    row = dict(record=rec)
    row.update(measure_record(orig, fs, win, T.lead2_rpeaks(orig["II"], fs)))
    return row


def digitised_clean_new100():
    """The digitised CLEAN pages of the earlier 99 reliable held-out recordings, measured with every candidate (used only to fit the photo calibration)."""
    ext = pd.read_csv(R + "extension/results_extension.csv")
    sel = pd.read_csv(R + "extension/selected_100.csv").set_index("record")
    files = {os.path.basename(f)[:-4]: f for f in glob.glob(R + "extension/extension_digitized_12lead/**/*.npz", recursive=True)}
    rows = []
    for _, r in ext[(ext.axis == "clean") & (ext.record != "21205_lr")].iterrows():
        if r.variant_id in files:
            z = np.load(files[r.variant_id])
            dig = {L: np.asarray(z[L], float) / 1000.0 for L in LEADS}
            win = {L: T.longest_run(np.isfinite(dig[L])) for L in LEADS}
            row = dict(variant_id=r.variant_id, ecg_id=int(sel.loc[r.record, "ecg_id"]))
            row.update(measure_record(dig, 1000, win, T.lead2_rpeaks(dig["II"], 1000)))
            rows.append(row)
    return pd.DataFrame(rows)


def run_dev():
    t0 = time.time()
    sel = pd.read_csv(R + "fresh/selected_dev_1000.csv")
    x12 = pd.read_csv(ROOT + "data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
    tasks = [(r.record, r.filename_lr.replace("records100", "records500").replace("_lr", "_hr")) for _, r in sel.iterrows()]
    with ProcessPoolExecutor(max_workers=10) as ex:
        rows = list(ex.map(dev_task, tasks, chunksize=8))
    d = pd.DataFrame(rows).merge(sel[["record", "ecg_id"]], on="record")
    for p in REF:
        d[f"ref_{p}"] = d.ecg_id.map(x12[REF[p]])
    d.to_csv(OUT + "sectionV_dev.csv", index=False)
    print("development measured", len(d), "recordings in", round(time.time() - t0), "s", flush=True)
    rng = np.random.default_rng(46)
    fold = rng.permutation(len(d)) % 5
    frozen, L = {}, ["# Section V development (1,000 unused original recordings, page-layout windows)", "",
                     "Reference = 12SL. Value share = share of recordings with a value. CV = 5-fold cross-validation by recording, calibration refitted on the training folds. Selection rule from the 2026-11-14 (night) plan entry.", ""]
    for p, name, tol in (("qt", "QT interval", RULE["qt"][1]), ("qrs", "QRS duration", RULE["qrs"][1])):
        ref = d[f"ref_{p}"].values
        rr = d["rr_ms"].values
        rows_ = []
        for c in CANDS[p]:
            raw = d[c].values
            share = float(np.isfinite(raw).mean())
            pred = np.full(len(d), np.nan)
            for k in range(5):
                tr, te = fold != k, fold == k
                cal = fit_cal(raw[tr], rr[tr], ref[tr], p)
                pred[te] = apply_cal(raw[te], rr[te], cal, p)
            ok = np.isfinite(pred) & np.isfinite(ref)
            diff = (pred - ref)[ok]
            rows_.append(dict(cand=c, share=share, n=int(ok.sum()), cv_median_abs=float(np.median(np.abs(diff))), cv_within=float((np.abs(diff) <= tol).mean()), cv_bias=float(diff.mean()),
                              rho=float(spearmanr(raw[ok], ref[ok])[0])))
        t = pd.DataFrame(rows_)
        elig = t[t.share >= 0.9].sort_values(["cv_median_abs", "cv_within"], ascending=[True, False])
        ch = elig.iloc[0]
        cal_all = fit_cal(d[ch.cand].values, rr, ref, p)
        frozen[p] = dict(candidate=str(ch.cand), orig_cal=cal_all, table=t.round(3).to_dict(orient="records"))
        L += [f"## {name}", "", "| Candidate | Recordings with a value | n | CV median abs diff (ms) | CV within tolerance | CV bias (ms) | rho (raw) |", "|---|---|---|---|---|---|---|"]
        for _, r in t.iterrows():
            L.append(f"| {r.cand} | {100 * r.share:.0f}% | {int(r.n)} | {r.cv_median_abs:.1f} | {100 * r.cv_within:.0f}% | {r.cv_bias:+.1f} | {r.rho:.2f} |")
        L += ["", f"**Frozen candidate: {ch.cand}**; original-signal calibration {cal_all}", ""]
    # photo calibration, fitted ONCE on the digitised clean pages of the earlier held-out recordings
    dg = digitised_clean_new100()
    x = dg.merge(pd.DataFrame({"ecg_id": x12.index, **{f"ref_{p}": x12[REF[p]].values for p in REF}}), on="ecg_id")
    L += ["## Photo calibration (fitted once on the digitised clean pages of 99 earlier held-out recordings)", ""]
    for p in REF:
        c = frozen[p]["candidate"]
        cal = fit_cal(x[c].values, x["rr_ms"].values, x[f"ref_{p}"].values, p)
        frozen[p]["photo_cal"] = cal
        pred = apply_cal(x[c].values, x["rr_ms"].values, cal, p)
        diff = pd.Series(pred - x[f"ref_{p}"].values).dropna()
        frozen[p]["photo_fit_in_sample"] = dict(n=int(len(diff)), median_abs=float(diff.abs().median()), within=float((diff.abs() <= RULE[p][1]).mean()), bias=float(diff.mean()))
        L.append(f"- {p.upper()}: candidate {c}, photo calibration {cal}; in-sample median abs diff {diff.abs().median():.1f} ms (for the record only: this fit is NOT a test)")
    frozen["written"] = time.strftime("%Y-%m-%d %H:%M")
    json.dump(frozen, open(OUT + "sectionV_frozen.json", "w"), indent=1)
    open(OUT + "SECTION_V_dev.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
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


def verdict_row(label, ref, val, p, has):
    diff = (val - ref)
    ok = np.isfinite(diff)
    s = stats(pd.Series(diff[ok]), RULE[p][1])
    share = float(np.isfinite(val[has]).mean()) if has.any() else 0.0
    rho = spearmanr(val[ok], ref[ok])[0] if ok.sum() > 4 else np.nan
    v = meets(p, s, share)
    if s.get("n", 0) >= 5:
        return (f"| {label} | {int(np.isfinite(val).sum())} of {len(val)} ({100 * share:.0f}%) | {rho:.2f} | {s['median_abs']:.1f} ({s['median_abs_ci'][0]:.1f} to {s['median_abs_ci'][1]:.1f}) | "
                f"{s['p90_abs']:.1f} | {s['bias']:+.1f} ({s['bias_ci'][0]:+.1f} to {s['bias_ci'][1]:+.1f}) | {100 * s['within']:.0f}% | **{'meets' if v else 'does not meet'}** |"), v, s, share
    return f"| {label} | {int(np.isfinite(val).sum())} of {len(val)} | n/a | n/a | n/a | n/a | n/a | does not meet |", False, s, share


HEAD = ["| Measurement | With a value | rho with 12SL | Median abs diff (95% CI) | 90th pct | Bias (95% CI) | Within tolerance | Rule |", "|---|---|---|---|---|---|---|---|"]


def run_test():
    fr = json.load(open(OUT + "sectionV_frozen.json"))
    out_csv = OUT + "sectionV_test_per_page.csv"
    if os.path.exists(out_csv) and "--force" not in sys.argv:
        sys.exit("The test was already run once (rule: run ONCE).")
    sel = pd.read_csv(R + "fresh/selected_fresh_100.csv")
    x12 = pd.read_csv(ROOT + "data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
    tasks = []
    for _, r in sel.iterrows():
        p = R + f"fresh/fresh_digitized_12lead/{r.page}.npz"
        if not os.path.exists(p):
            sys.exit(f"missing digitised page {r.page}: digitise all 100 pages first")
        tasks.append((r.page, p, r.filename_lr.replace("records100", "records500").replace("_lr", "_hr")))
    with ProcessPoolExecutor(max_workers=10) as ex:
        rows = list(ex.map(test_task, tasks, chunksize=4))
    m = pd.DataFrame(rows).merge(sel[["page", "ecg_id", "record", "is_abnormal", "flagged"]], on="page")
    ptb = pd.read_csv(ROOT + "data/ptbxl/ptbxl_database.csv").set_index("ecg_id")
    import ast
    m["af"] = m.ecg_id.map(lambda e: ("AFIB" in ast.literal_eval(ptb.loc[e, "scp_codes"])) or ("AFLT" in ast.literal_eval(ptb.loc[e, "scp_codes"])))
    for p in REF:
        c = fr[p]["candidate"]
        m[f"ref_{p}"] = m.ecg_id.map(x12[REF[p]])
        m[f"{p}_orig"] = apply_cal(m[f"orig_{c}"].values, m["orig_rr_ms"].values, fr[p]["orig_cal"], p)
        m[f"{p}_dig"] = apply_cal(m[f"dig_{c}"].values, m["dig_rr_ms"].values, fr[p]["photo_cal"], p)
    m.to_csv(out_csv, index=False)
    L = ["# Section V: QRS and QT, second attempt, tested ONCE on 100 fresh pages (EXPLORATORY)", "",
         "Rules fixed before any code ran (`docs/plan/analysis_plan_changes.md`, 2026-11-14 night). The fresh pages were drawn and digitised before any result was looked at. The acceptance rules are unchanged and are the assistant's proposal, **not approved by the guide**. "
         f"Frozen: QT = {fr['qt']['candidate']}, QRS = {fr['qrs']['candidate']}; (a) uses the calibration from the 1,000 development recordings, (b) the photo calibration fitted on the digitised pages of the earlier 99 held-out recordings. Difference = measured minus 12SL (ms).", ""]
    verdict = {}
    for p, name, tol in (("qt", "QT interval", "median abs diff <= 20 ms, 90% within 40 ms, |bias| <= 10 ms"), ("qrs", "QRS duration", "median abs diff <= 10 ms, 90% within 20 ms, |bias| <= 5 ms")):
        ref = m[f"ref_{p}"].values
        has = np.isfinite(ref)
        ra, va, sa, sha = verdict_row("(a) original signal in the photo windows", ref, m[f"{p}_orig"].values, p, has)
        rb, vb, sb, shb = verdict_row("(b) digitised clean page", ref, m[f"{p}_dig"].values, p, has)
        L += [f"## {name} (rule: {tol}; at least 90% with a value)", ""] + HEAD + [ra, rb]
        ok = np.isfinite(m[f"{p}_dig"]) & np.isfinite(m[f"{p}_orig"])
        sc = stats(pd.Series((m[f"{p}_dig"] - m[f"{p}_orig"])[ok]), RULE[p][1])
        if sc.get("n", 0) >= 5:
            L.append(f"| (c) digitised minus (a): what the photo adds | {int(ok.sum())} | | {sc['median_abs']:.1f} | {sc['p90_abs']:.1f} | {sc['bias']:+.1f} | | |")
        verdict[p] = (va, vb)
        L += ["", f"**{name} validated on the fresh pages: {'YES' if va and vb else 'NO'}** ((a) meets: {va}, (b) meets: {vb}).", ""]
        for lab, sub in (("atrial fibrillation / flutter pages", m[m.af]), ("other pages", m[~m.af])):
            d = (sub[f"{p}_dig"] - sub[f"ref_{p}"]).dropna()
            if len(d) >= 3:
                L.append(f"- (b) {lab}: n = {len(d)}, median abs diff {d.abs().median():.1f} ms, bias {d.mean():+.1f} ms")
        L.append("")
    L += ["## Limits", "", "- Drawn pages digitised on this computer (not photos); the phone-photo confirmation follows separately. 12SL is an algorithm. One digitiser.",
          "- The calibration was fitted on drawn pages; the fresh pages were never used to choose a method or a coefficient.",
          "- Nothing is shown to patients unless the fresh test AND the phone-photo confirmation both say YES."]
    open(OUT + "SECTION_V.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


def run_confirm():
    fr = json.load(open(OUT + "sectionV_frozen.json"))
    out_csv = OUT + "sectionV_confirm_per_photo.csv"
    if os.path.exists(out_csv) and "--force" not in sys.argv:
        sys.exit("The confirmation was already run once (rule: run ONCE).")
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
    for c in ("set", "photo", "version", "page", "ecg_id", "shot"):
        d[c] = d.key.map(lambda k: meta[k][c])
    for p in REF:
        d[f"ref_{p}"] = d.ecg_id.map(x12[REF[p]])
        d[p] = apply_cal(d[fr[p]["candidate"]].values, d["rr_ms"].values, fr[p]["photo_cal"], p)
    d.to_csv(out_csv, index=False)
    L = ["# Section V confirmation: the frozen second-attempt QRS and QT methods on own-phone photos (EXPLORATORY)", "",
         "Method and photo calibration exactly as frozen; rules fixed before the run. The same 100 photos confirmed an earlier version (Sections T and U), but this version was not developed on them. One phone, one screen; the two photos of a page are not independent.", ""]
    for p, name in (("qt", "QT interval"), ("qrs", "QRS duration")):
        L += [f"## {name}", ""] + HEAD
        for lab, x in [("V2 straightened, all (primary)", d[d.version == "V2"]), ("V0 original, all", d[d.version == "V0"]),
                       ("V2 straight shots", d[(d.version == "V2") & (d.shot == "straight")]), ("V2 angled shots", d[(d.version == "V2") & (d.shot == "angled")])]:
            row, v, s, sh = verdict_row(lab, x[f"ref_{p}"].values, x[p].values, p, np.isfinite(x[f"ref_{p}"].values))
            L.append(row)
        L.append("")
    open(OUT + "SECTION_V_confirm.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
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


if __name__ == "__main__":
    if "--dev" in sys.argv:
        run_dev()
    elif "--test" in sys.argv:
        run_test()
    elif "--confirm" in sys.argv:
        run_confirm()
    else:
        print(__doc__)
