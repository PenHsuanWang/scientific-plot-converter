"""Data ingestion utilities for loading CSV and Parquet files via Polars."""

from pathlib import Path

import polars as pl


def load_data(file_path: str | Path) -> pl.DataFrame:
    """Load tabular data from CSV or Parquet into memory using Polars.

    Handles null values commonly found in Fab data.

    :param file_path: The absolute or relative path to the data file.
    :type file_path: str or pathlib.Path
    :returns: A Polars DataFrame containing the ingested data.
    :rtype: polars.DataFrame
    :raises FileNotFoundError: If the file does not exist.
    :raises ValueError: If the file format is not supported.
    :raises RuntimeError: If Polars fails to parse the file.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    suffix = path.suffix.lower()

    try:
        if suffix == ".parquet":
            return pl.read_parquet(path)
        elif suffix == ".csv":
            return pl.read_csv(path, null_values=["NaN", "NA", "null", ""])
        else:
            raise ValueError(
                f"Unsupported file format: {suffix}. Must be .csv or .parquet."
            )
    except Exception as e:
        raise RuntimeError(
            f"Failed to ingest data from {path}: {str(e)}"
        ) from e
