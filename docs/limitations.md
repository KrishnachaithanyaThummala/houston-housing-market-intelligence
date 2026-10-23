# Limitations and remaining work

- Asking-price targets cannot validate true fair market value or independently establish underpricing. Categories are model-based screening indicators only.
- Historical June 2024 records do not prove current availability. The ZHVI-ratio adjustment is an approximate ZIP-level market adjustment, not an appraisal or current listing price.
- Source series is revised, later-vintage history. Historical observation-date alignment and conservative lag cannot establish values released at the original time.
- Both property and index sources are Zillow-derived and are not independent market observations.
- City-label ZIP scope is neither Houston municipal limits nor the entire metro. Houstonia, Missouri is excluded. Postal ZIPs and Census ZCTAs differ.
- Light JSON has no year-built field. Missing lots/bedrooms require fold-local imputation. Extreme properties and ambiguous records create uncertainty.
- Duplicate/coordinate grouping reduces overlap but cannot eliminate spatial dependence. Tests reflect this particular dataset and partitions.
- Global price bands and pooled forecast intervals have measured historical coverage only. Nominal 90% coverage is not guaranteed.
- The selected naive forecast is flat; it may lose to other methods on the held-out period. Selection is frozen rather than optimized using test data.
- Map serves up to 1,000 filtered held-out markers at a time. Outside-region points are hidden; all analytic rows remain saved. Seven generalized boundary polygons required validity repair.
- Only one deterministic assistant configuration has been tested. Four generative configurations are unavailable/unevaluated; no five-chatbot claim is made.
- Public hosting, a verified public URL, official Challenge 2 rubric/deadline, team names and a final slide deck remain pending.
