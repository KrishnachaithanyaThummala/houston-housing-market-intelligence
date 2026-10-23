# Buyer-focused demo script (2–3 minutes)

**0:00–0:25 — Problem.** “Imagine a University of Houston graduate exploring a first home. Asking prices, property characteristics and neighborhood market trends are difficult to compare in one place. Our application brings those views together while making the data dates and uncertainty visible.”

**0:25–0:45 — Evidence.** “We started with 25,948 publisher records from June 2024. After geographic and residential filtering, we retained 8,376 clean examples and matched 8,340 to market features. We separately prepared 98 Texas ZIP-level home-value series through September 2026.”

**0:45–1:20 — Property.** Open Housing map, narrow ZIP if helpful, select a marker and open its details. “This is a historical asking price, not a live listing. The estimate comes from a model that did not train on this example. The pricing gap is a screening indicator, not proof of a bargain. These SHAP contributions show how the trained model arrived at the estimate; they are not causal effects.”

**1:20–1:50 — Market.** Open Market forecasting for the ZIP. “The solid line is historical ZHVI; the dashed line is our selected forecast. We compared five approaches using earlier origins, and the last-observation baseline won selection. We show it honestly, including its flat path and empirical uncertainty band. This is a ZIP index, not an individual home's sale-price forecast.”

**1:50–2:15 — Assistant.** Open Housing assistant. Ask “What is the historical listing price?” then “What is its flood risk?” “The fallback answers using the actual selected record and states when a field is unavailable. We tested 60 fixed factual cases; this is not a claim of general conversational accuracy or five evaluated LLMs.”

**2:15–2:45 — Results and limits.** Open Model evaluation. “Training CV selected Random Forest with historical market features. Its test MAE was about \$102,585, median absolute error \$37,536 and R² 0.839. The data contains asking prices rather than appraisals, and historical ZHVI has been revised. The demonstrated benefit is an integrated, explainable workflow; we have not measured buyer savings.”

Before presenting: confirm team names and official time limit; test the fresh public URL; choose a known held-out example; keep reports and local app available as a fallback. Never announce a deployment URL that has not been verified.
