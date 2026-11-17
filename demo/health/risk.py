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
