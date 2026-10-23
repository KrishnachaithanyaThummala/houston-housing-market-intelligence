# Dataset audit

Listings: Natasha Lekh / datadetective08, [Houston housing market 2024](https://www.kaggle.com/datasets/datadetective08/houston-housing-market-2024), version 1, CC BY-NC-SA 4.0. Downloaded only the light JSON. Exact raw count: 25,948. No repeated property IDs. Publisher identifies June 5, 2024 as the snapshot; this is not each property's listing start date.

Texas and requested city-label scope: 10,483 records. Single-family, condo and townhouse subset: 8,428. Invalid price/ZIP/living-area rows removed: 50. Two additional residential prices below $20,000 were excluded as ambiguous sale-price entries; they are not asserted to be rentals. Clean residential records: 8,376.

Year built is absent from the light file; no property-age feature was invented. Lot values are converted from acres to square feet only when source units are known. Missing lot area: 1,156; missing bedrooms: 1. Missing predictors are imputed inside model folds. Tax assessments, Zestimates, rent estimates, prices and price changes are excluded from predictor construction. Full flattened schema and exclusion list: artifacts/evaluation/listings_audit.json.

ZHVI: 26,265 national rows; 321 months (2000-01-31–2026-09-30). Selected Texas city labels yield 98 unique ZIPs (Houston 97, South Houston 1). Houstonia exists only in Missouri in the supplied file and is excluded. Initial missing monthly observations: 129; none are silently filled. Every selected ZIP has the last month. City labels are not city boundaries or the full metro.

The source filename describes mid-tier smoothed seasonally adjusted SFR/condo values. [Zillow Research](https://www.zillow.com/research/data/) describes ZHVI as a modeled typical-home-value index. The source download date is unknown; inspection occurred October 23, 2026. Exact hashes and metadata are stored in artifacts/evaluation.
