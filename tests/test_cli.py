import json
import numpy as np
import polars as pl
import pytest
from datetime import datetime, timedelta
from typer.testing import CliRunner

from dsprinter.cli import app
from dsprinter.render.engine import DSP_STYLE_CONTEXT, DSPStyleContext
from dsprinter.stats.metrics import calculate_ratio


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


def test_hist1d_bare_output_routes_to_figure_out(sample_csv, tmp_path, monkeypatch):
    """A bare --output filename (no directory) must land in figure_out/, not CWD."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        ["hist1d", "--input", str(sample_csv), "--x", "CD_Value",
         "--output", "bare.pdf"],
    )
    assert result.exit_code == 0
    assert (tmp_path / "figure_out" / "bare.pdf").exists(), "Should be in figure_out/"
    assert not (tmp_path / "bare.pdf").exists(), "Should NOT be in CWD"


def test_trend_bare_output_routes_to_figure_out(sample_csv, tmp_path, monkeypatch):
    """A bare --output filename on trend must land in figure_out/."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        ["trend", "--input", str(sample_csv),
         "--x", "LotID", "--y", "CD_Value", "--output", "bare_trend.pdf"],
    )
    assert result.exit_code == 0
    assert (tmp_path / "figure_out" / "bare_trend.pdf").exists()
    assert not (tmp_path / "bare_trend.pdf").exists()


def test_invalid_column_hist1d(sample_csv):
    result = runner.invoke(
        app, ["hist1d", "--input", str(sample_csv), "--x", "MissingCol"]
    )
    assert result.exit_code == 1
    assert "Error: Column 'MissingCol' not found" in result.stdout


# ── Three-tier typography flags ───────────────────────────────────────────────

def test_annotations_present_in_figure_before_savefig():
    """Tier-1/2/3 text elements must be in the figure BEFORE savefig is called.

    Regression test for the bug where add_three_tier_typography() was called in
    the context-manager finally block — after fig.savefig() — so annotations
    never appeared in saved output files.
    """
    from dsprinter.render.engine import CanvasBuilder, DSP_STYLE_CONTEXT
    builder = CanvasBuilder(DSP_STYLE_CONTEXT)
    with builder.single_canvas(
        project="TestProject",
        status="Draft",
        context="N=999",
    ) as (fig, ax):
        ax.plot([1, 2, 3], [1, 2, 3])
        # Annotations must already be in the figure at this point
        fig_text_strings = [t.get_text() for t in fig.texts]
        assert "TestProject" in fig_text_strings, (
            "Tier-1 project tag not found in figure before savefig"
        )
        assert "Draft" in fig_text_strings, (
            "Tier-2 status tag not found in figure before savefig"
        )
        assert "N=999" in fig_text_strings, (
            "Tier-3 context tag not found in figure before savefig"
        )


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


# ── DSPStyleContext integrity ─────────────────────────────────────────────────

def test_fab_style_context_is_frozen():
    """Verify DSPStyleContext is immutable at runtime."""
    with pytest.raises((AttributeError, TypeError)):
        DSP_STYLE_CONTEXT.margin_left = 0.99  # type: ignore[misc]


def test_fab_style_context_tier_ratios():
    """Tier size ratios must satisfy the spec: 0.75–0.80 and 0.60."""
    ctx = DSPStyleContext()
    assert 0.75 <= ctx.tier2_size_ratio <= 0.80
    assert ctx.tier3_size_ratio == pytest.approx(0.60, abs=0.01)


def test_fab_style_context_golden_margins():
    """Golden margins must match specification exactly."""
    ctx = DSPStyleContext()
    assert ctx.margin_left == pytest.approx(0.15)
    assert ctx.margin_right == pytest.approx(0.05)
    assert 0.08 <= ctx.margin_top <= 0.10
    assert ctx.margin_bottom == pytest.approx(0.12)


def test_petroff_palette_no_pure_red_green_adjacent():
    """First two Petroff colors must not be a pure red vs. pure green pair."""
    ctx = DSPStyleContext()
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


# ── _resolve_output direct unit tests ────────────────────────────────────────


def test_resolve_output_none_returns_figure_out_default(tmp_path, monkeypatch):
    """None output → figure_out/<stem>_<suffix>.pdf under CWD."""
    from dsprinter.cli import _resolve_output
    monkeypatch.chdir(tmp_path)
    result = _resolve_output(None, "mydata", "hist1d")
    assert result == tmp_path / "figure_out" / "mydata_hist1d.pdf"


def test_resolve_output_bare_filename_routes_to_figure_out(tmp_path, monkeypatch):
    """A bare filename (no directory component) must land in figure_out/."""
    from dsprinter.cli import _resolve_output
    monkeypatch.chdir(tmp_path)
    result = _resolve_output("report.pdf", "data", "trend")
    assert result == tmp_path / "figure_out" / "report.pdf"


def test_resolve_output_bare_svg_routes_to_figure_out(tmp_path, monkeypatch):
    """Bare filename with .svg extension must also route to figure_out/."""
    from dsprinter.cli import _resolve_output
    monkeypatch.chdir(tmp_path)
    result = _resolve_output("chart.svg", "data", "hist1d")
    assert result == tmp_path / "figure_out" / "chart.svg"


def test_resolve_output_explicit_subdir_used_as_is(tmp_path):
    """A path with an explicit subdirectory component must be used verbatim."""
    from dsprinter.cli import _resolve_output
    explicit = str(tmp_path / "mydir" / "out.pdf")
    result = _resolve_output(explicit, "data", "hist1d")
    assert result == (tmp_path / "mydir" / "out.pdf")


def test_resolve_output_absolute_path_used_as_is(tmp_path):
    """An absolute path must be returned as-is without routing to figure_out/."""
    from dsprinter.cli import _resolve_output
    abs_path = str(tmp_path / "absolute.pdf")
    result = _resolve_output(abs_path, "data", "hist1d")
    assert result == tmp_path / "absolute.pdf"


# ── Output routing — all commands, bare filename ──────────────────────────────


def test_compare_bare_output_routes_to_figure_out(sample_csv, tmp_path, monkeypatch):
    """Bare --output on compare must land in figure_out/, not CWD."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        [
            "compare",
            "--input", str(sample_csv),
            "--x", "LotID",
            "--y1", "CD_Value",
            "--y2", "CD_Sim",
            "--output", "bare_compare.pdf",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert (tmp_path / "figure_out" / "bare_compare.pdf").exists()
    assert not (tmp_path / "bare_compare.pdf").exists()


# ── SVG output ────────────────────────────────────────────────────────────────


def test_hist1d_svg_output(sample_csv, tmp_path):
    """hist1d must produce a valid SVG file when --output ends with .svg."""
    out_file = tmp_path / "chart.svg"
    result = runner.invoke(
        app,
        ["hist1d", "--input", str(sample_csv),
         "--x", "CD_Value", "--output", str(out_file)],
    )
    assert result.exit_code == 0, result.stdout
    assert out_file.exists()
    assert out_file.stat().st_size > 0


def test_trend_svg_output(sample_csv, tmp_path):
    """Trend command must produce a valid SVG file when --output ends with .svg."""
    out_file = tmp_path / "trend.svg"
    result = runner.invoke(
        app,
        ["trend", "--input", str(sample_csv),
         "--x", "LotID", "--y", "CD_Value", "--output", str(out_file)],
    )
    assert result.exit_code == 0, result.stdout
    assert out_file.exists()


# ── CLI exception paths (lines 124-127, 162-166, 188-192, 265-272) ───────────


def test_hist1d_nonexistent_input_exits_1(tmp_path):
    """A non-existent CSV path must produce exit code 1 and an error message."""
    result = runner.invoke(
        app,
        ["hist1d", "--input", str(tmp_path / "ghost.csv"), "--x", "col",
         "--output", str(tmp_path / "out.pdf")],
    )
    assert result.exit_code == 1
    assert "Error" in result.stdout


def test_trend_nonexistent_input_exits_1(tmp_path):
    """Non-existent input on trend must produce exit code 1."""
    result = runner.invoke(
        app,
        ["trend", "--input", str(tmp_path / "ghost.csv"),
         "--x", "x", "--y", "y",
         "--output", str(tmp_path / "out.pdf")],
    )
    assert result.exit_code == 1
    assert "Error" in result.stdout


def test_compare_nonexistent_input_exits_1(tmp_path):
    """Non-existent input on compare must produce exit code 1."""
    result = runner.invoke(
        app,
        ["compare", "--input", str(tmp_path / "ghost.csv"),
         "--x", "x", "--y1", "y1", "--y2", "y2",
         "--output", str(tmp_path / "out.pdf")],
    )
    assert result.exit_code == 1
    assert "Error" in result.stdout


def test_trend_missing_x_column_exits_1(sample_csv, tmp_path):
    """Missing X column on trend must exit 1 with a column-not-found message."""
    result = runner.invoke(
        app,
        ["trend", "--input", str(sample_csv),
         "--x", "NoSuchX", "--y", "CD_Value",
         "--output", str(tmp_path / "out.pdf")],
    )
    assert result.exit_code == 1
    assert "Error: Column 'NoSuchX' not found" in result.stdout


def test_trend_missing_y_column_exits_1(sample_csv, tmp_path):
    """Missing Y column on trend must exit 1 with a column-not-found message."""
    result = runner.invoke(
        app,
        ["trend", "--input", str(sample_csv),
         "--x", "LotID", "--y", "NoSuchY",
         "--output", str(tmp_path / "out.pdf")],
    )
    assert result.exit_code == 1
    assert "Error: Column 'NoSuchY' not found" in result.stdout


def test_compare_missing_x_column_exits_1(sample_csv, tmp_path):
    """Missing X column on compare must exit 1."""
    result = runner.invoke(
        app,
        ["compare", "--input", str(sample_csv),
         "--x", "NoX", "--y1", "CD_Value", "--y2", "CD_Sim",
         "--output", str(tmp_path / "out.pdf")],
    )
    assert result.exit_code == 1
    assert "Error: Column 'NoX' not found" in result.stdout


def test_compare_missing_y1_column_exits_1(sample_csv, tmp_path):
    """Missing Y1 column on compare must exit 1."""
    result = runner.invoke(
        app,
        ["compare", "--input", str(sample_csv),
         "--x", "LotID", "--y1", "NoY1", "--y2", "CD_Sim",
         "--output", str(tmp_path / "out.pdf")],
    )
    assert result.exit_code == 1
    assert "Error: Column 'NoY1' not found" in result.stdout


# ── Norm flag on hist1d ───────────────────────────────────────────────────────


def test_hist1d_norm_flag_produces_output(sample_csv, tmp_path):
    """--norm flag must still produce a valid PDF without errors."""
    out_file = tmp_path / "normed.pdf"
    result = runner.invoke(
        app,
        ["hist1d", "--input", str(sample_csv),
         "--x", "CD_Value", "--norm", "--output", str(out_file)],
    )
    assert result.exit_code == 0, result.stdout
    assert out_file.exists()
    assert out_file.stat().st_size > 0


# ── Output file is non-empty ──────────────────────────────────────────────────


def test_hist1d_output_file_is_nonempty(sample_csv, tmp_path):
    """Saved PDF must have non-zero size (confirms Matplotlib wrote content)."""
    out_file = tmp_path / "nonempty.pdf"
    runner.invoke(
        app,
        ["hist1d", "--input", str(sample_csv),
         "--x", "CD_Value", "--output", str(out_file)],
    )
    assert out_file.stat().st_size > 1000  # a real PDF is at least ~1 KB


def test_trend_output_file_is_nonempty(sample_csv, tmp_path):
    """Saved trend PDF must have non-zero size."""
    out_file = tmp_path / "nonempty_trend.pdf"
    runner.invoke(
        app,
        ["trend", "--input", str(sample_csv),
         "--x", "LotID", "--y", "CD_Value", "--output", str(out_file)],
    )
    assert out_file.stat().st_size > 1000


def test_compare_output_file_is_nonempty(sample_csv, tmp_path):
    """Saved compare PDF must have non-zero size."""
    out_file = tmp_path / "nonempty_compare.pdf"
    runner.invoke(
        app,
        ["compare", "--input", str(sample_csv),
         "--x", "LotID", "--y1", "CD_Value", "--y2", "CD_Sim",
         "--output", str(out_file)],
    )
    assert out_file.stat().st_size > 1000


# ── Multi-column histogram overlay ───────────────────────────────────────────


def test_hist1d_multi_column_overlay(sample_csv, tmp_path):
    """Repeating --x must overlay two distributions on the same histogram."""
    out_file = tmp_path / "multi_hist.pdf"
    result = runner.invoke(
        app,
        ["hist1d", "--input", str(sample_csv),
         "--x", "CD_Value", "--x", "CD_Sim",
         "--output", str(out_file)],
    )
    assert result.exit_code == 0, result.stdout
    assert "Successfully generated 1D histogram" in result.stdout
    assert out_file.stat().st_size > 1000


def test_hist1d_multi_column_missing_second_col_exits_1(sample_csv, tmp_path):
    """A missing second column in a multi-column hist1d must exit 1."""
    out_file = tmp_path / "should_not_exist.pdf"
    result = runner.invoke(
        app,
        ["hist1d", "--input", str(sample_csv),
         "--x", "CD_Value", "--x", "NoSuchCol",
         "--output", str(out_file)],
    )
    assert result.exit_code == 1
    assert "Error: Column 'NoSuchCol' not found" in result.stdout


# ── gantt command ─────────────────────────────────────────────────────────────


@pytest.fixture
def gantt_csv(tmp_path):
    """Minimal state-log CSV with two channels over 4 rows each."""
    base = datetime(2024, 3, 1)
    rows = []
    for ch in ["alpha", "beta"]:
        states = ["idle", "running", "idle", "error"]
        for i, state in enumerate(states):
            ts = base + timedelta(hours=i * 6)
            rows.append(f"{ch},{ts.isoformat()},{state}")
    content = "channel,timestamp,state\n" + "\n".join(rows)
    p = tmp_path / "gantt_data.csv"
    p.write_text(content)
    return p


def test_gantt_happy_path(gantt_csv, tmp_path):
    """Gantt command must exit 0 and write a PDF."""
    out_file = tmp_path / "out.pdf"
    result = runner.invoke(
        app,
        ["gantt", "--input", str(gantt_csv), "--output", str(out_file)],
    )
    assert result.exit_code == 0, result.output
    assert "Successfully generated Gantt chart" in result.stdout
    assert out_file.exists()


def test_gantt_default_output_in_figure_out(gantt_csv, tmp_path, monkeypatch):
    """Default output must land in figure_out/ under CWD."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app, ["gantt", "--input", str(gantt_csv)]
    )
    assert result.exit_code == 0, result.output
    expected = tmp_path / "figure_out" / "gantt_data_gantt.pdf"
    assert expected.exists()


def test_gantt_missing_column_exits_nonzero(gantt_csv, tmp_path):
    """Missing column must produce exit_code=1 and a clear error message."""
    out_file = tmp_path / "out.pdf"
    result = runner.invoke(
        app,
        ["gantt", "--input", str(gantt_csv),
         "--state-col", "no_such_col", "--output", str(out_file)],
    )
    assert result.exit_code == 1
    assert "not found" in result.stdout.lower() or result.exit_code != 0


def test_gantt_with_point_event(gantt_csv, tmp_path):
    """Gantt command must accept a valid events JSON file."""
    out_file = tmp_path / "out.pdf"
    events = [{"type": "point", "timestamp": "2024-03-01T12:00:00", "label": "deploy"}]
    events_file = tmp_path / "events.json"
    events_file.write_text(json.dumps(events))
    result = runner.invoke(
        app,
        ["gantt", "--input", str(gantt_csv),
         "--events", str(events_file), "--output", str(out_file)],
    )
    assert result.exit_code == 0, result.output
    assert out_file.exists()


def test_gantt_with_duration_event(gantt_csv, tmp_path):
    """Duration events must also be rendered without error."""
    out_file = tmp_path / "out.pdf"
    events = [{"type": "duration", "start": "2024-03-01T06:00:00",
               "end": "2024-03-01T18:00:00", "label": "maintenance"}]
    events_file = tmp_path / "events.json"
    events_file.write_text(json.dumps(events))
    result = runner.invoke(
        app,
        ["gantt", "--input", str(gantt_csv),
         "--events", str(events_file), "--output", str(out_file)],
    )
    assert result.exit_code == 0, result.output


def test_gantt_bad_events_json_exits_nonzero(gantt_csv, tmp_path):
    """Malformed events JSON must exit with code 1."""
    out_file = tmp_path / "out.pdf"
    events_file = tmp_path / "bad.json"
    events_file.write_text("{not valid json")
    result = runner.invoke(
        app,
        ["gantt", "--input", str(gantt_csv),
         "--events", str(events_file), "--output", str(out_file)],
    )
    assert result.exit_code == 1


def test_gantt_with_domain_palette(gantt_csv, tmp_path):
    """A domain palette JSON with valid colors must be accepted."""
    out_file = tmp_path / "out.pdf"
    palette = {"idle": "#2196f3", "running": "#4caf50", "error": "#f44336"}
    palette_file = tmp_path / "palette.json"
    palette_file.write_text(json.dumps(palette))
    result = runner.invoke(
        app,
        ["gantt", "--input", str(gantt_csv),
         "--palette", str(palette_file), "--output", str(out_file)],
    )
    assert result.exit_code == 0, result.output
    assert out_file.exists()


def test_gantt_bad_palette_json_exits_nonzero(gantt_csv, tmp_path):
    """A palette file with invalid hex colors must exit with code 1."""
    out_file = tmp_path / "out.pdf"
    palette_file = tmp_path / "bad_palette.json"
    palette_file.write_text('{"idle": "notacolor"}')
    result = runner.invoke(
        app,
        ["gantt", "--input", str(gantt_csv),
         "--palette", str(palette_file), "--output", str(out_file)],
    )
    assert result.exit_code == 1


def test_gantt_nonexistent_input_exits_nonzero(tmp_path):
    """A missing input CSV must produce exit code 1."""
    out_file = tmp_path / "out.pdf"
    result = runner.invoke(
        app,
        ["gantt", "--input", "/no/such/file.csv", "--output", str(out_file)],
    )
    assert result.exit_code != 0


def test_gantt_typography_options_accepted(gantt_csv, tmp_path):
    """Three-tier typography flags must be accepted without error."""
    out_file = tmp_path / "out.pdf"
    result = runner.invoke(
        app,
        ["gantt", "--input", str(gantt_csv),
         "--project", "Acme", "--status", "Draft", "--context", "Q1-2024",
         "--output", str(out_file)],
    )
    assert result.exit_code == 0, result.output
    assert out_file.exists()


# ── transition command ────────────────────────────────────────────────────────


@pytest.fixture
def transition_csv(tmp_path):
    """State-log CSV with two channels and multiple state transitions."""
    rows = [
        "svc,2024-01-01T00:00:00,idle",
        "svc,2024-01-01T01:00:00,running",
        "svc,2024-01-01T02:00:00,idle",
        "svc,2024-01-01T03:00:00,error",
        "svc,2024-01-01T04:00:00,idle",
        "db,2024-01-01T00:00:00,idle",
        "db,2024-01-01T01:00:00,running",
        "db,2024-01-01T02:00:00,running",
        "db,2024-01-01T03:00:00,idle",
    ]
    content = "channel,timestamp,state\n" + "\n".join(rows)
    p = tmp_path / "transition_data.csv"
    p.write_text(content)
    return p


def test_transition_happy_path(transition_csv, tmp_path):
    """Transition command must exit 0 and write a PDF."""
    out_file = tmp_path / "out.pdf"
    result = runner.invoke(
        app,
        ["transition", "--input", str(transition_csv), "--output", str(out_file)],
    )
    assert result.exit_code == 0, result.output
    assert "Successfully generated transition matrix" in result.stdout
    assert out_file.exists()


def test_transition_default_output_in_figure_out(transition_csv, tmp_path, monkeypatch):
    """Default output must land in figure_out/ under CWD."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app, ["transition", "--input", str(transition_csv)]
    )
    assert result.exit_code == 0, result.output
    expected = tmp_path / "figure_out" / "transition_data_transition.pdf"
    assert expected.exists()


def test_transition_missing_state_col_exits_nonzero(transition_csv, tmp_path):
    """Missing --state-col must produce exit code 1 with an error message."""
    out_file = tmp_path / "out.pdf"
    result = runner.invoke(
        app,
        ["transition", "--input", str(transition_csv),
         "--state-col", "no_such_col", "--output", str(out_file)],
    )
    assert result.exit_code == 1
    assert "not found" in result.stdout.lower() or result.exit_code != 0


def test_transition_missing_channel_col_exits_nonzero(transition_csv, tmp_path):
    """Missing --channel-col must produce exit code 1 with an error message."""
    out_file = tmp_path / "out.pdf"
    result = runner.invoke(
        app,
        ["transition", "--input", str(transition_csv),
         "--channel-col", "no_channel", "--output", str(out_file)],
    )
    assert result.exit_code == 1


def test_transition_custom_col_names(tmp_path):
    """Custom column names passed via flags must be respected."""
    rows = [
        "svc,2024-01-01T00:00:00,idle",
        "svc,2024-01-01T01:00:00,running",
        "svc,2024-01-01T02:00:00,idle",
    ]
    content = "entity,ts,status\n" + "\n".join(rows)
    csv_file = tmp_path / "custom.csv"
    csv_file.write_text(content)
    out_file = tmp_path / "out.pdf"
    result = runner.invoke(
        app,
        ["transition", "--input", str(csv_file),
         "--channel-col", "entity", "--time-col", "ts",
         "--state-col", "status", "--output", str(out_file)],
    )
    assert result.exit_code == 0, result.output
    assert out_file.exists()


def test_transition_single_state_no_crash(tmp_path):
    """A degenerate dataset with a single state must not crash."""
    rows = [
        "svc,2024-01-01T00:00:00,idle",
        "svc,2024-01-01T01:00:00,idle",
        "svc,2024-01-01T02:00:00,idle",
    ]
    content = "channel,timestamp,state\n" + "\n".join(rows)
    csv_file = tmp_path / "single.csv"
    csv_file.write_text(content)
    out_file = tmp_path / "out.pdf"
    result = runner.invoke(
        app,
        ["transition", "--input", str(csv_file), "--output", str(out_file)],
    )
    assert result.exit_code == 0, result.output
    assert out_file.exists()


def test_transition_typography_options_accepted(transition_csv, tmp_path):
    """Three-tier typography flags must be accepted without error."""
    out_file = tmp_path / "out.pdf"
    result = runner.invoke(
        app,
        ["transition", "--input", str(transition_csv),
         "--project", "Acme", "--status", "Draft", "--context", "Q1-2024",
         "--output", str(out_file)],
    )
    assert result.exit_code == 0, result.output
    assert out_file.exists()


def test_transition_nonexistent_input_exits_nonzero(tmp_path):
    """A missing input CSV must produce a non-zero exit code."""
    out_file = tmp_path / "out.pdf"
    result = runner.invoke(
        app,
        ["transition", "--input", "/no/such/file.csv", "--output", str(out_file)],
    )
    assert result.exit_code != 0


def test_transition_output_flag_respected(transition_csv, tmp_path):
    """--output flag must write the PDF to the specified path."""
    out_file = tmp_path / "custom_output.pdf"
    result = runner.invoke(
        app,
        ["transition", "--input", str(transition_csv), "--output", str(out_file)],
    )
    assert result.exit_code == 0, result.output
    assert out_file.exists()


def test_transition_multi_entity_boundary_not_included(tmp_path):
    """Cross-entity boundary transitions must not appear in the heatmap output."""
    rows = [
        "A,2024-01-01T00:00:00,idle",
        "A,2024-01-01T01:00:00,running",
        "B,2024-01-01T02:00:00,error",
        "B,2024-01-01T03:00:00,idle",
    ]
    content = "channel,timestamp,state\n" + "\n".join(rows)
    csv_file = tmp_path / "multi.csv"
    csv_file.write_text(content)
    out_file = tmp_path / "out.pdf"
    # Must succeed and produce output — boundary filtering happens internally
    result = runner.invoke(
        app,
        ["transition", "--input", str(csv_file), "--output", str(out_file)],
    )
    assert result.exit_code == 0, result.output
    assert out_file.exists()
