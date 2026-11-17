# Section AA second attempt: fine-tuning on digitised development data (cross-validation, development only)

Items 658 ({'page': 400, 'real photo': 140, 'sim photo': 118}) from 450 recordings; 5-fold CV grouped by recording; chosen epochs 26. These are DEVELOPMENT numbers, not tests.

| Items | Parameter | Typical error (ms) | Bias (ms) | Slope on 12SL |
|---|---|---|---|---|
| all (658) | QRS | 4.8 | -0.6 | 0.84 |
| all (658) | QT | 7.7 | +0.6 | 0.80 |
| all (658) | QTc direct | 9.3 | -1.7 | 0.64 |
| page (400) | QRS | 5.0 | -1.9 | 0.88 |
| page (400) | QT | 7.2 | -1.1 | 0.88 |
| page (400) | QTc direct | 8.9 | -1.8 | 0.77 |
| real photo (140) | QRS | 3.8 | +0.1 | 0.76 |
| real photo (140) | QT | 9.0 | +0.4 | 0.60 |
| real photo (140) | QTc direct | 9.9 | -1.3 | 0.43 |
| sim photo (118) | QRS | 5.6 | +2.8 | 0.90 |
| sim photo (118) | QT | 7.8 | +6.4 | 0.83 |
| sim photo (118) | QTc direct | 9.7 | -1.9 | 0.73 |
