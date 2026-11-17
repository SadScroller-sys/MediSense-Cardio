"""Builds colab/MediSense_Cardio_ArmC_Kaggle_RealCaptures.ipynb  ("Arm C": real scans and phone photos of printed ECGs).

Data: Kaggle competition "PhysioNet - Digitization of ECG Images" (CC BY 4.0, data use allowed for academic research). For every recording the
training folder has the original ECG-Image-Kit page (-0001) and real captures of the SAME page (printed + scanned, scanned black and white,
phone photos of the print, photos of a laptop screen, stained/soaked, extensively damaged, mold), plus the true 12-lead signal as CSV.
The notebook runs on Kaggle with the competition attached as input (nothing to download).

What it does: picks N recordings by a fixed seeded rule, digitises every version with the same Open-ECG-Digitizer settings as the main study,
compares with the true signal (heart rate, aligned SNR, intervals), and saves all 12 digitised leads.
Exploratory arm: changes no rule of docs/plan/MASTER_PLAN.md. The metric functions are copied verbatim from the extension notebook.
"""
import ast
import json
import re

ROOT = "D:/Capstone Project"
ext = json.load(open(f"{ROOT}/colab/MediSense_Cardio_Extension_150.ipynb", encoding="utf-8"))["cells"]


def text_of(i):
    return "".join(ext[i]["source"])


def find(substr, kind="code"):
    r = [i for i, c in enumerate(ext) if c["cell_type"] == kind and substr in text_of(i)]
    assert r, substr
    return r[0]


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": [l + "\n" for l in text.split("\n")]}


def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": [l + "\n" for l in text.split("\n")]}


def sub(text, old, new, count=1):
    assert text.count(old) == count, f"expected {count} of {old[:70]!r}, found {text.count(old)}"
    return text.replace(old, new)


cells = []
cells.append(md("""# MediSense-Cardio -- Arm C: real scans and phone photos (Kaggle)

**Why:** the researchers who built the PhysioNet Challenge tested digitisers on *real* captures: pages that were printed, scanned, photographed with phones, stained, soaked or left to mold.
Our main study damages computer-drawn pages. This arm uses the Challenge's own real captures, so we can say how the same digitiser behaves on them.
Data: Kaggle competition *PhysioNet - Digitization of ECG Images* (CC BY 4.0). For each recording there are real captures of the same page and the true 12-lead signal.

**What it does:** picks 40 recordings with a fixed seeded rule (no result is seen), digitises every version (about 9 per recording, about 360 images), and compares with the true signal:
heart rate, aligned SNR and intervals. Same digitiser, same settings and same metric code as the main study. All 12 digitised leads are saved.

**Before you run (once):** right panel -> *Input* -> add the competition *PhysioNet - Digitization of ECG Images*;  *Settings* -> *Accelerator* = a GPU (T4 or P100) and *Internet* = On.
**Run:** *Run All*. Keep the tab open. About 2-3 hours. The first cells check everything in a few minutes and stop with a clear message if something is wrong.
**After:** *Output* tab -> download `results_armC.csv`, `armC_provenance.json`, `armC_selected.csv` and the folder `armC_digitized_12lead`.
This arm is exploratory and changes no rule of the master plan."""))

cells.append(md("## Step 1 -- Settings and the competition data"))
cells.append(code("""import os, glob, json, time, shutil, subprocess, sys, datetime
import numpy as np, pandas as pd

N_RECORDS = 40            # how many recordings (fixed before any result)
SEED = 42                 # fixed seed for the choice of recordings
WORK = '/kaggle/working'  # what is saved and can be downloaded
TMP = '/tmp/armC'         # scratch space, not saved
DIG_DIR = f'{TMP}/Open-ECG-Digitizer'
# the real-capture versions of each page (segment number in the file name -> label)
VERSIONS = {
    '0001': 'C0_kit_original',          # the page as drawn by ECG-Image-Kit (reference)
    '0003': 'C1_print_scan_colour',     # printed in colour, scanned in colour
    '0004': 'C2_print_scan_bw',         # printed in colour, scanned in black and white
    '0005': 'C3_phone_photo_print',     # mobile photo of the colour print
    '0006': 'C4_phone_photo_screen',    # mobile photo of the page on a laptop screen
    '0009': 'C5_stained_soaked_photo',  # mobile photo of a stained and soaked print
    '0010': 'C6_extensive_damage_photo',# mobile photo of a print with extensive damage
    '0011': 'C7_mold_scan_colour',      # scan of a print with mold, colour
    '0012': 'C8_mold_scan_bw',          # scan of a print with mold, black and white
}
os.makedirs(WORK, exist_ok=True); os.makedirs(TMP, exist_ok=True)

found = glob.glob('/kaggle/input/**/train.csv', recursive=True)
assert found, ('The competition data is not attached. Right panel -> Input -> Add Input -> search '
               '"PhysioNet - Digitization of ECG Images" -> add it. Then Run All again.')
COMP_DIR = os.path.dirname(found[0])
train = pd.read_csv(f'{COMP_DIR}/train.csv')
print('competition folder:', COMP_DIR)
print('train.csv columns:', list(train.columns), '| rows:', len(train))
assert 'id' in train.columns and 'fs' in train.columns, 'train.csv does not have the expected columns id and fs: paste this output into the chat'
train['id'] = train['id'].astype(str)
train_fs = dict(zip(train['id'], train['fs']))
print(train.head(3).to_string())"""))

cells.append(md("## Step 2 -- Choose the recordings (fixed rule: seeded random choice among recordings that have every version and the true signal)"))
cells.append(code("""def versions_present(i):
    return [c for c in VERSIONS if os.path.exists(f'{COMP_DIR}/train/{i}/{i}-{c}.png')]

all_ids = sorted(train['id'])
full = [i for i in all_ids if os.path.exists(f'{COMP_DIR}/train/{i}/{i}.csv') and len(versions_present(i)) == len(VERSIONS)]
print(f'{len(all_ids)} training recordings; {len(full)} have the true signal and all {len(VERSIONS)} versions.')
if len(full) < 10:
    ex = all_ids[0]
    print('Files of the first recording:', sorted(os.listdir(f'{COMP_DIR}/train/{ex}')))
assert len(full) >= 10, 'Too few recordings have all versions: paste the printout above into the chat.'
rng = np.random.default_rng(SEED)
chosen = sorted(rng.choice(full, size=min(N_RECORDS, len(full)), replace=False).tolist())
pd.DataFrame({'id': chosen, 'fs': [train_fs[i] for i in chosen]}).to_csv(f'{WORK}/armC_selected.csv', index=False)
print(f'Chosen {len(chosen)} recordings (seed {SEED}); first five: {chosen[:5]}')
truth0 = pd.read_csv(f'{COMP_DIR}/train/{chosen[0]}/{chosen[0]}.csv')
print('true-signal columns:', list(truth0.columns), '| rows:', len(truth0), '| fs:', train_fs[chosen[0]])
assert 'II' in truth0.columns, 'true-signal CSV has no column II: paste the printout above into the chat'"""))

cells.append(md("## Step 3 -- Install the tools and set up the digitiser (same as the main study)"))
cells.append(code("""def sh(cmd, cwd=None, show=True):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    if show and r.returncode != 0:
        print((r.stdout + r.stderr)[-1500:])
    return r

r = subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'neurokit2', 'opencv-python-headless', 'yacs', 'scikit-image', 'tqdm', 'torch-tps'],
                   capture_output=True, text=True)
print('pip install:', 'ok' if r.returncode == 0 else 'FAILED\\n' + r.stderr[-800:])
import neurokit2 as nk, cv2, torch
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print('device:', device)
if device == 'cpu':
    print('WARNING: no GPU. Right panel -> Settings -> Accelerator -> choose a GPU, then Run All again. On CPU this takes about 2 minutes per image.')"""))

cells.append(code("""if os.path.exists(DIG_DIR):
    shutil.rmtree(DIG_DIR)
r = sh(f'git clone https://github.com/Ahus-AIM/Open-ECG-Digitizer.git {DIG_DIR}')
assert os.path.isdir(f'{DIG_DIR}/src'), 'git clone failed. Is Internet switched on? Right panel -> Settings -> Internet -> On.'
sh('apt-get -qq install -y git-lfs', show=False)
sh('git lfs install', cwd=DIG_DIR, show=False)
sh('git lfs pull', cwd=DIG_DIR)
path = f'{DIG_DIR}/src/utils.py'
content = open(path).read()
if 'Stopper = object' not in content:      # patch only once
    content = content.replace("from ray.tune import Stopper",
                              "try:\\n    from ray.tune import Stopper\\nexcept ImportError:\\n    Stopper = object  # ray not needed for inference")
    open(path, 'w').write(content)
wts = {f: os.path.getsize(f'{DIG_DIR}/weights/{f}') for f in os.listdir(f'{DIG_DIR}/weights')} if os.path.isdir(f'{DIG_DIR}/weights') else {}
print('weights:', wts)
assert wts.get('unet_weights_07072025.pt', 0) > 1e6 and wts.get('lead_name_unet_weights_07072025.pt', 0) > 1e6, \\
    'The digitiser weight files are missing or only pointers (git-lfs problem): paste the messages above into the chat.'
print('Digitiser ready.')"""))

cfg = text_of(find("def write_digitizer_config"))
cfg = cfg.split("import torch\ndevice = 'cuda' if torch.cuda.is_available() else 'cpu'\nprint(f\"Using device: {device}\")\n", 1)[1]
cfg = sub(cfg, "'/content/Open-ECG-Digitizer/batch_config.yml'", "f'{DIG_DIR}/batch_config.yml'")
cfg = sub(cfg, 'print("Digitizer config helper ready.")', 'print("Digitizer config helper ready (same settings as the main study).")')
cells.append(code(cfg.strip("\n")))

cells.append(code("""def sh1(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()

prov = {
    'written_utc': datetime.datetime.utcnow().isoformat() + 'Z',
    'open_ecg_digitizer_commit': sh1(f'git -C {DIG_DIR} rev-parse HEAD'),
    'digitizer_weights': sorted(os.listdir(f'{DIG_DIR}/weights')),
    'competition_dir': COMP_DIR,
    'n_records': len(chosen),
    'seed': SEED,
    'versions': VERSIONS,
    'device': device,
}
with open(f'{WORK}/armC_provenance.json', 'w') as f:
    json.dump(prov, f, indent=2)
print(json.dumps(prov, indent=2))"""))

cells.append(md("## Step 4 -- Variant list and results checkpoint"))
cells.append(code("""variant_rows = []
for rid in chosen:
    for c, label in VERSIONS.items():
        variant_rows.append({'stem': rid, 'axis': label, 'level': 0, 'variant_id': f'{rid}__{label}',
                             'source_path': f'{COMP_DIR}/train/{rid}/{rid}-{c}.png'})
all_variants = pd.DataFrame(variant_rows)
RESULTS_PATH = f'{WORK}/results_armC.csv'
if os.path.exists(RESULTS_PATH):
    results_so_far = pd.read_csv(RESULTS_PATH)
    print(f'Resuming: {len(results_so_far)} results already in {RESULTS_PATH}')
else:
    results_so_far = pd.DataFrame()
done = set(results_so_far['variant_id']) if len(results_so_far) else set()
remaining = all_variants[~all_variants['variant_id'].isin(done)].reset_index(drop=True)
print(f'{len(all_variants)} variants in total, {len(remaining)} still to do.')"""))

t23 = text_of(find("def compute_metrics"))
a = t23.index("def extract_intervals"); b = t23.index("os.makedirs(f'{STUDY_DIR}/extension_digitized_12lead'")
c0 = t23.index("def aligned_snr"); d = t23.index("def compute_metrics")
funcs = t23[a:b].rstrip() + "\n\n" + t23[c0:d].rstrip()
cells.append(md("## Step 5 -- Measurement code (copied word for word from the main study)"))
cells.append(code("FS_CANONICAL = 1000.0\n\n" + funcs))

cells.append(code("""os.makedirs(f'{WORK}/armC_digitized_12lead', exist_ok=True)

def compute_metrics_C(batch_df, digitized_dir):
    rows = []
    for _, v in batch_df.iterrows():
        rid = v['stem']
        fs_gt = float(train_fs[rid])
        truth = pd.read_csv(f'{COMP_DIR}/train/{rid}/{rid}.csv')
        gt_signal = truth['II'].dropna().to_numpy(dtype=float)       # true lead II in mV
        csv_path = f'{digitized_dir}/{v["variant_id"]}_timeseries_canonical.csv'
        img = cv2.imread(v['source_path'])
        row = {'variant_id': v['variant_id'], 'record': rid, 'axis': v['axis'], 'level': v['level'],
               'img_h': None if img is None else img.shape[0], 'img_w': None if img is None else img.shape[1], 'fs_truth': fs_gt}

        gt_peaks, _ = nk.ecg_peaks(gt_signal, sampling_rate=fs_gt)
        gt_hr = np.nanmean(nk.ecg_rate(gt_peaks, sampling_rate=fs_gt, desired_length=len(gt_signal)))
        gt_iv = extract_intervals(gt_signal, fs_gt, gt_hr)
        row.update({'gt_hr': round(gt_hr, 1),
                    'gt_pr_ms': round(gt_iv['pr_ms'], 1) if not np.isnan(gt_iv['pr_ms']) else None,
                    'gt_qrs_ms': round(gt_iv['qrs_ms'], 1) if not np.isnan(gt_iv['qrs_ms']) else None,
                    'gt_qt_ms': round(gt_iv['qt_ms'], 1) if not np.isnan(gt_iv['qt_ms']) else None,
                    'gt_qtc_ms': round(gt_iv['qtc_ms'], 1) if not np.isnan(gt_iv['qtc_ms']) else None})
        # reference at 500 Hz for the aligned SNR
        if abs(fs_gt - 500.0) < 1e-6:
            gt500_sig = gt_signal
        else:
            from scipy.signal import resample_poly
            gt500_sig = resample_poly(gt_signal, 500, int(round(fs_gt)))

        none_cols = ['dig_hr', 'diff_bpm', 'snr_aligned_db', 'snr_lag_ms', 'snr_pcc', 'dig_pr_ms', 'dig_qrs_ms', 'dig_qt_ms', 'dig_qtc_ms',
                     'diff_pr_ms', 'diff_qrs_ms', 'diff_qt_ms', 'diff_qtc_ms']
        if not os.path.exists(csv_path):
            row.update({k: None for k in none_cols})
            rows.append(row)
            continue

        digitized = pd.read_csv(csv_path)
        dig_signal = digitized['II'].dropna().to_numpy() / 1000.0     # microvolts -> millivolts
        np.savez_compressed(f'{WORK}/armC_digitized_12lead/{v["variant_id"]}.npz',
                            **{c: digitized[c].to_numpy(dtype='float32') for c in digitized.columns})
        try:
            dig_peaks, _ = nk.ecg_peaks(dig_signal, sampling_rate=FS_CANONICAL)
            dig_hr = np.nanmean(nk.ecg_rate(dig_peaks, sampling_rate=FS_CANONICAL, desired_length=len(dig_signal)))
        except Exception:
            dig_hr = float('nan')
        dig_iv = extract_intervals(dig_signal, FS_CANONICAL, dig_hr) if len(dig_signal) > 10 else {
            'pr_ms': float('nan'), 'qrs_ms': float('nan'), 'qt_ms': float('nan'), 'qtc_ms': float('nan')}
        diff = abs(gt_hr - dig_hr) if not np.isnan(dig_hr) else None

        def safe_diff(g, d):
            return abs(g - d) if (g is not None and d is not None and not np.isnan(g) and not np.isnan(d)) else None

        snr_aligned, snr_lag, snr_pcc = float('nan'), float('nan'), float('nan')
        if len(dig_signal) > 10:
            snr_aligned, snr_lag, snr_pcc = aligned_snr(gt500_sig, dig_signal)
        def r1(x, n=1):
            return round(x, n) if (x is not None and not np.isnan(x)) else None
        row.update({'dig_hr': r1(dig_hr), 'diff_bpm': round(diff, 2) if diff is not None else None,
                    'snr_aligned_db': r1(snr_aligned, 2), 'snr_lag_ms': r1(snr_lag), 'snr_pcc': r1(snr_pcc, 3),
                    'dig_pr_ms': r1(dig_iv['pr_ms']), 'dig_qrs_ms': r1(dig_iv['qrs_ms']),
                    'dig_qt_ms': r1(dig_iv['qt_ms']), 'dig_qtc_ms': r1(dig_iv['qtc_ms'])})
        for k, g, d in (('pr', gt_iv['pr_ms'], dig_iv['pr_ms']), ('qrs', gt_iv['qrs_ms'], dig_iv['qrs_ms']),
                        ('qt', gt_iv['qt_ms'], dig_iv['qt_ms']), ('qtc', gt_iv['qtc_ms'], dig_iv['qtc_ms'])):
            x = safe_diff(g, d)
            row[f'diff_{k}_ms'] = round(x, 1) if x is not None else None
        rows.append(row)
    return pd.DataFrame(rows)

def run_batch(batch):
    \"\"\"Copy the real captures of one sub-batch, digitise them, return (metrics DataFrame, seconds, tool output).\"\"\"
    imgs, outd = f'{TMP}/images_batch', f'{TMP}/digitized_batch'
    for d in (imgs, outd):
        if os.path.exists(d):
            shutil.rmtree(d)
    os.makedirs(imgs)
    for _, v in batch.iterrows():
        shutil.copy(v['source_path'], f'{imgs}/{v["variant_id"]}.png')
    write_digitizer_config(imgs, outd)
    t0 = time.time()
    r = subprocess.run([sys.executable, '-m', 'src.digitize', '--config', f'{DIG_DIR}/batch_config.yml'],
                       cwd=DIG_DIR, capture_output=True, text=True)
    return compute_metrics_C(batch, outd), time.time() - t0, (r.stdout + r.stderr)

# smoke test: two images first, so a problem shows up in minutes and not after hours
smoke, secs, tool_out = run_batch(remaining.iloc[:2].reset_index(drop=True))
print(smoke[['variant_id', 'gt_hr', 'dig_hr', 'diff_bpm', 'snr_aligned_db']].to_string())
print(f'smoke test took {secs:.0f} s for 2 images')
if smoke['dig_hr'].isna().all():
    print('The digitiser made no usable output for the two test images (the original page and its scan). Last lines of its output:')
    print(tool_out[-1800:])
    raise SystemExit('STOPPED on purpose: paste the output above into the chat. Nothing else will run until this is fixed.')
print('Smoke test passed: continuing with the full run.')"""))

cells.append(md("## Step 6 -- Digitise everything in checkpointed sub-batches"))
cells.append(code("""SUBBATCH_SIZE = 15
SESSION_TIME_BUDGET_S = 9.5 * 3600
session_start = time.time()
n_done_session = 0
while len(remaining) > 0 and (time.time() - session_start) < SESSION_TIME_BUDGET_S:
    batch = remaining.iloc[:SUBBATCH_SIZE].reset_index(drop=True)
    batch_results, secs, _ = run_batch(batch)
    results_so_far = pd.concat([results_so_far, batch_results], ignore_index=True).drop_duplicates(subset='variant_id', keep='last')
    tmp_path = RESULTS_PATH + '.tmp'
    results_so_far.to_csv(tmp_path, index=False)
    os.replace(tmp_path, RESULTS_PATH)
    n_on_disk = len(pd.read_csv(RESULTS_PATH))
    assert n_on_disk == len(results_so_far), f'SAVE VERIFY FAILED: disk has {n_on_disk}, memory has {len(results_so_far)}'
    remaining = remaining.iloc[SUBBATCH_SIZE:].reset_index(drop=True)
    n_done_session += len(batch)
    print(f'Checkpointed {len(batch)} variants ({secs/len(batch):.1f} s/image). Done {len(results_so_far)}/{len(all_variants)}, '
          f'{len(remaining)} remaining, elapsed {(time.time()-session_start)/60:.0f} min.')
print('ALL VARIANTS COMPLETE.' if len(remaining) == 0 else f'{len(remaining)} variants remaining: run this cell again.')"""))

cells.append(md("## Step 7 -- Overview (what to look at first)"))
cells.append(code("""r = pd.read_csv(RESULTS_PATH).copy()
r['no_output'] = r['dig_hr'].isna()
r['wrong_hr_5bpm'] = r['diff_bpm'] > 5
summ = r.groupby('axis').agg(n=('variant_id', 'size'), no_output=('no_output', 'sum'), wrong_hr_5bpm=('wrong_hr_5bpm', 'sum'),
                             median_snr_db=('snr_aligned_db', 'median'), median_img_w=('img_w', 'median'), median_img_h=('img_h', 'median')).round(1)
print(summ.to_string())
print('\\nDownload from the Output tab: results_armC.csv, armC_provenance.json, armC_selected.csv, armC_digitized_12lead/')"""))

nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "name": "python3", "language": "python"},
                                   "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 4}
for n, c in enumerate(cells):
    if c["cell_type"] != "code":
        continue
    try:
        ast.parse("".join(c["source"]))
    except SyntaxError as e:
        raise SystemExit(f"cell {n} does not compile: {e}")
out = f"{ROOT}/colab/MediSense_Cardio_ArmC_Kaggle_RealCaptures.ipynb"
json.dump(nb, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(f"Wrote {out}: {len(cells)} cells, all code cells compile.")
