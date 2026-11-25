"""Stage 1: fetch the raw dataset and assert its shape.

Run: python -m src.ingest
"""
import hashlib
import sys
import urllib.request
from pathlib import Path

import pandas as pd

from src.config import DATA_URL, RAW

EXPECTED_MIN_ROWS = 700
REQUIRED_COLS = {"dteday", "cnt", "casual", "registered", "temp", "hum", "windspeed"}
EXPECTED_RAW_SHA256 = "a6bed1577f6e4de56dcfae6d8315985073cc0ad3446c8c99ed60c86a0b5ad9dc"


def verify_raw_integrity(raw_path: Path) -> None:
    if not raw_path.is_file():
        raise ValueError(f"{raw_path} must be a file")

    dir_contents = list(raw_path.parent.iterdir())
    if len(dir_contents) != 1 or dir_contents[0].name != "bike_daily.csv":
        raise ValueError(
            f"directory {raw_path.parent} must contain exactly one entry "
            f"'bike_daily.csv', found: {[d.name for d in dir_contents]}"
        )

    with open(raw_path, "rb") as f:
        actual_hash = hashlib.sha256(f.read()).hexdigest()

    if actual_hash != EXPECTED_RAW_SHA256:
        raise ValueError(
            f"SHA-256 mismatch. "
            f"Expected {EXPECTED_RAW_SHA256}, got {actual_hash}"
        )


def download(force: bool = False) -> None:
    if RAW.exists() and not force:
        return
    RAW.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(DATA_URL, RAW)


def load_raw() -> pd.DataFrame:
    df = pd.read_csv(RAW, parse_dates=["dteday"])
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"raw data is missing required columns: {sorted(missing)}")
    if len(df) < EXPECTED_MIN_ROWS:
        raise ValueError(f"raw data has only {len(df)} rows; expected >= {EXPECTED_MIN_ROWS}")
    return df


if __name__ == "__main__":
    download(force="--force" in sys.argv)
    verify_raw_integrity(RAW)
    df = load_raw()
    print(f"OK ingest: {len(df)} rows, {df.dteday.min().date()} -> {df.dteday.max().date()}, sha256={EXPECTED_RAW_SHA256}")
