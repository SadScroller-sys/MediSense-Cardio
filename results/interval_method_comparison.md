# Interval measurement methods vs 12SL (original PTB-XL signal, 500 Hz, 50 recordings)

rho = Spearman correlation with 12SL global value; MAD = median absolute difference; bias = mean difference (method minus 12SL).
For reference, 12SL vs Glasgow agree with rho 0.91 to 0.93 and MAD 4 to 6.5 ms (results/reference_vs_ptbxl_plus.md).

## pr
```
method aggregation  n   rho  MAD_ms  bias_ms
   dwt      leadII 46  0.35    56.3    -58.5
   dwt    median12 46  0.29    68.3    -65.5
   cwt      global 46  0.19   389.4   -402.8
   cwt      leadII 42 -0.06   744.7   -719.9
   cwt    median12 45 -0.06   612.4   -645.2
   dwt      global 46 -0.18    62.7    -59.1
```

## qrs
```
method aggregation  n   rho  MAD_ms  bias_ms
   cwt      global 50  0.12    42.5     40.0
   dwt    median12 50  0.11    83.2     78.4
   dwt      leadII 50  0.06    84.1     93.5
   dwt      global 50 -0.04   202.5    214.9
   cwt      leadII 31 -0.09    43.0     39.6
   cwt    median12 50 -0.14    26.2     10.5
```

## qt
```
method aggregation  n  rho  MAD_ms  bias_ms
   cwt    median12 49 0.66    28.9     34.8
   dwt      global 50 0.64   151.6    147.7
   cwt      leadII 45 0.56    34.6     55.9
   dwt      leadII 50 0.47    35.9     13.9
   cwt      global 50 0.44   202.5    224.1
   dwt    median12 50 0.38    32.9      9.1
```

## qtc_bazett
```
method aggregation  n  rho  MAD_ms  bias_ms
   cwt    median12 49 0.60    37.6     40.3
   cwt      leadII 45 0.54    39.9     65.1
   dwt      global 50 0.44   171.2    164.2
   dwt      leadII 50 0.28    46.1     14.7
   cwt      global 50 0.15   240.1    248.2
   dwt    median12 50 0.11    39.3      9.2
```

## qtc_fridericia
```
method aggregation  n  rho  MAD_ms  bias_ms
   cwt    median12 49 0.54    34.2     38.2
   cwt      leadII 45 0.48    35.8     61.6
   dwt      global 50 0.31   165.1    158.1
   dwt      leadII 50 0.26    44.0     14.2
   cwt      global 50 0.17   228.7    239.4
   dwt    median12 50 0.13    36.4      9.0
```
