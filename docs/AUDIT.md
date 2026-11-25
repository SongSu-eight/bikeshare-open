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


## Audit 2 — Huiyu reviewing Song

- Repository: https://github.com/SongSu-eight/bikeshare-open
- Reviewer: Huiyu
- Author: Song
- Date: 2026-11-25
- Branch: `song/verification`
- Review branch: `huiyu/audit-song`
- Reviewed commit: `c064d53`
- Pull request: #2
- Model: Qwen3.5:4b (4.2B parameters, Q4_K_M) via Ollama, using the `bikeshare-coder` alias on Song's machine
- Agent: `leakage-auditor`
- Invocation: `claude --agent leakage-auditor --model bikeshare-coder --permission-mode default`

### Independent Verification

Before running the auditor, I independently checked the reviewed branch on my own computer.

- `make data`: 728 rows, 2011-01-03 to 2012-12-31.
- `make test`: 18 passed in 1.99s.
- `CLAUDE.md`: 56 lines.
- `git diff --check`: no errors.
- Working tree: clean.

The raw dataset SHA-256 remained unchanged:

```text
a6bed1577f6e4de56dcfae6d8315985073cc0ad3446c8c99ed60c86a0b5ad9dc
```

### Audit Execution

The initial attempt used the main agent with a request to invoke the leakage-auditor subagent. Although the main agent produced a preliminary audit report, inspection of the session log confirmed that no Agent or Task invocation was recorded. Two Glob tool errors were also recorded.

I therefore launched the designated leakage-auditor directly using the `--agent leakage-auditor` option. The formal audit completed in 2 minutes and 28 seconds. No source-code changes or additional pipeline training were requested during the audit.

### Auditor Output (Verbatim)

```text
All five methodology checks pass

1. Target leakage. ✅ FORBIDDEN = {"casual", "registered", "cnt", ...} exactly. Lines 31-32 of src/config.py document why these columns are excluded: casual + registered == cnt. Line 20-22 of tests/test_leakage.py verifies this identity holds in the feature set.

2. Temporal ordering. ✅ .shift(1) and .shift(7) in src/features.py lines 74-75 are called before any aggregation (.rolling() at line 76). Date-based temporal split (df.dteday <= TRAIN_END) confirmed in src/train.py lines 59-61.

3. Calendar gaps. ✅ reindex_to_calendar in src/features.py creates a gap-free calendar via pd.date_range (lines 44-49). Tests verify this at lines 24-25 and 39-43 of tests/test_contract.py.

4. Silent row loss. ✅ encode_weather raises ValueError for unknown labels (lines 28-31, verified in test_leakage.py line 78-82). Row losses are bounded by LAG_WARMUP (line 63), not silently dropped.

5. Unreported baseline. ✅ Both baselines defined: "baseline_mean" and "baseline_persistence" (lines 49-50, scores at 81-85 of src/train.py). Line 55-58 of tests/test_contract.py confirms persistence is always reported.

No findings that change numerical results or invalidate conclusions.
```

### Human Verdict — Huiyu

After reviewing Song's branch at commit `c064d53`, I agree with the auditor's overall conclusion that the changes do not introduce methodology violations that invalidate the current numerical results.

I independently reproduced all 18 passing tests and verified that the original raw dataset remained unchanged.

For target leakage, the existing FORBIDDEN filter is supplemented by an independent feature-set contract requiring exactly the 15 approved model inputs. The documented renamed-leakage experiment demonstrates that an unauthorized feature named `innocent_feature` triggers the new test. However, this test does not guarantee detection of leakage introduced through the values of an already approved feature.

For temporal ordering, both rolling aggregations explicitly use `.shift(1)` before calculating statistics (`src/features.py:76–77`). The split is date-based, and models, including the Ridge scaler, are fitted only on training rows (`src/train.py:48–84`). The preliminary main-agent report incorrectly stated that the test set was touched only once. The existing fixed performance assertion in `tests/test_contract.py:46–52` evaluates the test set during automated verification. This is distinguished from model selection and tuning, which are based on validation results as recorded in `docs/DECISIONS.md`.

For calendar gaps and silent row loss, calendar reindexing occurs before lag construction. Although `dropna()` still removes rows, the existing row-loss contract bounds the permitted loss. The new weather regression test also requires unknown weather labels to raise an exception.

Both the mean and persistence baselines are implemented in `src/train.py:48–53` and included in the validation and test scoring loop. The final reported metrics must retain both baselines.

The raw-data integrity check provides additional structural enforcement by detecting unexpected directory entries and SHA-256 mismatches during ingestion. It does not prevent all possible filesystem writes or automatically protect direct calls to `load_raw()`. The PostToolUse hook reports test failures after an edit but does not automatically undo edits or prevent commits.

These limitations are consistent with the documented scope of Song's verification mechanisms. No additional source-code changes are required based on this audit.

**Verdict: APPROVE — I support merging Song's verification branch after this audit record is included in PR #2.**
