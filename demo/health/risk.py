"""Risk pilot 2 network (rules: docs/plan/analysis_plan_changes.md, 2026-11-16 'RISK PILOT 2'): the QRS/QT network body on the 24-channel page-layout input, plus the person's age as one extra number before the final layer.
Research prototype. Not a medical device."""
import torch
import torch.nn as nn

from . import intervals_ml as I

AGE_MEAN, AGE_SCALE = 60.0, 15.0


def age_in(age_years):
    """Age in years (clipped to 16..90) -> the network's age number."""
    import numpy as np
    return (np.clip(np.asarray(age_years, np.float32), 16, 90) - AGE_MEAN) / AGE_SCALE


class RiskNet(nn.Module):
    def __init__(self, n_in=24, chans=(32, 64, 128, 128, 256, 256)):
        super().__init__()
        self.body = I.IntervalNet(n_in=n_in, n_out=1, chans=chans).body
        self.head = nn.Linear(2 * chans[-1] + 1, 1)

    def forward(self, x, age):
        h = self.body(x)
        return self.head(torch.cat([h.mean(-1), h.amax(-1), age.reshape(-1, 1)], dim=1))


# ------------------------------------------------------------------ pilot 3 (18 Nov 2026): exploratory 5-year death estimate, ensemble of the five fold models (results/risk_pilot3/)
# It did NOT meet the calibration rule (slope 0.76 against 0.8), and stage 2 (transfer to pages and photos) was not run. It is shown only as an EXPLORATORY range in a separate research panel.
_RISK3 = {}
RANGE_HALF_WIDTH = 0.10      # typed or dataset age; 0.12 when the age is estimated from the ECG (rule written 2026-11-18 evening, before the run)
RANGE_HALF_WIDTH_EST = 0.12
AGE_ERROR_YEARS = 9    # mean absolute error of the ECG-estimated age (results/risk_pilot3/SECTION_RISK3B.md: 9.27 years)
# pilot-2 single model: moved by about 5 to 13 points between a clean ECG and a photo of it; pilot-3 stage 2 (results/risk_pilot3/SECTION_RISK3_STAGE2.md): the range covers the clean value for 88 to 97% of drawn pages but only 61 to 73% of photos


def estimate_age(leads):
    """Age in years estimated from the ECG (average of the five fold age networks, results/risk_pilot3/agenet_fold*.pt); None if it cannot be computed."""
    import os

    import numpy as np
    from . import data as D
    try:
        if "agenets" not in _RISK3:
            d = os.path.join(D.ROOT, "results", "risk_pilot3")
            dev = "cuda" if torch.cuda.is_available() else "cpu"
            nets = []
            for k in range(5):
                net = I.IntervalNet(n_in=24, n_out=1).to(dev)
                net.load_state_dict(torch.load(os.path.join(d, f"agenet_fold{k}.pt"), map_location=dev))
                net.eval()
                nets.append(net)
            _RISK3["agenets"], _RISK3["adev"] = nets, dev
        x = I.digitised_to_input250(leads)[None]
        if not np.isfinite(x).all():
            return None
        xt = torch.from_numpy(np.ascontiguousarray(x)).to(_RISK3["adev"])
        with torch.no_grad():
            a = float(np.mean([float(n(xt).squeeze().cpu()) for n in _RISK3["agenets"]])) * AGE_SCALE + AGE_MEAN
        return float(min(max(a, 16.0), 90.0))
    except Exception:
        return None


def risk3_estimate(leads, age_years):
    """Returns dict(p, low, high, group, n_models, age, estimated_age) or None (no models or no usable signal). age_years None: the age is estimated from the ECG. Fractions 0 to 1."""
    import json
    import os

    import numpy as np
    from . import data as D
    if leads is None:
        return None
    est_age = age_years is None
    if est_age:
        age_years = estimate_age(leads)
        if age_years is None:
            return None
    try:
        age_years = float(age_years)
    except (TypeError, ValueError):
        return None
    if not (16 <= age_years <= 90):
        return None
    try:
        if "nets" not in _RISK3:
            d = os.path.join(D.ROOT, "results", "risk_pilot3")
            info = json.load(open(os.path.join(d, "fold_info.json")))
            dev = "cuda" if torch.cuda.is_available() else "cpu"
            nets = []
            for k, f in enumerate(info):
                net = RiskNet().to(dev)
                net.load_state_dict(torch.load(os.path.join(d, f"model_fold{k}.pt"), map_location=dev))
                net.eval()
                nets.append((net, f["platt_a"], f["platt_b"]))
            _RISK3["nets"], _RISK3["dev"] = nets, dev
        dev = _RISK3["dev"]
        x = I.digitised_to_input250(leads)[None]
        if not np.isfinite(x).all():
            return None
        xt = torch.from_numpy(np.ascontiguousarray(x)).to(dev)
        at = torch.from_numpy(age_in(np.array([age_years], np.float32))).to(dev)
        ps = []
        with torch.no_grad():
            for net, a, b in _RISK3["nets"]:
                lg = float(net(xt, at).squeeze().cpu())
                ps.append(1.0 / (1.0 + np.exp(-(a * lg + b))))
        p = float(np.mean(ps))
        hw = RANGE_HALF_WIDTH_EST if est_age else RANGE_HALF_WIDTH
        return dict(p=p, low=max(0.0, p - hw), high=min(1.0, p + hw), age=age_years, estimated_age=est_age, group=("lower" if p < 0.05 else ("middle" if p < 0.15 else "higher")), n_models=len(ps))
    except Exception:
        return None


def risk3_curve(leads, ages):
    """The 5-year estimate (fraction) of the SAME ECG at each age in `ages` (years, 16 to 90), average of the five fold models after Platt scaling. None if it cannot be computed."""
    import os

    import numpy as np
    if leads is None:
        return None
    try:
        if risk3_estimate(leads, 60.0) is None:                     # loads the models and checks that the signal is usable
            return None
        dev = _RISK3["dev"]
        x = I.digitised_to_input250(leads)[None]
        ages = np.clip(np.asarray(ages, np.float32), 16, 90)
        xt = torch.from_numpy(np.ascontiguousarray(np.repeat(x, len(ages), axis=0))).to(dev)
        at = torch.from_numpy(age_in(ages).astype(np.float32)).to(dev)
        ps = []
        with torch.no_grad():
            for net, a, b in _RISK3["nets"]:
                lg = net(xt, at).squeeze(1).cpu().numpy()
                ps.append(1.0 / (1.0 + np.exp(-(a * lg + b))))
        return np.mean(ps, axis=0)
    except Exception:
        return None
