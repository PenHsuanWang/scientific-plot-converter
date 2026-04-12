"""Matplotlib rendering engine enforcing the CERN-style scientific layout."""

from contextlib import contextmanager
from typing import Generator

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

FAB_STYLE = {
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 12,
    "savefig.format": "pdf",
    "pdf.fonttype": 42,  # TrueType vector fonts
    "svg.fonttype": "none",
    "axes.linewidth": 1.2,
    "lines.linewidth": 1.5,
    "grid.alpha": 0.5,
    "grid.linestyle": "--",
}


def setup_scientific_style() -> None:
    """Apply global CERN-Style matplotlib settings.

    Locks typography to 10pt/12pt Arial/Helvetica and ensures
    vector-safe output parameters.
    """
    mpl.rcParams.update(FAB_STYLE)


@contextmanager
def plot_context(
    figsize: tuple[float, float] = (8, 6),
) -> Generator[tuple[Figure, Axes], None, None]:
    """Create a figure and axes with scientific style enforced.

    :param figsize: Width and height of the figure in inches.
    :type figsize: tuple[float, float]
    :returns: A ``(Figure, Axes)`` tuple for plot construction.
    :rtype: tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]
    """
    setup_scientific_style()
    fig, ax = plt.subplots(figsize=figsize)
    try:
        yield fig, ax
    finally:
        plt.close(fig)


def add_fab_header(
    ax: Axes, metadata: dict[str, str], status: str = "INTERNAL ONLY"
) -> None:
    """Add the Top-Left Status and Top-Right Metadata blocks to the axes.

    :param ax: The matplotlib Axes instance to annotate.
    :type ax: matplotlib.axes.Axes
    :param metadata: Key-value pairs rendered as the top-right header.
    :type metadata: dict[str, str]
    :param status: Status label placed in the top-left corner.
    :type status: str
    """
    ax.text(
        0.01, 1.02, status, transform=ax.transAxes,
        fontsize=10, fontweight="bold", va="bottom", ha="left",
    )
    if metadata:
        meta_str = " | ".join(f"{k}: {v}" for k, v in metadata.items())
        ax.text(
            0.99, 1.02, meta_str, transform=ax.transAxes,
            fontsize=9, va="bottom", ha="right", color="dimgray",
        )


def add_stats_legend(ax: Axes, stats: dict[str, float]) -> None:
    """Add a non-obtrusive stats legend box (N, μ, σ, Cpk) to the axes.

    :param ax: The matplotlib Axes instance to annotate.
    :type ax: matplotlib.axes.Axes
    :param stats: Dictionary with keys ``n``, ``mean``, ``sigma``,
        and optionally ``cpk``.
    :type stats: dict[str, float]
    """
    textstr = "\n".join([
        f"$N$ = {int(stats.get('n', 0.0))}",
        f"$\\mu$ = {stats.get('mean', 0.0):.4g}",
        f"$\\sigma$ = {stats.get('sigma', 0.0):.4g}",
    ])
    if "cpk" in stats:
        textstr += f"\n$C_{{pk}}$ = {stats['cpk']:.2f}"

    props = dict(boxstyle="round", facecolor="white", alpha=0.8, edgecolor="gray")
    ax.text(
        0.95, 0.95, textstr, transform=ax.transAxes, fontsize=10,
        verticalalignment="top", horizontalalignment="right", bbox=props,
    )
