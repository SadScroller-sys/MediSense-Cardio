"""Dataset inventory (gap 2 after the 2026-11-11 freeze): ONE sheet that lists, for every recording we used, what image data and what reference data exists.
Reads (never modifies) only files that already exist; invents nothing. Writes results/DATASET_INVENTORY.csv (one row per recording) and results/DATASET_INVENTORY.md (per-set summary).
Run:  python -I scripts/analysis/dataset_inventory.py"""
import glob
import os
import re

import pandas as pd

ROOT = "D:/Capstone Project/"
R = ROOT + "results/"
db = pd.read_csv(ROOT + "data/ptbxl/ptbxl_database.csv")
db["record"] = db["filename_lr"].str.split("/").str[-1]
FLAGS = ["baseline_drift", "static_noise", "burst_noise", "electrodes_problems", "extra_beats", "pacemaker"]
db["ptbxl_flagged"] = db[FLAGS].apply(lambda c: c.notna() & (c.astype(str).str.strip() != ""), axis=0).any(axis=1)
x12 = pd.read_csv(ROOT + "data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
pr_col = next((c for c in x12.columns if c.startswith("PR_Int") or c == "PR_Int_Global"), None)
qrs_col = next((c for c in x12.columns if c.startswith("QRS_Dur") and c.endswith("Global")), None)
qt_col = "QT_Int_Global"
scp = pd.read_csv(ROOT + "data/ptbxl/scp_statements.csv", index_col=0)

rows = []
PAGE = dict(image_type="computer-drawn page (ECG-Image-Kit), colour RGBA PNG", image_size_px="2200 x 1700", calibration="25 mm/s, 10 mm/mV, 200 dpi (known by construction)")


def add_ptbxl(rec, ecg_id, set_name, n_images, conditions, saved, extra=None):
    d = db[db.ecg_id == ecg_id].iloc[0] if (db.ecg_id == ecg_id).any() else None
    row = dict(set=set_name, recording_id=rec, ecg_id=ecg_id, signal_source="PTB-XL records100 (100 Hz), 12 leads", signal_fs_hz=100, true_signal_available=True, n_leads=12,
               n_images=n_images, image_conditions=conditions, digitised_12lead_saved=saved,
               has_12SL=bool(ecg_id in x12.index),
               ref_qt_12SL_ms=(x12.loc[ecg_id, qt_col] if ecg_id in x12.index else None),
               ref_pr_12SL_ms=(x12.loc[ecg_id, pr_col] if (pr_col and ecg_id in x12.index) else None),
               ref_qrs_12SL_ms=(x12.loc[ecg_id, qrs_col] if (qrs_col and ecg_id in x12.index) else None),
               ptbxl_flagged=(bool(d.ptbxl_flagged) if d is not None else None))
    row.update(PAGE)
    if extra:
        row.update(extra)
    rows.append(row)


# ---- simulated sweeps: first 50 and new 100
ref = pd.read_csv(R + "extension/reference_check_150.csv")
v2 = pd.read_csv(R + "v2_intervals/results_v2.csv")
ext = pd.read_csv(R + "extension/results_extension.csv")
sel = pd.read_csv(R + "extension/selected_100.csv").set_index("record")
n_v2 = v2.groupby("record").size()
n_ext = ext.groupby("record").size()
saved = {}
for f in glob.glob(R + "extension/extension_digitized_12lead/**/*.npz", recursive=True):
    saved[os.path.basename(f).split("-0__")[0]] = saved.get(os.path.basename(f).split("-0__")[0], 0) + 1
for _, r in ref.iterrows():
    first = r["set"] == "first50"
    d = db[db.record == r["record"]].iloc[0]
    cls = sel.loc[r["record"], "diagnostic_class"] if (not first and r["record"] in sel.index) else None
    add_ptbxl(r["record"], int(r["ecg_id"]), "simulated first50" if first else "simulated new100",
              int(n_v2.get(r["record"], 0) if first else n_ext.get(r["record"], 0)),
              "clean + 6 damage types x 5 levels (31 versions)" if first else "clean + level 3 and 5 of 6 damage types (13 versions)",
              ("no (not saved)" if first else f"yes ({saved.get(r['record'], 0)} of 13 saved)"),
              extra=dict(ref_hr_100hz_bpm=r["hr100"], ref_hr_500hz_bpm=r["hr500"], reference_uncertain=bool(r["reference_uncertain"]),
                         diagnostic_class=cls, age=d.get("age"), sex=("female" if d.get("sex") == 1 else "male")))

# ---- real captures (PhysioNet Challenge images, read inside Kaggle): Arm C (40) and C+ (100)
truth = pd.read_csv(R + "truth/truth_meta.csv").set_index("id")
for name, f, folder in [("real captures Arm C", "armC/armC_selected.csv", "armC/armC_digitized_12lead"), ("real captures C+", "armCext/armCext_selected_all.csv", "armCext/armCext_digitized_12lead_all")]:
    s = pd.read_csv(R + f)
    files = glob.glob(R + folder + "/**/*.npz", recursive=True)
    cnt = {}
    for p in files:
        m = re.search(r"(\d{6,})", os.path.basename(p))
        if m:
            cnt[int(m.group(1))] = cnt.get(int(m.group(1)), 0) + 1
    for _, r in s.iterrows():
        rid = int(r["id"])
        t = truth.loc[rid] if rid in truth.index else None
        rows.append(dict(set=name, recording_id=rid, ecg_id=None, signal_source="Challenge truth export (Kaggle), 12 leads", signal_fs_hz=float(r["fs"]), true_signal_available=bool(t is not None),
                         n_leads=12, n_images=9, image_conditions="9 capture types: kit original, print-scan colour/bw, phone photo of print, phone photo of screen, stained, damaged, mould scan colour/bw",
                         image_type="real scans and phone photos", image_size_px="varies (e.g. 2200 x 1700, 2132 x 1652)",
                         calibration="from the grid by the digitiser (25 mm/s, 10 mm/mV assumed)", digitised_12lead_saved=f"yes ({cnt.get(rid, 0)} of 9 saved)",
                         has_12SL=False, ptbxl_flagged=None, true_lead_II_seconds=(float(t.duration_s_from_II) if t is not None else None)))

# ---- own phone photos: pages P01-P30 and Q01-Q20 (drawn from PTB-XL, photographed from a laptop screen)
for name, f, n in [("own phone set 1 (P01-P30)", "ownphotos/pages_mapping.csv", 2), ("own phone set 2 (Q01-Q20)", "ownphotos2/pages_mapping.csv", 2)]:
    m = pd.read_csv(R + f)
    for _, r in m.iterrows():
        add_ptbxl(r["page"], int(r["ecg_id"]), name, n, "photos of a laptop screen: straight and from about 30 degrees", "yes (digitised on Kaggle)",
                  extra=dict(image_type="phone photo of a screen (page drawn by ECG-Image-Kit)", image_size_px="phone photo, varies",
                             calibration="from the grid by the digitiser", age=r["age"]))

inv = pd.DataFrame(rows)
os.makedirs(R, exist_ok=True)
inv.to_csv(R + "DATASET_INVENTORY.csv", index=False)

# ---- summary
lines = ["# Dataset inventory (written by scripts/analysis/dataset_inventory.py)", "",
         "One row per recording is in `DATASET_INVENTORY.csv` (columns: set, recording_id, ecg_id, signal source and rate, true signal available, number of leads, number of images and conditions, image type and size, calibration, whether digitised 12-lead signals are saved, 12SL availability and values, reference heart rates, flags).", "",
         "## Per set", "", "| Set | Recordings | Images | Image type | True signal | 12SL | Digitised signals saved |", "|---|---|---|---|---|---|---|"]
for s, g in inv.groupby("set", sort=False):
    ni = int(g.n_images.sum())
    sv = g.digitised_12lead_saved.astype(str).str.startswith("yes").sum()
    lines.append(f"| {s} | {len(g)} | {ni} | {g.image_type.iloc[0]} | {int(g.true_signal_available.sum())} of {len(g)} | {int(g.has_12SL.sum())} of {len(g)} | {sv} of {len(g)} recordings |")
lines += ["", "## Reference quality (simulated sets)", ""]
sim = inv[inv.set.str.startswith("simulated")]
lines.append(f"- Reference-uncertain (100 Hz and 500 Hz heart rates differ by more than 5 bpm): {int(sim.reference_uncertain.sum())} of {len(sim)}.")
lines.append(f"- PTB-XL quality flag (drift, static, burst noise, electrodes, extra beats, pacemaker): {int(sim.ptbxl_flagged.sum())} of {len(sim)}.")
lines += ["", "## What this sheet shows and what is missing", "",
          "- Pairs: every image has a true digital signal. For the simulated sets and your phone pages the page IS drawn from that signal, so the pair is exact. For the real captures the Challenge provides the true signal (we exported lead II only, 10 s at 1,000 Hz; so waveform comparison for real captures is limited to lead II).",
          "- 12SL commercial measurements exist for all PTB-XL recordings (PTB-XL+). They do not exist for the Challenge recordings, which have their own ids.",
          "- The first 50 recordings have no saved digitised signals, so no waveform or interval error can be computed for them.",
          "- No expert beat annotations (P, QRS, T boundaries) are used; 12SL and Glasgow medians are the interval references.",
          "- Image quality is described by the damage type and level (simulated) or capture type (real), not by one quality number."]
open(R + "DATASET_INVENTORY.md", "w", encoding="utf-8").write("\n".join(lines) + "\n")
print(inv.groupby("set", sort=False).size().to_string())
print("columns:", list(inv.columns))
