"""CLI entry points for FabPlot-CLI.

Defines the ``hist1d`` and ``trend`` commands, parses user arguments,
and delegates to the rendering pipeline.
"""

import sys
from pathlib import Path
from typing import Optional

import typer

from fabplot.data.io import load_data
from fabplot.render.plots import render_hist1d, render_trend

app = typer.Typer(
    help=(
        "FabPlot-CLI: A standardized Python CLI utility to generate"
        " 'Scientific-Grade' semiconductor visualizations."
    ),
    add_completion=False,
)


@app.command()
def hist1d(
    input: str = typer.Option(
        ..., "--input", "-i", help="Input CSV/Parquet file path."
    ),
    x: str = typer.Option(
        ..., "--x", "-x", help="Column name to plot on the X-axis."
    ),
    norm: bool = typer.Option(
        False,
        "--norm",
        "-n",
        help="Normalize to Yield Density (PDF) instead of raw counts.",
    ),
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
        if x not in df.columns:
            typer.secho(
                f"Error: Column '{x}' not found in input data.",
                fg=typer.colors.RED,
            )
            sys.exit(1)

        data_arr = df[x].to_numpy()
        out_path = (
            Path(output)
            if output
            else Path.cwd() / "figure_out" / (Path(input).stem + "_hist1d.pdf")
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        metadata = {"File": Path(input).name, "N_Records": str(len(df))}

        render_hist1d(
            data_arr,
            column_name=x,
            output_path=out_path,
            norm=norm,
            metadata=metadata,
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
        out_path = (
            Path(output)
            if output
            else Path.cwd() / "figure_out" / (Path(input).stem + "_trend.pdf")
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        metadata = {"File": Path(input).name, "N_Records": str(len(df))}

        render_trend(
            x_arr,
            y_arr,
            x_name=x,
            y_name=y,
            output_path=out_path,
            metadata=metadata,
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


if __name__ == "__main__":
    app()
