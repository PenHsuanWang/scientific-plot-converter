import numpy as np
import polars as pl
import pytest
from typer.testing import CliRunner

from fabplot.cli import app


runner = CliRunner()


@pytest.fixture
def sample_csv(tmp_path):
    df = pl.DataFrame({
        "LotID": np.arange(1, 101),
        "CD_Value": np.random.normal(loc=10.0, scale=0.5, size=100),
    })
    file_path = tmp_path / "sample_data.csv"
    df.write_csv(file_path)
    return file_path


def test_hist1d_command(sample_csv, tmp_path):
    out_file = tmp_path / "hist.pdf"
    result = runner.invoke(
        app,
        [
            "hist1d",
            "--input", str(sample_csv),
            "--x", "CD_Value",
            "--output", str(out_file),
        ],
    )
    assert result.exit_code == 0
    assert "Successfully generated 1D histogram" in result.stdout
    assert out_file.exists()


def test_trend_command(sample_csv, tmp_path):
    out_file = tmp_path / "trend.pdf"
    result = runner.invoke(
        app,
        [
            "trend",
            "--input", str(sample_csv),
            "--x", "LotID",
            "--y", "CD_Value",
            "--output", str(out_file),
        ],
    )
    assert result.exit_code == 0
    assert "Successfully generated trend plot" in result.stdout
    assert out_file.exists()


def test_invalid_column_hist1d(sample_csv):
    result = runner.invoke(
        app, ["hist1d", "--input", str(sample_csv), "--x", "MissingCol"]
    )
    assert result.exit_code == 1
    assert "Error: Column 'MissingCol' not found" in result.stdout
