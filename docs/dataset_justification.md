# Dataset justification

The Houston listings dataset supplies property-level asking prices, structural attributes and coordinates for a buyer-oriented historical demonstration. The original publisher and version are preserved instead of silently substituting an unrelated cleaned dataset. The light file reduces download/processing overhead but omits year built and other detailed attributes; absent predictors are not invented.

Zillow's ZIP-level ZHVI supplies a regional monthly history that property snapshots lack. Historical lag features can be evaluated for incremental prediction value, and the time series supports explicit 6/12-month forecasting experiments. A modeled index complements a historical asking-price snapshot but cannot convert it into verified current inventory or independent transaction evidence. Shared Zillow origin, revisions and geographic mismatch are explicit limitations.

The requested Texas city-label scope yields 98 market series. Strict filtering excludes Houstonia, Missouri and does not silently expand to Katy, Cypress or other metro cities present in the listing data. Census 2020 ZCTAs support approximate ZIP choropleths with source and approximation disclosed.
