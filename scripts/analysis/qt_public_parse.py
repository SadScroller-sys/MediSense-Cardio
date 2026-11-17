"""Parse LUDB and QT Database expert marks into training arrays (rules: docs/plan/analysis_plan_changes.md 2026-11-16 night). Writes results/qt_public/ludb.npz and qtdb.npz.
Usage: demo\.venv-gpu\Scripts\python.exe -I scripts/analysis/qt_public_parse.py"""
import glob
import os

import numpy as np
import wfdb

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = ROOT + "/results/qt_public/"
os.makedirs(OUT, exist_ok=True)
LUDB = ROOT + "/data/ludb/lobachevsky-university-electrocardiography-database-1.0.1/data/"
QTDB = ROOT + "/data/qtdb/qt-database-1.0.0/"
LEADS = ["i", "ii", "iii", "avr", "avl", "avf", "v1", "v2", "v3", "v4", "v5", "v6"]


def triples(sample, sym, mid):
    out = []
    for i in range(len(sym) - 2):
        if sym[i] == "(" and sym[i + 1] == mid and sym[i + 2] == ")":
            out.append((sample[i], sample[i + 1], sample[i + 2]))
    return out


def beats_from(trip_qrs, trip_t):
    """trip_qrs, trip_t: lists of (on, peak, off) for one lead; returns list of (qrs_on, qrs_off, t_end or None)."""
    res = []
    for k, (a, p, b) in enumerate(trip_qrs):
        nxt = trip_qrs[k + 1][0] if k + 1 < len(trip_qrs) else 1 << 30
        te = [t[2] for t in trip_t if t[0] > b and t[0] < nxt]
        res.append((a, p, b, te[0] if te else None))
    return res


def ludb():
    recs = sorted({os.path.splitext(os.path.basename(f))[0] for f in glob.glob(LUDB + "*.dat")}, key=int)
    X, Q, T, NB, ID = [], [], [], [], []
    for rc in recs:
        r = wfdb.rdrecord(LUDB + rc)
        sig = r.p_signal.T  # 12 x 5000 mV, 500 Hz
        per = {}
        for L in LEADS:
            a = wfdb.rdann(LUDB + rc, L)
            per[L] = beats_from(triples(a.sample, a.symbol, "N"), triples(a.sample, a.symbol, "t"))
        ref = per["ii"]
        qs, ts = [], []
        for (a, p, b, te) in ref:
            ons, offs, tes = [a], [b], ([te] if te is not None else [])
            for L in LEADS:
                if L == "ii":
                    continue
                for (a2, p2, b2, te2) in per[L]:
                    if abs(p2 - p) <= 25:
                        ons.append(a2)
                        offs.append(b2)
                        if te2 is not None:
                            tes.append(te2)
                        break
            on, off = min(ons), max(offs)
            qs.append((off - on) * 2.0)
            if tes:
                ts.append((max(tes) - on) * 2.0)
        if len(qs) < 3 or len(ts) < 3:
            print("LUDB record", rc, "skipped (too few marked beats)", len(qs), len(ts))
            continue
        x = sig.reshape(12, 2500, 2).mean(2)
        X.append(x.astype(np.float32)); Q.append(np.median(qs)); T.append(np.median(ts)); NB.append(len(ts)); ID.append(int(rc))
    np.savez(OUT + "ludb.npz", X=np.stack(X), qrs=np.array(Q, np.float32), qt=np.array(T, np.float32), nbeats=np.array(NB), rec=np.array(ID))
    print("LUDB records kept:", len(ID), "| QRS median", np.median(Q), "| QT median", np.median(T), "| QT range", np.min(T), np.max(T))


def qtdb():
    X, Q, T, ID = [], [], [], []
    for f in sorted(glob.glob(QTDB + "*.q1c")):
        rc = f[:-4]
        name = os.path.basename(rc)
        try:
            r = wfdb.rdrecord(rc)
            a = wfdb.rdann(rc, "q1c")
        except Exception as e:  # noqa: BLE001
            print("QTDB", name, "failed", e)
            continue
        sig = r.p_signal.T.astype(np.float32)
        if r.fs != 250 or sig.shape[0] < 2:
            continue
        beats = beats_from(triples(a.sample, a.symbol, "N"), triples(a.sample, a.symbol, "t"))
        beats = [b for b in beats if b[3] is not None]
        if len(beats) < 3:
            continue
        start = beats[0][0] - 100
        while start + 2500 <= sig.shape[1]:
            inw = [b for b in beats if b[0] >= start and b[3] < start + 2500]
            if len(inw) >= 3:
                w = np.zeros((12, 2500), np.float32)
                w[1] = np.nan_to_num(sig[0, start:start + 2500])
                w[10] = np.nan_to_num(sig[1, start:start + 2500])
                X.append(w); Q.append(np.median([(b[2] - b[0]) * 4.0 for b in inw])); T.append(np.median([(b[3] - b[0]) * 4.0 for b in inw])); ID.append(name)
            start += 2500
    np.savez(OUT + "qtdb.npz", X=np.stack(X), qrs=np.array(Q, np.float32), qt=np.array(T, np.float32), rec=np.array(ID))
    print("QTDB windows:", len(ID), "from", len(set(ID)), "records | QRS median", np.median(Q), "| QT median", np.median(T))


ludb()
qtdb()
