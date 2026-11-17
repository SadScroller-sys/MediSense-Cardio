"""Section B (MASTER_PLAN 4b items 4, 9, 10, 11, 12 and the flagged/unflagged effect): reference checks, interval preservation, a second heart-rate
detector, subgroups. Exploratory except where stated (MASTER_PLAN): no pass/fail.

Methods fixed before looking at results (2026-11-07):
  * Interval method = the best method found in results/interval_method_comparison.md: NeuroKit2 continuous-wavelet delineation ('cwt'),
    R peaks found once on lead II and reused for all 12 leads, QT per lead = mean over beats of (T offset - QRS onset), median over the 12 leads.
    RR = median R-R interval of lead II. QTc Fridericia = QT / RR^(1/3) (main), Bazett = QT / sqrt(RR) (sensitivity). Always "by this method".
  * Truth for the preservation analysis = the same method on the ORIGINAL 500 Hz PTB-XL record; digitised = the saved 12-lead signal at 1,000 Hz.
  * QTc abnormal: >= 460 ms (female), >= 450 ms (male). QTc false reassurance (per MASTER_PLAN): a record is at risk if its original QTc is abnormal AND its own clean digitised page reads
    abnormal; an event = a damaged version of an at-risk record whose digitised QTc reads normal and under-reads the original by more than a tolerance (10 ms main; 0 and 20 ms shown).
  * Second heart-rate detector = NeuroKit2 'pantompkins1985' on cleaned lead II, HR = mean of 60/RR; reference from the same detector on the 100 Hz original (like for like).
  * Subgroups: sex; age band (<40, 40-59, 60-79, 80+); diagnostic superclass of the highest-likelihood SCP code (PTB-XL scp_statements); true HR range (<60, 60-100, >100).
Unreliable recordings excluded (15192, 21205). Reads (never modifies) results_v2.csv, results_extension.csv, the saved 12-lead npz folder, PTB-XL and PTB-XL+ files.
Heavy part (interval and heart-rate computation) runs in parallel and is cached in results/analysis/sectionB_cache_*.csv (delete the file to recompute)."""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):   # one math thread per worker: 14 workers x many threads ran the machine out of memory
    os.environ.setdefault(_v, "1")
import ast
import glob
import multiprocessing as mp
import os
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = "D:/Capstone Project/"
OUT = ROOT + "results/analysis/"
NPZ = ROOT + "results/extension/extension_digitized_12lead/extension_digitized_12lead/"
UNREL = {"15192_lr", "21205_lr"}
SHARED = {0, 3, 5}
AXES = ["resolution", "blur", "rotate", "jpeg", "brightness", "gridcontrast"]
LEADS = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]


# ---------------------------------------------------------------- workers (top level for multiprocessing)
def _mean_ms(a, b, fs):
    n = min(len(a), len(b))
    if n == 0:
        return np.nan
    dd = (b[:n] - a[:n])
    dd = dd[np.isfinite(dd)]
    return float(np.mean(dd)) / fs * 1000.0 if len(dd) else np.nan


def _prep_lead(sig, fs, min_s=1.5, min_fill=0.9):
    """Span from the first to the last finite sample of a lead; small gaps inside it are filled by linear interpolation.
    Returns (start, segment) or None if the span is shorter than min_s seconds or less than min_fill of it is finite."""
    sig = np.asarray(sig, dtype=float)
    idx = np.where(np.isfinite(sig))[0]
    if len(idx) == 0:
        return None
    a0, b0 = int(idx[0]), int(idx[-1]) + 1
    seg = sig[a0:b0].copy()
    fin = np.isfinite(seg)
    if len(seg) < min_s * fs or fin.mean() < min_fill:
        return None
    if not fin.all():
        seg[~fin] = np.interp(np.where(~fin)[0], np.where(fin)[0], seg[fin])
    return a0, seg


def _qt_median12(leads, fs):
    """leads: 12 arrays. A digitised page shows each lead only inside its own ~2.5 s window (lead II, the rhythm strip, spans ~10 s) and the saved
    signals have small gaps (filled by interpolation, see _prep_lead). R peaks come from lead II; each lead is delineated inside its own window using the
    lead-II peaks that fall in it (at least 2 beats). Returns qt (median over leads), qt_II (lead II alone), rr (median R-R of lead II, s), hr_pt, n_leads_ok."""
    import neurokit2 as nk
    out = dict(qt=np.nan, qt_II=np.nan, rr=np.nan, hr_pt=np.nan, n_leads_ok=0)
    try:
        p2 = _prep_lead(leads[1], fs, min_s=3.0)
        if p2 is None:
            return out
        a2, ii = p2
        cl = nk.ecg_clean(ii, sampling_rate=fs, method="neurokit")
        _, rp = nk.ecg_peaks(cl, sampling_rate=fs)
        rl = np.asarray(rp["ECG_R_Peaks"])
        if len(rl) < 3:
            return out
        out["rr"] = float(np.median(np.diff(rl)) / fs)
        rpk = rl + a2                      # peak positions in whole-page sample coordinates
        try:
            _, rp2 = nk.ecg_peaks(cl, sampling_rate=fs, method="pantompkins1985")
            r2 = rp2["ECG_R_Peaks"]
            out["hr_pt"] = float(np.mean(60.0 / (np.diff(r2) / fs))) if len(r2) >= 3 else np.nan
        except Exception:
            pass
        qts = []
        for li, sig in enumerate(leads):
            pr = _prep_lead(sig, fs)
            if pr is None:
                continue
            a0, seg = pr
            pk = rpk[(rpk >= a0 + int(0.1 * fs)) & (rpk < a0 + len(seg) - int(0.1 * fs))] - a0
            if len(pk) < 2:
                continue
            try:
                c = nk.ecg_clean(seg, sampling_rate=fs, method="neurokit")
                _, w = nk.ecg_delineate(c, {"ECG_R_Peaks": pk}, sampling_rate=fs, method="cwt")
                q = _mean_ms(np.array(w.get("ECG_R_Onsets", []), dtype=float), np.array(w.get("ECG_T_Offsets", []), dtype=float), fs)
                if np.isfinite(q):
                    qts.append(q)
                    if li == 1:
                        out["qt_II"] = q
            except Exception:
                continue
        out["n_leads_ok"] = len(qts)
        if qts:
            out["qt"] = float(np.median(qts))
    except Exception:
        pass
    return out


def work_digitised(path):
    z = np.load(path, allow_pickle=False)
    r = _qt_median12([z[k] for k in LEADS], 1000)
    r["variant_id"] = os.path.basename(path)[:-4]
    return r


def work_original(rec):
    import wfdb
    num = rec.split("_")[0]
    folder = f"{int(num) // 1000 * 1000:05d}"
    r5 = wfdb.rdrecord(ROOT + f"data/ptbxl/records500/{folder}/{num}_hr")
    order = [r5.sig_name.index(n) for n in [s.upper() if s.startswith("a") else s for s in LEADS]]
    r = _qt_median12([r5.p_signal[:, i] for i in order], r5.fs)
    # reference heart rate with the second detector on the 100 Hz record, like for like
    import neurokit2 as nk
    try:
        r1 = wfdb.rdrecord(ROOT + f"data/ptbxl/records100/{folder}/{num}_lr")
        ii = r1.p_signal[:, r1.sig_name.index("II")]
        cl = nk.ecg_clean(ii, sampling_rate=r1.fs, method="neurokit")
        r2 = nk.ecg_peaks(cl, sampling_rate=r1.fs, method="pantompkins1985")[1]["ECG_R_Peaks"]
        r["ref_hr_pt"] = float(np.mean(60.0 / (np.diff(r2) / r1.fs)))
    except Exception:
        r["ref_hr_pt"] = np.nan
    r["record"] = rec
    return r


def run_pool(fn, items, label, workers=6):
    from concurrent.futures import ProcessPoolExecutor, as_completed
    res = []
    with ProcessPoolExecutor(workers) as ex:
        futs = {ex.submit(fn, it): it for it in items}
        for n, f in enumerate(as_completed(futs), 1):
            try:
                res.append(f.result(timeout=900))
            except Exception as exc:  # a dead worker raises here instead of hanging
                raise SystemExit(f"{label}: FAILED on {futs[f]}: {exc!r}")
            if n % 50 == 0 or n == len(items):
                print(f"{label}: {n}/{len(items)} done", flush=True)
    return res


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


def pct(k, n):
    if n == 0:
        return "n/a"
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {100 * k / n:.1f}% ({100 * lo:.0f}-{100 * hi:.0f})"


def md_table(t):
    t = t.copy()
    head = "| " + " | ".join(map(str, t.columns)) + " |\n|" + "---|" * len(t.columns) + "\n"
    return head + "\n".join("| " + " | ".join("" if (isinstance(z, float) and np.isnan(z)) else str(z) for z in r) + " |" for r in t.itertuples(index=False))


def main():
    os.makedirs(OUT, exist_ok=True)
    e = pd.read_csv(ROOT + "results/extension/results_extension.csv")
    v = pd.read_csv(ROOT + "results/v2_intervals/results_v2.csv")
    recs = sorted(e.record.unique())
    # ------------------------------------------------ heavy computation (cached)
    c_dig, c_org = OUT + "sectionB_cache_digitised.csv", OUT + "sectionB_cache_original.csv"
    if not (os.path.exists(c_dig) and os.path.exists(c_org)):
        files = sorted(glob.glob(NPZ + "*.npz"))
        assert len(files) == 1300
        org = pd.DataFrame(run_pool(work_original, recs, "original"))
        dig = pd.DataFrame(run_pool(work_digitised, files, "digitised"))
        org.to_csv(c_org, index=False)
        dig.to_csv(c_dig, index=False)
    org = pd.read_csv(c_org)
    dig = pd.read_csv(c_dig)

    db = pd.read_csv(ROOT + "data/ptbxl/ptbxl_database.csv")
    db["record"] = db.filename_lr.str.split("/").str[-1]
    x12 = pd.read_csv(ROOT + "data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
    ref = pd.read_csv(ROOT + "results/extension/reference_check_150.csv")

    L = ["# Section B results: reference checks, interval preservation, second heart-rate detector, subgroups\n",
         "*Generated by `scripts/analysis/section_B.py`. Exploratory (MASTER_PLAN): no pass or fail. Intervals are 'by this method' (NeuroKit2 continuous wavelet: median over 12 leads on the original records, lead II only on digitised pages), never a clinical rate.*\n"]

    # ------------------------------------------------ B1 reference checks on the new 100
    r100 = ref[ref.set == "new100"]
    L.append("## B1. Reference checks on the new 100\n")
    L.append(f"- **Heart rate, 100 Hz vs 500 Hz record** (same detector): {len(r100)} recordings; median difference {r100.abs_diff.median():.2f} bpm; "
             f"{int(r100.reference_uncertain.sum())} recordings differ by more than 5 bpm (reference-uncertain), {int((r100.abs_diff > 10).sum())} by more than 10 bpm.")
    org = org.merge(db[["record", "ecg_id", "sex", "age"]], on="record")
    org["qtc_fri"] = org.qt / np.cbrt(org.rr)
    org["qtc_baz"] = org.qt / np.sqrt(org.rr)
    org["qtc_fri_II"] = org.qt_II / np.cbrt(org.rr)
    org["qtc_baz_II"] = org.qt_II / np.sqrt(org.rr)
    ref12 = x12.reindex(org.ecg_id.values)
    rows = []
    for lab, a, col in (("QT, median of 12 leads", org.qt.values, "QT_Int_Global"), ("QTc Bazett, median of 12 leads", org.qtc_baz.values, "QT_IntBazett_Global"),
                        ("QTc Fridericia, median of 12 leads", org.qtc_fri.values, "QT_IntFridericia_Global"),
                        ("QT, lead II only (used for B2)", org.qt_II.values, "QT_Int_Global"), ("QTc Bazett, lead II only", org.qtc_baz_II.values, "QT_IntBazett_Global"),
                        ("QTc Fridericia, lead II only", org.qtc_fri_II.values, "QT_IntFridericia_Global")):
        b = ref12[col].values
        ok = np.isfinite(a) & np.isfinite(b)
        rho = pd.Series(a[ok]).corr(pd.Series(b[ok]), method="spearman")
        rows.append(dict(quantity=lab, n=int(ok.sum()), spearman_rho=round(rho, 2), median_abs_diff_ms=round(float(np.median(np.abs(a[ok] - b[ok]))), 1),
                         bias_ms=round(float(np.mean(a[ok] - b[ok])), 1)))
    b1 = pd.DataFrame(rows)
    b1.to_csv(OUT + "sectionB_reference_qt_vs_12sl.csv", index=False)
    L.append("- **QT and QTc on the original 500 Hz signal (our method) vs the commercial 12SL global values, new 100** (first 50 earlier: QT rho 0.66, median abs. difference 28.9 ms):\n")
    L.append(md_table(b1) + "\n")

    # ------------------------------------------------ B2 QT/QTc preservation on digitised signals
    d = e[["variant_id", "record", "axis", "level", "sex", "gt_hr", "dig_hr", "diff_bpm"]].merge(dig, on="variant_id")
    d = d[~d.record.isin(UNREL)]
    # NeuroKit2's wavelet delineation cannot process the ~2.5 s windows in which a digitised page shows leads I-III, aVR-aVF, V1-V6, so the digitised side
    # can only be measured on lead II (the 10 s rhythm strip). The truth is therefore the same method on the ORIGINAL lead II (500 Hz).
    d["qt"] = d["qt_II"]
    o2 = org[["record", "qt_II", "rr"]].rename(columns={"qt_II": "qt", "rr": "rr"})
    o2["qtc_fri"] = o2.qt / np.cbrt(o2.rr)
    o2["qtc_baz"] = o2.qt / np.sqrt(o2.rr)
    d = d.merge(o2.rename(columns=lambda c: c if c == "record" else c + "_orig"), on="record")
    d["qtc_fri"] = d.qt / np.cbrt(d.rr)
    d["qtc_baz"] = d.qt / np.sqrt(d.rr)
    d["qt_err"] = d.qt - d.qt_orig
    d["qtc_fri_err"] = d.qtc_fri - d.qtc_fri_orig
    d["qtc_baz_err"] = d.qtc_baz - d.qtc_baz_orig
    rows = []
    for (ax, lv), g in d.groupby(["axis", "level"]):
        o = g.dropna(subset=["qtc_fri_err"])
        k60 = int((o.qtc_fri_err.abs() > 60).sum())
        rows.append(dict(axis=ax, level=int(lv), images=len(g), with_qt=len(o), median_abs_qt_err_ms=round(o.qt_err.abs().median(), 1),
                         median_abs_qtc_fri_err_ms=round(o.qtc_fri_err.abs().median(), 1), median_abs_qtc_baz_err_ms=round(o.qtc_baz_err.abs().median(), 1),
                         qtc_fri_wrong_gt60ms=pct(k60, len(o))))
    b2 = pd.DataFrame(rows)
    b2["axis"] = pd.Categorical(b2.axis, ["clean"] + AXES, ordered=True)
    b2 = b2.sort_values(["axis", "level"])
    b2.to_csv(OUT + "sectionB_qt_preservation.csv", index=False)
    L.append("## B2. QT and QTc preservation: digitised lead II vs the original lead II, same method (new 100)\n")
    L.append("Lead II only: the wavelet method cannot process the 2.5 s windows of the other leads on a digitised page. 'with_qt' = images where the method returned a QT. Error = digitised minus original, in ms. The clean-page row is the measurement floor of the method itself.\n")
    L.append(md_table(b2) + "\n")

    # QTc false reassurance
    thr = lambda s: np.where(s == "female", 460.0, 450.0)
    fr_rows = []
    for form, col in (("Fridericia (main)", "qtc_fri"), ("Bazett (sensitivity)", "qtc_baz")):
        d["thr"] = thr(d.sex.values)
        d["abn_true"] = d[col + "_orig"] >= d.thr
        d["abn_dig"] = d[col] >= d.thr
        clean_ok = d[d.axis == "clean"].set_index("record").abn_dig
        d["clean_abn"] = d.record.map(clean_ok)
        prol = d.drop_duplicates("record")
        n_prol = int(prol.abn_true.sum())
        risk_recs = set(d[(d.abn_true) & (d.clean_abn == True)].record)  # noqa: E712
        tests = d[d.record.isin(risk_recs) & (d.axis != "clean") & d[col].notna()]
        for tol in (0, 10, 20):
            ev = tests[(~tests.abn_dig) & ((tests[col + "_orig"] - tests[col]) > tol)]
            fr_rows.append(dict(formula=form, tolerance_ms=tol, truly_prolonged_records=n_prol, at_risk_records=len(risk_recs), at_risk_tests=len(tests),
                                events=len(ev), records_with_events=ev.record.nunique(), rate=pct(len(ev), len(tests)),
                                events_by_damage=", ".join(f"{a} {n}" for a, n in ev.axis.value_counts().items()) or "none"))
    b2b = pd.DataFrame(fr_rows)
    b2b.to_csv(OUT + "sectionB_qtc_false_reassurance.csv", index=False)
    L.append("### QTc false reassurance (by this method; truth = same method on the original signal; threshold >= 460 ms women, >= 450 ms men)\n")
    L.append(md_table(b2b) + "\n")
    L.append("Too few events to rank damage types; do not quote the breakdown as a finding.\n")

    # ------------------------------------------------ B3 second heart-rate detector
    d3 = d.merge(org[["record", "ref_hr_pt"]], on="record")
    d3["wrong5_main"] = d3.diff_bpm > 5
    d3["wrong5_pt"] = (d3.hr_pt - d3.ref_hr_pt).abs() > 5
    d3["out_pt"] = d3.hr_pt.notna()
    rows = []
    for (ax, lv), g in d3.groupby(["axis", "level"]):
        rows.append(dict(axis=ax, level=int(lv), n=len(g), wrong5_main_detector=pct(int(g.wrong5_main.sum()), len(g)),
                         wrong5_second_detector=pct(int(g.wrong5_pt.sum()), len(g)), no_output_second=int((~g.out_pt).sum())))
    b3 = pd.DataFrame(rows)
    b3["axis"] = pd.Categorical(b3.axis, ["clean"] + AXES, ordered=True)
    b3 = b3.sort_values(["axis", "level"])
    b3.to_csv(OUT + "sectionB_second_hr_detector.csv", index=False)
    both = d3[d3.out_pt & d3.dig_hr.notna()]
    agree = float(((both.wrong5_main) == (both.wrong5_pt)).mean())
    L.append("## B3. Does the heart-rate result depend on the peak detector? (new 100, second detector Pan-Tompkins on the same saved signals)\n")
    L.append(f"Both detectors agree on the 'wrong > 5 bpm' label for {100 * agree:.1f}% of {len(both)} images with output.\n")
    L.append(md_table(b3) + "\n")
    da = pd.read_csv(OUT + "sectionB_detector_agreement.csv")
    L.append("**Limit of this check.** On the ORIGINAL signals (no damage, 500 Hz lead II) the alternative detectors disagree with the main heart-rate reference "
             "(difference > 5 bpm) on many recordings (`section_B_detector_check.py`):\n")
    L.append(md_table(da) + "\n")
    L.append("So Pan-Tompkins is a noisy second opinion: its 'wrong' rate is already 13% on clean pages (main detector 3%), and no other detector tested is closer. "
             "Read the table as ranking and excess over the clean page, not as absolute rates: resolution level 5 and blur level 5 stay the worst; "
             "rotation level 5 also looks bad under this detector (and 21 pages give no output); JPEG, brightness and grid fading stay near the clean level. "
             "The main-detector verdict C1 was fixed in advance and is not changed by this check.\n")

    # ------------------------------------------------ B4 subgroups (all 150)
    a = pd.concat([v.assign(set="first50")[["set", "record", "axis", "level", "sex", "gt_hr", "dig_hr", "diff_bpm"]],
                   e.assign(set="new100")[["set", "record", "axis", "level", "sex", "gt_hr", "dig_hr", "diff_bpm"]]], ignore_index=True)
    a = a[~a.record.isin(UNREL) & a.level.isin(SHARED)].merge(db[["record", "age", "scp_codes", "baseline_drift", "static_noise", "burst_noise",
                                                                  "electrodes_problems", "extra_beats", "pacemaker"]], on="record")
    scp = pd.read_csv(ROOT + "data/ptbxl/scp_statements.csv", index_col=0)
    cls = scp["diagnostic_class"].to_dict()

    def superclass(s):
        try:
            dct = ast.literal_eval(s)
        except Exception:
            return "unknown"
        best = sorted(((lk, k) for k, lk in dct.items() if isinstance(cls.get(k), str)), reverse=True)
        return cls[best[0][1]] if best else "no diagnostic code"

    a["diag"] = a.scp_codes.map(superclass)
    a["age_band"] = pd.cut(a.age, [0, 39.5, 59.5, 79.5, 200], labels=["<40", "40-59", "60-79", "80+"])
    a["hr_range"] = pd.cut(a.gt_hr, [0, 60, 100, 400], labels=["<60", "60-100", ">100"], right=False)
    FL = ["baseline_drift", "static_noise", "burst_noise", "electrodes_problems", "extra_beats", "pacemaker"]
    a["flagged"] = a[FL].apply(lambda s: s.notna() & (s.astype(str).str.strip() != "")).any(axis=1)
    a["wrong5"] = a.diff_bpm > 5
    a["none"] = a.dig_hr.isna()
    a["hard_damage"] = a.axis.isin(["resolution", "blur"]) & (a.level == 5)
    rows = []
    for gname in ("sex", "age_band", "diag", "hr_range", "flagged"):
        for lab, g in a.groupby(gname, observed=True):
            nrec = g.record.nunique()
            c_ = g[g.axis == "clean"]
            h_ = g[g.hard_damage]
            o_ = g[(~g.hard_damage) & (g.axis != "clean")]
            rows.append(dict(group=gname, value=str(lab), recordings=nrec, clean_wrong=pct(int(c_.wrong5.sum()), len(c_)),
                             resolution_blur_level5_wrong=pct(int(h_.wrong5.sum()), len(h_)), all_other_versions_wrong=pct(int(o_.wrong5.sum()), len(o_))))
    b4 = pd.DataFrame(rows)
    b4.to_csv(OUT + "sectionB_subgroups.csv", index=False)
    L.append("## B4. Subgroups (all 150 recordings, 13 shared versions; wrong heart rate > 5 bpm; Wilson 95% in brackets)\n")
    L.append("Exploratory and small: most groups hold a few dozen recordings, so only large differences mean anything. "
             "'Flagged' = PTB-XL notes drift, noise, electrode problems, extra beats or pacemaker.\n")
    L.append(md_table(b4) + "\n")
    L.append("No-output rates are not shown here; they are in Section C.\n")
    open(OUT + "SECTION_B.md", "w", encoding="utf-8").write("\n".join(L))

    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 80)
    print(b1.to_string(index=False)); print()
    print(b2.to_string(index=False)); print()
    print(b2b.to_string(index=False)); print()
    print(f"HR detector label agreement: {100 * agree:.1f}% of {len(both)}"); print(b3.to_string(index=False)); print()
    print(b4.to_string(index=False))


if __name__ == "__main__":
    mp.freeze_support()
    main()
