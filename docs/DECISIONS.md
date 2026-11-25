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


- 2026-11-25 (Song): Added the `/seed-fault` skill to standardize fault introduction, evidence collection, human approval, repair, and verification. Used it for three controlled source-code faults. Human supervision was retained because the local agent sometimes misunderstood tool permissions and hook behavior.

- 2026-11-25 (Song): Retained the original PostToolUse hook and permission rules. The hook reports leakage test failures after an edit but does not undo edits or prevent commits. The attempted Bash copy was denied by Claude Code, although the precise permission-matching mechanism was not established.

- 2026-11-25 (Song): Added SHA-256 and raw-directory integrity checks to the ingestion workflow as independent structural enforcement. Temporary-copy experiments confirmed that both unexpected files and modified CSV contents were detected. The original dataset remained unchanged.

- 2026-11-25 (Song): Added a regression test requiring unknown weather labels to raise ValueError. The original fault passed all 16 tests; after adding the test, the same fault produced a PostToolUse hook failure. All 17 tests passed after repair.

- 2026-11-25 (Team): Feature selection and target-transformation decisions are based on validation results only. The existing automated test-set performance assertion is retained as a fixed verification check, not as a criterion for tuning or selecting features. Final reported test metrics are generated after methodological decisions are finalized.

- 2026-11-25 (Song): Added an independent feature-set contract test requiring exactly the 15 approved model inputs. A temporary copy of the forbidden casual column under the name innocent_feature triggered the PostToolUse hook. All 18 tests passed after repair. The feature set and modelling pipeline remain unchanged.

- 2026-11-25 (Song): Updated CLAUDE.md to document raw-data integrity requirements, unknown-weather exception handling, and the /seed-fault workflow. These rules preserve the verification mechanisms and make future agent behavior consistent with the methodological contract.

- 2026-11-25 (Song): Removed report-related ignore rules from .gitignore so that the required metrics and self-audit artifacts can be committed.

- 2026-11-25 (Huiyu): Updated CLAUDE.md to require the seven-day rolling standard deviation to exclude today's demand and to require explicit classification of new raw columns.

- 2026-11-25 (Team): Retained daily total ridership (cnt) as the forecasting target. Final demand growth of 63.39% and 104 of 184 test days exceeding the training maximum support the distribution-shift interpretation of HGB's weak test performance.

- 2026-11-25 (Team): Prefer persistence for deployment when absolute daily forecasting error is the primary cost. Final Ridge test R2 is higher (0.6356 vs 0.5099), but its MAE is slightly worse (840.3 vs 840.1). Retain both in the reported comparison without further tuning.
