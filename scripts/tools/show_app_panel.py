"""Print the text of the heart-health results panel for one saved digitised page or photo (no photo needed, no GPU): shows exactly what the app would show.
Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/tools/show_app_panel.py <digitised.npz> [GREEN|AMBER]"""
import os
import re
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
sys.path.insert(0, os.path.join(ROOT, "safeguard"))
from health import assess as A  # noqa: E402
from health import dashboard as DB  # noqa: E402
import ecg_traffic_light as T  # noqa: E402

z = T.load_npz(sys.argv[1])
leads = {k: np.asarray(v, float) for k, v in np.load(sys.argv[1]).items()}
chk = T.check(z)
light = sys.argv[2] if len(sys.argv) > 2 else chk["light"]
ii = np.asarray(leads["II"], float)
import neurokit2 as nk  # noqa: E402

x = ii[np.isfinite(ii)] / 1000.0
xc = nk.ecg_clean(x, sampling_rate=1000, method="neurokit")
pk, _ = nk.ecg_peaks(xc, sampling_rate=1000)
hr = float(np.nanmean(nk.ecg_rate(pk, sampling_rate=1000, desired_length=len(x))))
a = A.assess(leads, light, chk.get("reasons"), True, hr, int(pk["ECG_R_Peaks"].sum()), (chk.get("features") or {}).get("rr_cv"), float("nan"), float("nan"), no_output=False)
txt = re.sub(r"<h4>", "\n\n## ", DB.results_panel(a))
txt = re.sub(r"</tr>", "\n", txt)
txt = re.sub(r"</t[dh]>", " | ", txt)
txt = re.sub(r"<[^>]+>", " ", txt)
print("light used:", light, "| heart rate:", round(hr, 1))
print(re.sub(r"[ \t]+", " ", txt))
