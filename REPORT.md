## Results

We forecast daily Capital Bikeshare demand (`cnt`) using the supplied 2011–2012 mirror. Calendar reindexing and seven-day lag warm-up leave 714 of 728 raw observations: 348 training days (2011), 182 validation days (H1 2012), and 184 test days (H2 2012). Weather is treated as available at prediction time, and yesterday's demand is known. Before refers to the unmodified starter (`429fffb`, 14 features); After refers to the final pipeline (`65e76ae`, 15 features). Both were reproduced with `make all` on identical raw data and temporal splits, after feature selection was finalized. MAE is measured in daily rides.

| Feature set | Model | Valid R² | Valid MAE | Test R² | Test MAE |
|---|---|---:|---:|---:|---:|
| Before | baseline_mean | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| Before | baseline_persistence | 0.4507 | 900.6 | 0.5099 | 840.1 |
| Before | ridge | 0.6475 | 832.9 | 0.5833 | 947.1 |
| Before | hgb | 0.2185 | 1296.6 | -0.4975 | 1972.6 |
| After | baseline_mean | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| After | baseline_persistence | 0.4507 | 900.6 | 0.5099 | 840.1 |
| After | ridge | 0.7224 | 700.4 | 0.6356 | 840.3 |
| After | hgb | 0.0977 | 1381.6 | -0.6959 | 2108.4 |

The After rows match `reports/metrics.json`. All 18 tests passed after the final run, and the raw CSV SHA-256 remained `a6bed1577f6e4de56dcfae6d8315985073cc0ad3446c8c99ed60c86a0b5ad9dc`.

## Headline finding

The starter's leaky demonstration produces R² = 1.000 because `casual + registered == cnt` exactly; it learns an identity, not a forecast. Under the valid temporal split, the final training-mean baseline reaches test R² = -2.1441, persistence reaches 0.5099, Ridge reaches 0.6356, and HGB reaches -0.6959. HGB still beats the mean baseline despite its negative R². Raw annual mean demand rose from 3,427.33 to 5,599.93 rides per day (+63.39%); 104 of 184 test days (56.52%) exceeded the training maximum of 6,043, and test demand reached 8,714. This distribution shift makes extrapolation important: boosted trees extrapolate poorly beyond the feature ranges observed in training, whereas Ridge can extrapolate through its linear lag coefficients. This is a plausible explanation for HGB's weak test performance, not a proof that growth explains all its errors. The small training sample (348 days) and fixed boosting settings may also contribute to weak validation performance. Ridge's R² advantage over persistence does not imply a corresponding MAE advantage.

We retained `cnt_roll_std_7` (the sample standard deviation of the preceding seven calendar days, excluding today) because validation Ridge R² increased by 0.0749 and MAE decreased by 132.5 rides, despite HGB validation R² decreasing by 0.1208 and MAE increasing by 85.0 rides; both baselines remained unchanged.

## Exercise 4: target transformation

To reduce the need for HGB to extrapolate the absolute demand level, we trained it on the first difference `cnt - cnt_lag_1`, then reconstructed the demand prediction by adding `cnt_lag_1` to the predicted difference. The experiment retained the 15 approved inputs, the 2011 training period, and the H1 2012 validation period. On validation, HGB improved from R² = 0.0977 and MAE = 1381.6 to R² = 0.5642 and MAE = 885.8, an improvement of 0.4665 in R² and a reduction of 495.8 rides in MAE. It surpassed persistence (0.4507, 900.6) but not Ridge (0.7224, 700.4).

The transformation is defensible for one-day-ahead forecasting because yesterday's observed demand is available before predicting today's count. It changes the task to forecasting a daily increment without introducing the current target into the inputs. It is not automatically valid for multi-day forecasting when yesterday's observed count is unavailable. We evaluated this transformation on validation only and retained the untransformed official pipeline because Ridge remained stronger. Final reported test metrics were generated after methodological decisions were finalized. The inherited automated Ridge performance assertion does access the test set during `make test`; it was kept as a fixed verification check, not used for tuning or feature selection (see `docs/DECISIONS.md`).

## Exercise 5: ridge vs persistence

We would deploy persistence as the default for this dataset if the operational cost is proportional to absolute daily forecasting error. Final Ridge improves test R² by 0.1257 (0.6356 versus 0.5099), but its MAE is 840.3 rides versus persistence's 840.1. The new feature narrows Ridge's earlier MAE disadvantage (947.1 versus 840.1) without reversing it. Ridge has better validation MAE (700.4 versus 900.6) and better test R², which makes it worth monitoring as a candidate if large errors carry disproportionate costs. However, the observed test MAE provides no practical absolute-error advantage to justify the extra complexity or dependence on weather inputs. We retain Ridge in the reported comparison without claiming that it is universally superior to predicting yesterday's count.

## Attribution

Model: Qwen3.5:4b (4.2B parameters, Q4_K_M) via Ollama, using `bikeshare-coder` with a 65,536-token configured context; no model-size switch during the reported experiments. Huiyu used Song's local Ollama service when her own environment could not run reliably.

**Agent-generated or agent-assisted work:**

- Huiyu: `src/features.py` (`cnt_roll_std_7`), its test in `tests/test_leakage.py`, raw-column classification in `src/config.py` and `tests/test_contract.py`, and the validation-only target-transformation experiment.
- Song: `.claude/skills/seed-fault/SKILL.md`, controlled fault edits and repairs, `verify_raw_integrity()` in `src/ingest.py`, and the weather and feature-set regression tests in `tests/test_leakage.py`.
- Both: agent-assisted updates to `CLAUDE.md`, evidence and decision documentation, independent auditor reports, and this write-up (with ChatGPT assistance). We reviewed the actual outputs and approved the edits rather than relying on the agents' claims.

**Human methodological decisions (recorded in `docs/DECISIONS.md`):**

- Both: forecast `cnt`, retain the starter's forbidden-column policy, use chronological splits, and compare against both mean and persistence baselines.
- Huiyu: use strictly past demand for rolling variability; retain the new feature based on validation results; explicitly classify raw columns; evaluate the first-difference target but keep the official model comparison untransformed.
- Song: retain the hook and permission rules, require actual fault-detection evidence, add raw-data integrity checks, and close the weather and renamed-feature test gaps.
- Both: interpret the growth-related model failure and the Ridge–persistence trade-off honestly, prefer persistence for absolute-error deployment, and distinguish fixed automated test assertions from model selection.

The two independent audits are recorded in `docs/AUDIT.md`, including human verdicts. The SDK self-audit in `reports/audit.jsonl` returned `leakage: none`, `temporal_ok: true`, `baseline_reported: true`, `reproducible: true`, and high confidence, but its four findings still required review. The alleged missing mean baseline for HGB is incorrect: both baselines are scored on the same splits in `src/train.py:48–85` and appear in `reports/metrics.json`. The comments about `VALID_END` and `TRAIN_END` describe the correct existing dates (`src/config.py:57–58`), not defects. The recommendation to remove `src/leakage_demo.py` is rejected because it is an intentionally leaky teaching demonstration, not part of `make all`, and the assignment requires retaining starter files. We preserve the actual JSONL unchanged and do not equate the SDK's `0 flagged` summary with an empty findings list.
