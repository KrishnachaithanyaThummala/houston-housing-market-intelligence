# Dataset integration

- Listings before/after left join: 8,376 / 8,376.
- Unique listing ZIPs / ZHVI ZIPs: 98 / 98.
- Matched ZIP codes: 96.
- Matched listing rows: 8,340 (99.57%).
- Unmatched ZIPs: 77029, 77433; 36 rows.
- Duplicate ZHVI ZIP keys: zero. Merge explicitly validates many-to-one cardinality.

Integrated rows remain in data/processed/integrated.parquet. The common A/B modeling cohort excludes the 36 unmatched rows, producing 8,340 records. The app serves validation/test examples from that cohort, not unmatched or in-sample training estimates.

Historical feature date: April 30, 2024, before the June 5 snapshot, with 6/12-month changes. Latest September 2026 ZHVI is retained for display/adjustment only and is never a historical price predictor. The conservative lag does not establish 2024 release availability: this is a later revised vintage of ZHVI. Historical backtests are retrospective.
