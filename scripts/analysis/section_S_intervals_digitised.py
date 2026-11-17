"""Section S (EXPLORATORY, gap 3 after the freeze; rules fixed BEFORE the run in docs/plan/analysis_plan_changes.md, 2026-11-13, amended the same day before any result):
PR, QRS and QT measured on the DIGITISED lead II (the only lead that covers the full 10 s of a page) of the new 100 recordings and compared with the commercial 12SL global values (PTB-XL+).
Frozen methods (highest rho on the first 50 original signals, lead II): QT = NeuroKit2 cwt delineation, PR = dwt, QRS = dwt. Beats whose window [R - 0.30 s, R + 0.60 s] holds a gap or leaves the page are dropped;
per beat QT = T_off - R_on, QRS = R_off - R_on, PR = R_on - P_on; the recording value is the median over beats (at least 3 beats, else no value).
Three measurements: (a) the SAME method on the ORIGINAL 500 Hz lead II, (b) the digitised lead II (primary), (c) digitised minus (a).
Writes results/analysis/sectionS_per_image.csv and results/analysis/SECTION_S.md.   Run:  python -I scripts/analysis/section_S_intervals_digitised.py"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import glob
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
REF = {"qt": "QT_Int_Global", "pr": "PR_Int_Global", "qrs": "QRS_Dur_Global"}
RULE = {"qt": (20, 40, 10), "pr": (20, 40, 10), "qrs": (10, 20, 5)}   # median abs diff, 90% within, |bias| (ms)  -- fixed before the run
PRE_MS, POST_MS, MIN_BEATS = 300, 600, 3
METHOD = {"qt": "cwt", "pr": "dwt", "qrs": "dwt"}   # fixed before the run


def read_all_leads(rel):
    """PTB-XL record (16-bit) -> dict lead -> mV, gain read from the header."""
    base = ROOT + "data/ptbxl/" + rel
    hdr = open(base + ".hea").read().splitlines()
    n = int(hdr[0].split()[1])
    names, gains = [], []
    for h in hdr[1:1 + n]:
        p = h.split()
        names.append(p[-1])
        gains.append(float(p[2].split("(")[0].split("/")[0]))
    dat = np.fromfile(base + ".dat", dtype="<i2").reshape(-1, n).astype(float)
    return {names[i]: dat[:, i] / gains[i] for i in range(n)}


def fill(x):
    ok = np.isfinite(x)
    if ok.sum() < 100:
        return None
    return np.interp(np.arange(len(x)), np.flatnonzero(ok), x[ok])


def lead_ii_rpeaks(x, fs):
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


def delineate(cl, rl, fs, method):
    _, w = nk.ecg_delineate(cl, {"ECG_R_Peaks": rl}, sampling_rate=fs, method=method)
    g = lambda k: np.array(w.get(k, []), dtype=float)
    return g("ECG_P_Onsets"), g("ECG_R_Onsets"), g("ECG_R_Offsets"), g("ECG_T_Offsets")


def measure_lead2(sig, fs):
    """QT / PR / QRS (ms) from one lead II array at rate fs (NaN = unread). Returns dict with the median over usable beats and the beat counts."""
    res = {k: np.nan for k in ("qt", "pr", "qrs")}
    res.update(n_beats_qt=0, n_beats_pr=0, n_beats_qrs=0)
    f = fill(sig)
    if f is None:
        return res
    ok = np.isfinite(sig)
    cl = nk.ecg_clean(f, sampling_rate=fs, method="neurokit")
    _, info = nk.ecg_peaks(cl, sampling_rate=fs)
    pre, post = int(PRE_MS * fs / 1000), int(POST_MS * fs / 1000)
    r = np.array([p for p in np.asarray(info.get("ECG_R_Peaks", []), int) if p - pre >= 0 and p + post < len(sig) and ok[p - pre:p + post].all()], int)
    if len(r) < MIN_BEATS:
        return res
    ms = 1000.0 / fs
    for method in sorted(set(METHOD.values())):
        try:
            pon, ron, roff, toff = delineate(cl, r, fs, method)
        except Exception:
            continue
        n = min(len(pon), len(ron), len(roff), len(toff))
        pon, ron, roff, toff = pon[:n], ron[:n], roff[:n], toff[:n]
        for k, v in (("qt", (toff - ron) * ms), ("pr", (ron - pon) * ms), ("qrs", (roff - ron) * ms)):
            if METHOD[k] != method:
                continue
            v = v[np.isfinite(v) & (v > 0)]
            res[f"n_beats_{k}"] = int(len(v))
            if len(v) >= MIN_BEATS:
                res[k] = float(np.median(v))
    return res


def work(task):
    vid, npz, rel500, with_original = task
    z = np.load(npz)
    row = dict(variant_id=vid)
    try:
        for k, v in measure_lead2(np.asarray(z["II"], float) / 1000.0, 1000).items():
            row[f"dig_{k}"] = v
    except Exception as e:
        row["error_dig"] = str(e)[:80]
    if with_original:
        try:
            orig = read_all_leads(rel500)                                         # 500 Hz
            for k, v in measure_lead2(orig["II"], 500).items():
                row[f"orig_{k}"] = v
        except Exception as e:
            row["error_orig"] = str(e)[:80]
    return row


def stats(d, diff, tol, seed=0):
    """d: DataFrame with columns; diff: Series (measured - reference), may contain NaN. Returns dict."""
    x = diff.dropna()
    if len(x) < 5:
        return dict(n=len(x))
    ad = x.abs()
    out = dict(n=len(x), median_abs=float(ad.median()), p90_abs=float(ad.quantile(.9)), bias=float(x.mean()), within=float((ad <= tol).mean()))
    rng = np.random.default_rng(seed)
    idx = np.arange(len(x))
    bm, bb = [], []
    for _ in range(1000):
        s = rng.choice(idx, len(idx))
        bm.append(float(np.median(ad.values[s])))
        bb.append(float(np.mean(x.values[s])))
    out.update(median_abs_ci=(float(np.percentile(bm, 2.5)), float(np.percentile(bm, 97.5))), bias_ci=(float(np.percentile(bb, 2.5)), float(np.percentile(bb, 97.5))))
    return out


def meets(p, s):
    tm, tw, tb = RULE[p]
    return bool(s.get("n", 0) >= 5 and s["median_abs"] <= tm and s["within"] >= 0.9 and abs(s["bias"]) <= tb)


def main():
    t0 = time.time()
    ext = pd.read_csv(R + "extension/results_extension.csv")
    sel = pd.read_csv(R + "extension/selected_100.csv").set_index("record")
    files = {os.path.basename(f)[:-4]: f for f in glob.glob(R + "extension/extension_digitized_12lead/**/*.npz", recursive=True)}
    tasks = []
    for _, r in ext.iterrows():
        if r.variant_id in files and r.record in sel.index:
            rel500 = sel.loc[r.record, "filename_lr"].replace("records100", "records500").replace("_lr", "_hr")
            tasks.append((r.variant_id, files[r.variant_id], rel500, r.axis == "clean"))
    tasks.sort(key=lambda t: not t[3])                                           # clean pages first
    rows = []
    with ProcessPoolExecutor(max_workers=10) as ex:
        for i, row in enumerate(ex.map(work, tasks, chunksize=4)):
            rows.append(row)
            if (i + 1) % 100 == 0:
                print(i + 1, "of", len(tasks), round(time.time() - t0), "s", flush=True)
    m = pd.DataFrame(rows).merge(ext[["variant_id", "record", "axis", "level"]], on="variant_id")
    m["ecg_id"] = m.record.map(sel.ecg_id)
    x12 = pd.read_csv(ROOT + "data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
    for k, c in REF.items():
        m[f"ref_{k}"] = m.ecg_id.map(x12[c])
    os.makedirs(OUT, exist_ok=True)
    m.to_csv(OUT + "sectionS_per_image.csv", index=False)
    print("measured", len(m), "images in", round(time.time() - t0), "s", flush=True)
    return m


def summary(m):
    sys.path.insert(0, ROOT + "safeguard")
    import ecg_traffic_light as T
    model = T.load_model()
    f = pd.read_csv(OUT + "sectionD2_features.csv").set_index("variant_id")
    m = m.copy()
    m["green"] = [bool(vid in f.index and (f.loc[vid, "n_beats"] >= 3) and T.score_from_features(f.loc[vid].to_dict(), model) < model["amber_threshold"]) for vid in m.variant_id]
    clean = m[(m.axis == "clean") & (m.record != "21205_lr")].copy()            # 21205 = unreliable recording, excluded as everywhere else
    L = ["# Section S: PR, QRS and QT on the digitised signals, against 12SL (EXPLORATORY, added after the freeze)", "",
         "Rules and the acceptance rule were written before the run (`docs/plan/analysis_plan_changes.md`, 2026-11-13). The acceptance rule was proposed by the assistant and is **not approved by the guide**. "
         "Reference = PTB-XL+ 12SL global value. Difference = measured minus 12SL (ms). Frozen methods (lead II only, amended before any result): QT cwt, PR dwt, QRS dwt; beats with a gap or outside the page dropped; "
         "median over beats, at least 3 beats. Tolerance rule (median absolute difference / share within / |bias|): QT and PR 20 ms / 90% within 40 ms / 10 ms; QRS 10 ms / 90% within 20 ms / 5 ms.", "",
         f"Primary set: clean pages of the new 100 recordings, 21205 excluded (unreliable): {len(clean)} recordings.", ""]
    verdict = {}
    for p, name in [("qt", "QT"), ("pr", "PR"), ("qrs", "QRS")]:
        tm, tw, tb = RULE[p]
        L += [f"## {name} (rule: median |diff| <= {tm} ms, 90% within {tw} ms, |bias| <= {tb} ms)", "",
              "| Measurement | Recordings with a value | rho with 12SL | Median abs diff (95% CI) | 90th pct abs diff | Bias (95% CI) | Within tolerance | Rule |", "|---|---|---|---|---|---|---|---|"]
        res = {}
        for label, col in [("(a) same method on the original lead II (500 Hz)", f"orig_{p}"), ("(b) digitised clean page", f"dig_{p}")]:
            ok = clean[col].notna() & clean[f"ref_{p}"].notna()
            s = stats(clean, (clean[col] - clean[f"ref_{p}"])[ok], tw)
            res[label[:3]] = s
            rho = spearmanr(clean.loc[ok, col], clean.loc[ok, f"ref_{p}"])[0] if ok.sum() > 4 else np.nan
            has = int(clean[col].notna().sum())
            if s.get("n", 0) >= 5:
                L.append(f"| {label} | {has} of {len(clean)} | {rho:.2f} | {s['median_abs']:.1f} ({s['median_abs_ci'][0]:.1f} to {s['median_abs_ci'][1]:.1f}) | {s['p90_abs']:.1f} | {s['bias']:+.1f} ({s['bias_ci'][0]:+.1f} to {s['bias_ci'][1]:+.1f}) | {100 * s['within']:.0f}% | **{'meets' if meets(p, s) else 'does not meet'}** |")
            else:
                L.append(f"| {label} | {has} of {len(clean)} | n/a | n/a | n/a | n/a | n/a | does not meet |")
        ok = clean[f"dig_{p}"].notna() & clean[f"orig_{p}"].notna()
        sc = stats(clean, (clean[f"dig_{p}"] - clean[f"orig_{p}"])[ok], tw)
        if sc.get("n", 0) >= 5:
            L.append(f"| (c) digitised minus (a): what the photo adds | {int(ok.sum())} | | {sc['median_abs']:.1f} | {sc['p90_abs']:.1f} | {sc['bias']:+.1f} | | |")
        share = clean[f"dig_{p}"].notna().mean()
        validated = bool(meets(p, res.get("(a)", {})) and meets(p, res.get("(b)", {})) and share >= 0.9)
        verdict[name] = (validated, share, meets(p, res.get("(a)", {})), meets(p, res.get("(b)", {})))
        L += ["", f"Share of recordings with a digitised value: {100 * share:.0f}%. **Validated under the pre-set rule: {'YES' if validated else 'NO'}** "
                  f"((a) meets: {verdict[name][2]}, (b) meets: {verdict[name][3]}, value share at least 90%: {share >= 0.9}).", ""]
    L += ["## Summary", "", "| Parameter | (a) original lead II | (b) digitised clean page | Validated |", "|---|---|---|---|"]
    for k, (v, sh, a, b) in verdict.items():
        L.append(f"| {k} | {'meets' if a else 'does not meet'} | {'meets' if b else 'does not meet'} | {'YES' if v else 'NO'} |")
    L += ["", "## Secondary (descriptive): digitised, all versions, by damage type and level; and GREEN images only", "",
          "GREEN here = safeguard score below the AMBER threshold (0.2585) and at least 3 beats; the out-of-range guard is not applied (as written in the rules). Bias and median absolute difference in ms.", "",
          "| Group | Images | QT median abs / bias | PR median abs / bias | QRS median abs / bias | QT value share |", "|---|---|---|---|---|---|"]
    allv = m[m.record != "21205_lr"].copy()
    allv["group"] = np.where(allv.axis == "clean", "clean", allv.axis + " " + allv.level.astype(str))
    groups = [("all versions", allv), ("GREEN images only", allv[allv.green])] + [(g, x) for g, x in allv.groupby("group", sort=False)]
    for g, x in groups:
        cells = []
        for p in ("qt", "pr", "qrs"):
            ok = x[f"dig_{p}"].notna() & x[f"ref_{p}"].notna()
            d = (x[f"dig_{p}"] - x[f"ref_{p}"])[ok]
            cells.append(f"{d.abs().median():.0f} / {d.mean():+.0f}" if len(d) >= 5 else "n/a")
        L.append(f"| {g} | {len(x)} | " + " | ".join(cells) + f" | {100 * x.dig_qt.notna().mean():.0f}% |")
    L += ["", "## Limits", "", "- 12SL is an algorithm, not an expert annotation; 12SL and Glasgow differ by 4 to 6.5 ms for QT, so tolerances below that are not meaningful.",
          "- One digitiser, simulated pages, 99 recordings in the primary set; lead II only (the other leads cover only 2.5 s of a page, too short for the wavelet detector), which is weaker than the median-of-12-leads method on the original signal (QT rho 0.56 instead of 0.66).",
          "- The acceptance thresholds are the assistant's proposal. A different threshold could change a verdict; the table above gives the raw errors so a reader can apply their own.",
          "- QTc is not evaluated. Nothing from this section is shown to patients unless the Validated column says YES."]
    return "\n".join(L)


if __name__ == "__main__":
    if os.path.exists(OUT + "sectionS_per_image.csv") and "--reuse" in sys.argv:
        mm = pd.read_csv(OUT + "sectionS_per_image.csv")
    else:
        mm = main()
    open(OUT + "SECTION_S.md", "w", encoding="utf-8").write(summary(mm))
    print("written SECTION_S.md")
