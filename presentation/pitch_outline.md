# Pitch outline

Suggested 2–3 minute format, based on the supplied guide. Team names and actual Challenge 2 rules/deadline still need confirmation. This is a prepared outline, not a final slide deck.

1. **Buyer problem:** A University of Houston graduate wants to compare a historical home's asking price with a model estimate and understand its ZIP market trend.
2. **Data:** Original 25,948-record 2024 publisher snapshot; 8,376 cleaned city-scope residential records; 98 ZIP ZHVI histories through September 2026. Explain the two units and why city labels matter.
3. **Method:** Historical feature cutoff, grouped CV, held-out evaluation, actual SHAP and chronological forecast origins. No Zestimate predictor and no claim that asking price equals appraised value.
4. **Evidence:** Selected Random Forest test MAE $102,585, median absolute error $37,536, R² 0.839. Five regression families × two feature sets; five pseudo-label classifiers; five forecast methods. The naive forecast wins earlier selection origins; do not conceal it.
5. **Demo:** Map → historical property → estimate/category/SHAP → ZIP forecast and uncertainty → grounded factual question.
6. **Limits and impact:** Demonstrated integration and explainability, not measured buyer savings. Historical records, revised ZHVI, empirical intervals and one deterministic assistant. No verified mispricing or guaranteed future prices. End with the actual public URL only after it is deployed and checked.
