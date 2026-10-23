# Historical asking-price prediction

Selected using grouped training-only CV MAE: **Random Forest**, **B: property + historical ZHVI**. Fixed modest configurations and 3 folds; no exhaustive hyperparameter search. Both experiments share the same eligible records and persisted splits. All preprocessing is fit within folds. Log1p targets are inverse-transformed before dollar evaluation.

Partitions: {'train': 4974, 'validation': 1717, 'test': 1649}. Address/rounded coordinate connected groups prevent direct duplicate/near-coordinate overlap. This cannot eliminate all spatial dependence. Training-only ZIP holdout stress-test MAE: \$92,746.42 on 850 cases; its distribution differs from the final test.

| experiment                    | model             |     cv_mae |   cv_mae_std |   validation_mae |   test_mae |    test_rmse |   test_r2 |   test_median_absolute_error |   test_median_absolute_percentage_error |   test_n |   milliseconds_per_prediction |
|:------------------------------|:------------------|-----------:|-------------:|-----------------:|-----------:|-------------:|----------:|-----------------------------:|----------------------------------------:|---------:|------------------------------:|
| A: property only              | Ridge             | 266603.136 |    17795.988 |       977670.403 | 443364.336 | 12649318.561 |  -305.150 |                    49805.999 |                                  15.215 |     1649 |                         0.002 |
| A: property only              | Random Forest     | 127573.992 |     5520.229 |       121544.757 | 107295.861 |   276243.210 |     0.854 |                    37649.798 |                                  11.464 |     1649 |                         0.017 |
| A: property only              | Gradient Boosting | 131804.197 |     8323.752 |       128067.591 | 113964.649 |   285950.256 |     0.844 |                    44849.396 |                                  12.898 |     1649 |                         0.003 |
| A: property only              | XGBoost           | 130226.182 |     8502.415 |       120632.281 | 107875.922 |   264622.440 |     0.866 |                    42957.672 |                                  12.835 |     1649 |                         0.003 |
| A: property only              | LightGBM          | 128841.136 |     7347.765 |       117691.490 | 101538.856 |   246344.069 |     0.884 |                    38843.851 |                                  11.641 |     1649 |                         0.009 |
| B: property + historical ZHVI | Ridge             | 229418.404 |    14523.324 |       728937.132 | 297951.782 |  6976620.856 |   -92.130 |                    49957.752 |                                  14.713 |     1649 |                         0.004 |
| B: property + historical ZHVI | Random Forest     | 124285.160 |     3665.949 |       118015.880 | 102585.379 |   290107.227 |     0.839 |                    37535.614 |                                  11.332 |     1649 |                         0.018 |
| B: property + historical ZHVI | Gradient Boosting | 128307.637 |     4626.459 |       121888.063 | 106761.487 |   293170.085 |     0.836 |                    42161.697 |                                  12.480 |     1649 |                         0.004 |
| B: property + historical ZHVI | XGBoost           | 126501.885 |     5848.063 |       118929.945 | 104344.367 |   282110.838 |     0.848 |                    42592.141 |                                  12.396 |     1649 |                         0.003 |
| B: property + historical ZHVI | LightGBM          | 124920.328 |     5747.825 |       117505.490 |  99280.648 |   249158.292 |     0.881 |                    39257.344 |                                  11.732 |     1649 |                         0.005 |

Selected model test MAE: **\$102,585.38**, RMSE **\$290,107.23**, R² **0.8390**, median absolute error **\$37,535.61**. Median absolute percentage error: **11.33%**. Median-price baseline MAE: **\$295,951.42**. R² is not accuracy.

Some alternatives have lower final test MAE. We keep the earlier CV selection rather than reselecting on test results. Ridge's large test errors show instability after inverse-transforming extrapolated log predictions; all measured results remain visible.

Validation residual 90th-percentile radius: \$192,005.26. Held-out empirical coverage: 88.78%, below the 90% target. This broad global band is not a formal appraisal interval. Training examples use nested cross-fitting and may use a different fold-selected model; the app shows held-out records so its SHAP explanation matches the displayed estimate.

Model predicts historical asking prices, not independently measured fair market value. Dataset vintage, listing-price target, outliers and shared Zillow provenance limit interpretation.
