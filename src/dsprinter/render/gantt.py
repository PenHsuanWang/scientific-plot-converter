"""Gantt chart rendering for multi-channel categorical state timelines.

Provides :func:`render_gantt`, the Application-layer orchestrator for the
``dp gantt`` command, together with the domain value objects
:class:`ChannelData`, :class:`PointEvent`, :class:`DurationEvent`,
:class:`DomainPalette`, and the heuristic :class:`AggregationEngine`.
"""

import re
import warnings
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import matplotlib.dates as mdates
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
from matplotlib.axes import Axes

from dsprinter.render.engine import (
    CanvasBuilder,
    DSP_STYLE_CONTEXT,
    DSPStyleContext,
)
from dsprinter.stats.metrics import (
    compute_state_bins,
    state_distribution,
    validate_grayscale_contrast,
)

# Default DPI used for the aggregation pixel-density heuristic.
# Matches Matplotlib's default figure DPI (100) so the decision is
# consistent with what the saved file actually renders at.
_FIG_DPI: float = 100.0

_builder = CanvasBuilder(DSP_STYLE_CONTEXT)


# ── Domain value objects ───────────────────────────────────────────────────────


@dataclass(frozen=True)
class ChannelData:
    """Immutable representation of one channel's categorical state timeline.

    :param name: Display label for this channel/entity.
    :param records: Tuple of ``(start, end, state)`` half-open intervals.
    """

    name: str
    records: tuple[tuple[datetime, datetime, str], ...]


@dataclass(frozen=True)
class PointEvent:
    """Single-timestamp event rendered as a vertical dashed line.

    :param timestamp: Exact moment of the event.
    :param label: Legend label.
    :param color: Line color (default: Petroff dark red ``#bd1f01``).
    :param linestyle: Matplotlib line style (default: ``"--"``).
    """

    timestamp: datetime
    label: str
    color: str = "#bd1f01"
    linestyle: str = "--"


@dataclass(frozen=True)
class DurationEvent:
    """Time-span event rendered as a semi-transparent shaded region.

    :param start: Start of the event window.
    :param end: End of the event window.
    :param label: Legend label.
    :param color: Fill color (default: Petroff gray ``#94a4a2``).
    :param alpha: Transparency (default: 0.25).
    """

    start: datetime
    end: datetime
    label: str
    color: str = "#94a4a2"
    alpha: float = 0.25


_HEX_COLOR_RE: re.Pattern[str] = re.compile(r"^#[0-9A-Fa-f]{6}$")


class DomainPalette:
    """Domain-specific state → hex-color mapping with WCAG contrast validation.

    On construction the mapping is validated: each color must be a valid
    ``#RRGGBB`` hex string, and consecutive pairs are checked against the
    3:1 grayscale contrast threshold.  A :class:`UserWarning` is emitted for
    violations but rendering is **not** blocked.

    :param mapping: Dict mapping categorical state labels to ``#RRGGBB`` colors.
    :raises ValueError: If any color is not a valid ``#RRGGBB`` hex string.
    """

    def __init__(self, mapping: dict[str, str]) -> None:
        """Validate *mapping* and store a defensive copy."""
        for state, color in mapping.items():
            if not _HEX_COLOR_RE.match(color):
                raise ValueError(
                    f"Invalid hex color {color!r} for state {state!r}; "
                    "expected '#RRGGBB' format."
                )
        violations = validate_grayscale_contrast(list(mapping.values()))
        if violations:
            warnings.warn(
                f"Domain palette has {len(violations)} color pair(s) below the "
                f"3:1 grayscale contrast threshold: {violations}",
                UserWarning,
                stacklevel=2,
            )
        self._mapping: dict[str, str] = dict(mapping)

    def get(self, state: str, default: str = "") -> str:
        """Return the mapped color for *state*, or *default* if absent."""
        return self._mapping.get(state, default)

    def states(self) -> list[str]:
        """Return the ordered list of mapped state labels."""
        return list(self._mapping.keys())


class AggregationEngine:
    """Decides whether to aggregate Gantt intervals into fixed time buckets.

    The heuristic compares the shortest observed state duration (in pixels)
    against ``DSPStyleContext.gantt_min_px_width``.  When individual spans
    would render narrower than this threshold the engine signals that data
    should be aggregated into hourly or daily proportional bars.

    :param style: Style context supplying ``gantt_min_px_width``.
    """

    def __init__(self, style: DSPStyleContext = DSP_STYLE_CONTEXT) -> None:
        """Store the style context."""
        self._style: DSPStyleContext = style

    def should_aggregate(
        self,
        records: Sequence[tuple[datetime, datetime, str]],
        canvas_width_inches: float,
        dpi: float,
        time_range: timedelta,
    ) -> bool:
        """Return ``True`` when density-based aggregation should be applied.

        :param records: All records across all channels.
        :param canvas_width_inches: Figure width in inches.
        :param dpi: Figure DPI used for pixel calculation.
        :param time_range: Total timespan of the dataset.
        """
        if not records:
            return False
        total_secs = time_range.total_seconds()
        if total_secs <= 0:
            return False

        canvas_px = canvas_width_inches * dpi
        px_per_second = canvas_px / total_secs

        valid_durations = [
            (end - start).total_seconds()
            for start, end, _ in records
            if (end - start).total_seconds() > 0
        ]
        if not valid_durations:
            return False

        min_duration_s = min(valid_durations)
        return min_duration_s * px_per_second < self._style.gantt_min_px_width

    def get_bucket_size(self, time_range: timedelta) -> timedelta:
        """Return the aggregation bucket width appropriate for *time_range*.

        * ≤ 7 days → hourly buckets (:class:`timedelta(hours=1) <timedelta>`)
        * > 7 days → daily buckets (:class:`timedelta(days=1) <timedelta>`)
        """
        if time_range.total_seconds() <= 7 * 24 * 3600:
            return timedelta(hours=1)
        return timedelta(days=1)


# ── Private rendering helpers ─────────────────────────────────────────────────


def _render_exact(
    ax: Axes,
    channel: ChannelData,
    color_map: dict[str, str],
    legend_handles: dict[str, mpatches.Patch],
) -> None:
    """Render exact-interval broken bars for one channel panel."""
    state_xranges: defaultdict[str, list[tuple[float, float]]] = defaultdict(list)
    for start, end, state in channel.records:
        x0 = mdates.date2num(start)  # type: ignore[no-untyped-call]
        x1 = mdates.date2num(end)  # type: ignore[no-untyped-call]
        if x1 > x0:
            state_xranges[state].append((x0, x1 - x0))

    for state, xranges in state_xranges.items():
        color = color_map.get(state, "#cccccc")
        ax.broken_barh(xranges, (0.1, 0.8), facecolors=color, edgecolors="none")
        if state not in legend_handles:
            legend_handles[state] = mpatches.Patch(color=color, label=state)


def _render_aggregated(
    ax: Axes,
    channel: ChannelData,
    bucket_size: timedelta,
    time_range: tuple[datetime, datetime],
    color_map: dict[str, str],
    legend_handles: dict[str, mpatches.Patch],
) -> None:
    """Render proportional stacked bars for one channel in aggregation mode."""
    global_start, global_end = time_range
    bins = compute_state_bins(channel.records, bucket_size, time_range)

    bucket_start = global_start
    for bin_data in bins:
        bucket_end = min(bucket_start + bucket_size, global_end)
        x_left = mdates.date2num(bucket_start)  # type: ignore[no-untyped-call]
        x_right = mdates.date2num(bucket_end)  # type: ignore[no-untyped-call]
        bin_width = x_right - x_left

        cumulative = x_left
        for state, proportion in bin_data.items():
            seg_width = bin_width * proportion
            if seg_width > 0:
                color = color_map.get(state, "#cccccc")
                ax.broken_barh(
                    [(cumulative, seg_width)],
                    (0.1, 0.8),
                    facecolors=color,
                    edgecolors="none",
                )
                if state not in legend_handles:
                    legend_handles[state] = mpatches.Patch(color=color, label=state)
            cumulative += seg_width
        bucket_start = bucket_end


def _apply_axis_style(ax: Axes, channel_name: str) -> None:
    """Fix Y-axis to [0, 1], hide ticks, and label with the channel name."""
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_ylabel(
        channel_name,
        rotation=0,
        ha="right",
        va="center",
        fontsize=DSP_STYLE_CONTEXT.base_font_size,
    )


def _add_row_stats(ax: Axes, channel: ChannelData) -> None:
    """Annotate the right margin with compact per-channel statistics."""
    dist = state_distribution(channel.records)
    lines = [f"N={len(channel.records)}"]
    for state, pct in sorted(dist.items(), key=lambda kv: -kv[1])[:3]:
        lines.append(f"{state}: {pct:.0f}%")
    ax.text(
        1.01,
        0.5,
        "\n".join(lines),
        transform=ax.transAxes,
        fontsize=DSP_STYLE_CONTEXT.base_font_size - 1,
        va="center",
        ha="left",
        clip_on=False,
        family="monospace",
    )


def _apply_event_overlays(
    axes: list[Axes],
    events: list[PointEvent | DurationEvent],
    global_start: datetime,
    global_end: datetime,
) -> list[mlines.Line2D | mpatches.Patch]:
    """Draw event overlays on every panel and return legend handles."""
    handles: list[mlines.Line2D | mpatches.Patch] = []
    for ev in events:
        if isinstance(ev, PointEvent):
            if not (global_start <= ev.timestamp <= global_end):
                warnings.warn(
                    f"PointEvent '{ev.label}' at {ev.timestamp} is outside the "
                    "plotted time range and will be skipped.",
                    UserWarning,
                    stacklevel=4,
                )
                continue
            x_pos = mdates.date2num(ev.timestamp)  # type: ignore[no-untyped-call]
            for ax in axes:
                ax.axvline(
                    x_pos,
                    color=ev.color,
                    linestyle=ev.linestyle,
                    linewidth=1.2,
                    alpha=0.9,
                    zorder=10,
                )
            handles.append(
                mlines.Line2D(
                    [],
                    [],
                    color=ev.color,
                    linestyle=ev.linestyle,
                    linewidth=1.5,
                    label=ev.label,
                )
            )
        elif isinstance(ev, DurationEvent):
            if ev.end < global_start or ev.start > global_end:
                warnings.warn(
                    f"DurationEvent '{ev.label}' [{ev.start}, {ev.end}] is outside "
                    "the plotted time range and will be skipped.",
                    UserWarning,
                    stacklevel=4,
                )
                continue
            for ax in axes:
                ax.axvspan(
                    mdates.date2num(ev.start),  # type: ignore[no-untyped-call]
                    mdates.date2num(ev.end),  # type: ignore[no-untyped-call]
                    color=ev.color,
                    alpha=ev.alpha,
                    zorder=9,
                )
            handles.append(
                mpatches.Patch(color=ev.color, alpha=ev.alpha, label=ev.label)
            )
    return handles


# ── Public API ────────────────────────────────────────────────────────────────


def render_gantt(
    channels: list[ChannelData],
    output_path: str | Path,
    events: list[PointEvent | DurationEvent] | None = None,
    domain_palette: DomainPalette | None = None,
    figsize: tuple[float, float] | None = None,
    project: str | None = None,
    status: str | None = None,
    context: str | None = None,
) -> None:
    """Render and save a multi-channel categorical state Gantt chart.

    Automatically switches between **exact-interval** rendering (broken bars
    spanning precise start/end times) and **aggregated** rendering (stacked
    proportional bars per time bucket) based on the data density relative to
    the canvas resolution.  The switch is zero-config; see
    :class:`AggregationEngine` for the heuristic.

    :param channels: Ordered list of channels to plot (one panel each).
    :type channels: list[ChannelData]
    :param output_path: Destination file path; must end in ``.pdf`` or ``.svg``.
    :type output_path: str or pathlib.Path
    :param events: Optional point or duration event overlays spanning all panels.
    :type events: list[PointEvent | DurationEvent] or None
    :param domain_palette: Optional state-to-color override mapping.
    :type domain_palette: DomainPalette or None
    :param figsize: Override auto-scaled ``(width, height)`` in inches.
    :type figsize: tuple[float, float] or None
    :param project: Tier-1 brand / project tag.
    :type project: str or None
    :param status: Tier-2 status label.
    :type status: str or None
    :param context: Tier-3 context string.
    :type context: str or None
    :raises ValueError: If *channels* is empty or *output_path* has an
        unsupported extension.
    """
    if not channels:
        raise ValueError("channels must not be empty.")
    out = Path(output_path)
    if out.suffix.lower() not in {".pdf", ".svg"}:
        raise ValueError(
            f"output_path must end in '.pdf' or '.svg'; got {out.suffix!r}."
        )

    # ── 1. Collect ordered unique state labels across all channels ────────
    seen_states: list[str] = []
    for ch in channels:
        for _, _, state in ch.records:
            if state not in seen_states:
                seen_states.append(state)

    # ── 2. Build color map: domain palette overrides Petroff fallback ─────
    palette = DSP_STYLE_CONTEXT.petroff_palette
    color_map: dict[str, str] = {}
    petroff_idx = 0
    for state in seen_states:
        override = domain_palette.get(state) if domain_palette else ""
        if override:
            color_map[state] = override
        else:
            color_map[state] = palette[petroff_idx % len(palette)]
            petroff_idx += 1

    # ── 3. Compute global time range across all channels and events ───────
    all_starts: list[datetime] = []
    all_ends: list[datetime] = []
    for ch in channels:
        for start, end, _ in ch.records:
            all_starts.append(start)
            all_ends.append(end)
    if events:
        for ev in events:
            if isinstance(ev, PointEvent):
                all_starts.append(ev.timestamp)
                all_ends.append(ev.timestamp)
            else:
                all_starts.append(ev.start)
                all_ends.append(ev.end)

    if not all_starts:
        global_start = datetime.now()
        global_end = global_start + timedelta(hours=1)
    else:
        global_start = min(all_starts)
        global_end = max(all_ends)
        if global_end <= global_start:
            global_end = global_start + timedelta(hours=1)
    time_range = global_end - global_start

    # ── 4. Aggregation mode (uniform decision across all channels) ────────
    n_ch = len(channels)
    fig_h = max(4.0, 2.5 * n_ch)
    fig_size = figsize or (12.0, fig_h)

    agg_engine = AggregationEngine(DSP_STYLE_CONTEXT)
    all_records = [r for ch in channels for r in ch.records]
    use_aggregation = agg_engine.should_aggregate(
        all_records, fig_size[0], _FIG_DPI, time_range
    )
    bucket_size = (
        agg_engine.get_bucket_size(time_range) if use_aggregation else timedelta(0)
    )

    # ── 5. Build figure and populate each channel panel ───────────────────
    legend_handles: dict[str, mpatches.Patch] = {}

    with _builder.gantt_canvas(
        n_channels=n_ch,
        figsize=fig_size,
        project=project,
        status=status,
        context=context,
    ) as (fig, axes):
        _render_panels(
            channels, axes, use_aggregation, bucket_size,
            (global_start, global_end), color_map, legend_handles,
        )

        # ── X-axis: shared limits and date formatting on bottom panel ─────
        x_min = mdates.date2num(global_start)  # type: ignore[no-untyped-call]
        x_max = mdates.date2num(global_end)  # type: ignore[no-untyped-call]
        for ax in axes:
            ax.set_xlim(x_min, x_max)

        locator = mdates.AutoDateLocator()  # type: ignore[no-untyped-call]
        axes[-1].xaxis.set_major_locator(locator)
        fmt = mdates.ConciseDateFormatter(locator)  # type: ignore[no-untyped-call]
        axes[-1].xaxis.set_major_formatter(fmt)
        axes[-1].set_xlabel("Time")

        # ── Event overlays ────────────────────────────────────────────────
        event_handles = _apply_event_overlays(
            axes, events or [], global_start, global_end
        )

        # ── Unified bottom legend ─────────────────────────────────────────
        all_handles: list[Any] = list(legend_handles.values()) + list(event_handles)
        if all_handles:
            fig.legend(
                handles=all_handles,
                loc="lower center",
                ncol=min(len(all_handles), 6),
                frameon=False,
                fontsize=DSP_STYLE_CONTEXT.base_font_size,
            )

        _builder.autoadjust_xticklabels(axes[-1])
        fig.savefig(out)


def _render_panels(
    channels: list[ChannelData],
    axes: list[Axes],
    use_aggregation: bool,
    bucket_size: timedelta,
    time_range: tuple[datetime, datetime],
    color_map: dict[str, str],
    legend_handles: dict[str, mpatches.Patch],
) -> None:
    """Populate each channel panel with bars, Y-axis styling, and stats."""
    for ch, ax in zip(channels, axes):
        if not ch.records:
            ax.text(
                0.5,
                0.5,
                "No Data",
                transform=ax.transAxes,
                ha="center",
                va="center",
                fontsize=DSP_STYLE_CONTEXT.base_font_size,
                color="gray",
                style="italic",
            )
        elif use_aggregation:
            _render_aggregated(
                ax, ch, bucket_size, time_range, color_map, legend_handles
            )
        else:
            _render_exact(ax, ch, color_map, legend_handles)

        _apply_axis_style(ax, ch.name)
        _add_row_stats(ax, ch)


# Suppress unused import — Figure is referenced only in docstrings / type stubs
__all__ = [
    "AggregationEngine",
    "ChannelData",
    "DomainPalette",
    "DurationEvent",
    "PointEvent",
    "render_gantt",
]
