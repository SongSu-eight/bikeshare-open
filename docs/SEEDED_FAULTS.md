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
