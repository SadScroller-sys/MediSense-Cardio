"""Builds colab/MediSense_Cardio_TrafficLight_Demo.ipynb : a one-click demo (Run All) of the traffic-light safeguard.
Everything is embedded (tool code, model, six example signals from the own-phone photos, their photo thumbnails, the evaluation tables), so it runs on Kaggle, Colab or locally with only `pip install neurokit2`.
The six examples are chosen by a fixed rule (below), not by how nice they look."""
import base64
import io
import json
import os

import numpy as np
import pandas as pd
from PIL import Image, ImageOps

ROOT = "D:/Capstone Project/"
OUT = ROOT + "results/analysis/"
O = pd.read_csv(OUT + "sectionP_own_lights_labels.csv")
O["err"] = (O.dig_hr_clean - O.gt_hr_clean).abs()
# fixed selection rule: GREEN = first two (by file name) straight, GREEN; AMBER = first AMBER; RED+wrong = the two with the largest error; RED with no usable heart rate = first
O = O.sort_values("variant_id")
pick = []
pick += list(O[(O.light == "GREEN") & (O.shot == "A_straight")].variant_id[:2])
pick += list(O[O.light == "AMBER"].variant_id[:1])
pick += list(O[(O.light == "RED") & O.wrong].sort_values("err", ascending=False).variant_id[:2])
pick += list(O[(O.light == "RED") & O.none].variant_id[:1])
assert len(pick) == 6, pick
ex = {}
thumbs = {}
truth = {}
for v in pick:
    z = np.load(ROOT + f"results/ownphotos/kaggle_out/ownphotos_digitized_12lead/{v}.npz")
    buf = io.BytesIO()
    def _q(x):                      # microvolts rounded to integers (error <= 0.5 uV); NaN stored as -32768 (the notebook turns it back into NaN)
        x = np.asarray(x, float)
        assert np.nanmax(np.abs(x)) < 32000, "amplitude too large for int16"
        return np.where(np.isfinite(x), np.round(x), -32768).astype("int16")
    np.savez_compressed(buf, **{k: _q(z[k]) for k in z.files})
    ex[v] = base64.b64encode(buf.getvalue()).decode()
    im = ImageOps.exif_transpose(Image.open(f"C:/Users/Nihar Sai/Downloads/ownphotos/{v}.jpg")).convert("RGB")
    im.thumbnail((380, 380))
    b = io.BytesIO()
    im.save(b, "JPEG", quality=55)
    thumbs[v] = base64.b64encode(b.getvalue()).decode()
    r = O[O.variant_id == v].iloc[0]
    truth[v] = dict(page=r.page, shot=r.shot, tool_light=r.light, true_hr=None if pd.isna(r.gt_hr_clean) else round(float(r.gt_hr_clean), 1),
                    read_hr=None if pd.isna(r.dig_hr_clean) else round(float(r.dig_hr_clean), 1), none=bool(r.none), wrong=bool(r.wrong))
tabs = {k: pd.read_csv(OUT + f"sectionP_{k}.csv").to_csv(index=False) for k in ("comp_with_output_all", "comp_incl_no_output_all", "own_with_output", "own_incl_no_output")}
tool_src = open(ROOT + "safeguard/ecg_traffic_light.py", encoding="utf-8").read()
model_src = open(ROOT + "safeguard/model.json", encoding="utf-8").read()


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": [l + "\n" for l in t.split("\n")]}


def code(t):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [l + "\n" for l in t.split("\n")]}


cells = [md("""# MediSense-Cardio -- Traffic-light safeguard for ECG digitisers (demo, click Run All)

**The problem:** a program that turns a photo of an ECG back into a signal sometimes gives a wrong heart rate, and nothing tells the user.
**What this tool does:** it looks only at the digitised ECG line (never at the true signal) and shows a light: **GREEN** = no warning, **AMBER** = check it, **RED** = do not trust the heart rate.
**What you will see (about 1-2 minutes):** (1) six real examples from our own phone photos of ECG pages on a screen, each with the photo, the signal the digitiser drew, the light and the reasons; (2) how often each light was right on 1,200+ competition captures and on our 60 own-phone photos; (3) the limits.

*Research prototype, not a medical device. Built and frozen before it was tested on the real photos.*"""),
         code("""import subprocess, sys
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'neurokit2'], capture_output=True)
import os, io, json, base64, warnings
import numpy as np, pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from PIL import Image
warnings.filterwarnings('ignore')
os.makedirs('safeguard', exist_ok=True)
open('safeguard/ecg_traffic_light.py', 'w', encoding='utf-8').write(%s)
open('safeguard/model.json', 'w', encoding='utf-8').write(%s)
sys.path.insert(0, 'safeguard')
import ecg_traffic_light as T
print('Tool loaded. Thresholds: AMBER from score', round(T.load_model()['amber_threshold'], 3), '| RED from score', round(T.load_model()['red_threshold'], 3))""" % (repr(tool_src), repr(model_src))),
         md("## 1. Six real examples (our own phone photos of ECG pages on a laptop screen)\n*Chosen by a fixed rule, not by how nice they look: the first two GREEN straight photos, the first AMBER photo, the two RED photos with the largest heart-rate error, and the first RED photo with no usable heart rate.*"),
         code("""EXAMPLES = %s
THUMBS = %s
TRUTH = %s
COL = {'GREEN': '#2e9e4f', 'AMBER': '#f0a30a', 'RED': '#d62728'}
for vid in EXAMPLES:
    leads = {k: np.where(v == -32768, np.nan, v.astype(float)) for k, v in np.load(io.BytesIO(base64.b64decode(EXAMPLES[vid]))).items()}
    r = T.check(leads)
    tr = TRUTH[vid]
    fig, ax = plt.subplots(1, 2, figsize=(13, 3.6), gridspec_kw={'width_ratios': [1, 2.4]})
    ax[0].imshow(Image.open(io.BytesIO(base64.b64decode(THUMBS[vid])))); ax[0].axis('off')
    ax[0].set_title(f"photo ({tr['shot'].replace('_', ' ')})", fontsize=10)
    sig = np.asarray(leads['II'], float) / 1000.0
    t = np.arange(len(sig)) / 1000.0
    ax[1].plot(t, sig, lw=0.8, color='#333')
    ax[1].set_xlabel('seconds'); ax[1].set_ylabel('lead II (mV)'); ax[1].set_title('what the digitiser drew (lead II)', fontsize=10)
    fig.suptitle(f"{vid}   ->   {r['light']}", fontsize=14, weight='bold', color=COL[r['light']])
    plt.tight_layout(); plt.show()
    print('Reasons shown by the tool:', '; '.join(r['reasons']))
    if tr['none']:
        print(f"For the demo only (the true signal is not used by the tool): true heart rate {tr['true_hr']} bpm; the digitised signal gave no usable heart rate.")
    else:
        print(f"For the demo only (the true signal is not used by the tool): true heart rate {tr['true_hr']} bpm, read from the digitised signal {tr['read_hr']} bpm -> {'WRONG (> 5 bpm off)' if tr['wrong'] else 'right (within 5 bpm)'}")
    assert r['light'] == tr['tool_light'], 'the notebook gives a different light from the evaluation run'
    print('-' * 100)""" % (repr(ex), repr(thumbs), repr(truth))),
         md("## 2. How often was each light right? (the tool was frozen before these tests)\n*Wrong heart rate = more than 5 bpm away from the true value. The tool was trained only on simulated damage; thresholds were chosen only on the training data.*"),
         code("""from io import StringIO
TABS = %s
names = {'comp_with_output_all': 'Competition real captures (1,203 readings with an output)', 'own_with_output': 'Our own phone (54 readings with an output)',
         'comp_incl_no_output_all': 'Competition, counting "no output" as a failure', 'own_incl_no_output': 'Our own phone, counting "no usable heart rate" as a failure'}
dfs = {k: pd.read_csv(StringIO(v)) for k, v in TABS.items()}
for k in ('comp_with_output_all', 'own_with_output'):
    print(names[k]); display(dfs[k][['light', 'readings', 'wrong', 'wrong_rate', 'share_of_all_wrong', 'share_of_all_right']]) if 'display' in globals() else print(dfs[k].to_string(index=False))
fig, axs = plt.subplots(1, 2, figsize=(12, 3.8), sharey=True)
for a, k in zip(axs, ('comp_with_output_all', 'own_with_output')):
    d = dfs[k]; rate = [100 * w / n if n else 0 for w, n in zip(d.wrong, d.readings)]
    a.bar(d.light, rate, color=[COL[x] for x in d.light])
    for i, (r_, n_, w_) in enumerate(zip(rate, d.readings, d.wrong)):
        a.text(i, r_ + 1, f'{w_}/{n_}', ha='center', fontsize=10)
    a.set_title(names[k], fontsize=10); a.set_ylabel('percent of readings with a wrong heart rate'); a.set_ylim(0, 100)
plt.tight_layout(); plt.show()""" % repr(tabs)),
         md("""## 3. How to read this and what the limits are
- **GREEN readings were almost always right** (competition: 2 wrong out of 917; own phone: 0 wrong out of 22). **RED readings were wrong far more often** (competition 37%, own phone 76%). AMBER is in between.
- Together AMBER and RED hold most of the wrong readings (competition 96%, own phone 100% of the wrong ones with an output), at the price of flagging some right readings (competition 21%).
- **It checks the signal, not the truth.** It says "the beats in this signal are unreliable". Irregular rhythms such as atrial fibrillation are flagged more often than regular ones, even when the heart rate is right.
- **Limits:** only 46 wrong readings on the competition real captures and 14 on our phone; one phone, one screen, 30 ECG recordings; the intervals shown elsewhere treat images as independent, which is optimistic; the digitiser was trained on pages like the ones we tested. The tool was trained on simulated damage and thresholds were fixed before the real-photo tests. One safety rule (out-of-range guard) was added after a unit test showed noise got GREEN, before any real-photo evaluation.
- **Not a medical device.** It is a research prototype for a capstone study.""")]
nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "name": "python3", "language": "python"}, "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
json.dump(nb, open(ROOT + "colab/MediSense_Cardio_TrafficLight_Demo.ipynb", "w", encoding="utf-8"), indent=1)
print("written", len(cells), "cells;", round(os.path.getsize(ROOT + "colab/MediSense_Cardio_TrafficLight_Demo.ipynb") / 1e6, 2), "MB; examples:", pick)
