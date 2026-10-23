# Judge questions and evidence-based answers

1. **Why this problem?** It connects a buyer's property-level question with broader ZIP trends; user studies or measured savings have not been performed.
2. **Why these datasets?** Listings provide historical property attributes and asking prices; ZHVI adds monthly market context. They measure different things.
3. **Why Houston?** It is the requested study area and provides locally relevant examples for UH buyers. We do not claim universal transferability.
4. **Why city and ZIP filtering?** It prevents broader-metro or out-of-state records entering the requested scope. Houstonia exists only in Missouri in this file and is excluded.
5. **How are the datasets integrated?** Normalize five-digit ZIPs and validate many-to-one joins. All 8,376 cleaned rows remain; 36 unmatched rows are excluded from the common A/B modeling cohort.
6. **How is leakage prevented?** Predictor allowlist excludes Zestimate, rent estimates, assessment, price-derived and time/status fields. Historical April 2024 features precede the June snapshot. Grouped partitions and fold-local preprocessing reduce overlap. Revised-vintage leakage cannot be ruled out and is disclosed.
7. **Why five models?** The brief asks for comparisons; we use modest fixed configurations and grouped CV, without claiming that more complexity guarantees improvement.
8. **How is the winner selected?** Training grouped CV dollar MAE. The selected model is kept even when another model has lower final test MAE.
9. **Listing price versus market value?** The target is an asking price. We cannot validate an appraisal or true fair market value from these labels.
10. **What is the pricing category?** A configurable gap relative to an out-of-sample estimate, ±10% by default. It is a model screen, not a verified bargain label.
11. **How reliable are forecasts?** Five methods are evaluated on four chronological origins, with separate selection, calibration and final test. Errors and empirical interval coverage are shown by horizon.
12. **Why ZIP rather than home forecasts?** The available monthly target is ZIP ZHVI; we have no verified repeated home-price time series.
13. **Why ZHVI?** It offers a consistent modeled local history. It is not observed sales, and the supplied vintage revises history.
14. **What about both sources being Zillow-derived?** They are not independent evidence. Shared modeling/source biases remain a limitation.
15. **How is the assistant validated?** Sixty fixed fact/refusal checks across six held-out properties passed. Only deterministic Q&A was evaluated; four LLM variants remain untested.
16. **How is this different from real estate websites?** It is a reproducible historical research workflow with visible evaluation, provenance and uncertainty. We make no unique-market or superior-commercial-product claim.
17. **What makes it AI-powered?** Trained supervised regressors/classifiers and forecast models power the analytics; the assistant fallback itself is deterministic.
18. **What is the measurable impact?** Measured prediction errors, forecast backtests and factual checks. We have not measured purchase outcomes, savings or adoption.
19. **How is uncertainty handled?** Independent validation/calibration errors create empirical bands, with observed test coverage and limitations. No guaranteed coverage or invented bounds.
20. **Can judges use it?** The local app runs and the deployment package is prepared. Public access must be verified after hosting sign-in; no unverified public URL is claimed.
21. **What would more time improve?** Historical vintages, true transaction outcomes, more spatial/time tests, live-data permissions, grounded LLM evaluation and user testing.
22. **What was built during the event?** Source and model artifacts are available, but event dates and participation conditions are unspecified. The team must identify which work falls within the official event window rather than claim it all occurred there.
