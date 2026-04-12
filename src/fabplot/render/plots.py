"""Concrete plot builders for histogram, trend, and compare chart rendering."""

from pathlib import Path

import numpy as np

from fabplot.render.engine import (
    CanvasBuilder,
    FAB_STYLE_CONTEXT,
    add_stats_legend,
)
from fabplot.stats.metrics import (
    calculate_metrics,
    calculate_ratio,
    calculate_smart_bins,
)

_builder = CanvasBuilder(FAB_STYLE_CONTEXT)


def render_hist1d(
    data: np.ndarray,
    column_name: str,
    output_path: str | Path,
    norm: bool = False,
    metadata: dict[str, str] | None = None,
    project: str | None = None,
    status: str | None = None,
    context: str | None = None,
) -> None:
    """Render and save a 1D histogram with smart binning and stats overlay.

    :param data: Raw 1D array of the metric values to plot.
    :type data: numpy.ndarray
    :param column_name: Label for the X-axis and plot title.
    :type column_name: str
    :param output_path: Destination file path (.pdf or .svg).
    :type output_path: str or pathlib.Path
    :param norm: If ``True``, normalise to Yield Density (PDF).
    :type norm: bool
    :param metadata: Deprecated key-value pairs (ignored; use ``context``).
    :type metadata: dict[str, str] or None
    :param project: Tier-1 brand / project tag (top-left, bold).
    :type project: str or None
    :param status: Tier-2 status label (italic, 77 % size).
    :type status: str or None
    :param context: Tier-3 context string (top-right, 60 % size).
    :type context: str or None
    """
    valid_data = data[~np.isnan(data)]
    palette = FAB_STYLE_CONTEXT.petroff_palette

    with _builder.single_canvas(
        project=project, status=status, context=context
    ) as (fig, ax):
        bins = calculate_smart_bins(valid_data)

        ax.hist(
            valid_data, bins=bins, density=norm,
            color=palette[0], edgecolor="black",
            hatch="///", alpha=0.7,
        )
        ax.hist(
            valid_data, bins=bins, density=norm,
            histtype="step", color=palette[0], linewidth=1.5,
        )

        stats = calculate_metrics(valid_data)
        add_stats_legend(ax, stats)

        ax.set_xlabel(f"{column_name}")
        ax.set_ylabel("Yield Density (PDF)" if norm else "Counts")
        ax.set_title(f"Distribution Analysis: {column_name}")
        ax.grid(True)

        fig.savefig(output_path)


def render_trend(
    x_data: np.ndarray,
    y_data: np.ndarray,
    x_name: str,
    y_name: str,
    output_path: str | Path,
    metadata: dict[str, str] | None = None,
    project: str | None = None,
    status: str | None = None,
    context: str | None = None,
) -> None:
    """Render and save a trend chart with UCL/LCL control limits.

    :param x_data: Array of time or lot-number values for the X-axis.
    :type x_data: numpy.ndarray
    :param y_data: Array of metric values for the Y-axis.
    :type y_data: numpy.ndarray
    :param x_name: Label for the X-axis.
    :type x_name: str
    :param y_name: Label for the Y-axis and plot title.
    :type y_name: str
    :param output_path: Destination file path (.pdf or .svg).
    :type output_path: str or pathlib.Path
    :param metadata: Deprecated key-value pairs (ignored; use ``context``).
    :type metadata: dict[str, str] or None
    :param project: Tier-1 brand / project tag (top-left, bold).
    :type project: str or None
    :param status: Tier-2 status label (italic, 77 % size).
    :type status: str or None
    :param context: Tier-3 context string (top-right, 60 % size).
    :type context: str or None
    """
    palette = FAB_STYLE_CONTEXT.petroff_palette

    with _builder.single_canvas(
        project=project, status=status, context=context
    ) as (fig, ax):
        sort_idx = np.argsort(x_data)
        x_sorted = x_data[sort_idx]
        y_sorted = y_data[sort_idx]

        ax.plot(
            x_sorted, y_sorted, marker="o", linestyle="-",
            color=palette[0], markersize=4, alpha=0.8,
        )

        stats = calculate_metrics(y_sorted)
        mean = stats.get("mean", 0.0)
        sigma = stats.get("sigma", 0.0)

        if sigma > 0:
            ucl = mean + 3 * sigma
            lcl = mean - 3 * sigma
            ax.axhline(mean, color=palette[2], linestyle="--", alpha=0.7, label="Mean")
            ax.axhspan(
                lcl, ucl, color=palette[3], alpha=0.15,
                label=r"$\pm 3\sigma$ (Control Limits)",
            )
            ax.legend(loc="lower right")

        add_stats_legend(ax, stats)

        ax.set_xlabel(x_name)
        ax.set_ylabel(y_name)
        ax.set_title(f"Trend Analysis: {y_name} over {x_name}")
        ax.grid(True)

        fig.savefig(output_path)


def render_compare(
    x_data: np.ndarray,
    y1_data: np.ndarray,
    y2_data: np.ndarray,
    x_name: str,
    y1_name: str,
    y2_name: str,
    output_path: str | Path,
    ratio_label: str = "Ratio",
    project: str | None = None,
    status: str | None = None,
    context: str | None = None,
) -> None:
    """Render and save a 7:3 composite comparison chart.

    The main (upper) panel shows both series.  The lower ratio panel
    shows ``y1 / y2`` aligned to the same X-axis.

    :param x_data: Shared X-axis values.
    :type x_data: numpy.ndarray
    :param y1_data: First data series (numerator of ratio).
    :type y1_data: numpy.ndarray
    :param y2_data: Second data series (denominator of ratio).
    :type y2_data: numpy.ndarray
    :param x_name: X-axis label.
    :type x_name: str
    :param y1_name: Legend label for the first series.
    :type y1_name: str
    :param y2_name: Legend label for the second series.
    :type y2_name: str
    :param output_path: Destination file path (.pdf or .svg).
    :type output_path: str or pathlib.Path
    :param ratio_label: Y-axis label for the lower ratio panel.
    :type ratio_label: str
    :param project: Tier-1 brand / project tag (top-left, bold).
    :type project: str or None
    :param status: Tier-2 status label (italic, 77 % size).
    :type status: str or None
    :param context: Tier-3 context string (top-right, 60 % size).
    :type context: str or None
    """
    palette = FAB_STYLE_CONTEXT.petroff_palette
    sort_idx = np.argsort(x_data)
    x_s = x_data[sort_idx]
    y1_s = y1_data[sort_idx]
    y2_s = y2_data[sort_idx]
    ratio = calculate_ratio(y1_s, y2_s)

    with _builder.composite_canvas(
        project=project, status=status, context=context
    ) as (fig, ax_main, ax_ratio):
        # ── Upper panel: both data series ─────────────────────────────
        ax_main.plot(
            x_s, y1_s, marker="o", linestyle="-",
            color=palette[0], markersize=4, alpha=0.85, label=y1_name,
        )
        ax_main.plot(
            x_s, y2_s, marker="s", linestyle="--",
            color=palette[1], markersize=4, alpha=0.85, label=y2_name,
        )
        ax_main.legend(loc="best")
        ax_main.set_ylabel("Value")
        ax_main.set_title(f"Comparison: {y1_name} vs {y2_name}")
        ax_main.grid(True)
        add_stats_legend(ax_main, calculate_metrics(y1_s))

        # ── Lower panel: ratio ────────────────────────────────────────
        ax_ratio.plot(
            x_s, ratio, marker=".", linestyle="-",
            color=palette[2], markersize=3, alpha=0.85,
        )
        ax_ratio.axhline(
            1.0, color=palette[3], linestyle="--", linewidth=1.0, alpha=0.8
        )
        ax_ratio.set_xlabel(x_name)
        ax_ratio.set_ylabel(ratio_label)
        ax_ratio.grid(True)

        fig.savefig(output_path)
