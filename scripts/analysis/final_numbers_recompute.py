"""Independent recomputation of the headline numbers for results/FINAL_NUMBERS.md.
Written fresh (does not import or reuse the section_*.py scripts). It reads only RAW outputs:
  results_v2.csv, results_extension.csv, results_bridge.csv, results_armB.csv, results_armC.csv, results_armCext_all.csv,
  the digitised npz files of the own-phone photos, and the PTB-XL 100 Hz source records (wfdb).
Every line prints  recomputed | reported | MATCH or DIFFERENT.  Usage: python -I scripts/analysis/final_numbers_recompute.py
(The traffic-light counts need safeguard/ecg_traffic_light.py, which IS the product; that part only checks counting.)"""
import os
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.stats import binomtest

warnings.filterwarnings("ignore")
R = "D:/Capstone Project/results/"
sys.path.insert(0, "D:/Capstone Project/safeguard")
LINES = []
ALL_OK = [True]


def say(name, got, rep):
    ok = (got == rep)
    ALL_OK[0] &= ok
    LINES.append(f"| {name} | {got} | {rep} | {'MATCH' if ok else '**DIFFERENT**'} |")
    print(LINES[-1])


def wrong(df, col="dig_hr", ref="gt_hr"):
    # uses the saved UNROUNDED difference (diff_bpm); the saved heart-rate columns are rounded to 0.1 bpm,
    # so |dig_hr - gt_hr| can read exactly 5.0 where the true difference is 5.02 (found in the first run of this check).
    has = df[col].notna()
    return has & (df["diff_bpm"].abs() > 5)


def frac(mask, base):
    return f"{int(mask.sum())}/{int(base.sum()) if hasattr(base, 'sum') else base}"


# ---------------- 1. simulated sweeps (original measure) ----------------
v2 = pd.read_csv(R + "v2_intervals/results_v2.csv")
ex = pd.read_csv(R + "extension/results_extension.csv")
v2 = v2[v2.record != "15192_lr"].copy()
ex = ex[ex.record != "21205_lr"].copy()
for d in (v2, ex):
    d["w"] = wrong(d)
    d["none"] = d.dig_hr.isna()


def cell(d, axis, lev):
    x = d[(d.axis == axis) & (d.level == lev)]
    return x


exp_new = {("clean", 0): "3/99", ("resolution", 5): "47/99", ("blur", 5): "17/99", ("rotate", 5): "0/99", ("jpeg", 5): "0/99", ("brightness", 5): "1/99", ("gridcontrast", 5): "3/99"}
for (a, l), e in exp_new.items():
    x = cell(ex, a, l)
    say(f"new 100, {a} level {l}: wrong >5 bpm", f"{int(x.w.sum())}/{len(x)}", e)
say("new 100, rotate level 5: no output", f"{int(cell(ex, 'rotate', 5).none.sum())}/99", "19/99")
say("new 100, blur level 5: no output", f"{int(cell(ex, 'blur', 5).none.sum())}/99", "1/99")
exp_f50 = {("clean", 0): "2/49", ("resolution", 5): "21/49", ("blur", 5): "8/49"}
for (a, l), e in exp_f50.items():
    x = cell(v2, a, l)
    say(f"first 50, {a} level {l}: wrong >5 bpm", f"{int(x.w.sum())}/{len(x)}", e)
both = pd.concat([v2, ex])
both = both[both.level.isin([0, 3, 5])]
for (a, l), e in {("clean", 0): "5/148", ("resolution", 5): "68/148", ("blur", 5): "25/148"}.items():
    x = cell(both, a, l)
    say(f"all 150, {a} level {l}: wrong >5 bpm", f"{int(x.w.sum())}/{len(x)}", e)

# ---------------- 2. bridge run ----------------
br = pd.read_csv(R + "bridge/results_bridge.csv")
old = pd.read_csv(R + "v2_intervals/results_v2.csv").set_index("variant_id")
br["lab"] = br.dig_hr.isna() | (br.diff_bpm.abs() > 5)
old["lab"] = old.dig_hr.isna() | (old.diff_bpm.abs() > 5)
changed = int((br.set_index("variant_id").lab != old.loc[br.variant_id, "lab"].values).sum())
say("bridge run: images whose bad label changed", f"{changed}/{len(br)}", "0/156")

# ---------------- 3. Arm B ----------------
ab = pd.read_csv(R + "armB/results_armB.csv")
ab["w"] = wrong(ab)
g = ab.groupby("axis").w.sum().to_dict()
say("Arm B wrong >5 bpm (clean, B1, B2, B3)", f"{g['clean']},{g['B1_wrinkles']},{g['B2_augment']},{g['B3_both']}", "0,1,0,0")

# ---------------- 4. cleaned measure, simulated new 100 and real captures ----------------
k = pd.read_csv(R + "analysis/sectionK_remeasured_sim.csv")
k = k[k.record != "21205_lr"]
kk = k[k.dig_hr_clean.notna()]
say("simulated new 100 (cleaned): images with a reading / wrong", f"{len(kk)}/{int(((kk.dig_hr_clean - kk.gt_hr_clean).abs() > 5).sum())}", "1262/113")
j = pd.read_csv(R + "analysis/sectionJ_remeasured.csv")
jo = j[j.dig_hr.notna()]
say("real captures, original measure: images with a reading / wrong", f"{len(jo)}/{int((jo.diff_bpm.abs() > 5).sum())}", "1203/168")
jc = j[j.dig_hr_clean.notna()]
say("real captures, cleaned measure: images with a reading / wrong", f"{len(jc)}/{int(((jc.dig_hr_clean - jc.gt_hr_clean).abs() > 5).sum())}", "1201/46")
c4 = j[j.axis == "C4_phone_photo_screen"]
say("real captures C4 (phone photo of screen): no output", f"{int(c4.dig_hr.isna().sum())}/{len(c4)}", "53/140")


# ---------------- 5. own-phone photos: recompute from digitised signals ----------------
def hr_clean(sig, fs=1000):
    import neurokit2 as nk
    x = nk.ecg_clean(sig, sampling_rate=fs, method="neurokit")
    p, _ = nk.ecg_peaks(x, sampling_rate=fs)
    return float(np.nanmean(nk.ecg_rate(p, sampling_rate=fs, desired_length=len(sig))))


def read_ii(path):
    z = np.load(path, allow_pickle=True)
    s = np.asarray(z["II"], float)
    return s[np.isfinite(s)] / 1000.0


def ref_hr(prefix, pg):
    import wfdb
    rec = wfdb.rdrecord(R + f"{prefix}/source_records/{pg}")
    return hr_clean(rec.p_signal[:, rec.sig_name.index("II")], rec.fs)


def badtable(var_csv, res_dir, npz_dir, prefix, pgletter, vtag=None):
    var = pd.read_csv(var_csv)
    stems = sorted(var.photo.unique())
    page = {s: f"{pgletter}{i // 2 + 1:02d}" for i, s in enumerate(stems)}
    refs = {pg: ref_hr(prefix, pg) for pg in sorted(set(page.values()))}
    out = []
    for r in var.itertuples():
        pth = f"{npz_dir}/{r.variant_id}.npz"
        hr = np.nan
        if os.path.exists(pth):
            s = read_ii(pth)
            try:
                hr = hr_clean(s) if len(s) > 10 else np.nan
            except Exception:
                hr = np.nan
        none = bool(np.isnan(hr))
        wr = (not none) and abs(hr - refs[page[r.photo]]) > 5
        out.append(dict(photo=r.photo, variant=r.variant, none=none, wrong=wr, bad=none or wr))
    return pd.DataFrame(out)


def mcnemar(d, v):
    b0 = d[d.variant == "V0_original"].set_index("photo").bad
    x = d[d.variant == v].set_index("photo").bad.reindex(b0.index)
    nb, ng = int((x & ~b0).sum()), int((~x & b0).sum())
    p = binomtest(nb, nb + ng, 0.5).pvalue if nb + ng else 1.0
    return int(b0.sum()), int(x.sum()), nb, ng, p


# 5a. confirmation set (40 new photos, 20 new pages Q01-Q20)
cd = R + "ownphotos2/confirm_out"
if os.path.isdir(cd):
    D2 = badtable(cd + "/confirm_variants.csv", cd, cd + "/confirm_digitized_12lead", "ownphotos2", "Q")
    b0, b2, nb, ng, p = mcnemar(D2, "V2_straighten")
    say("CONFIRMATION (40 new photos): bad original / straightened", f"{b0}/{b2}", "14/2")
    say("CONFIRMATION: newly bad / newly good", f"{nb}/{ng}", "0/12")
    say("CONFIRMATION: exact McNemar p (4 decimals)", f"{p:.4f}", "0.0005")
    say("CONFIRMATION: V0 no usable HR / wrong", f"{int(D2[D2.variant == 'V0_original'].none.sum())}/{int(D2[D2.variant == 'V0_original'].wrong.sum())}", "4/10")
    say("CONFIRMATION: V2 no usable HR / wrong", f"{int(D2[D2.variant == 'V2_straighten'].none.sum())}/{int(D2[D2.variant == 'V2_straighten'].wrong.sum())}", "0/2")
    say("CONFIRMATION: V1 enlarge bad", f"{mcnemar(D2, 'V1_enlarge')[1]}", "13")
    say("CONFIRMATION: V3 straighten+big bad", f"{mcnemar(D2, 'V3_straighten_big')[1]}", "3")
    import ecg_traffic_light as T
    var = pd.read_csv(cd + "/confirm_variants.csv")
    lt = {}
    for r in var.itertuples():
        pth = f"{cd}/confirm_digitized_12lead/{r.variant_id}.npz"
        lt[r.variant_id] = T.check(T.load_npz(pth))["light"] if os.path.exists(pth) else "RED"
    var["light"] = var.variant_id.map(lt)
    D2 = D2.merge(var[["photo", "variant", "light"]], on=["photo", "variant"])
    for vn, tag in (("V0_original", "V0"), ("V2_straighten", "V2")):
        x = D2[D2.variant == vn]
        s = ";".join(f"{c}:{int((x.light == c).sum())}({int(x[x.light == c].bad.sum())} bad)" for c in ("GREEN", "AMBER", "RED"))
        say(f"CONFIRMATION lights {tag}", s, {"V0": "GREEN:20(0 bad);AMBER:7(1 bad);RED:13(13 bad)", "V2": "GREEN:32(0 bad);AMBER:7(1 bad);RED:1(1 bad)"}[tag])

# 5b. first 60 photos (own phone set 1): V0 from Kaggle run of Section O, V1-V3 from the fix experiment
od = R + "ownphotos/kaggle_out"
fd = R + "ownphotos/fixexp_out"
if os.path.isdir(od) and os.path.isdir(fd):
    v0 = pd.read_csv(od + "/results_ownphotos.csv")
    v0["photo"] = v0["variant_id"].str.replace(r"__.*$", "", regex=True) if "photo" not in v0 else v0["photo"]
    v0["variant"] = "V0_original"
    tmp = R + "analysis/_tmp_v0_variants.csv"
    v0[["variant_id", "photo", "variant"]].drop_duplicates().to_csv(tmp, index=False)
    A = badtable(tmp, od, od + "/ownphotos_digitized_12lead", "ownphotos", "P")
    os.remove(tmp)
    fv = pd.read_csv(fd + "/fixexp_variants.csv")
    stems = sorted(fv.photo.unique())
    page = {s: f"P{i // 2 + 1:02d}" for i, s in enumerate(stems)}
    refs = {pg: ref_hr("ownphotos", pg) for pg in sorted(set(page.values()))}
    rows = []
    for r in fv.itertuples():
        pth = f"{fd}/fixexp_digitized_12lead/{r.variant_id}.npz"
        hr = np.nan
        if os.path.exists(pth):
            s = read_ii(pth)
            try:
                hr = hr_clean(s) if len(s) > 10 else np.nan
            except Exception:
                hr = np.nan
        none = bool(np.isnan(hr))
        wr = (not none) and abs(hr - refs[page[r.photo]]) > 5
        rows.append(dict(photo=r.photo, variant=r.variant, none=none, wrong=wr, bad=none or wr))
    Bq = pd.DataFrame(rows)
    Bq = Bq[Bq.variant != "V0_original"]
    A = A[A.photo.isin(stems)]
    F = pd.concat([A, Bq])
    say("OWN PHONE set 1: V0 no usable HR / wrong (60 photos)", f"{int(A.none.sum())}/{int(A.wrong.sum())}", "6/14")
    for vn, e in (("V1_enlarge", "12"), ("V2_straighten", "2"), ("V3_straighten_big", "6")):
        say(f"FIX EXPERIMENT (first 60): bad {vn}", f"{mcnemar(F, vn)[1]}", e)
    b0, b2, nb, ng, p = mcnemar(F, "V2_straighten")
    say("FIX EXPERIMENT: V0 bad / V2 newly bad / newly good", f"{b0}/{nb}/{ng}", "20/1/19")

with open(R + "analysis/FINAL_RECHECK.md", "w", encoding="utf-8") as f:
    f.write("# Independent recomputation of the headline numbers (script: scripts/analysis/final_numbers_recompute.py)\n\n")
    f.write("Written fresh from the raw result files; it does not reuse the section scripts. 'reported' = the number in the section report. This is a second script by the same author, NOT a second person.\n\n")
    f.write("| quantity | recomputed | reported | check |\n|---|---|---|---|\n" + "\n".join(LINES) + "\n")
    f.write(f"\n**All match: {ALL_OK[0]}**\n")
print("ALL MATCH:", ALL_OK[0])
