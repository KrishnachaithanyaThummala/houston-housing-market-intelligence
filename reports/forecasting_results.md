# ZIP-level ZHVI forecasts

Methods actually executed: Naive, Damped trend, ARIMA, Prophet, XGBoost lags. Failed ZIP/method/origin runs: 0. Forecasts exist for 98 ZIPs.

Origins: [{'cutoff': '2022-09-30', 'phase': 'selection'}, {'cutoff': '2023-09-30', 'phase': 'selection'}, {'cutoff': '2024-09-30', 'phase': 'calibration'}, {'cutoff': '2025-09-30', 'phase': 'test'}]. Every origin uses only earlier observations. Initial gaps are trimmed; internal gaps restart contiguous training history. Minimum history is 60 months. Selection uses mean absolute error at months 6 and 12 across ZIPs and two earlier origins. One separate origin calibrates relative-error bands; the last origin is held out for evaluation. Comparisons use common cases, not favorable subsets. Hyperparameters are modest and fixed, not exhaustively tuned. Seasonality is disabled in Prophet for this seasonally adjusted series; ARIMA uses (1,1,0) with drift; lag XGBoost recursively predicts log returns.

Selected method: **Naive**. Its flat forecast is a measured baseline result. Some alternatives do better in the final held-out period; that does not justify changing selection using the test outcome.

| phase       | method       |   horizon |       mae |   smape |      bias |   n |      rmse |   naive_mae |   mae_skill_vs_naive |
|:------------|:-------------|----------:|----------:|--------:|----------:|----:|----------:|------------:|---------------------:|
| calibration | ARIMA        |         6 |  3110.819 |   1.019 |  1767.080 |  98 |  4000.040 |    4648.346 |                0.331 |
| calibration | ARIMA        |        12 | 11757.670 |   3.980 | 10881.365 |  98 | 13902.674 |   12166.112 |                0.034 |
| calibration | Damped trend |         6 |  3437.750 |   1.195 |  -201.009 |  98 |  4645.117 |    4648.346 |                0.260 |
| calibration | Damped trend |        12 |  8305.921 |   2.367 |  4874.365 |  98 | 12256.191 |   12166.112 |                0.317 |
| calibration | Naive        |         6 |  4648.346 |   1.411 |   939.916 |  98 |  8687.941 |    4648.346 |                0.000 |
| calibration | Naive        |        12 | 12166.112 |   4.282 |  7083.562 |  98 | 17645.362 |   12166.112 |                0.000 |
| calibration | Prophet      |         6 | 21201.310 |   7.436 | 15289.444 |  98 | 25482.670 |    4648.346 |               -3.561 |
| calibration | Prophet      |        12 | 35249.735 |  12.693 | 29365.353 |  98 | 39043.530 |   12166.112 |               -1.897 |
| calibration | XGBoost lags |         6 |  3908.558 |   1.370 |  2311.465 |  98 |  4851.501 |    4648.346 |                0.159 |
| calibration | XGBoost lags |        12 | 12322.003 |   4.168 | 10667.135 |  98 | 15276.169 |   12166.112 |               -0.013 |
| selection   | ARIMA        |         6 |  5459.704 |   1.890 |  3324.468 | 196 |  7745.163 |    4211.128 |               -0.296 |
| selection   | ARIMA        |        12 |  9290.293 |   3.032 |  4285.531 | 196 | 12700.638 |    5963.377 |               -0.558 |
| selection   | Damped trend |         6 |  6016.314 |   1.971 |  1906.211 | 196 |  9580.653 |    4211.128 |               -0.429 |
| selection   | Damped trend |        12 | 11164.118 |   3.233 |  -178.843 | 196 | 19782.734 |    5963.377 |               -0.872 |
| selection   | Naive        |         6 |  4211.128 |   1.333 |   315.374 | 196 |  6066.697 |    4211.128 |                0.000 |
| selection   | Naive        |        12 |  5963.377 |   1.554 | -3239.795 | 196 | 11448.512 |    5963.377 |                0.000 |
| selection   | Prophet      |         6 | 12588.747 |   4.170 | -6421.771 | 196 | 18158.922 |    4211.128 |               -1.989 |
| selection   | Prophet      |        12 | 15200.293 |   4.945 | -2426.515 | 196 | 21365.659 |    5963.377 |               -1.549 |
| selection   | XGBoost lags |         6 |  5370.358 |   1.928 |  3795.621 | 196 |  6998.969 |    4211.128 |               -0.275 |
| selection   | XGBoost lags |        12 |  8765.377 |   3.007 |  4295.009 | 196 | 11377.681 |    5963.377 |               -0.470 |
| test        | ARIMA        |         6 |  3460.024 |   1.069 | -1525.113 |  98 |  6084.193 |    4631.725 |                0.253 |
| test        | ARIMA        |        12 |  6531.249 |   2.118 |  1691.468 |  98 | 10377.941 |    8782.033 |                0.256 |
| test        | Damped trend |         6 |  5119.737 |   1.790 | -3742.319 |  98 |  7235.021 |    4631.725 |               -0.105 |
| test        | Damped trend |        12 |  8261.160 |   3.140 | -5093.770 |  98 | 11502.979 |    8782.033 |                0.059 |
| test        | Naive        |         6 |  4631.725 |   1.214 |  -794.657 |  98 | 10391.679 |    4631.725 |                0.000 |
| test        | Naive        |        12 |  8782.033 |   2.440 |   616.710 |  98 | 19525.219 |    8782.033 |                0.000 |
| test        | Prophet      |         6 | 32990.773 |  11.904 | 27533.026 |  98 | 37650.785 |    4631.725 |               -6.123 |
| test        | Prophet      |        12 | 43335.360 |  15.342 | 36172.773 |  98 | 48632.154 |    8782.033 |               -3.935 |
| test        | XGBoost lags |         6 |  3425.071 |   1.086 | -1074.857 |  98 |  5499.519 |    4631.725 |                0.261 |
| test        | XGBoost lags |        12 |  7250.643 |   2.382 |   804.299 |  98 | 10147.040 |    8782.033 |                0.174 |

Intervals: Pooled ZIP relative absolute errors, 90th percentile, separate calibration origin; not guaranteed coverage. Coverage: 6 months 92.86%; 12 months 97.96%. Target is 90%; spatial dependence among ZIPs and time-varying errors limit calibration. These are empirical forecast bands, not invented confidence bounds. Full monthly backtests are stored separately from endpoint summaries.

Future observations run October 2026–September 2027. Forecasts describe ZIP-level modeled home values, not future sale prices of individual houses. All historical evaluations use the supplied revised ZHVI vintage and cannot verify real-time historical performance.
