# Pricing-gap pseudo-label evaluation

Production uses a configurable gap rule: (asking price − out-of-sample estimate) / estimate. Less than −10% is Potentially Underpriced, greater than +10% is Potentially Overpriced, and boundaries are included in Approximately Fairly Priced.

Training labels use 3 outer folds, with model family and feature set chosen on inner folds that omit each outer held-out record. Validation/test estimates come from the training-only selected regressor. These are pseudo-labels; none establish true bargains or market mispricing.

Classifier predictors exclude asking price, exact gap and regression estimate to avoid trivial formula reproduction. Selection uses validation macro F1, then frozen test evaluation. Selected reproduction model: Random Forest. Class counts: {'Approximately Fairly Priced': 3748, 'Potentially Underpriced': 2332, 'Potentially Overpriced': 2260}.

| model               |   validation_macro_f1 |   test_accuracy |   test_macro_f1 |
|:--------------------|----------------------:|----------------:|----------------:|
| Logistic Regression |                 0.411 |           0.445 |           0.429 |
| Random Forest       |                 0.448 |           0.485 |           0.467 |
| Gradient Boosting   |                 0.377 |           0.476 |           0.396 |
| XGBoost             |                 0.433 |           0.491 |           0.433 |
| LightGBM            |                 0.434 |           0.497 |           0.451 |

Full precision/recall/F1 and confusion matrices are saved in artifacts/evaluation/classification_report.json. The deterministic rule agrees with its own labels by definition; treating that agreement as independent 100% accuracy would be misleading. The auxiliary classifier is not used to override the production rule.
