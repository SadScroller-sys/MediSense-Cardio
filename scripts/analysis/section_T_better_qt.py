"""Section T (EXPLORATORY): a better QT method. Rules fixed BEFORE any code ran: docs/plan/analysis_plan_changes.md, 2026-11-14.
Median-beat QRS-onset / T-end measurement (own code, no NeuroKit2 delineation), 3 aggregators x 2 T-end methods = 6 candidates.
  python -I scripts/analysis/section_T_better_qt.py --dev     development on the first 50 ORIGINAL signals (page-layout windows), picks one candidate + one offset, writes sectionT_frozen.json
  python -I scripts/analysis/section_T_better_qt.py --test    test ONCE on the new 100: (a) original signal in the photo windows, (b) digitised clean page (primary). Refuses to run twice.
Reads only saved files. Writes results/analysis/sectionT_*.csv|json and SECTION_T.md."""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import glob
import json
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor

import neurokit2 as nk
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

warnings.filterwarnings("ignore")
ROOT = "D:/Capstone Project/"
R = ROOT + "results/"
OUT = R + "analysis/"
LEADS = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
LAYOUT = {"I": (0, 2.5), "II": (0, 10), "III": (0, 2.5), "aVR": (2.5, 5), "aVL": (2.5, 5), "aVF": (2.5, 5), "V1": (5, 7.5), "V2": (5, 7.5), "V3": (5, 7.5), "V4": (7.5, 10), "V5": (7.5, 10), "V6": (7.5, 10)}
# ---- constants fixed in the rules (2026-11-14) ----
SMOOTH_MS, PRE_MS, TMAX_MS, RR_FRAC = 10, 300, 600, 0.7
SLOPE_FRAC, ONSET_BACK_MS, QRS_SEARCH_MS = 0.05, 150, 60
BASE_FROM_MS, BASE_TO_MS, T_START_MS, TAN_SEARCH_MS, THR_FRAC, MIN_LEADS = 40, 10, 100, 200, 0.15, 4
CANDS = [f"{a}_{t}" for a in "ABC" for t in ("tangent", "threshold")]
TOL = (20, 40, 10)                  # median abs diff, 90% within, |bias| (ms): the acceptance rule
NAME = {"AVR": "aVR", "AVL": "aVL", "AVF": "aVF"}


def read_all_leads(rel):
    base = ROOT + "data/ptbxl/" + rel
    hdr = open(base + ".hea").read().splitlines()
    n = int(hdr[0].split()[1])
    names, gains = [], []
    for h in hdr[1:1 + n]:
        p = h.split()
        names.append(NAME.get(p[-1], p[-1]))
        gains.append(float(p[2].split("(")[0].split("/")[0]))
    dat = np.fromfile(base + ".dat", dtype="<i2").reshape(-1, n).astype(float)
    return {names[i]: dat[:, i] / gains[i] for i in range(n)}


def fill(x):
    ok = np.isfinite(x)
    return None if ok.sum() < 100 else np.interp(np.arange(len(x)), np.flatnonzero(ok), x[ok])


def lead2_rpeaks(x, fs):
    f = fill(x)
    if f is None:
        return np.array([], int)
    c = nk.ecg_clean(f, sampling_rate=fs, method="neurokit")
    _, info = nk.ecg_peaks(c, sampling_rate=fs)
    p = np.asarray(info.get("ECG_R_Peaks", []), int)
    ok = np.isfinite(x)
    w = int(0.05 * fs)
    return np.array([i for i in p if ok[max(0, i - w):i + w].all()], int)


def longest_run(ok):
    d = np.diff(np.r_[0, ok.astype(int), 0])
    s, e = np.flatnonzero(d == 1), np.flatnonzero(d == -1)
    if len(s) == 0:
        return 0, 0
    k = int(np.argmax(e - s))
    return int(s[k]), int(e[k])


def smooth(x, fs):
    n = max(3, int(SMOOTH_MS * fs / 1000) | 1)
    return np.convolve(x, np.ones(n) / n, mode="same")


def ms2n(ms, fs):
    return int(round(ms * fs / 1000.0))


def median_beat(sig, fs, a, b, rpk, tmax_ms):
    """Pointwise median of the beats [R - 300 ms, R + tmax] that lie inside the finite window [a, b). Returns (beat, n_beats) or (None, 0)."""
    if b - a < ms2n(PRE_MS + 100, fs):
        return None, 0
    seg = smooth(np.asarray(sig[a:b], float), fs)
    pre, post = ms2n(PRE_MS, fs), ms2n(tmax_ms, fs)
    beats = [seg[p - a - pre:p - a + post] for p in rpk if p - pre >= a + 2 and p + post <= b - 2]
    beats = [x for x in beats if len(x) == pre + post and np.isfinite(x).all()]
    if not beats:
        return None, 0
    return np.median(np.vstack(beats), axis=0), len(beats)


def beat_features(mb, fs):
    """QRS onset and T end (ms relative to the R anchor) from one median beat; the anchor is at index PRE_MS. Returns dict (NaN where it fails)."""
    out = dict(onset=np.nan, tend_tangent=np.nan, tend_threshold=np.nan)
    r0 = ms2n(PRE_MS, fs)
    d = np.gradient(mb) * fs
    lo, hi = max(1, r0 - ms2n(QRS_SEARCH_MS, fs)), min(len(mb) - 2, r0 + ms2n(QRS_SEARCH_MS, fs))
    smax = np.max(np.abs(d[lo:hi]))
    if not np.isfinite(smax) or smax < 1e-6:
        return out
    i = lo + int(np.argmax(np.abs(d[lo:r0 + 1])))
    limit = r0 - ms2n(ONSET_BACK_MS, fs)
    while i > max(limit, ms2n(BASE_FROM_MS, fs) + 1) and abs(d[i]) >= SLOPE_FRAC * smax:
        i -= 1
    onset = i
    b0, b1 = onset - ms2n(BASE_FROM_MS, fs), onset - ms2n(BASE_TO_MS, fs)
    if b0 < 0 or b1 <= b0:
        return out
    y = mb - np.median(mb[b0:b1])
    t0, t1 = r0 + ms2n(T_START_MS, fs), len(mb) - 1
    if t1 - t0 < ms2n(60, fs):
        return out
    tpk = t0 + int(np.argmax(np.abs(y[t0:t1 + 1])))
    if tpk > t1 - ms2n(20, fs):
        return out                                           # T peak at the edge of the window: the T wave is not complete
    yy = y * (1.0 if y[tpk] >= 0 else -1.0)
    dd = np.gradient(yy) * fs
    e = min(tpk + ms2n(TAN_SEARCH_MS, fs), len(mb) - 1)
    k = tpk + int(np.argmin(dd[tpk:e + 1]))
    slope = dd[k] / fs
    out["onset"] = (onset - r0) * 1000.0 / fs
    if slope < 0:
        te = k - yy[k] / slope
        if tpk < te <= len(mb) - 1 + ms2n(50, fs):
            out["tend_tangent"] = (te - r0) * 1000.0 / fs
    below = np.flatnonzero(yy[tpk:] <= THR_FRAC * yy[tpk])
    if len(below):
        out["tend_threshold"] = (tpk + below[0] - r0) * 1000.0 / fs
    return out


def measure_record(leads, fs, windows, rpk):
    """leads: dict lead -> array at fs (NaN = unread); windows: dict lead -> (a, b) in samples; rpk: R-peak indices of lead II at fs. Returns dict candidate -> QT (ms)."""
    res = {c: np.nan for c in CANDS}
    res["n_leads"] = 0
    if len(rpk) < 3:
        return res
    rr = np.median(np.diff(rpk)) * 1000.0 / fs
    tmax = min(TMAX_MS, RR_FRAC * rr)
    if tmax < 250:
        return res
    per = {}
    for L in LEADS:
        a, b = windows.get(L, (0, 0))
        if b - a <= 0 or L not in leads:
            continue
        mb, n = median_beat(leads[L], fs, a, b, rpk, tmax)
        if mb is None:
            continue
        f = beat_features(mb, fs)
        if np.isfinite(f["onset"]):
            per[L] = f
    res["n_leads"] = len(per)
    for t in ("tangent", "threshold"):
        key = f"tend_{t}"
        if "II" in per and np.isfinite(per["II"][key]):
            res[f"A_{t}"] = per["II"][key] - per["II"]["onset"]
        ok = [f for f in per.values() if np.isfinite(f[key])]
        if len(ok) >= MIN_LEADS:
            res[f"B_{t}"] = float(np.median([f[key] - f["onset"] for f in ok]))
            res[f"C_{t}"] = float(np.percentile([f[key] for f in ok], 90) - np.percentile([f["onset"] for f in ok], 10))
    return res


# ------------------------------------------------------------------ statistics
def stats(diff, tol_within=TOL[1], seed=0):
    x = pd.Series(diff).dropna()
    if len(x) < 5:
        return dict(n=len(x))
    ad = x.abs()
    out = dict(n=len(x), median_abs=float(ad.median()), p90_abs=float(ad.quantile(.9)), bias=float(x.mean()), within=float((ad <= tol_within).mean()))
    rng = np.random.default_rng(seed)
    bm, bb = [], []
    for _ in range(1000):
        s = rng.choice(len(x), len(x))
        bm.append(float(np.median(ad.values[s])))
        bb.append(float(np.mean(x.values[s])))
    out.update(median_abs_ci=(float(np.percentile(bm, 2.5)), float(np.percentile(bm, 97.5))), bias_ci=(float(np.percentile(bb, 2.5)), float(np.percentile(bb, 97.5))))
    return out


def meets(s):
    return bool(s.get("n", 0) >= 5 and s["median_abs"] <= TOL[0] and s["within"] >= 0.9 and abs(s["bias"]) <= TOL[2])


# ------------------------------------------------------------------ development
def dev_task(a):
    rec, rel500 = a
    orig = read_all_leads(rel500)
    fs = 500
    win = {L: (int(LAYOUT[L][0] * fs), int(LAYOUT[L][1] * fs) - 1) for L in LEADS}
    rpk = lead2_rpeaks(orig["II"], fs)
    row = dict(record=rec)
    row.update(measure_record(orig, fs, win, rpk))
    return row


def run_dev():
    t0 = time.time()
    ref = pd.read_csv(R + "extension/reference_check_150.csv")
    ref = ref[ref.set == "first50"]
    db = pd.read_csv(ROOT + "data/ptbxl/ptbxl_database.csv")
    db["record"] = db.filename_lr.str.split("/").str[-1]
    x12 = pd.read_csv(ROOT + "data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
    tasks = []
    for _, r in ref.iterrows():
        fl = db.loc[db.record == r.record, "filename_lr"].iloc[0]
        tasks.append((r.record, fl.replace("records100", "records500").replace("_lr", "_hr")))
    with ProcessPoolExecutor(max_workers=10) as ex:
        rows = list(ex.map(dev_task, tasks, chunksize=2))
    d = pd.DataFrame(rows).merge(ref[["record", "ecg_id"]], on="record")
    d["ref_qt"] = d.ecg_id.map(x12["QT_Int_Global"])
    d.to_csv(OUT + "sectionT_dev.csv", index=False)
    table = []
    for c in CANDS:
        ok = d[c].notna() & d.ref_qt.notna()
        diff = (d[c] - d.ref_qt)[ok]
        share = float(d[c].notna().mean())
        if len(diff) < 5:
            table.append(dict(cand=c, share=share, n=len(diff)))
            continue
        off = float(diff.median())
        rho = float(spearmanr(d.loc[ok, c], d.loc[ok, "ref_qt"])[0])
        table.append(dict(cand=c, share=share, n=len(diff), bias_before=float(diff.mean()), offset=off, median_abs_after=float((diff - off).abs().median()), rho=rho))
    t = pd.DataFrame(table)
    elig = t[(t.share >= 0.9) & t.median_abs_after.notna()].sort_values(["median_abs_after", "rho"], ascending=[True, False])
    chosen = None if elig.empty else elig.iloc[0]
    frozen = dict(candidate=None if chosen is None else str(chosen.cand), offset_ms=None if chosen is None else float(chosen.offset), development_recordings=int(len(d)),
                  table=t.round(3).to_dict(orient="records"), rule="highest share>=0.9, then smallest median abs diff after the offset, ties by rho", written=time.strftime("%Y-%m-%d %H:%M"))
    json.dump(frozen, open(OUT + "sectionT_frozen.json", "w"), indent=1)
    L = ["# Section T development (first 50 recordings, original 500 Hz signals cut to the page layout)", "",
         "Reference = 12SL QT. Offset = the median difference on these 50 recordings (applied before the median absolute difference is taken). Selection rule from the 2026-11-14 plan entry.", "",
         "| Candidate | Recordings with a value | n compared | Bias before offset (ms) | Offset (ms) | Median abs diff after offset (ms) | rho |", "|---|---|---|---|---|---|---|"]
    for _, r in t.iterrows():
        L.append(f"| {r.cand} | {100 * r.share:.0f}% | {int(r.n)} | " + (f"{r.bias_before:+.1f} | {r.offset:+.1f} | {r.median_abs_after:.1f} | {r.rho:.2f} |" if pd.notna(r.get('offset')) else "n/a | n/a | n/a | n/a |"))
    L += ["", f"**Frozen choice: {frozen['candidate']}, offset {frozen['offset_ms'] if frozen['offset_ms'] is None else round(frozen['offset_ms'], 1)} ms.**" if chosen is not None else "**No candidate reached 90% of recordings with a value; nothing is frozen.**"]
    open(OUT + "SECTION_T_dev.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))
    print("dev done in", round(time.time() - t0), "s")


# ------------------------------------------------------------------ test
def test_task(a):
    vid, npz, rel500, with_original = a
    z = np.load(npz)
    dig = {L: np.asarray(z[L], float) / 1000.0 for L in LEADS}
    win = {L: longest_run(np.isfinite(dig[L])) for L in LEADS}
    row = dict(variant_id=vid)
    try:
        for k, v in measure_record(dig, 1000, win, lead2_rpeaks(dig["II"], 1000)).items():
            row[f"dig_{k}"] = v
    except Exception as e:
        row["error_dig"] = str(e)[:80]
    if with_original:
        try:
            orig = read_all_leads(rel500)
            win5 = {L: (a_ // 2, b_ // 2) for L, (a_, b_) in win.items()}
            for k, v in measure_record(orig, 500, win5, lead2_rpeaks(orig["II"], 500)).items():
                row[f"orig_{k}"] = v
        except Exception as e:
            row["error_orig"] = str(e)[:80]
    return row


def run_test():
    fr = json.load(open(OUT + "sectionT_frozen.json"))
    if not fr.get("candidate"):
        sys.exit("nothing is frozen: run --dev first")
    out_csv = OUT + "sectionT_test_per_image.csv"
    if os.path.exists(out_csv) and "--force" not in sys.argv:
        sys.exit("The test was already run once (rule: run ONCE). Use --force only to repeat an identical run after a crash.")
    t0 = time.time()
    cand, off = fr["candidate"], fr["offset_ms"]
    ext = pd.read_csv(R + "extension/results_extension.csv")
    sel = pd.read_csv(R + "extension/selected_100.csv").set_index("record")
    files = {os.path.basename(f)[:-4]: f for f in glob.glob(R + "extension/extension_digitized_12lead/**/*.npz", recursive=True)}
    tasks = []
    for _, r in ext.iterrows():
        if r.variant_id in files and r.record in sel.index:
            tasks.append((r.variant_id, files[r.variant_id], sel.loc[r.record, "filename_lr"].replace("records100", "records500").replace("_lr", "_hr"), r.axis == "clean"))
    tasks.sort(key=lambda t: not t[3])
    with ProcessPoolExecutor(max_workers=10) as ex:
        rows = list(ex.map(test_task, tasks, chunksize=4))
    m = pd.DataFrame(rows).merge(ext[["variant_id", "record", "axis", "level"]], on="variant_id")
    m["ecg_id"] = m.record.map(sel.ecg_id)
    x12 = pd.read_csv(ROOT + "data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
    m["ref_qt"] = m.ecg_id.map(x12["QT_Int_Global"])
    m["qt_dig"] = m[f"dig_{cand}"] - off
    m["qt_orig"] = m[f"orig_{cand}"] - off if f"orig_{cand}" in m else np.nan
    m.to_csv(out_csv, index=False)
    print("test measured", len(m), "images in", round(time.time() - t0), "s")
    return m


def summary(m, fr):
    sys.path.insert(0, ROOT + "safeguard")
    import ecg_traffic_light as T
    model = T.load_model()
    f = pd.read_csv(OUT + "sectionD2_features.csv").set_index("variant_id")
    m = m.copy()
    m["green"] = [bool(v in f.index and (f.loc[v, "n_beats"] >= 3) and T.score_from_features(f.loc[v].to_dict(), model) < model["amber_threshold"]) for v in m.variant_id]
    clean = m[(m.axis == "clean") & (m.record != "21205_lr")]
    L = ["# Section T: a better QT method, tested once on the new 100 (EXPLORATORY, added after the freeze)", "",
         "Rules fixed before any code ran (`docs/plan/analysis_plan_changes.md`, 2026-11-14). Development on the first 50 original signals chose "
         f"**candidate {fr['candidate']}** with a constant offset of **{fr['offset_ms']:+.1f} ms** (see the development table below). The acceptance rule is the assistant's proposal and is **not approved by the guide**: "
         "median absolute difference <= 20 ms, at least 90% within 40 ms, |bias| <= 10 ms, and at least 90% of recordings with a value, for BOTH the original signal in the photo windows (a) and the digitised photo (b).", "",
         f"Primary set: clean pages of the new 100 recordings, 21205 excluded: {len(clean)} recordings. Difference = measured minus 12SL (ms).", "",
         "| Measurement | Recordings with a value | rho with 12SL | Median abs diff (95% CI) | 90th pct abs diff | Bias (95% CI) | Within 40 ms | Rule |", "|---|---|---|---|---|---|---|---|"]
    res = {}
    for label, col, key in [("(a) frozen method on the original signal, photo windows", "qt_orig", "a"), ("(b) digitised clean page", "qt_dig", "b")]:
        ok = clean[col].notna() & clean.ref_qt.notna()
        s = stats((clean[col] - clean.ref_qt)[ok])
        res[key] = (s, float(clean[col].notna().mean()))
        rho = spearmanr(clean.loc[ok, col], clean.loc[ok, "ref_qt"])[0] if ok.sum() > 4 else np.nan
        if s.get("n", 0) >= 5:
            L.append(f"| {label} | {int(clean[col].notna().sum())} of {len(clean)} | {rho:.2f} | {s['median_abs']:.1f} ({s['median_abs_ci'][0]:.1f} to {s['median_abs_ci'][1]:.1f}) | {s['p90_abs']:.1f} | {s['bias']:+.1f} ({s['bias_ci'][0]:+.1f} to {s['bias_ci'][1]:+.1f}) | {100 * s['within']:.0f}% | **{'meets' if meets(s) else 'does not meet'}** |")
        else:
            L.append(f"| {label} | {int(clean[col].notna().sum())} of {len(clean)} | n/a | n/a | n/a | n/a | n/a | does not meet |")
    ok = clean.qt_dig.notna() & clean.qt_orig.notna()
    sc = stats((clean.qt_dig - clean.qt_orig)[ok])
    if sc.get("n", 0) >= 5:
        L.append(f"| (c) digitised minus (a): what the photo adds | {int(ok.sum())} | | {sc['median_abs']:.1f} | {sc['p90_abs']:.1f} | {sc['bias']:+.1f} | | |")
    va = res["a"][0]
    vb = res["b"][0]
    validated = bool(meets(va) and meets(vb) and res["a"][1] >= 0.9 and res["b"][1] >= 0.9)
    L += ["", f"Share with a value: original {100 * res['a'][1]:.0f}%, digitised {100 * res['b'][1]:.0f}%. **QT validated under the pre-set rule: {'YES' if validated else 'NO'}** "
              f"((a) meets: {meets(va)}, (b) meets: {meets(vb)}, both value shares at least 90%: {res['a'][1] >= 0.9 and res['b'][1] >= 0.9}).", "",
          "For comparison, the earlier NeuroKit2 method (Section S): original 36 ms typical error, digitised 26 ms, 54 to 55% within 40 ms, 69 to 70% of recordings with a value.", "",
          "## Secondary (descriptive): digitised, all versions, by damage type and level; GREEN images only", "",
          "| Group | Images | Median abs / bias (ms) | Within 40 ms | Value share |", "|---|---|---|---|---|"]
    allv = m[m.record != "21205_lr"].copy()
    allv["group"] = np.where(allv.axis == "clean", "clean", allv.axis + " " + allv.level.astype(str))
    for g, x in [("all versions", allv), ("GREEN images only", allv[allv.green])] + [(g, x) for g, x in allv.groupby("group", sort=False)]:
        ok = x.qt_dig.notna() & x.ref_qt.notna()
        d = (x.qt_dig - x.ref_qt)[ok]
        L.append(f"| {g} | {len(x)} | " + (f"{d.abs().median():.0f} / {d.mean():+.0f} | {100 * (d.abs() <= 40).mean():.0f}% | " if len(d) >= 5 else "n/a | n/a | ") + f"{100 * x.qt_dig.notna().mean():.0f}% |")
    L += ["", "## Development table (first 50 recordings; for the record)", ""]
    L += ["| Candidate | Recordings with a value | Bias before offset | Offset | Median abs after offset | rho |", "|---|---|---|---|---|---|"]
    for r in fr["table"]:
        L.append(f"| {r['cand']} | {100 * r['share']:.0f}% | " + (f"{r['bias_before']:+.1f} | {r['offset']:+.1f} | {r['median_abs_after']:.1f} | {r['rho']:.2f} |" if r.get("offset") is not None else "n/a | n/a | n/a | n/a |"))
    L += ["", "## Limits", "", "- 12SL is an algorithm, not an expert measurement; 12SL and Glasgow differ by 4 to 6.5 ms.",
          "- The method was developed on 50 recordings with 6 candidates and one offset, so a small amount of overfitting is possible; the 100 test recordings were not used to tune it.",
          "- One digitiser, simulated pages. QTc is not evaluated. Nothing from this section is shown to patients unless the verdict above says YES."]
    return "\n".join(L)


# ------------------------------------------------------------------ confirmation on NEW photos (own phone), method and offset unchanged
def confirm_task(a):
    key, npz = a
    z = np.load(npz)
    dig = {L: np.asarray(z[L], float) / 1000.0 for L in LEADS}
    win = {L: longest_run(np.isfinite(dig[L])) for L in LEADS}
    row = dict(key=key)
    try:
        row.update(measure_record(dig, 1000, win, lead2_rpeaks(dig["II"], 1000)))
    except Exception as e:
        row["error"] = str(e)[:80]
    return row


def run_confirm():
    fr = json.load(open(OUT + "sectionT_frozen.json"))
    cand, off = fr["candidate"], fr["offset_ms"]
    out_csv = OUT + "sectionT_confirm_per_photo.csv"
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
                else:
                    print("missing", path)
    with ProcessPoolExecutor(max_workers=10) as ex:
        rows = list(ex.map(confirm_task, tasks, chunksize=2))
    d = pd.DataFrame(rows)
    for c in ("set", "photo", "version", "page", "ecg_id", "shot"):
        d[c] = d.key.map(lambda k: meta[k][c])
    d["ref_qt"] = d.ecg_id.map(x12["QT_Int_Global"])
    d["qt"] = d[cand] - off
    d.to_csv(out_csv, index=False)
    L = ["# Section T confirmation: the frozen QT method on NEW photos (own phone; EXPLORATORY)", "",
         f"Method and offset exactly as frozen before the held-out test (candidate {cand}, offset {off:+.1f} ms); rules fixed before the run (`docs/plan/analysis_plan_changes.md`, 2026-11-14, later entry). "
         "Photos of drawn PTB-XL pages shown on a laptop screen, one phone; P01-P30 and Q01-Q20 (not among the 150). Reference = 12SL QT. A photo with no QT value counts as \"no value\". "
         "The acceptance rule is the assistant's proposal, not approved by the guide. The two photos of a page are not independent, so the intervals are optimistic.", "",
         "| Photos | n photos | With a value | rho | Median abs diff (95% CI) | 90th pct | Bias (95% CI) | Within 40 ms | Rule |", "|---|---|---|---|---|---|---|---|---|"]
    verdict = {}
    groups = [("V2 straightened, all (primary)", d[d.version == "V2"]), ("V0 original, all", d[d.version == "V0"])]
    for ver in ("V2", "V0"):
        for shot in ("straight", "angled"):
            groups.append((f"{ver} {shot}", d[(d.version == ver) & (d.shot == shot)]))
        for s in ("P", "Q"):
            groups.append((f"{ver} set {s}", d[(d.version == ver) & (d.set == s)]))
    for name, x in groups:
        ok = x.qt.notna() & x.ref_qt.notna()
        s = stats((x.qt - x.ref_qt)[ok])
        share = float(x.qt.notna().mean())
        rho = spearmanr(x.loc[ok, "qt"], x.loc[ok, "ref_qt"])[0] if ok.sum() > 4 else np.nan
        v = bool(meets(s) and share >= 0.9)
        verdict[name] = (v, share, s)
        if s.get("n", 0) >= 5:
            L.append(f"| {name} | {len(x)} | {int(x.qt.notna().sum())} ({100 * share:.0f}%) | {rho:.2f} | {s['median_abs']:.1f} ({s['median_abs_ci'][0]:.1f} to {s['median_abs_ci'][1]:.1f}) | {s['p90_abs']:.1f} | {s['bias']:+.1f} ({s['bias_ci'][0]:+.1f} to {s['bias_ci'][1]:+.1f}) | {100 * s['within']:.0f}% | **{'meets' if v else 'does not meet'}** |")
        else:
            L.append(f"| {name} | {len(x)} | {int(x.qt.notna().sum())} ({100 * share:.0f}%) | n/a | n/a | n/a | n/a | n/a | does not meet |")
    v2 = verdict["V2 straightened, all (primary)"]
    L += ["", f"**Confirmed on new photos under the pre-set rule (primary, straightened): {'YES' if v2[0] else 'NO'}** "
              f"(median abs diff {v2[2].get('median_abs', float('nan')):.1f} ms, bias {v2[2].get('bias', float('nan')):+.1f} ms, within 40 ms {100 * v2[2].get('within', float('nan')):.0f}%, photos with a value {100 * v2[1]:.0f}%).", "",
          "## Limits", "", "- One phone, one screen, drawn pages shown on a screen, 50 recordings; the two photos of a page are not independent.",
          "- 12SL is an algorithm, not an expert measurement. QTc is not evaluated.",
          "- Nothing from this section is shown to patients unless the verdict above says YES AND the held-out test (Section T) is also met."]
    open(OUT + "SECTION_T_confirm.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    if "--confirm" in sys.argv:
        run_confirm()
    elif "--dev" in sys.argv:
        run_dev()
    elif "--test" in sys.argv:
        mm = run_test()
        open(OUT + "SECTION_T.md", "w", encoding="utf-8").write(summary(mm, json.load(open(OUT + "sectionT_frozen.json"))))
        print("written SECTION_T.md")
    else:
        print(__doc__)
