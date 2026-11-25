# Decisions

One line per methodological decision: what you chose, why, and what it changed.
Agents append here via the `/new-feature` skill; you append here by hand.

- Exclude `casual`, `registered`: they sum to `cnt` exactly. Leaky model R^2 1.000 -> honest ridge 0.583.
- Exclude `cnt_2d_bfr`: a shipped 2-day lag we cannot test the alignment of. Build our own lags instead.
- Exclude `instant`, `yr`, `days_since_2011`: time indexes let a tree predict a flat constant past 2011 and a linear model extrapolate a trend we have no grounds for.
- Split 2011 / H1 2012 / H2 2012 by date. Test set touched once, after all feature work.
- Report mean and persistence baselines with every score. Persistence (test R^2 0.510, MAE 840) is within 0.07 R^2 of ridge and beats it on MAE; that caveat goes in the report.

- 2026-11-24 (Huiyu): Added and retained `cnt_roll_std_7`, the sample standard deviation of demand over the previous seven calendar days. All inputs are known before the prediction day; calendar reindexing precedes shifting and rolling. Validation R2 changed from 0.6475 to 0.7224 for Ridge (+0.0749) and from 0.2185 to 0.0977 for HGB (-0.1208). Ridge MAE decreased from 832.9 to 700.4, while HGB MAE increased from 1296.6 to 1381.6. Both baselines were unchanged. Retained for the Ridge improvement. Test set was not scored.

- 2026-11-24 (Huiyu): Explicitly classified all 18 raw columns and added a contract test to detect unclassified columns. An in-memory unknown numeric column correctly triggered an AssertionError. All 16 tests passed on the original data. This is a test-level guard, not a runtime ingestion restriction.

- 2026-11-24 (Huiyu): Exercise 4: trained HGB on cnt minus cnt_lag_1 and reconstructed predictions by adding back cnt_lag_1. With the same 15 features, validation R2 improved from 0.0977 to 0.5642 (+0.4665), and MAE decreased from 1381.6 to 885.8. The transformation is defensible for daily forecasting because yesterday demand is known at prediction time. It beats persistence but not ridge. Only validation was scored in this experiment. Keep the official pipeline untransformed.
