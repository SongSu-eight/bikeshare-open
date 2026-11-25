# Teammate Leakage Audits

## Audit 1 — Song reviewing Huiyu

- Repository: https://github.com/SongSu-eight/bikeshare-open
- Reviewer: Song
- Author: Huiyu
- Branch: `huiyu/methodology`
- Reviewed commit: `7b2e95a`
- Pull request: #1
- Model: Qwen3.5:4b via Ollama, 64K configured context
- Agent: `leakage-auditor`

### Auditor Output (Verbatim)

```text
Audit Report: Commit 7b2e95a ✅

Commit message: "Update agent rules for rolling feature and raw column classification"

---

Findings Summary

┌───────────────────┬────────────┬────────────────────────────────────────────────────────────────────────────────┐
│       Check       │   Status   │                                    Details                                     │
├───────────────────┼────────────┼────────────────────────────────────────────────────────────────────────────────┤
│ Check 1: Target   │            │ FORBIDDEN correctly excludes casual, registered, cnt with reasoning. Test at   │
│ Leakage           │ ✅ PASSED  │ tests/test_leakage.py Line 20-22 verifies the identity casual + registered ==  │
│                   │            │ cnt.                                                                           │
├───────────────────┼────────────┼────────────────────────────────────────────────────────────────────────────────┤
│ Check 2: Temporal │ ✅ PASSED  │ Lag features apply .shift(1) before aggregation (src/features.py L76-77). Test │
│  Ordering         │            │  at Lines 50-57 confirms rolling window excludes today (days k=1 to 7).        │
├───────────────────┼────────────┼────────────────────────────────────────────────────────────────────────────────┤
│ Check 3: Calendar │ ✅ PASSED  │ reindex_to_calendar() fills gaps using pd.date_range() before computing lags   │
│  Gaps             │            │  (src/features.py L34-50). Comment explains .shift(1) moves by rows, not days.  │
├───────────────────┼────────────┼────────────────────────────────────────────────────────────────────────────────┤
│ Check 4: Silent   │ ⚠️ MINOR   │ dropna() at Line 79 drops rows but doesn't count or report how many. Suggested │
│ Row Loss          │ ISSUE      │  adding a row loss metric or bound to LAG_WARMUP.                              │
├───────────────────┼────────────┼────────────────────────────────────────────────────────────────────────────────┤
│ Check 5:          │ ✅         │ No unreported baselines are present — this is by design. The pipeline trains   │
│ Unreported        │ VERIFIED   │ prediction models without implementing baseline forecasting.                   │
│ Baseline          │ OK         │                                                                                │
└───────────────────┴────────────┴────────────────────────────────────────────────────────────────────────────────┘

---

Recommendation

Commit 7b2e95a is audit-clean for the five checks per CLAUDE.md requirements. The minor issue around silent row loss should be addressed:

# Consider tracking dropped rows:
dropped_rows = ~out.index.isin(calendar_index[out['cnt'] != 0])
print(f"Dropped {sum(dropped_rows)} rows due to NaN after shift/aggregate")

This would provide visibility into how many calendar days are lost before computing lag features.
```

### Human Verdict — Song

After reviewing Huiyu's code at commit `7b2e95a`, I agree with the auditor's conclusions on target leakage, temporal ordering, and calendar gaps. I also confirmed that the data is split by date and that the Ridge scaler is fitted only on the training set. However, I noticed two problems with the auditor's assessment. First, although it correctly pointed out that `dropna()` does not directly report how many rows are removed, it overlooked the existing row-loss test in `tests/test_contract.py:28–43`. When I ran the pipeline myself, the number of rows decreased from 728 to 714, which was within the expected limit, and all 16 tests passed. Second, while I agree that there is no missing baseline, the auditor's explanation is incorrect. Both the mean and persistence baselines are already implemented in `src/train.py:33–53`. Based on my review, neither of these findings identifies an actual error that would change the current numerical results. I therefore support merging Huiyu's branch without implementing the auditor's suggested change to the row-loss handling.
