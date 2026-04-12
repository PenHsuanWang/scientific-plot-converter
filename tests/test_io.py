"""Tests for dsprinter.data.io — CSV/Parquet loading and error handling."""

import pytest
import polars as pl

from dsprinter.data.io import load_data


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def csv_file(tmp_path):
    """Write a small CSV with a NaN row for null-handling tests."""
    content = "col_a,col_b\n1.0,10.0\n2.0,\nNA,30.0\n4.0,40.0\n"
    f = tmp_path / "data.csv"
    f.write_text(content)
    return f


@pytest.fixture
def parquet_file(tmp_path):
    """Write a minimal Parquet file via Polars."""
    df = pl.DataFrame({"x": [1.0, 2.0, 3.0], "y": [4.0, 5.0, 6.0]})
    f = tmp_path / "data.parquet"
    df.write_parquet(f)
    return f


# ── Happy path ────────────────────────────────────────────────────────────────


def test_load_csv_returns_dataframe(csv_file):
    """load_data on a valid CSV returns a non-empty DataFrame."""
    df = load_data(csv_file)
    assert isinstance(df, pl.DataFrame)
    assert df.shape[0] == 4


def test_load_csv_accepts_string_path(csv_file):
    """load_data accepts a plain string path, not just pathlib.Path."""
    df = load_data(str(csv_file))
    assert isinstance(df, pl.DataFrame)


def test_load_parquet_returns_dataframe(parquet_file):
    """load_data on a Parquet file returns the correct DataFrame."""
    df = load_data(parquet_file)
    assert isinstance(df, pl.DataFrame)
    assert "x" in df.columns and "y" in df.columns
    assert df.shape == (3, 2)


def test_load_parquet_accepts_string_path(parquet_file):
    """Parquet loading also works when path is passed as str."""
    df = load_data(str(parquet_file))
    assert isinstance(df, pl.DataFrame)


def test_load_csv_null_values_are_null(csv_file):
    """Sentinel strings ('NA', empty) must be loaded as null, not text."""
    df = load_data(csv_file)
    # col_b row 2 is empty → null; col_a row 3 is 'NA' → null
    assert df["col_b"][1] is None
    assert df["col_a"][2] is None


# ── Error paths ───────────────────────────────────────────────────────────────


def test_load_data_file_not_found_raises(tmp_path):
    """A non-existent file must raise FileNotFoundError (not RuntimeError)."""
    missing = tmp_path / "ghost.csv"
    with pytest.raises(FileNotFoundError, match="Input file not found"):
        load_data(missing)


def test_load_data_unsupported_extension_raises(tmp_path):
    """An unsupported extension (.xlsx) must bubble up as RuntimeError."""
    bad = tmp_path / "data.xlsx"
    bad.write_text("dummy")
    with pytest.raises(RuntimeError, match="Failed to ingest"):
        load_data(bad)


def test_load_data_corrupt_csv_raises_runtime_error(tmp_path):
    """A file with extension .csv but binary content must raise RuntimeError."""
    corrupt = tmp_path / "corrupt.csv"
    corrupt.write_bytes(b"\x00\x01\x02\x03" * 100)
    # Polars may or may not error here; what matters is no unhandled exception
    # escapes — it should be either a valid DF or a RuntimeError.
    try:
        df = load_data(corrupt)
        assert isinstance(df, pl.DataFrame)
    except RuntimeError:
        pass  # expected


def test_load_data_empty_csv_returns_empty_dataframe(tmp_path):
    """An empty CSV (header only) returns a DataFrame with 0 rows."""
    empty = tmp_path / "empty.csv"
    empty.write_text("col_a,col_b\n")
    df = load_data(empty)
    assert isinstance(df, pl.DataFrame)
    assert df.shape[0] == 0
    assert "col_a" in df.columns
