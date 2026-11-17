"""Section U (EXPLORATORY): PR interval and QRS duration with my own median-beat method. Rules fixed BEFORE any code ran: docs/plan/analysis_plan_changes.md, 2026-11-14 (later still).
Reuses the beat cutting of Section T (scripts/analysis/section_T_better_qt.py). QRS onset/offset by slope; P onset by tangent or threshold; 3 aggregators x 2 alternatives per parameter.
  python -I scripts/analysis/section_U_pr_qrs.py --dev       first 50 ORIGINAL signals in the page layout: choose one candidate + one offset per parameter, write sectionU_frozen.json
  python -I scripts/analysis/section_U_pr_qrs.py --test      ONCE on the new 100: (a) original in the photo windows, (b) digitised clean page
  python -I scripts/analysis/section_U_pr_qrs.py --confirm   ONCE on the 100 own-phone photos (straightened primary), method and offsets unchanged"""
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
_spec = importlib.util.spec_from_file_location("T", ROOT + "scripts/analysis/section_T_better_qt.py")
T = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T)
LEADS, LAYOUT, ms2n = T.LEADS, T.LAYOUT, T.ms2n
# ---- constants fixed in the rules ----
QRS_FWD_MS, P_FROM_MS, P_TO_MS, P_TAN_MS, P_MIN_MV, P_EDGE_MS, P_THR = 150, 250, 30, 100, 0.02, 10, 0.15
RULE = {"pr": (20, 40, 10), "qrs": (10, 20, 5)}              # median abs diff, 90% within, |bias| (ms)
REF = {"pr": "PR_Int_Global", "qrs": "QRS_Dur_Global"}
CANDS = {"qrs": [f"qrs_{a}_{f}" for a in "ABC" for f in ("5", "10")], "pr": [f"pr_{a}_{m}" for a in "ABC" for m in ("tan", "thr")]}


def edges(mb, fs, frac):
    r0 = ms2n(T.PRE_MS, fs)
    d = np.gradient(mb) * fs
    lo, hi = max(1, r0 - ms2n(T.QRS_SEARCH_MS, fs)), min(len(mb) - 2, r0 + ms2n(T.QRS_SEARCH_MS, fs))
    smax = np.max(np.abs(d[lo:hi]))
    if not np.isfinite(smax) or smax < 1e-6:
        return None
    i = lo + int(np.argmax(np.abs(d[lo:r0 + 1])))
    limit = max(r0 - ms2n(T.ONSET_BACK_MS, fs), ms2n(T.BASE_FROM_MS, fs) + 1)
    while i > limit and abs(d[i]) >= frac * smax:
        i -= 1
    j = r0 + int(np.argmax(np.abs(d[r0:hi + 1])))
    lim = min(r0 + ms2n(QRS_FWD_MS, fs), len(mb) - 3)
    while j < lim and abs(d[j]) >= frac * smax:
        j += 1
    return i, j


def lead_feats(mb, fs):
    """QRS onset/offset (5% and 10% slope fractions) and P onset (tangent, threshold), ms relative to the R anchor. PR uses the 5% onset."""
    f = dict(on5=np.nan, off5=np.nan, on10=np.nan, off10=np.nan, p_tan=np.nan, p_thr=np.nan)
    r0 = ms2n(T.PRE_MS, fs)
    ms = 1000.0 / fs
    e5, e10 = edges(mb, fs, 0.05), edges(mb, fs, 0.10)
    if e10:
        f["on10"], f["off10"] = (e10[0] - r0) * ms, (e10[1] - r0) * ms
    if not e5:
        return f
    onset = e5[0]
    f["on5"], f["off5"] = (onset - r0) * ms, (e5[1] - r0) * ms
    b0, b1 = onset - ms2n(T.BASE_FROM_MS, fs), onset - ms2n(T.BASE_TO_MS, fs)
    ps, pe = onset - ms2n(P_FROM_MS, fs), onset - ms2n(P_TO_MS, fs)
    if b0 < 0 or b1 <= b0 or ps < 1 or pe <= ps + ms2n(30, fs):
        return f
    y = mb - np.median(mb[b0:b1])
    ppk = ps + int(np.argmax(np.abs(y[ps:pe + 1])))
    if abs(y[ppk]) < P_MIN_MV or ppk <= ps + ms2n(P_EDGE_MS, fs):
        return f
    yy = y * (1.0 if y[ppk] >= 0 else -1.0)
    dd = np.gradient(yy) * fs
    back = max(ppk - ms2n(P_TAN_MS, fs), 1)
    k = back + int(np.argmax(dd[back:ppk + 1]))
    slope = dd[k] / fs
    if slope > 0:
        t = k - yy[k] / slope
        if 0 <= t < ppk:
            f["p_tan"] = (t - r0) * ms
    rev = yy[:ppk + 1][::-1] <= P_THR * yy[ppk]
    if rev.any():
        j = ppk - int(np.argmax(rev))
        if j >= 1:
            f["p_thr"] = (j - r0) * ms
    return f


def measure_record(leads, fs, windows, rpk):
    res = {c: np.nan for p in CANDS for c in CANDS[p]}
    if len(rpk) < 3:
        return res
    rr = np.median(np.diff(rpk)) * 1000.0 / fs
    tmax = min(T.TMAX_MS, T.RR_FRAC * rr)
    if tmax < 250:
        return res
    per = {}
    for L in LEADS:
        a, b = windows.get(L, (0, 0))
        if b - a <= 0 or L not in leads:
            continue
        mb, n = T.median_beat(leads[L], fs, a, b, rpk, tmax)
        if mb is not None:
            per[L] = lead_feats(mb, fs)
    mn = T.MIN_LEADS
    for fr in ("5", "10"):
        on, off = f"on{fr}", f"off{fr}"
        ok = [f for f in per.values() if np.isfinite(f[on]) and np.isfinite(f[off])]
        if "II" in per and np.isfinite(per["II"][on]) and np.isfinite(per["II"][off]) and per["II"][off] > per["II"][on]:
            res[f"qrs_A_{fr}"] = per["II"][off] - per["II"][on]
        if len(ok) >= mn:
            res[f"qrs_B_{fr}"] = float(np.median([f[off] - f[on] for f in ok]))
            res[f"qrs_C_{fr}"] = float(np.percentile([f[off] for f in ok], 90) - np.percentile([f[on] for f in ok], 10))
    for m in ("tan", "thr"):
        pk = f"p_{m}"
        ok = [f for f in per.values() if np.isfinite(f["on5"]) and np.isfinite(f[pk])]
        if "II" in per and np.isfinite(per["II"]["on5"]) and np.isfinite(per["II"][pk]) and per["II"]["on5"] > per["II"][pk]:
            res[f"pr_A_{m}"] = per["II"]["on5"] - per["II"][pk]
        if len(ok) >= mn:
            res[f"pr_B_{m}"] = float(np.median([f["on5"] - f[pk] for f in ok]))
            res[f"pr_C_{m}"] = float(np.percentile([f["on5"] for f in ok], 10) - np.percentile([f[pk] for f in ok], 10))
    return res


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


def run_dev():
    ref = pd.read_csv(R + "extension/reference_check_150.csv")
    ref = ref[ref.set == "first50"]
    db = pd.read_csv(ROOT + "data/ptbxl/ptbxl_database.csv")
    db["record"] = db.filename_lr.str.split("/").str[-1]
    x12 = pd.read_csv(ROOT + "data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
    tasks = [(r.record, db.loc[db.record == r.record, "filename_lr"].iloc[0].replace("records100", "records500").replace("_lr", "_hr")) for _, r in ref.iterrows()]
    with ProcessPoolExecutor(max_workers=10) as ex:
        rows = list(ex.map(dev_task, tasks, chunksize=2))
    d = pd.DataFrame(rows).merge(ref[["record", "ecg_id"]], on="record")
    for p in REF:
        d[f"ref_{p}"] = d.ecg_id.map(x12[REF[p]])
    d.to_csv(OUT + "sectionU_dev.csv", index=False)
    frozen, L = {}, ["# Section U development (first 50 recordings, original 500 Hz signals cut to the page layout)", "",
                     "Reference = 12SL. Value share = share of the recordings that HAVE a 12SL value. Offset = the median difference on these recordings. Selection rule from the 2026-11-14 plan entry.", ""]
    for p, name in (("qrs", "QRS duration"), ("pr", "PR interval")):
        has = d[f"ref_{p}"].notna()
        rows_ = []
        for c in CANDS[p]:
            ok = d[c].notna() & has
            diff = (d[c] - d[f"ref_{p}"])[ok]
            share = float(d.loc[has, c].notna().mean())
            if len(diff) < 5:
                rows_.append(dict(cand=c, share=share, n=int(len(diff))))
                continue
            off = float(diff.median())
            rows_.append(dict(cand=c, share=share, n=int(len(diff)), bias_before=float(diff.mean()), offset=off, median_abs_after=float((diff - off).abs().median()),
                              rho=float(spearmanr(d.loc[ok, c], d.loc[ok, f"ref_{p}"])[0])))
        t = pd.DataFrame(rows_)
        elig = t[(t.share >= 0.9) & t.get("median_abs_after", pd.Series(dtype=float)).notna()].sort_values(["median_abs_after", "rho"], ascending=[True, False]) if "median_abs_after" in t else t.iloc[0:0]
        ch = None if elig.empty else elig.iloc[0]
        frozen[p] = dict(candidate=None if ch is None else str(ch.cand), offset_ms=None if ch is None else float(ch.offset), table=t.round(3).to_dict(orient="records"))
        L += [f"## {name}", "", "| Candidate | Recordings with a value | n compared | Bias before offset (ms) | Offset (ms) | Median abs diff after offset (ms) | rho |", "|---|---|---|---|---|---|---|"]
        for _, r in t.iterrows():
            L.append(f"| {r.cand} | {100 * r.share:.0f}% | {int(r.n)} | " + (f"{r.bias_before:+.1f} | {r.offset:+.1f} | {r.median_abs_after:.1f} | {r.rho:.2f} |" if pd.notna(r.get("offset")) else "n/a | n/a | n/a | n/a |"))
        L += ["", f"**Frozen: {frozen[p]['candidate']}" + (f", offset {frozen[p]['offset_ms']:+.1f} ms.**" if ch is not None else " (no candidate reached 90% value share).**"), ""]
    frozen["written"] = time.strftime("%Y-%m-%d %H:%M")
    json.dump(frozen, open(OUT + "sectionU_frozen.json", "w"), indent=1)
    open(OUT + "SECTION_U_dev.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


# ------------------------------------------------------------------ test and confirmation
def test_task(a):
    vid, npz, rel500, with_original = a
    z = np.load(npz)
    dig = {L: np.asarray(z[L], float) / 1000.0 for L in LEADS}
    win = {L: T.longest_run(np.isfinite(dig[L])) for L in LEADS}
    row = dict(variant_id=vid)
    try:
        for k, v in measure_record(dig, 1000, win, T.lead2_rpeaks(dig["II"], 1000)).items():
            row[f"dig_{k}"] = v
    except Exception as e:
        row["error_dig"] = str(e)[:80]
    if with_original:
        try:
            orig = T.read_all_leads(rel500)
            win5 = {L: (a_ // 2, b_ // 2) for L, (a_, b_) in win.items()}
            for k, v in measure_record(orig, 500, win5, T.lead2_rpeaks(orig["II"], 500)).items():
                row[f"orig_{k}"] = v
        except Exception as e:
            row["error_orig"] = str(e)[:80]
    return row


def run_test():
    fr = json.load(open(OUT + "sectionU_frozen.json"))
    out_csv = OUT + "sectionU_test_per_image.csv"
    if os.path.exists(out_csv) and "--force" not in sys.argv:
        sys.exit("The test was already run once (rule: run ONCE).")
    ext = pd.read_csv(R + "extension/results_extension.csv")
    sel = pd.read_csv(R + "extension/selected_100.csv").set_index("record")
    files = {os.path.basename(f)[:-4]: f for f in glob.glob(R + "extension/extension_digitized_12lead/**/*.npz", recursive=True)}
    tasks = [(r.variant_id, files[r.variant_id], sel.loc[r.record, "filename_lr"].replace("records100", "records500").replace("_lr", "_hr"), r.axis == "clean")
             for _, r in ext.iterrows() if r.variant_id in files and r.record in sel.index]
    tasks.sort(key=lambda t: not t[3])
    with ProcessPoolExecutor(max_workers=10) as ex:
        rows = list(ex.map(test_task, tasks, chunksize=4))
    m = pd.DataFrame(rows).merge(ext[["variant_id", "record", "axis", "level"]], on="variant_id")
    m["ecg_id"] = m.record.map(sel.ecg_id)
    x12 = pd.read_csv(ROOT + "data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
    for p in REF:
        c, off = fr[p]["candidate"], fr[p]["offset_ms"]
        m[f"ref_{p}"] = m.ecg_id.map(x12[REF[p]])
        m[f"{p}_dig"] = m[f"dig_{c}"] - off
        m[f"{p}_orig"] = (m[f"orig_{c}"] - off) if f"orig_{c}" in m else np.nan
    m.to_csv(out_csv, index=False)
    return m


def verdict_rows(label, x, col, p):
    ok = x[col].notna() & x[f"ref_{p}"].notna()
    has = x[f"ref_{p}"].notna()
    s = T.stats((x[col] - x[f"ref_{p}"])[ok], tol_within=RULE[p][1])
    share = float(x.loc[has, col].notna().mean()) if has.any() else 0.0
    rho = spearmanr(x.loc[ok, col], x.loc[ok, f"ref_{p}"])[0] if ok.sum() > 4 else np.nan
    v = meets(p, s, share)
    if s.get("n", 0) >= 5:
        row = (f"| {label} | {int(x[col].notna().sum())} of {len(x)} ({100 * share:.0f}% of those with a reference) | {rho:.2f} | {s['median_abs']:.1f} ({s['median_abs_ci'][0]:.1f} to {s['median_abs_ci'][1]:.1f}) | "
               f"{s['p90_abs']:.1f} | {s['bias']:+.1f} ({s['bias_ci'][0]:+.1f} to {s['bias_ci'][1]:+.1f}) | {100 * s['within']:.0f}% | **{'meets' if v else 'does not meet'}** |")
    else:
        row = f"| {label} | {int(x[col].notna().sum())} of {len(x)} | n/a | n/a | n/a | n/a | n/a | does not meet |"
    return row, v, s, share


HEAD = ["| Measurement | With a value | rho with 12SL | Median abs diff (95% CI) | 90th pct | Bias (95% CI) | Within tolerance | Rule |", "|---|---|---|---|---|---|---|---|"]


def summary_test(m, fr):
    sys.path.insert(0, ROOT + "safeguard")
    import ecg_traffic_light as TL
    model = TL.load_model()
    f = pd.read_csv(OUT + "sectionD2_features.csv").set_index("variant_id")
    m = m.copy()
    m["green"] = [bool(v in f.index and (f.loc[v, "n_beats"] >= 3) and TL.score_from_features(f.loc[v].to_dict(), model) < model["amber_threshold"]) for v in m.variant_id]
    clean = m[(m.axis == "clean") & (m.record != "21205_lr")]
    L = ["# Section U: PR and QRS with my own method, tested once on the new 100 (EXPLORATORY, added after the freeze)", "",
         "Rules fixed before any code ran (`docs/plan/analysis_plan_changes.md`, 2026-11-14 later entries). The acceptance rules are the assistant's proposal and are **not approved by the guide**. "
         f"Frozen on the first 50: QRS = {fr['qrs']['candidate']} (offset {fr['qrs']['offset_ms']:+.1f} ms), PR = {fr['pr']['candidate']} (offset {fr['pr']['offset_ms']:+.1f} ms). "
         f"Primary set: clean pages of the new 100 recordings, 21205 excluded ({len(clean)} recordings). Difference = measured minus 12SL.", ""]
    out = {}
    for p, name, tol in (("qrs", "QRS duration", "median abs diff <= 10 ms, 90% within 20 ms, |bias| <= 5 ms"), ("pr", "PR interval", "median abs diff <= 20 ms, 90% within 40 ms, |bias| <= 10 ms")):
        L += [f"## {name} (rule: {tol}; at least 90% with a value)", ""] + HEAD
        ra, va, sa, sha = verdict_rows("(a) frozen method on the original signal, photo windows", clean, f"{p}_orig", p)
        rb, vb, sb, shb = verdict_rows("(b) digitised clean page", clean, f"{p}_dig", p)
        L += [ra, rb]
        ok = clean[f"{p}_dig"].notna() & clean[f"{p}_orig"].notna()
        sc = T.stats((clean[f"{p}_dig"] - clean[f"{p}_orig"])[ok], tol_within=RULE[p][1])
        if sc.get("n", 0) >= 5:
            L.append(f"| (c) digitised minus (a): what the photo adds | {int(ok.sum())} | | {sc['median_abs']:.1f} | {sc['p90_abs']:.1f} | {sc['bias']:+.1f} | | |")
        out[p] = (va, vb)
        L += ["", f"**{name} validated on the held-out test: {'YES' if va and vb else 'NO'}** ((a) meets: {va}, (b) meets: {vb}). Still needs the new-photo confirmation.", ""]
    L += ["## Secondary (descriptive): digitised, all versions, by damage; GREEN images only (median abs diff / bias in ms; value share)", "",
          "| Group | Images | QRS | PR |", "|---|---|---|---|"]
    allv = m[m.record != "21205_lr"].copy()
    allv["group"] = np.where(allv.axis == "clean", "clean", allv.axis + " " + allv.level.astype(str))
    for g, x in [("all versions", allv), ("GREEN images only", allv[allv.green])] + [(g, x) for g, x in allv.groupby("group", sort=False)]:
        cells = []
        for p in ("qrs", "pr"):
            ok = x[f"{p}_dig"].notna() & x[f"ref_{p}"].notna()
            d = (x[f"{p}_dig"] - x[f"ref_{p}"])[ok]
            sh = x.loc[x[f"ref_{p}"].notna(), f"{p}_dig"].notna().mean()
            cells.append((f"{d.abs().median():.0f} / {d.mean():+.0f}; {100 * sh:.0f}%" if len(d) >= 5 else "n/a"))
        L.append(f"| {g} | {len(x)} | " + " | ".join(cells) + " |")
    L += ["", "## Development tables (first 50 recordings; for the record)", ""]
    for p, name in (("qrs", "QRS"), ("pr", "PR")):
        L += [f"**{name}**", "", "| Candidate | Value share | Bias before offset | Offset | Median abs after offset | rho |", "|---|---|---|---|---|---|"]
        for r in fr[p]["table"]:
            L.append(f"| {r['cand']} | {100 * r['share']:.0f}% | " + (f"{r['bias_before']:+.1f} | {r['offset']:+.1f} | {r['median_abs_after']:.1f} | {r['rho']:.2f} |" if r.get("offset") is not None else "n/a | n/a | n/a | n/a |"))
        L.append("")
    L += ["## Limits", "", "- The pixel size (about 5 ms at 200 dpi) bounds the QRS duration error from below; blurred or small photos cannot meet a 10 ms rule.",
          "- 12SL is an algorithm, not an expert measurement. Developed on 50 recordings with 6 candidates per parameter and one offset: mild overfitting is possible.",
          "- One digitiser, simulated pages. Nothing from this section is shown to patients unless the held-out test AND the new-photo confirmation both say YES."]
    return "\n".join(L)


def run_confirm():
    fr = json.load(open(OUT + "sectionU_frozen.json"))
    out_csv = OUT + "sectionU_confirm_per_photo.csv"
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
        rows = list(ex.map(T.confirm_task if False else confirm_task, tasks, chunksize=2))
    d = pd.DataFrame(rows)
    for c in ("set", "photo", "version", "page", "ecg_id", "shot"):
        d[c] = d.key.map(lambda k: meta[k][c])
    for p in REF:
        d[f"ref_{p}"] = d.ecg_id.map(x12[REF[p]])
        d[p] = d[fr[p]["candidate"]] - fr[p]["offset_ms"]
    d.to_csv(out_csv, index=False)
    L = ["# Section U confirmation: the frozen PR and QRS methods on NEW photos (own phone; EXPLORATORY)", "",
         "Method and offsets exactly as frozen before the held-out test; rules fixed before the run. Photos of drawn PTB-XL pages shown on a laptop screen, one phone; P01-P30 and Q01-Q20 (not among the 150). "
         "Reference = 12SL; photos whose recording has no 12SL value are left out of the comparison. The acceptance rules are the assistant's proposal, not approved by the guide. The two photos of a page are not independent.", ""]
    for p, name in (("qrs", "QRS duration"), ("pr", "PR interval")):
        L += [f"## {name}", ""] + HEAD
        for lab, x in [("V2 straightened, all (primary)", d[d.version == "V2"]), ("V0 original, all", d[d.version == "V0"]),
                       ("V2 straight shots", d[(d.version == "V2") & (d.shot == "straight")]), ("V2 angled shots", d[(d.version == "V2") & (d.shot == "angled")]),
                       ("V2 set P", d[(d.version == "V2") & (d.set == "P")]), ("V2 set Q", d[(d.version == "V2") & (d.set == "Q")])]:
            row, v, s, sh = verdict_rows(lab, x, p, p)
            L.append(row)
        L.append("")
    open(OUT + "SECTION_U_confirm.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
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
        mm = run_test()
        open(OUT + "SECTION_U.md", "w", encoding="utf-8").write(summary_test(mm, json.load(open(OUT + "sectionU_frozen.json"))))
        print("written SECTION_U.md")
    elif "--confirm" in sys.argv:
        run_confirm()
    else:
        print(__doc__)
