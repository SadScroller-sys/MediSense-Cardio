"""Learned QRS duration and QT model (Section AA; rules: docs/plan/analysis_plan_changes.md, 2026-11-15). Page-layout input at 250 Hz, digitiser emulation in training, regression on 12SL targets.
Research prototype. Not a medical device."""
import os
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import torch
import torch.nn as nn

from . import data as D

ROOT = D.ROOT
OUT = os.path.join(ROOT, "results", "intervals_ml") + os.sep
FS = 250
T = 2500
TARGETS = ["QRS_Dur_Global", "QT_Int_Global"]


# ------------------------------------------------------------------------------------------------ data: PTB-XL 500 Hz -> 250 Hz (block mean of 2), cached
def _read500(fn):
    base = D.PT + fn
    hdr = open(base + ".hea").read().splitlines()
    n = int(hdr[0].split()[1])
    names = [h.split()[-1].lower() for h in hdr[1:1 + n]]
    gains = [float(h.split()[2].split("(")[0].split("/")[0]) for h in hdr[1:1 + n]]
    dat = np.fromfile(base + ".dat", dtype="<i2").reshape(-1, n).astype(np.float32)[:5000]
    out = np.zeros((12, T), np.float32)
    for k, L in enumerate(D.LEADS):
        j = names.index(L.lower())
        out[k] = dat[:, j].reshape(T, 2).mean(1) / gains[j]
    return out


def load_ptbxl250(db):
    os.makedirs(D.CACHE, exist_ok=True)
    f = D.CACHE + "ptbxl250_mV_f16.npy"
    if os.path.exists(f):
        a = np.load(f, mmap_mode="r")
        if len(a) == len(db):
            return a
    fns = db.filename_hr.tolist()
    a = np.zeros((len(fns), 12, T), np.float16)
    with ThreadPoolExecutor(8) as ex:
        for n, x in enumerate(ex.map(_read500, fns)):
            a[n] = x.astype(np.float16)
            if n % 2000 == 0:
                print("reading PTB-XL 500 Hz", n, "of", len(fns), flush=True)
    np.save(f, a)
    return a


def layout_masks(device):
    m = torch.zeros(12, T, dtype=torch.bool, device=device)
    for k, L in enumerate(D.LEADS):
        a, b = D.LAYOUT[L]
        m[k, int(a * FS):int(b * FS)] = True
    return m


# ------------------------------------------------------------------------------------------------ digitiser emulation (fixed, not fitted to our pages)
def _smooth(x, sigma_samples):
    """Gaussian smoothing with one sigma for the whole batch element group x (b, 12, T)."""
    if sigma_samples < 0.2:
        return x
    r = int(np.ceil(3 * sigma_samples))
    k = torch.exp(-0.5 * (torch.arange(-r, r + 1, device=x.device).float() / sigma_samples) ** 2)
    k = (k / k.sum()).view(1, 1, -1)
    b, c, t = x.shape
    return nn.functional.conv1d(nn.functional.pad(x.reshape(b * c, 1, t), (r, r), mode="replicate"), k).reshape(b, c, t)


def emulate(x, gen=None):
    """x (B, 12, T) mV at 250 Hz -> emulated digitiser output: 5 ms time grid with random phase, smoothing sigma U(0, 8) ms, one-pixel amplitude steps, gain, noise, baseline wander."""
    B = x.shape[0]
    dev = x.device
    # time grid (200 Hz, random phase): piecewise-constant in time, linear interpolation between the 250 Hz samples
    ph = torch.rand(B, 1, device=dev, generator=gen)
    t = torch.arange(T, device=dev).float().unsqueeze(0) * 0.004
    tq = (torch.floor(t / 0.005 + ph) - ph) * 0.005 + 0.0025
    pos = (tq / 0.004).clamp(0, T - 1.001)
    i0 = pos.floor().long()
    fr = (pos - i0.float()).unsqueeze(1)
    g0 = torch.gather(x, 2, i0.unsqueeze(1).expand(-1, 12, -1))
    g1 = torch.gather(x, 2, (i0 + 1).unsqueeze(1).expand(-1, 12, -1))
    x = g0 * (1 - fr) + g1 * fr
    # smoothing: four sigma groups
    sig = torch.rand(B, device=dev, generator=gen) * 8.0 / 4.0          # sigma in samples (0 to 8 ms)
    out = torch.empty_like(x)
    edges = torch.tensor([0.0, 0.5, 1.0, 1.5, 2.01], device=dev)
    for a, b in zip(edges[:-1], edges[1:]):
        m = (sig >= a) & (sig < b)
        if m.any():
            out[m] = _smooth(x[m], float((a + b) / 2))
    x = out
    x = x * (0.9 + 0.2 * torch.rand(B, 1, 1, device=dev, generator=gen))
    x = x + 0.01 * torch.randn(x.shape, device=dev, generator=gen)
    x = torch.round(x / 0.0128) * 0.0128
    tt = torch.arange(T, device=dev).float() / FS
    f = 0.1 + 0.4 * torch.rand(B, 1, 1, device=dev, generator=gen)
    p = 6.2832 * torch.rand(B, 1, 1, device=dev, generator=gen)
    return x + 0.1 * torch.rand(B, 1, 1, device=dev, generator=gen) * torch.sin(6.2832 * f * tt + p)


def make_input(raw, mask, emulate_digitiser=False, gen=None):
    """raw (B, 12, T) mV -> (B, 24, T): optional digitiser emulation, page-layout cut, mean removal, mask channels."""
    x = emulate(raw, gen) if emulate_digitiser else raw
    m = mask.unsqueeze(0).expand(x.shape[0], -1, -1)
    x = x * m
    mean = x.sum(-1, keepdim=True) / m.sum(-1, keepdim=True).clamp(min=1)
    return torch.cat([(x - mean) * m, m.float()], dim=1)


def digitised_to_input250(leads):
    """leads: dict lead -> (10000,) microvolts at 1 kHz with NaN -> (24, 2500) float32 (block mean of 4, NaN-aware)."""
    import warnings
    x = np.full((12, T), np.nan, np.float32)
    for k, L in enumerate(D.LEADS):
        if L in leads and leads[L] is not None:
            a = np.asarray(leads[L], float)[:10000] / 1000.0
            if len(a) < 10000:
                a = np.concatenate([a, np.full(10000 - len(a), np.nan)])
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                x[k] = np.nanmean(a.reshape(T, 4), axis=1)
    mask = np.isfinite(x)
    return D.finalize(x, mask)


# ------------------------------------------------------------------------------------------------ model
class IntervalNet(nn.Module):
    def __init__(self, n_in=24, n_out=2, chans=(32, 64, 128, 128, 256, 256)):
        super().__init__()
        layers, c0 = [nn.BatchNorm1d(n_in)], n_in
        for c in chans:
            layers += [nn.Conv1d(c0, c, 7, stride=2, padding=3, bias=False), nn.BatchNorm1d(c), nn.ReLU(inplace=True)]
            c0 = c
        self.body = nn.Sequential(*layers)
        self.head = nn.Linear(2 * c0, n_out)

    def forward(self, x):
        h = self.body(x)
        return self.head(torch.cat([h.mean(-1), h.amax(-1)], dim=1))
