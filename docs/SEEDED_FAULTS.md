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
