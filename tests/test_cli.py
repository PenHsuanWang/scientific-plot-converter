import numpy as np
import polars as pl
import pytest
from typer.testing import CliRunner

from fabplot.cli import app
from fabplot.render.engine import FAB_STYLE_CONTEXT, FabStyleContext
from fabplot.stats.metrics import calculate_ratio


runner = CliRunner()


@pytest.fixture
def sample_csv(tmp_path):
    df = pl.DataFrame({
        "LotID": np.arange(1, 101),
        "CD_Value": np.random.normal(loc=10.0, scale=0.5, size=100),
        "CD_Sim": np.random.normal(loc=10.2, scale=0.4, size=100),
    })
    file_path = tmp_path / "sample_data.csv"
    df.write_csv(file_path)
    return file_path


# ── Existing commands (backward-compat) ──────────────────────────────────────

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


def test_hist1d_default_output(sample_csv, tmp_path, monkeypatch):
    """Verify default output lands in figure_out/ under the working directory."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        ["hist1d", "--input", str(sample_csv), "--x", "CD_Value"],
    )
    assert result.exit_code == 0
    expected = tmp_path / "figure_out" / "sample_data_hist1d.pdf"
    assert expected.exists()


def test_invalid_column_hist1d(sample_csv):
    result = runner.invoke(
        app, ["hist1d", "--input", str(sample_csv), "--x", "MissingCol"]
    )
    assert result.exit_code == 1
    assert "Error: Column 'MissingCol' not found" in result.stdout


# ── Three-tier typography flags ───────────────────────────────────────────────

def test_hist1d_three_tier_flags(sample_csv, tmp_path):
    """Three-tier flags must be accepted and the output file still created."""
    out_file = tmp_path / "hist_tagged.pdf"
    result = runner.invoke(
        app,
        [
            "hist1d",
            "--input", str(sample_csv),
            "--x", "CD_Value",
            "--project", "FabCo",
            "--status", "Preliminary",
            "--context", "2024-Q3 | N=100",
            "--output", str(out_file),
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert out_file.exists()


def test_trend_three_tier_flags(sample_csv, tmp_path):
    """Three-tier flags must be accepted on the trend command."""
    out_file = tmp_path / "trend_tagged.pdf"
    result = runner.invoke(
        app,
        [
            "trend",
            "--input", str(sample_csv),
            "--x", "LotID",
            "--y", "CD_Value",
            "--project", "FabCo",
            "--status", "Internal Use Only",
            "--context", "Fab-A | N=100",
            "--output", str(out_file),
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert out_file.exists()


# ── FabStyleContext integrity ─────────────────────────────────────────────────

def test_fab_style_context_is_frozen():
    """Verify FabStyleContext is immutable at runtime."""
    with pytest.raises((AttributeError, TypeError)):
        FAB_STYLE_CONTEXT.margin_left = 0.99  # type: ignore[misc]


def test_fab_style_context_tier_ratios():
    """Tier size ratios must satisfy the spec: 0.75–0.80 and 0.60."""
    ctx = FabStyleContext()
    assert 0.75 <= ctx.tier2_size_ratio <= 0.80
    assert ctx.tier3_size_ratio == pytest.approx(0.60, abs=0.01)


def test_fab_style_context_golden_margins():
    """Golden margins must match specification exactly."""
    ctx = FabStyleContext()
    assert ctx.margin_left == pytest.approx(0.15)
    assert ctx.margin_right == pytest.approx(0.05)
    assert 0.08 <= ctx.margin_top <= 0.10
    assert ctx.margin_bottom == pytest.approx(0.12)


def test_petroff_palette_no_pure_red_green_adjacent():
    """First two Petroff colors must not be a pure red vs. pure green pair."""
    ctx = FabStyleContext()
    c1, c2 = ctx.petroff_palette[0], ctx.petroff_palette[1]
    # A pure red would have R≫G,B; a pure green would have G≫R,B.
    # We verify neither of the first two slots is pure red (#ff0000) or
    # pure green (#00ff00).
    assert c1.lower() not in ("#ff0000", "#00ff00")
    assert c2.lower() not in ("#ff0000", "#00ff00")


# ── calculate_ratio unit tests ────────────────────────────────────────────────

def test_calculate_ratio_normal():
    y1 = np.array([2.0, 4.0, 6.0])
    y2 = np.array([1.0, 2.0, 3.0])
    result = calculate_ratio(y1, y2)
    np.testing.assert_array_almost_equal(result, [2.0, 2.0, 2.0])


def test_calculate_ratio_zero_denominator():
    y1 = np.array([1.0, 2.0])
    y2 = np.array([0.0, 2.0])
    result = calculate_ratio(y1, y2)
    assert np.isnan(result[0])
    assert result[1] == pytest.approx(1.0)


def test_calculate_ratio_nan_denominator():
    y1 = np.array([1.0, 2.0])
    y2 = np.array([np.nan, 2.0])
    result = calculate_ratio(y1, y2)
    assert np.isnan(result[0])
    assert result[1] == pytest.approx(1.0)


# ── compare command ───────────────────────────────────────────────────────────

def test_compare_command(sample_csv, tmp_path):
    out_file = tmp_path / "compare.pdf"
    result = runner.invoke(
        app,
        [
            "compare",
            "--input", str(sample_csv),
            "--x", "LotID",
            "--y1", "CD_Value",
            "--y2", "CD_Sim",
            "--output", str(out_file),
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "Successfully generated comparison chart" in result.stdout
    assert out_file.exists()


def test_compare_with_all_flags(sample_csv, tmp_path):
    out_file = tmp_path / "compare_full.pdf"
    result = runner.invoke(
        app,
        [
            "compare",
            "--input", str(sample_csv),
            "--x", "LotID",
            "--y1", "CD_Value",
            "--y2", "CD_Sim",
            "--ratio-label", "Data / MC",
            "--project", "FabCo",
            "--status", "Simulation",
            "--context", "2024-Q4 | N=100",
            "--output", str(out_file),
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert out_file.exists()


def test_compare_default_output(sample_csv, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        [
            "compare",
            "--input", str(sample_csv),
            "--x", "LotID",
            "--y1", "CD_Value",
            "--y2", "CD_Sim",
        ],
    )
    assert result.exit_code == 0, result.stdout
    expected = tmp_path / "figure_out" / "sample_data_compare.pdf"
    assert expected.exists()


def test_compare_missing_column(sample_csv, tmp_path):
    out_file = tmp_path / "compare.pdf"
    result = runner.invoke(
        app,
        [
            "compare",
            "--input", str(sample_csv),
            "--x", "LotID",
            "--y1", "CD_Value",
            "--y2", "NonExistentCol",
            "--output", str(out_file),
        ],
    )
    assert result.exit_code == 1
    assert "Error: Column 'NonExistentCol' not found" in result.stdout
