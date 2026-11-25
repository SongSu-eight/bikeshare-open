# Verification Evidence

## Exercise 1: Feature test before implementation

Failing test commit: f98be47
Feature implementation commit: 5f151e3

```text
python -m pytest tests/ -q
...........F...                                                          [100%]
=================================== FAILURES ===================================
_______________________ test_rolling_std_excludes_today ________________________

feats =         dteday  instant  season  ...  cnt_lag_1 cnt_lag_7   cnt_roll_7
0   2011-01-10     10.0  WINTER  ...      822.0...    1787.0  1530.142857
713 2012-12-31    731.0  WINTER  ...     1796.0     920.0  1531.428571

[714 rows x 28 columns]

    def test_rolling_std_excludes_today(feats):
        """Verify sample std of the previous seven calendar days."""
        date = pd.Timestamp("2011-08-01")
        expected = 333.4868456033554
>       assert "cnt_roll_std_7" in feature_columns(feats)
E       AssertionError: assert 'cnt_roll_std_7' in ['temp', 'atemp', 'hum', 'windspeed', 'dayofweek', 'is_weekend', ...]
E        +  where ['temp', 'atemp', 'hum', 'windspeed', 'dayofweek', 'is_weekend', ...] = feature_columns(        dteday  instant  season  ...  cnt_lag_1 cnt_lag_7   cnt_roll_7\n0   2011-01-10     10.0  WINTER  ...      822.0...    1787.0  1530.142857\n713 2012-12-31    731.0  WINTER  ...     1796.0     920.0  1531.428571\n\n[714 rows x 28 columns])

tests/test_leakage.py:73: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_std_excludes_today - AssertionErro...
1 failed, 14 passed in 2.37s
make: *** [Makefile:16: test] Error 1
```

### After implementation

```text
python -m pytest tests/ -q
...............                                                          [100%]
15 passed in 1.22s
```

## Unclassified Column Contract Test

Injected an unknown numeric column into an in-memory DataFrame. The contract test correctly rejected it. The original CSV was unchanged.

```text
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import runpy; from src.ingest import load_raw; test = runpy.run_path("tests/test_contract.py")["test_no_unclassified_raw_columns"]; test(load_raw().assign(unclassified_probe=1))
                                                                                                                                        ~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "tests/test_contract.py", line 64, in test_no_unclassified_raw_columns
    assert not unknown, f"Unclassified raw columns: {sorted(unknown)}"
           ^^^^^^^^^^^
AssertionError: Unclassified raw columns: ['unclassified_probe']
```

After the probe: 16 tests passed. Raw CSV SHA256 remained unchanged.



## Exercise 2: Seeded Faults — Song

### Fault 1: Forbidden column in the feature set

Skill used: `/seed-fault`

#### Exact change

In `src/features.py`, I deliberately allowed `casual` to bypass the FORBIDDEN filter.

```diff
- return [c for c in numeric if c not in FORBIDDEN]
+ return [c for c in numeric if c not in FORBIDDEN or c == "casual"]
```

The agent initially proposed removing the entire FORBIDDEN filter. I rejected that edit because I wanted to test one forbidden column at a time.

#### Hook stderr (actual output)

```text
PostToolUse:Edit hook reported a problem
[${CLAUDE_PROJECT_DIR}/.claude/hooks/check_leakage.sh]: Leakage tests failed after editing /home/songsu/ma6/bikeshare-open/src/features.py:

feats =         dteday  instant  season      yr mnth  ... weather_severity cnt_lag_1  cnt_lag_7   cnt_roll_7  cnt_roll_std_7
0...0  WINTER  2012.0  DEC  ...              1.0    1796.0      920.0  1531.428571      887.135250

[714 rows x 29 columns]

    def test_no_forbidden_features(feats):
        """Guards the gate, not the data: feature_columns() excludes FORBIDDEN by
        construction, so this cannot discover a *new* leaky column. What it
        catches is someone editing feature_columns() or FORBIDDEN -- which is
        exactly the fault the Step 7 hook demonstrates."""
        cols = set(feature_columns(feats))
>       assert not (cols & FORBIDDEN), f"forbidden columns in feature set: {cols & FORBIDDEN}"
E       AssertionError: forbidden columns in feature set: {'casual'}
E       assert not ({'atemp', 'casual', 'cnt_lag_1', 'cnt_lag_7', 'cnt_roll_7', 'cnt_roll_std_7', ...} & {'casual', 'cnt', 'cnt_2d_bfr', 'days_since_2011', 'instant', 'registered', ...})

tests/test_leakage.py:31: AssertionError
=============================================== short test summary info ================================================
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: forbidden columns in feature set: {'casual'}
1 failed, 7 passed in 0.51s
```

#### Detection and repair

The hook successfully detected the fault through `test_no_forbidden_features` and returned the failure to the agent. It did not prevent or undo the edit, since PostToolUse runs after the change has been made.

The agent stopped and waited for my approval before repairing the fault. With one explicit repair instruction, it restored the original return statement without changing any tests or verification rules.

Repair turns: 1, with explicit human guidance.

#### Independent verification after repair

```text
python -m pytest tests/ -q
................                                                         [100%]
16 passed in 1.88s
```

The source code diff was empty. The raw CSV remained unchanged:

```text
a6bed1577f6e4de56dcfae6d8315985073cc0ad3446c8c99ed60c86a0b5ad9dc  data/raw/bike_daily.csv
```

#### Human assessment

The verification mechanism worked as intended. However, the agent incorrectly described the hook as blocking the edit and claimed that other forbidden columns entered the feature set. The actual change only allowed `casual` through. I checked the code and test output rather than relying on the agent's explanation. This experiment confirms that the existing test can detect a deliberate violation of the forbidden-column filter.



### Fault 2: Missing shift in the rolling mean

Skill used: `/seed-fault`

#### Exact change

In `src/features.py`, I deliberately removed `.shift(1)` from `cnt_roll_7` so that the rolling mean would include today's target value. All other features, including `cnt_roll_std_7`, were left unchanged.

```diff
- out["cnt_roll_7"] = out[TARGET].shift(1).rolling(LAG_WARMUP).mean()
+ out["cnt_roll_7"] = out[TARGET].rolling(LAG_WARMUP).mean()
```

#### Hook stderr (actual output)

```text
PostToolUse:Edit hook reported a problem
[${CLAUDE_PROJECT_DIR}/.claude/hooks/check_leakage.sh]: Leakage tests failed after editing /home/songsu/ma6/bikeshare-open/src/features.py:
[714 rows x 29 columns]

    def test_rolling_mean_excludes_today(feats):
        """cnt_roll_7 must be the mean of the 7 calendar days *before* today."""
        by_date = feats.set_index("dteday")[TARGET]
        date = feats.dteday.iloc[200]
        window = [date - pd.Timedelta(days=k) for k in range(1, 8)]
        if all(d in by_date.index for d in window):
            expected = sum(by_date[d] for d in window) / 7
>           assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)
E           assert np.float64(4389.0) == 4414.857142857143 ± 0.00441486
E
E             comparison failed
E             Obtained: 4389.0
E             Expected: 4414.857142857143 ± 0.00441486

tests/test_leakage.py:57: AssertionError
=============================================== short test summary info ================================================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.float64(4389.0) == 4414.857142857143 ± 0.0...
1 failed, 7 passed in 0.66s
```

#### Detection and repair

The hook detected the fault immediately through `test_rolling_mean_excludes_today`. The calculated rolling mean was 4389.0 instead of the expected 4414.857142857143, showing that removing `.shift(1)` changed the feature calculation.

After I recorded the failure and approved the repair, the agent restored `.shift(1)` without modifying other features or tests.

Repair turns: 1, with explicit human guidance.

#### Independent verification after repair

```text
python -m pytest tests/ -q
................                                                         [100%]
16 passed in 1.03s
```

The working tree was clean, and the raw CSV remained unchanged:

```text
a6bed1577f6e4de56dcfae6d8315985073cc0ad3446c8c99ed60c86a0b5ad9dc  data/raw/bike_daily.csv
```

#### Human assessment

Unlike the first fault, the agent introduced the requested change correctly on its first attempt. The test caught the numerical difference, confirming that it checks whether the rolling mean uses strictly earlier observations. However, the agent again described the hook as blocking a commit. The hook actually reports failures after an edit rather than preventing commits. This experiment demonstrates that the existing test can detect temporal leakage even when the feature name and data type remain unchanged.



### Fault 3: Missing exception in the weather encoder

Skill used: `/seed-fault`

#### Exact change

In `src/features.py`, I deliberately removed the exception check from `encode_weather()` to see whether the verification system could detect the loss of protection against unknown weather labels.

```diff
-    if unknown:
-        raise ValueError(f"unmapped weather labels: {sorted(unknown)}")
```

#### Baseline test output

```text
python -m pytest tests/ -q
................                                                         [100%]
16 passed in 1.99s
```

#### Hook stderr

No hook failure or stderr was observed after the edit. Unlike the previous two faults, this change was not detected by the existing leakage tests.

#### Independent test output with the fault present

```text
........                                                                                                         [100%]
8 passed in 0.60s
```

Full test suite:

```text
python -m pytest tests/ -q
................                                                                                                 [100%]
16 passed in 1.37s
```

No existing test failed, even though the exception check had been removed.

#### Additional verification

To understand why the tests still passed, I called `encode_weather()` with an unknown weather label using an in-memory Series. No raw data was modified.

```python
probe = pd.Series(["GOOD", "UNKNOWN", "BAD"])
print(encode_weather(probe))
```

Actual output:

```text
Input:
0       GOOD
1    UNKNOWN
2        BAD
dtype: str

Encoded output:
0    0.0
1    NaN
2    2.0
dtype: float64
```

The unknown label was silently converted to NaN instead of raising an exception. In the feature pipeline, this could cause a row to be silently removed by the subsequent dropna() operation.

#### Detection and repair

The agent attempted to stage the faulty file and later tried to execute the hook script directly without its required payload. I rejected these requests and ran the tests independently.

After recording the verification gap, I instructed the agent to restore the original exception check.

Repair turns: 1, with explicit human guidance.

#### Independent verification after repair

```text
python -m pytest tests/ -q
................                                                         [100%]
16 passed in 1.81s
```

The same unknown-weather probe was repeated:

```text
Input:
0       GOOD
1    UNKNOWN
2        BAD
dtype: str
PASS: ValueError("unmapped weather labels: ['UNKNOWN']")
```

The working tree was clean, and the raw CSV remained unchanged:

```text
a6bed1577f6e4de56dcfae6d8315985073cc0ad3446c8c99ed60c86a0b5ad9dc  data/raw/bike_daily.csv
```

#### Human assessment

This fault revealed a limitation that the first two experiments did not. Both the leakage tests and the full test suite passed while the code was faulty. The existing dataset contains known weather labels, so removing the exception check did not cause an observable failure on that data. However, the in-memory probe demonstrated that an unknown label would be silently accepted as NaN. A test that explicitly checks whether unknown weather labels raise a ValueError would catch this fault. The experiment showed that passing tests alone does not guarantee correctness when important edge cases are not covered.



### Fault 4: Bash copy into the raw data directory

#### Attempted change

I asked the agent to copy a harmless probe file into `data/raw/` using Bash rather than the Edit or Write tools. A separate probe file was used to avoid modifying the original dataset.

```bash
cp -n ~/ma6/evidence/song/raw_write_probe.txt data/raw/raw_write_probe.txt
```

#### Actual permission output

```text
$ cp -n ~/ma6/evidence/song/raw_write_probe.txt data/raw/raw_write_probe.txt
1 action not run · permission denied · rule from shared project settings
│ Reason: Permission to use Bash with command cp -n ~/ma6/evidence/song/raw_write_probe.txt data/raw/raw_write_probe.txt has been denied.
```

The command was not executed. No PostToolUse hook failure or stderr was observed.

#### Independent verification

```text
===== Raw Data Directory =====
total 96
drwxr-xr-x 2 songsu songsu  4096 Nov 10 09:52 .
drwxr-xr-x 4 songsu songsu  4096 Nov 10 09:52 ..
-rw-r--r-- 1 songsu songsu 86325 Nov 10 09:52 bike_daily.csv
===== Probe Destination =====
Probe does not exist
===== Raw Data Hash =====
a6bed1577f6e4de56dcfae6d8315985073cc0ad3446c8c99ed60c86a0b5ad9dc  data/raw/bike_daily.csv
===== Git Status =====
```

The destination file did not exist, the original CSV hash remained unchanged, and the working tree was clean.

#### Existing structural enforcement

The project settings contain the following deny rules:

```json
"deny": [
  "Write(./data/raw/**)",
  "Edit(./data/raw/**)",
  "Bash(rm -rf:*)"
]
```

The existing PostToolUse hook has the matcher `Edit|Write`. Therefore, it does not directly monitor Bash copy operations.

Although no explicit Bash copy deny rule appears in the settings, Claude Code v2.1.332 denied the attempted command. The precise internal permission-matching mechanism was not established.

#### Human assessment and additional protection

The agent incorrectly suggested that either the PostToolUse hook or filesystem permissions had blocked the command. The actual output identified the Claude Code permission system as the source of the denial.

A raw-data integrity check in `make data` would provide an additional independent layer of protection. It could verify both the expected SHA-256 hash of the original CSV and the contents of the raw data directory. This would detect changes to the original dataset or unexpected files introduced through Bash or other tools, regardless of whether the agent's permission system intercepted the operation.

Such a check would detect unauthorized changes before data ingestion, rather than prevent the original write itself.

No repair was necessary because the attempted copy was denied.



## Verification improvements after the seeded fault experiments

### Weather encoder regression test

The original Fault 3 experiment revealed that neither the leakage tests nor the full test suite detected the missing exception.

To address this gap, I added `test_weather_rejects_unknown_labels()` to `tests/test_leakage.py`. The test uses an in-memory Series containing an unknown weather label and requires a ValueError.

The existing PostToolUse hook was left unchanged because it already runs this test file.

Before reintroducing the fault:

```text
17 passed in 1.39s
```

I then asked the agent to remove the same two lines from `encode_weather()` using Edit. The PostToolUse hook reported:

```text
[${CLAUDE_PROJECT_DIR}/.claude/hooks/check_leakage.sh]: Leakage tests failed after editing /home/songsu/ma6/bikeshare-open/src/features.py:

E       Failed: DID NOT RAISE ValueError

tests/test_leakage.py:81: Failed

FAILED tests/test_leakage.py::test_weather_rejects_unknown_labels - Failed: DID NOT RAISE ValueError
1 failed, 8 passed in 0.73s
```

The agent restored the original exception check in one repair turn with explicit human guidance.

Independent verification after repair:

```text
17 passed in 0.99s
```

The original source code was restored, and the new regression test was retained.

Commit: `efc170a`.

### Additional structural enforcement: raw data integrity

Implemented `verify_raw_integrity()` in `src/ingest.py` and connected it to the existing `make data` workflow.

The function verifies the expected SHA-256 hash and requires the raw directory to contain exactly one entry, `bike_daily.csv`.

Normal ingestion:

```text
OK ingest: 728 rows, 2011-01-03 -> 2012-12-31, sha256=a6bed1577f6e4de56dcfae6d8315985073cc0ad3446c8c99ed60c86a0b5ad9dc
```

Independent verification using temporary copies:

```text
PASS: Original data accepted
PASS: Unexpected file
Detected: directory /tmp/tmp_fd3cw_2 must contain exactly one entry 'bike_daily.csv', found: ['raw_write_probe.txt', 'bike_daily.csv']

PASS: Modified CSV
Detected: SHA-256 mismatch. Expected a6bed1577f6e4de56dcfae6d8315985073cc0ad3446c8c99ed60c86a0b5ad9dc, got 450f3dcd8b885b4b3fc710fc7ec9be80c3f730602c3cddb721695dba3051ecda

All integrity verification cases passed.
```

No original raw data was modified.

This mechanism detects unexpected changes during ingestion. It does not prevent Bash writes themselves and is not automatically invoked by direct calls to `load_raw()`.

The existing permission rules and PostToolUse hook remain unchanged.

Commit: `ef2f923`.

### Verification summary before the renamed leakage test

| Fault | Initial detection | Final verification mechanism |
|---|---|---|
| Forbidden column | Detected | Existing leakage test |
| Missing shift | Detected | Existing rolling mean test |
| Missing weather exception | Not detected | New regression test and existing hook |
| Bash copy into raw directory | Permission denied | Existing permissions plus independent raw-data integrity check |

All 17 tests pass, and the original raw dataset remains unchanged.



### Additional verification: renamed leakage column

The existing forbidden-column test checks feature names against FORBIDDEN. A leaked column copied under an innocent name could therefore escape that test.

To close this gap, I added `test_only_approved_features_enter_model()` in `tests/test_leakage.py`, using an independent set of the 15 approved features.

Before introducing the fault:

```text
18 passed in 1.20s
```

The agent temporarily inserted the following line into `build_features()` using Edit:

```diff
+    out["innocent_feature"] = out["casual"]
```

The PostToolUse hook detected the unexpected feature through `test_only_approved_features_enter_model`.

Observed failure summary:

```text
tests/test_leakage.py:105: AssertionError
1 failed, 9 passed in 0.55s
```

The original forbidden-column test did not fail, demonstrating why an independent feature-set contract is necessary.

The agent removed the temporary leakage column in one repair turn with explicit human guidance.

Independent verification after repair:

```text
18 passed in 1.40s
```

The original feature-building code was restored, and the raw CSV remained unchanged.

This test detects unauthorized feature names, including renamed leakage columns. It does not guarantee detection of leakage introduced through modifications to the values of existing approved features.

Commit: `1dd5ada`.
