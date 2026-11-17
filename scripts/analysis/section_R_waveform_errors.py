"""Section R (EXPLORATORY, gap 1 after the freeze; rules fixed BEFORE the run in docs/plan/analysis_plan_changes.md, 2026-11-13):
waveform errors of the digitised lead II against the true lead II: MAE and RMSE (mV), Pearson r, gain error, R-peak amplitude error (mV), R-peak timing error (ms), alignment lag (ms).
Truth: PTB-XL records100 lead II (100 Hz, mV) resampled to 1,000 Hz (simulated sets and own-phone pages) or the exported Challenge lead II (real captures).
Alignment: shift within +-0.5 s maximising the Pearson correlation on the overlapping finite samples; means removed on the overlap; the gain is NOT fitted.
Reads only saved results. Writes results/analysis/sectionR_waveform_per_image.csv and results/analysis/SECTION_R.md.
Run:  python -I scripts/analysis/section_R_waveform_errors.py"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import glob
import time
import warnings

import neurokit2 as nk
import numpy as np
import pandas as pd
from scipy.signal import resample

warnings.filterwarnings("ignore")
ROOT = "D:/Capstone Project/"
R = ROOT + "results/"
OUT = R + "analysis/"
FS = 1000


def read_ptbxl_lead2(filename_lr):
    """PTB-XL records100 lead II in mV (16-bit, gain read from the header)."""
    base = ROOT + "data/ptbxl/" + filename_lr
    hdr = open(base + ".hea").read().splitlines()
    line = [h for h in hdr[1:] if h.split()[-1] == "II"][0].split()
    gain = float(line[2].split("(")[0].split("/")[0])
    n_leads = int(hdr[0].split()[1])
    dat = np.fromfile(base + ".dat", dtype="<i2").reshape(-1, n_leads)
    names = [h.split()[-1] for h in hdr[1:1 + n_leads]]
    return dat[:, names.index("II")].astype(float) / gain


def to_1k(sig, fs):
    n = int(round(len(sig) / fs * FS))
    x = resample(np.asarray(sig, float), n)
    return x[:10000] if n >= 10000 else np.pad(x, (0, 10000 - n), constant_values=np.nan)


def fill(x):
    ok = np.isfinite(x)
    if ok.sum() < 100:
        return None
    return np.interp(np.arange(len(x)), np.flatnonzero(ok), x[ok])


def rpeaks(x):
    """R-peak indices on the cleaned signal; peaks inside gaps of a digitised signal are dropped."""
    f = fill(x)
    if f is None:
        return np.array([], int)
    c = nk.ecg_clean(f, sampling_rate=FS, method="neurokit")
    _, info = nk.ecg_peaks(c, sampling_rate=FS)
    p = np.asarray(info.get("ECG_R_Peaks", []), int)
    ok = np.isfinite(x)
    return np.array([i for i in p if ok[max(0, i - 50):i + 50].all()], int)


def _corr(a, b, lag):
    n = len(a)
    if lag >= 0:
        x, y = a[:n - lag], b[lag:]
    else:
        x, y = a[-lag:], b[:n + lag]
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < len(a) * 0.2:
        return -2.0
    x, y = x[m], y[m]
    sx, sy = x.std(), y.std()
    if sx < 1e-9 or sy < 1e-9:
        return -2.0
    return float(np.mean((x - x.mean()) * (y - y.mean())) / (sx * sy))


def best_lag(true, dig, max_ms=500):
    """lag (ms): dig[i + lag] matches true[i]. Coarse at 250 Hz, refined at 1 ms."""
    a4, b4 = true[::4], dig[::4]
    cs = [(_corr(a4, b4, L), L) for L in range(-max_ms // 4, max_ms // 4 + 1)]
    c0 = max(cs)[1] * 4
    fine = [(_corr(true, dig, L), L) for L in range(c0 - 8, c0 + 9)]
    r, L = max(fine)
    return L, r


def metrics(true, dig):
    d = dict(readable_share=float(np.isfinite(dig).mean()))
    if d["readable_share"] < 0.5 or np.isfinite(true).sum() < 5000:
        return d
    L, r = best_lag(true, dig)
    n = len(true)
    t = true[:n - L] if L >= 0 else true[-L:]
    g = dig[L:] if L >= 0 else dig[:n + L]
    m = np.isfinite(t) & np.isfinite(g)
    t, g = t[m], g[m]
    t = t - t.mean()
    g = g - g.mean()
    err = g - t
    d.update(lag_ms=L, pearson_r=float(np.corrcoef(t, g)[0, 1]), mae_mV=float(np.mean(np.abs(err))), rmse_mV=float(np.sqrt(np.mean(err ** 2))),
             gain_error_pct=100.0 * ((np.percentile(g, 95) - np.percentile(g, 5)) / (np.percentile(t, 95) - np.percentile(t, 5)) - 1.0), n_overlap=int(m.sum()))
    # R peaks after alignment
    tp = rpeaks(true)
    dp = rpeaks(dig) - L
    am, tm = [], []
    tt = true - np.nanmean(true)
    dd = dig - np.nanmean(dig)
    used = set()
    for p in tp:
        if len(dp) == 0:
            break
        j = int(np.argmin(np.abs(dp - p)))
        if abs(dp[j] - p) <= 100 and j not in used:
            used.add(j)
            q = int(dp[j] + L)
            if 0 <= q < len(dd) and np.isfinite(dd[q]) and np.isfinite(tt[p]):
                tm.append(abs(dp[j] - p))
                am.append(dd[q] - tt[p])
    d.update(n_true_beats=int(len(tp)), n_matched_beats=len(tm),
             timing_err_ms=float(np.median(tm)) if tm else np.nan, rpeak_amp_err_mV=float(np.median(am)) if am else np.nan)
    return d


def run():
    t0 = time.time()
    rows = []
    # ---- simulated new 100
    ext = pd.read_csv(R + "extension/results_extension.csv")
    sel = pd.read_csv(R + "extension/selected_100.csv").set_index("record")
    files = {os.path.basename(f)[:-4]: f for f in glob.glob(R + "extension/extension_digitized_12lead/**/*.npz", recursive=True)}
    cache = {}
    for i, r in ext.iterrows():
        f = files.get(r.variant_id)
        if f is None or r.record not in sel.index:
            continue
        if r.record not in cache:
            cache[r.record] = to_1k(read_ptbxl_lead2(sel.loc[r.record, "filename_lr"]), 100)
        dig = np.load(f)["II"].astype(float) / 1000.0
        rows.append(dict(set="simulated new100", variant_id=r.variant_id, recording=r.record, group=f"{r.axis} {r.level}" if r.axis != "clean" else "clean", **metrics(cache[r.record], dig)))
        if (i + 1) % 200 == 0:
            print("sim", i + 1, round(time.time() - t0), "s", flush=True)
    # ---- real captures (lead II truth only)
    tz = np.load(R + "truth/truth_lead_II.npz", allow_pickle=True)
    tmeta = pd.read_csv(R + "truth/truth_meta.csv").set_index("id")
    tcache = {}
    for name, csv, folder in [("real Arm C", "armC/results_armC.csv", "armC/armC_digitized_12lead"), ("real C+", "armCext/results_armCext_all.csv", "armCext/armCext_digitized_12lead_all")]:
        rr = pd.read_csv(R + csv)
        fl = {os.path.basename(f)[:-4]: f for f in glob.glob(R + folder + "/**/*.npz", recursive=True)}
        for i, r in rr.iterrows():
            f = fl.get(r.variant_id)
            rid = int(str(r.variant_id).split("__")[0])
            if f is None or f"r{rid}" not in tz.files:
                continue
            if rid not in tcache:
                tcache[rid] = to_1k(tz[f"r{rid}"], float(tmeta.loc[rid, "fs"]))
            dig = np.load(f)["II"].astype(float) / 1000.0
            rows.append(dict(set=name, variant_id=r.variant_id, recording=rid, group=str(r.axis), **metrics(tcache[rid], dig)))
            if (i + 1) % 300 == 0:
                print(name, i + 1, round(time.time() - t0), "s", flush=True)
    # ---- own phone photos (original photos only): P set (60) and Q set (40); 2 photos per page, matched by file-name order (as in Sections O and Q2)
    for name, mapping, files_, ids in [
        ("own phone P", "ownphotos/pages_mapping.csv", {os.path.basename(f)[:-4]: f for f in glob.glob(R + "ownphotos/kaggle_out/ownphotos_digitized_12lead/**/*.npz", recursive=True)}, None),
        ("own phone Q", "ownphotos2/pages_mapping.csv", {os.path.basename(f)[:-4]: f for f in glob.glob(R + "ownphotos2/confirm_out/confirm_digitized_12lead/**/*V0_original.npz", recursive=True)}, None)]:
        pm = pd.read_csv(R + mapping)
        keys = sorted(files_)
        for k, key in enumerate(keys):
            page = pm.iloc[k // 2]
            tr = to_1k(read_ptbxl_lead2(page.filename_lr), 100)
            dig = np.load(files_[key])["II"].astype(float) / 1000.0
            rows.append(dict(set=name, variant_id=key, recording=page["page"], group="straight" if k % 2 == 0 else "angled", **metrics(tr, dig)))
    df = pd.DataFrame(rows)
    os.makedirs(OUT, exist_ok=True)
    df.to_csv(OUT + "sectionR_waveform_per_image.csv", index=False)
    print("done", len(df), "images in", round(time.time() - t0), "s")
    return df


def q(x):
    x = pd.Series(x).dropna()
    if len(x) == 0:
        return "n/a"
    return f"{x.median():.3g} ({x.quantile(.25):.3g} to {x.quantile(.75):.3g}; p90 {x.quantile(.9):.3g})"


def summary(df):
    L = ["# Section R: waveform errors of the digitised lead II (EXPLORATORY, added after the freeze)", "",
         "Rules fixed before the run: `docs/plan/analysis_plan_changes.md` 2026-11-13. Truth = the signal the page was drawn from (PTB-XL 100 Hz, resampled to 1 kHz) or the exported Challenge lead II. "
         "Shift within +-0.5 s, means removed, **gain not fitted**. Cells show median (middle half; 90th percentile). Descriptive only: no pass/fail rule.", "",
         "Limits: the simulated truth is a 100 Hz signal interpolated to 1 kHz, so timing differences below about 5 to 10 ms are not meaningful; real captures are compared on lead II only; "
         "MAE and RMSE are on mean-removed signals, so they do not include a constant offset.", ""]
    cols = [("mae_mV", "MAE (mV)"), ("rmse_mV", "RMSE (mV)"), ("pearson_r", "Pearson r"), ("gain_error_pct", "gain error (%)"), ("rpeak_amp_err_mV", "R amplitude error (mV)"),
            ("timing_err_ms", "R timing error (ms)"), ("lag_ms", "lag (ms)")]

    def table(d, title):
        out = [f"### {title}", "", "| Group | Images | Readable | " + " | ".join(c[1] for c in cols) + " |", "|---|---|---|" + "---|" * len(cols)]
        for g, x in d.groupby("group", sort=False):
            readable = x.mae_mV.notna().sum()
            out.append(f"| {g} | {len(x)} | {readable} | " + " | ".join(q(x[c[0]]) for c in cols) + " |")
        return out + [""]

    sim = df[df.set == "simulated new100"]
    L += table(sim[sim.group == "clean"], "Primary: simulated new 100, clean page")
    order = ["blur 3", "blur 5", "resolution 3", "resolution 5", "rotate 3", "rotate 5", "jpeg 3", "jpeg 5", "brightness 3", "brightness 5", "gridcontrast 3", "gridcontrast 5"]
    s2 = sim[sim.group != "clean"].copy()
    s2["group"] = pd.Categorical(s2.group, categories=[o for o in order if o in set(s2.group)] + sorted(set(s2.group) - set(order)), ordered=True)
    L += table(s2.sort_values("group").assign(group=lambda d: d.group.astype(str)), "Simulated new 100 by damage type and level (descriptive)")
    for s, title in [("real Arm C", "Real captures, Arm C (40 recordings), by capture type"), ("real C+", "Real captures, C+ (100 recordings), by capture type"),
                     ("own phone P", "Own phone set 1 (60 photos of a screen)"), ("own phone Q", "Own phone set 2 (40 photos of a screen, original photos)")]:
        d = df[df.set == s]
        if len(d):
            L += table(d, title)
    unreadable = df[df.mae_mV.isna()].groupby("set").size()
    L += ["### Photos excluded as unreadable (fewer than half of lead II samples read, or no overlap)", ""] + [f"- {k}: {v} of {int((df.set == k).sum())}" for k, v in unreadable.items()] + [""]
    return "\n".join(L)


if __name__ == "__main__":
    d = run()
    open(OUT + "SECTION_R.md", "w", encoding="utf-8").write(summary(d))
    print("written SECTION_R.md")
