"""CLI entry points for dsprinter.

Defines the ``hist1d``, ``trend``, and ``compare`` commands, parses user
arguments, and delegates to the rendering pipeline.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import polars as pl
import typer

from dsprinter.data.io import load_data
from dsprinter.render.gantt import (
    ChannelData,
    DomainPalette,
    DurationEvent,
    PointEvent,
    render_gantt,
)
from dsprinter.render.plots import render_compare, render_hist1d, render_trend

app = typer.Typer(
    help=(
        "dsprinter: A standardized Python CLI utility to generate"
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


def _load_events(
    events_path: Optional[str],
) -> list[PointEvent | DurationEvent]:
    """Parse an events JSON file into a list of typed event objects.

    :param events_path: Path to the JSON file, or ``None`` to return an empty list.
    :returns: Ordered list of :class:`PointEvent` and :class:`DurationEvent` objects.
    :raises typer.Exit: On malformed JSON or unknown event ``type`` fields.
    """
    if events_path is None:
        return []
    try:
        raw = json.loads(Path(events_path).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        typer.secho(
            f"Error reading events file '{events_path}': {exc}",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    parsed: list[PointEvent | DurationEvent] = []
    for item in raw:
        kind = item.get("type", "")
        if kind == "point":
            parsed.append(
                PointEvent(
                    timestamp=_parse_dt(item["timestamp"]),
                    label=item.get("label", ""),
                    color=item.get("color", "#bd1f01"),
                    linestyle=item.get("linestyle", "--"),
                )
            )
        elif kind == "duration":
            parsed.append(
                DurationEvent(
                    start=_parse_dt(item["start"]),
                    end=_parse_dt(item["end"]),
                    label=item.get("label", ""),
                    color=item.get("color", "#94a4a2"),
                    alpha=float(item.get("alpha", 0.25)),
                )
            )
        else:
            typer.secho(
                f"Error: Unknown event type '{kind}' in '{events_path}'.",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=1)
    return parsed


def _load_domain_palette(palette_path: Optional[str]) -> Optional[DomainPalette]:
    """Parse a domain palette JSON file into a :class:`DomainPalette`.

    :param palette_path: Path to a ``{"state": "#RRGGBB", …}`` JSON file,
        or ``None`` to skip custom palette loading.
    :returns: A :class:`DomainPalette` instance, or ``None``.
    :raises typer.Exit: On malformed JSON or invalid color values.
    """
    if palette_path is None:
        return None
    try:
        mapping: dict[str, str] = json.loads(Path(palette_path).read_text())
        return DomainPalette(mapping)
    except (OSError, json.JSONDecodeError) as exc:
        typer.secho(
            f"Error reading palette file '{palette_path}': {exc}",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)
    except ValueError as exc:
        typer.secho(f"Error in palette: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


def _parse_dt(value: str) -> datetime:
    """Parse an ISO-8601 datetime string, stripping timezone info."""
    dt = datetime.fromisoformat(value)
    return dt.replace(tzinfo=None)


@app.command()
def gantt(
    input: str = typer.Option(
        ...,
        "--input",
        "-i",
        help="Input CSV file with columns: channel, timestamp, state.",
    ),
    channel_col: str = typer.Option(
        "channel",
        "--channel-col",
        help="Column name for the entity/channel identifier.",
    ),
    time_col: str = typer.Option(
        "timestamp",
        "--time-col",
        help="Column name for the event timestamp (ISO-8601 or datetime).",
    ),
    state_col: str = typer.Option(
        "state",
        "--state-col",
        help="Column name for the categorical state label.",
    ),
    events: Optional[str] = typer.Option(
        None,
        "--events",
        help=(
            "Path to a JSON file of global event overlays "
            "[{\"type\":\"point\",…},{\"type\":\"duration\",…}]."
        ),
    ),
    palette: Optional[str] = typer.Option(
        None,
        "--palette",
        help='Path to a domain palette JSON file {"state": "#RRGGBB", …}.',
    ),
    project: Optional[str] = _PROJECT,
    status: Optional[str] = _STATUS,
    context: Optional[str] = _CONTEXT,
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path (.pdf or .svg). Defaults to figure_out/<input>_gantt.pdf.",
    ),
) -> None:
    """Generate a multi-channel categorical state Gantt chart.

    Reads a state-log CSV (one row per state-entry event) and renders a
    vertically faceted Gantt chart with one panel per channel.  Automatically
    aggregates high-density data to prevent visual aliasing.
    """
    try:
        df = load_data(input)
        for col in [channel_col, time_col, state_col]:
            if col not in df.columns:
                typer.secho(
                    f"Error: Column '{col}' not found in input data.",
                    fg=typer.colors.RED,
                )
                raise typer.Exit(code=1)

        # Parse timestamps; silently skip if already datetime
        try:
            df = df.with_columns(
                pl.col(time_col).str.to_datetime(strict=False)
            )
        except Exception:
            pass  # column already datetime — no action needed

        event_list = _load_events(events)
        domain_palette = _load_domain_palette(palette)

        # ── Build ChannelData objects ──────────────────────────────────────
        channels_out: list[ChannelData] = []
        for ch_name in sorted(df[channel_col].unique().to_list()):
            ch_df = (
                df.filter(pl.col(channel_col) == ch_name)
                .sort(time_col)
            )
            ts_list: list[datetime] = ch_df[time_col].to_list()
            state_list: list[str] = ch_df[state_col].cast(pl.Utf8).to_list()

            if not ts_list:
                continue

            # Infer end times: each record ends when the next begins; last
            # record ends at max_ts + max(1 s, 1% of total span)
            global_min_ts = ts_list[0]
            global_max_ts = ts_list[-1]
            total_span = (global_max_ts - global_min_ts).total_seconds()
            tail_secs = max(1.0, total_span * 0.01)

            records: list[tuple[datetime, datetime, str]] = []
            for idx, (start_ts, state) in enumerate(zip(ts_list, state_list)):
                if idx + 1 < len(ts_list):
                    end_ts = ts_list[idx + 1]
                else:
                    end_ts = global_max_ts + timedelta(seconds=tail_secs)
                records.append((start_ts, end_ts, state))

            channels_out.append(
                ChannelData(name=str(ch_name), records=tuple(records))
            )

        if not channels_out:
            typer.secho(
                "Error: No valid channel data found in input.",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=1)

        out_path = _resolve_output(output, Path(input).stem, "gantt")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        render_gantt(
            channels=channels_out,
            output_path=out_path,
            events=event_list,
            domain_palette=domain_palette,
            project=project,
            status=status,
            context=context,
        )
        typer.secho(
            f"Successfully generated Gantt chart at {out_path}",
            fg=typer.colors.GREEN,
        )

    except typer.Exit:
        raise
    except Exception as e:
        typer.secho(f"Error generating Gantt chart: {e}", fg=typer.colors.RED)
        sys.exit(1)


if __name__ == "__main__":
    app()
