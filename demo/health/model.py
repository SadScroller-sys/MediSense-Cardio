"""Heart health module, model (rules: docs/plan/analysis_plan_changes.md, 2026-11-15). Small 1-D CNN on the page-layout input (24 channels x 1000 samples).
Research prototype. Not a medical device."""
import json
import os

import numpy as np
import torch
import torch.nn as nn

from . import data as D

ROOT = D.ROOT
OUT = os.path.join(ROOT, "results", "health") + os.sep


class EcgNet(nn.Module):
    def __init__(self, n_in=24, n_out=6, chans=(32, 64, 128, 128, 256)):
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


def layout_masks(device):
    """(12, T) bool tensor: where each lead exists on the page."""
    m = torch.zeros(12, D.T, dtype=torch.bool, device=device)
    for k, L in enumerate(D.LEADS):
        a, b = D.LAYOUT[L]
        m[k, int(a * D.FS):int(b * D.FS)] = True
    return m


def strong_damage(x, gen=None):
    """STRONG photo-style damage for training networks A2/B2 (rules: docs/plan/analysis_plan_changes.md 2026-11-17 'SET Q'): gain per lead 0.7-1.3, noise 0.01-0.05 mV, baseline wander up to 0.3 mV,
    held pieces of 60-200 ms in some leads, time shift per lead up to 20 ms, one-pixel amplitude steps of 0.0128 mV. x (B, 12, T) mV at 100 Hz on the device."""
    B, C, T_ = x.shape
    dev_ = x.device
    sh = torch.randint(-2, 3, (B, C), device=dev_, generator=gen)           # +-20 ms at 100 Hz, per lead
    idx = (torch.arange(T_, device=dev_).view(1, 1, -1) - sh.unsqueeze(-1)).clamp(0, T_ - 1)
    x = torch.gather(x, 2, idx)
    x = x * (0.7 + 0.6 * torch.rand(B, C, 1, device=dev_, generator=gen))
    x = x + (0.01 + 0.04 * torch.rand(B, 1, 1, device=dev_, generator=gen)) * torch.randn(x.shape, device=dev_, generator=gen)
    t = torch.arange(T_, device=dev_).float() / D.FS
    f = 0.1 + 0.4 * torch.rand(B, 1, 1, device=dev_, generator=gen)
    ph = 6.2832 * torch.rand(B, 1, 1, device=dev_, generator=gen)
    x = x + 0.3 * torch.rand(B, 1, 1, device=dev_, generator=gen) * torch.sin(6.2832 * f * t + ph)
    for _ in range(2):                                                         # held pieces: 60-200 ms (6-20 samples at 100 Hz)
        st = torch.randint(0, T_ - 25, (B, 1, 1), device=dev_, generator=gen)
        ln = torch.randint(6, 21, (B, 1, 1), device=dev_, generator=gen)
        sel = torch.rand(B, C, 1, device=dev_, generator=gen) < 0.2
        pos = torch.arange(T_, device=dev_).view(1, 1, -1)
        inside = (pos >= st) & (pos < st + ln) & sel
        held = torch.gather(x, 2, st.expand(-1, C, 1))
        x = torch.where(inside, held.expand(-1, -1, T_), x)
    return torch.round(x / 0.0128) * 0.0128


def make_input(raw, mask, augment=False, gen=None):
    """raw (B, 12, T) mV on the device -> (B, 24, T): optional augmentation (gain, noise, baseline wander), page-layout cut, mean removal, mask channels."""
    x = raw.clone()
    if augment == "strong":
        x = strong_damage(x, gen)
    elif augment:
        B = x.shape[0]
        x = x * (0.8 + 0.4 * torch.rand(B, 1, 1, device=x.device, generator=gen))
        x = x + 0.01 * torch.randn(x.shape, device=x.device, generator=gen)
        t = torch.arange(D.T, device=x.device).float() / D.FS
        f = 0.1 + 0.4 * torch.rand(B, 1, 1, device=x.device, generator=gen)
        ph = 6.2832 * torch.rand(B, 1, 1, device=x.device, generator=gen)
        amp = 0.1 * torch.rand(B, 1, 1, device=x.device, generator=gen)
        x = x + amp * torch.sin(6.2832 * f * t + ph)
    m = mask.unsqueeze(0).expand(x.shape[0], -1, -1)
    x = x * m
    cnt = m.sum(-1, keepdim=True).clamp(min=1)
    mean = x.sum(-1, keepdim=True) / cnt
    x = (x - mean) * m
    return torch.cat([x, m.float()], dim=1)


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


def load_model(device="cpu"):
    net = EcgNet().to(device)
    net.load_state_dict(torch.load(OUT + "model.pt", map_location=device))
    net.eval()
    cal = json.load(open(OUT + "calibration.json"))
    return net, cal


@torch.no_grad()
def logits_from_inputs(net, X24, device="cpu", bs=256):
    """X24 (N, 24, T) float32 numpy -> (N, 6) logits."""
    out = []
    for i in range(0, len(X24), bs):
        out.append(net(torch.from_numpy(np.ascontiguousarray(X24[i:i + bs])).to(device)).cpu().numpy())
    return np.concatenate(out)


def calibrated(cal, logits):
    """Platt scaling per class: p = sigmoid(a * logit + b), a and b fitted on fold 9 only."""
    a = np.array([cal["platt"][c]["a"] for c in D.CLASSES])
    b = np.array([cal["platt"][c]["b"] for c in D.CLASSES])
    return sigmoid(logits * a + b)
