"""Heart health module, data layer (rules: docs/plan/analysis_plan_changes.md, 2026-11-15 "Heart health module").
Labels, the page-layout cut (the SAME input for training and for the app), the exclusion list and the digitised test sets.
Research prototype. Not a medical device."""
import ast
import glob
import os

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
R = os.path.join(ROOT, "results") + os.sep
PT = os.path.join(ROOT, "data", "ptbxl") + os.sep
CACHE = os.path.join(ROOT, "data", "health_cache") + os.sep
LEADS = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
LAYOUT = {"I": (0, 2.5), "II": (0, 10), "III": (0, 2.5), "aVR": (2.5, 5), "aVL": (2.5, 5), "aVF": (2.5, 5), "V1": (5, 7.5), "V2": (5, 7.5), "V3": (5, 7.5), "V4": (7.5, 10), "V5": (7.5, 10), "V6": (7.5, 10)}
CLASSES = ["NORM", "MI", "STTC", "CD", "HYP", "AF"]
FS = 100
T = 1000


# ------------------------------------------------------------------------------------------------ labels
def load_db():
    db = pd.read_csv(PT + "ptbxl_database.csv").set_index("ecg_id").sort_index()
    scp = pd.read_csv(PT + "scp_statements.csv", index_col=0)
    scp = scp[scp.diagnostic == 1]
    rows = []
    for i, s in db.scp_codes.items():
        codes = ast.literal_eval(s)
        sup = {scp.loc[k, "diagnostic_class"] for k in codes if k in scp.index}
        rows.append([c in sup for c in CLASSES[:5]] + [("AFIB" in codes) or ("AFLT" in codes)])
    Y = pd.DataFrame(rows, index=db.index, columns=CLASSES).astype(np.float32)
    return db, Y


# ------------------------------------------------------------------------------------------------ the page-layout input
def finalize(x, mask):
    """x (12, T) mV with NaN outside, mask (12, T) bool -> (24, T) float32: mean removed inside the window, zero outside, plus the mask channels."""
    x = np.where(mask, x, 0.0).astype(np.float32)
    for k in range(12):
        m = mask[k]
        if m.any():
            x[k, m] -= x[k, m].mean()
    return np.concatenate([x, mask.astype(np.float32)], axis=0)


def page_layout_from_signal(sig):
    """sig (12, 1000) mV at 100 Hz (training side): keep each lead only inside its page window."""
    mask = np.zeros((12, T), bool)
    for k, L in enumerate(LEADS):
        a, b = LAYOUT[L]
        mask[k, int(a * FS):int(b * FS)] = True
    return finalize(sig.astype(np.float32), mask)


def digitised_to_input(leads):
    """leads: dict lead -> array (10000,) microvolts at 1 kHz, NaN = not read (the digitiser output, as saved or as the app gets it) -> (24, 1000)."""
    x = np.full((12, T), np.nan, np.float32)
    for k, L in enumerate(LEADS):
        if L in leads and leads[L] is not None:
            a = np.asarray(leads[L], float)[:10000] / 1000.0
            if len(a) < 10000:
                a = np.concatenate([a, np.full(10000 - len(a), np.nan)])
            with np.errstate(all="ignore"):
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    x[k] = np.nanmean(a.reshape(T, 10), axis=1)
    return finalize(x, np.isfinite(x))


# ------------------------------------------------------------------------------------------------ PTB-XL signals (100 Hz, cached)
def _read_record(fn):
    base = PT + fn
    hdr = open(base + ".hea").read().splitlines()
    n = int(hdr[0].split()[1])
    names = [h.split()[-1].lower() for h in hdr[1:1 + n]]
    gains = [float(h.split()[2].split("(")[0].split("/")[0]) for h in hdr[1:1 + n]]
    dat = np.fromfile(base + ".dat", dtype="<i2").reshape(-1, n).astype(np.float32)
    out = np.zeros((12, T), np.float32)
    for k, L in enumerate(LEADS):
        j = names.index(L.lower())
        out[k] = dat[:T, j] / gains[j]
    return out


def load_ptbxl100(db):
    """(N, 12, 1000) float16 in db order (ecg_id ascending), cached in data/health_cache/."""
    os.makedirs(CACHE, exist_ok=True)
    f = CACHE + "ptbxl100_mV_f16.npy"
    if os.path.exists(f):
        a = np.load(f, mmap_mode="r")
        if len(a) == len(db):
            return a
    a = np.zeros((len(db), 12, T), np.float16)
    for n, fn in enumerate(db.filename_lr):
        a[n] = _read_record(fn).astype(np.float16)
        if n % 4000 == 0:
            print("reading PTB-XL 100 Hz", n, "of", len(db), flush=True)
    np.save(f, a)
    return a


# ------------------------------------------------------------------------------------------------ our digitised sets and the exclusion list
def digitised_sets():
    """DataFrame, one row per digitised input: set (T2 drawn pages, T3 phone photos), name, ecg_id, group (cluster for the bootstrap), path."""
    rows = []
    sel = pd.read_csv(R + "extension/selected_100.csv")
    for _, r in sel.iterrows():
        fs_ = glob.glob(R + f"extension/extension_digitized_12lead/**/{r.record}-*__clean*.npz", recursive=True)
        if fs_:
            rows.append(dict(set="T2", source="new100", name=r.record, ecg_id=int(r.ecg_id), group=r.record, path=fs_[0]))
    for tag, csv, folder in (("fresh F", "fresh/selected_fresh_100.csv", "fresh/fresh_digitized_12lead/{p}.npz"), ("sealed G", "fresh_g/selected_g_100.csv", "fresh_g/g_digitized_12lead/{p}.npz")):
        for _, r in pd.read_csv(R + csv).iterrows():
            f = R + folder.format(p=r.page)
            if os.path.exists(f):
                rows.append(dict(set="T2", source=tag, name=r.page, ecg_id=int(r.ecg_id), group=r.page, path=f))
    u = pd.read_csv(R + "analysis/sectionU_confirm_per_photo.csv")
    u = u[u.version == "V2"]
    for _, r in u.iterrows():
        folder = "ownphotos/fixexp_out/fixexp_digitized_12lead/" if r.set == "P" else "ownphotos2/confirm_out/confirm_digitized_12lead/"
        f = R + folder + f"{r.photo}__V2_straighten.npz"
        if os.path.exists(f):
            rows.append(dict(set="T3", source=f"phone {r.set}", name=r.photo, ecg_id=int(r.ecg_id), group=r.page, path=f))
    x = pd.read_csv(R + "analysis/sectionX_confirm_per_photo.csv")
    for _, r in x.iterrows():
        f = R + f"fresh_g/photos_digitized_12lead/{r.photo}__V2_straighten.npz"
        if os.path.exists(f):
            rows.append(dict(set="T3", source="phone G", name=r.photo, ecg_id=int(r.ecg_id), group=r.page, path=f))
    return pd.DataFrame(rows)


def excluded_ids():
    """Every recording that appears in any of our digitised or photo sets: removed from training, fold 9 and fold 10 (rule logged 2026-11-15)."""
    ids = set()
    inv = pd.read_csv(R + "DATASET_INVENTORY.csv")
    ids |= set(inv.ecg_id.dropna().astype(int))
    for f in ("extension/selected_100.csv", "fresh/selected_fresh_100.csv", "fresh_g/selected_g_100.csv", "paper_h/selected_h_20.csv", "ownphotos/pages_mapping.csv", "ownphotos2/pages_mapping.csv"):
        d = pd.read_csv(R + f)
        ids |= set(d.ecg_id.astype(int))
    ids |= set(digitised_sets().ecg_id)
    return ids
