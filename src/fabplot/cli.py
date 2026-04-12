"""CLI entry points for FabPlot-CLI.

Defines the ``hist1d``, ``trend``, and ``compare`` commands, parses user
arguments, and delegates to the rendering pipeline.
"""

import sys
from pathlib import Path
from typing import List, Optional

import typer

from fabplot.data.io import load_data
from fabplot.render.plots import render_compare, render_hist1d, render_trend

app = typer.Typer(
    help=(
        "FabPlot-CLI: A standardized Python CLI utility to generate"
        " 'Scientific-Grade' semiconductor visualizations."
    ),
    add_completion=False,
)

# ── Shared option factories ────────────────────────────────────────────────────


def _project_opt() -> Optional[str]:  # pragma: no cover
    return None


_PROJECT = typer.Option(
    None, "--project", "-p", help="Tier-1 brand/project tag (top-left, bold)."
)
_STATUS = typer.Option(
    None, "--status", help="Tier-2 status label (italic), e.g. 'Internal Use Only'."
)
_CONTEXT = typer.Option(
    None,
    "--context",
    help="Tier-3 context string (top-right), e.g. '2024-Q3 | N=1000'.",
)


def _resolve_output(output: Optional[str], stem: str, suffix: str) -> Path:
    """Resolve the output path, routing bare filenames into ``figure_out/``.

    :param output: Raw ``--output`` value from the CLI (may be ``None``).
    :param stem: Input file stem used when building the default name.
    :param suffix: Command suffix appended to the default name (e.g. ``"hist1d"``).
    :returns: Absolute-ish ``Path`` ready for ``mkdir`` + ``savefig``.
    :rtype: pathlib.Path

    Rules:

    * ``None`` → ``<cwd>/figure_out/<stem>_<suffix>.pdf``
    * Bare filename (no directory component) → ``<cwd>/figure_out/<name>``
    * Path with an explicit directory component → used as-is.
    """
    if output is None:
        return Path.cwd() / "figure_out" / f"{stem}_{suffix}.pdf"
    p = Path(output)
    if p.parent == Path("."):
        # Bare filename only — keep name/extension, route to figure_out/
        return Path.cwd() / "figure_out" / p.name
    return p


@app.command()
def hist1d(
    input: str = typer.Option(
        ..., "--input", "-i", help="Input CSV/Parquet file path."
    ),
    x: List[str] = typer.Option(
        ...,
        "--x",
        "-x",
        help=(
            "Column name(s) to plot. Repeat the flag to overlay multiple"
            " distributions: --x col1 --x col2."
        ),
    ),
    norm: bool = typer.Option(
        False,
        "--norm",
        "-n",
        help="Normalize to Yield Density (PDF) instead of raw counts.",
    ),
    project: Optional[str] = _PROJECT,
    status: Optional[str] = _STATUS,
    context: Optional[str] = _CONTEXT,
    style: Optional[str] = typer.Option(
        None, "--style", "-s", help="Optional YAML style recipe path."
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path (.pdf or .svg). Defaults to figure_out/<input>_hist1d.pdf.",
    ),
) -> None:
    """Generate a 1D histogram with smart binning and Cpk overlay."""
    try:
        df = load_data(input)
        for col in x:
            if col not in df.columns:
                typer.secho(
                    f"Error: Column '{col}' not found in input data.",
                    fg=typer.colors.RED,
                )
                sys.exit(1)

        data_arrays = [df[col].to_numpy() for col in x]
        out_path = _resolve_output(output, Path(input).stem, "hist1d")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        render_hist1d(
            data_arrays,
            column_name=list(x),
            output_path=out_path,
            norm=norm,
            project=project,
            status=status,
            context=context,
        )
        typer.secho(
            f"Successfully generated 1D histogram at {out_path}",
            fg=typer.colors.GREEN,
        )

    except Exception as e:
        typer.secho(
            f"Error generating hist1d plot: {e}", fg=typer.colors.RED
        )
        sys.exit(1)


@app.command()
def trend(
    input: str = typer.Option(
        ..., "--input", "-i", help="Input CSV/Parquet file path."
    ),
    x: str = typer.Option(
        ..., "--x", "-x", help="Column name for Time or Lot number."
    ),
    y: str = typer.Option(
        ...,
        "--y",
        "-y",
        help="Column name for the metric to plot on the Y-axis.",
    ),
    project: Optional[str] = _PROJECT,
    status: Optional[str] = _STATUS,
    context: Optional[str] = _CONTEXT,
    style: Optional[str] = typer.Option(
        None, "--style", "-s", help="Optional YAML style recipe path."
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path (.pdf or .svg). Defaults to figure_out/<input>_trend.pdf.",
    ),
) -> None:
    """Generate a Time-Series or Lot-Series trend chart with Control Limits."""
    try:
        df = load_data(input)
        for col in [x, y]:
            if col not in df.columns:
                typer.secho(
                    f"Error: Column '{col}' not found in input data.",
                    fg=typer.colors.RED,
                )
                sys.exit(1)

        x_arr = df[x].to_numpy()
        y_arr = df[y].to_numpy()
        out_path = _resolve_output(output, Path(input).stem, "trend")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        render_trend(
            x_arr,
            y_arr,
            x_name=x,
            y_name=y,
            output_path=out_path,
            project=project,
            status=status,
            context=context,
        )
        typer.secho(
            f"Successfully generated trend plot at {out_path}",
            fg=typer.colors.GREEN,
        )

    except Exception as e:
        typer.secho(
            f"Error generating trend plot: {e}", fg=typer.colors.RED
        )
        sys.exit(1)


@app.command()
def compare(
    input: str = typer.Option(
        ..., "--input", "-i", help="Input CSV/Parquet file path."
    ),
    x: str = typer.Option(
        ..., "--x", "-x", help="Column name for the shared X-axis."
    ),
    y1: str = typer.Option(
        ..., "--y1", help="Column name for the first (primary) data series."
    ),
    y2: str = typer.Option(
        ..., "--y2", help="Column name for the second (reference) data series."
    ),
    ratio_label: Optional[str] = typer.Option(
        None,
        "--ratio-label",
        help="Y-axis label for the lower ratio panel. Defaults to 'Ratio'.",
    ),
    project: Optional[str] = _PROJECT,
    status: Optional[str] = _STATUS,
    context: Optional[str] = _CONTEXT,
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path (.pdf or .svg). Defaults to figure_out/<input>_compare.pdf.",
    ),
) -> None:
    """Generate a 7:3 composite comparison chart (main panel + ratio panel).

    Both --y1 and --y2 are required. The upper panel shows both series;
    the lower panel shows y1 / y2 on a shared, pixel-aligned X-axis.
    """
    try:
        df = load_data(input)
        for col in [x, y1, y2]:
            if col not in df.columns:
                typer.secho(
                    f"Error: Column '{col}' not found in input data.",
                    fg=typer.colors.RED,
                )
                sys.exit(1)

        x_arr = df[x].to_numpy()
        y1_arr = df[y1].to_numpy()
        y2_arr = df[y2].to_numpy()

        out_path = _resolve_output(output, Path(input).stem, "compare")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        render_compare(
            x_arr,
            y1_arr,
            y2_arr,
            x_name=x,
            y1_name=y1,
            y2_name=y2,
            output_path=out_path,
            ratio_label=ratio_label or "Ratio",
            project=project,
            status=status,
            context=context,
        )
        typer.secho(
            f"Successfully generated comparison chart at {out_path}",
            fg=typer.colors.GREEN,
        )

    except Exception as e:
        typer.secho(
            f"Error generating compare plot: {e}", fg=typer.colors.RED
        )
        sys.exit(1)


if __name__ == "__main__":
    app()
