# Final model comparison and current status

- Regression: five model families × two feature sets evaluated; selected Random Forest, held-out MAE \$102,585.38. Selection uses training CV, not the test leaderboard.
- Classification: five models evaluated for pseudo-label reproduction; selected Random Forest. Production remains the deterministic gap rule.
- Forecasting: five methods evaluated at four origins for 98 ZIPs; selected Naive using earlier origins. All 12 future months exported.
- Assistant: one deterministic grounded configuration, 60/60 narrow fixed checks. Four LLM configurations remain unevaluated.
- SHAP: actual selected-model TreeExplainer with additivity check; log-target contributions.
- Map: 98 Census ZCTA boundaries and filtered historical property markers. Generalized polygons are repaired; outside-region points are hidden.
- App: seven functional sections, saved artifacts, no training at startup. Local tests and browser verification are documented separately.
- Still pending: public deployment and verified public URL, actual deadline/Challenge 2 rubric, final team names, generative-LLM comparison and a final presentation deck. Pitch outline, demo script and judge Q&A accompany the project.
