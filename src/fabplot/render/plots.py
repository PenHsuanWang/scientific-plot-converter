"""Concrete plot builders for histogram and trend chart rendering."""

from pathlib import Path

import numpy as np

from fabplot.render.engine import add_fab_header, add_stats_legend, plot_context
from fabplot.stats.metrics import calculate_metrics, calculate_smart_bins


def render_hist1d(
    data: np.ndarray,
    column_name: str,
    output_path: str | Path,
    norm: bool = False,
    metadata: dict[str, str] | None = None,
) -> None:
    """Render and save a 1D histogram with smart binning and stats.

    :param data: Raw 1D array of the metric values to plot.
    :type data: numpy.ndarray
    :param column_name: Label for the X-axis and plot title.
    :type column_name: str
    :param output_path: Destination file path (.pdf or .svg).
    :type output_path: str or pathlib.Path
    :param norm: If ``True``, normalise to Yield Density (PDF).
    :type norm: bool
    :param metadata: Key-value pairs passed to the Fab-Header block.
    :type metadata: dict[str, str] or None
    """
    valid_data = data[~np.isnan(data)]

    with plot_context() as (fig, ax):
        bins = calculate_smart_bins(valid_data)

        # Filled histogram with hatching for colour-blind accessibility
        _counts, bin_edges, _patches = ax.hist(
            valid_data, bins=bins, density=norm,
            color="lightsteelblue", edgecolor="black",
            hatch="///", alpha=0.7,
        )
        # Step outline reusing computed bin edges for exact alignment
        ax.hist(
            valid_data, bins=list(bin_edges), density=norm,
            histtype="step", color="navy", linewidth=1.5,
        )

        stats = calculate_metrics(valid_data)
        add_stats_legend(ax, stats)
        add_fab_header(ax, metadata or {})

        ax.set_xlabel(column_name)
        ax.set_ylabel("Yield Density (PDF)" if norm else "Counts")
        ax.set_title(f"Distribution Analysis: {column_name}")
        ax.grid(True)

        fig.savefig(output_path, bbox_inches="tight")


def render_trend(
    x_data: np.ndarray,
    y_data: np.ndarray,
    x_name: str,
    y_name: str,
    output_path: str | Path,
    metadata: dict[str, str] | None = None,
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
    :param metadata: Key-value pairs passed to the Fab-Header block.
    :type metadata: dict[str, str] or None
    """
    with plot_context() as (fig, ax):
        sort_idx = np.argsort(x_data)
        x_sorted = x_data[sort_idx]
        y_sorted = y_data[sort_idx]

        ax.plot(
            x_sorted, y_sorted, marker="o", linestyle="-",
            color="navy", markersize=4, alpha=0.8,
        )

        stats = calculate_metrics(y_sorted)
        mean = stats.get("mean", 0.0)
        sigma = stats.get("sigma", 0.0)

        if sigma > 0:
            ucl = mean + 3 * sigma
            lcl = mean - 3 * sigma
            ax.axhline(
                mean, color="green", linestyle="--", alpha=0.7, label="Mean"
            )
            ax.axhspan(
                lcl, ucl, color="gray", alpha=0.15,
                label=r"$\pm 3\sigma$ (Control Limits)",
            )
            ax.legend(loc="lower right", framealpha=0.9)

        add_stats_legend(ax, stats)
        add_fab_header(ax, metadata or {})

        ax.set_xlabel(x_name)
        ax.set_ylabel(y_name)
        ax.set_title(f"Trend Analysis: {y_name} over {x_name}")
        ax.grid(True)

        fig.savefig(output_path, bbox_inches="tight")
