"""Dual-panel state transition matrix heatmap rendering.

Provides :func:`render_transition`, the Application-layer orchestrator for the
``dp transition`` command, together with the domain value objects
:class:`TransitionJob` and :class:`TransitionMatrix`.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import numpy as np
import polars as pl
from matplotlib.axes import Axes
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LogNorm, Normalize
from matplotlib.figure import Figure

from dsprinter.render.engine import (
    CanvasBuilder,
    DSP_STYLE_CONTEXT,
    DSPStyleContext,
)
from dsprinter.stats.metrics import (
    cell_text_color,
    compute_transition_matrix,
    row_normalize_matrix,
)

_builder = CanvasBuilder(DSP_STYLE_CONTEXT)


# ── Domain value objects ───────────────────────────────────────────────────────


@dataclass(frozen=True)
class TransitionJob:
    """Immutable aggregate root for a single ``dp transition`` invocation.

    :param channel_col: DataFrame column identifying each independent entity.
    :param time_col: Datetime column used to establish temporal order.
    :param state_col: Categorical state label column.
    :param output: Resolved output file path.
    :param project: Tier-1 brand / project tag for three-tier typography.
    :param status: Tier-2 status label.
    :param context: Tier-3 context string.
    """

    channel_col: str = "channel"
    time_col: str = "timestamp"
    state_col: str = "state"
    output: Path = field(default_factory=lambda: Path("transition_matrix.pdf"))
    project: str | None = None
    status: str | None = None
    context: str | None = None


@dataclass
class TransitionMatrix:
    """Immutable container for the count and probability transition matrices.

    Arrays are deep-copied and made read-only in :meth:`__post_init__` to
    prevent accidental mutation after construction.  ``frozen=True`` cannot
    be used because :class:`numpy.ndarray` is not hashable; the writeable-flag
    approach provides equivalent runtime immutability.

    :param state_labels: Alphabetically ordered state category names.
    :param count_matrix: N×N int64 raw transition counts.
    :param prob_matrix: N×N float64 row-normalized conditional probabilities.
    """

    state_labels: tuple[str, ...]
    count_matrix: np.ndarray  # shape (N, N), int64
    prob_matrix: np.ndarray   # shape (N, N), float64

    def __post_init__(self) -> None:
        """Deep-copy arrays and mark them read-only."""
        self.count_matrix = self.count_matrix.copy()
        self.count_matrix.flags.writeable = False
        self.prob_matrix = self.prob_matrix.copy()
        self.prob_matrix.flags.writeable = False

    @property
    def n_states(self) -> int:
        """Number of unique state categories."""
        return len(self.state_labels)


# ── Private rendering helpers ─────────────────────────────────────────────────


def _draw_diagonal_borders(ax: Axes, n: int) -> None:
    """Overlay bold black Rectangle patches on the N diagonal cells.

    Self-transitions (Current State == Next State) receive a bold solid border
    at ``zorder=5`` so they are visually distinct from cross-category
    transitions without obscuring the underlying cell colour.

    :param ax: Target axes.
    :param n: Matrix dimension (number of state categories).
    """
    for i in range(n):
        rect = mpatches.Rectangle(
            (i - 0.5, i - 0.5), 1.0, 1.0,
            linewidth=2.5,
            edgecolor="black",
            facecolor="none",
            zorder=5,
        )
        ax.add_patch(rect)


def _annotate_cells(
    ax: Axes,
    data: np.ndarray,
    fmt: Callable[[float], str],
    mappable: ScalarMappable,
    style: DSPStyleContext,
) -> None:
    """Print formatted values in each cell with luminance-inverted text color.

    Uses :func:`~dsprinter.stats.metrics.cell_text_color` and the WCAG 2.1
    luminance formula to choose black or white text that guarantees ≥ 4.5:1
    contrast against each cell's background colour.

    :param ax: Target axes (must have already called ``imshow``).
    :param data: N×N array whose values are formatted and drawn.
    :param fmt: Format callable mapping a float to its display string.
    :param mappable: The ``AxesImage`` returned by ``imshow``; used to derive
        the background colour of each cell via :meth:`ScalarMappable.to_rgba`.
    :param style: Style context supplying the base font size.
    """
    n = data.shape[0]
    for i in range(n):
        for j in range(n):
            val = float(data[i, j])
            # to_rgba requires an array input; index [0] yields the (4,) RGBA row.
            rgba = mappable.to_rgba(np.array([val]))[0]
            # to_hex requires a plain tuple — convert explicitly for mypy.
            bg_hex = mcolors.to_hex(
                (float(rgba[0]), float(rgba[1]), float(rgba[2]), float(rgba[3]))
            )
            text_color = cell_text_color(bg_hex)
            ax.text(
                j, i, fmt(val),
                ha="center", va="center",
                color=text_color,
                fontsize=style.base_font_size,
                zorder=6,
            )


def _render_count_panel(
    ax: Axes,
    matrix: TransitionMatrix,
    style: DSPStyleContext,
    fig: Figure,
) -> None:
    """Render the left (count) heatmap panel with LogNorm and YlOrRd palette.

    Zero cells render at the colourmap minimum (pale yellow).  Counts spanning
    multiple orders of magnitude remain distinguishable because the colour
    mapping is logarithmic.

    :param ax: Target axes (left panel).
    :param matrix: Transition matrix value object.
    :param style: DSPrinter style context.
    :param fig: Parent figure (needed for ``fig.colorbar``).
    """
    labels = list(matrix.state_labels)
    n = matrix.n_states
    data = matrix.count_matrix.astype(float)

    # vmax must be > vmin=1 to avoid log(1)/log(1) = 0 division; use ≥ 2
    vmax = max(float(data.max()), 2.0)
    norm = LogNorm(vmin=1, vmax=vmax)

    im = ax.imshow(data, cmap="YlOrRd", norm=norm, aspect="auto", origin="upper")
    fig.colorbar(im, ax=ax, label="Transition Count (log scale)")

    ax.set_xticks(range(n))
    ax.set_xticklabels(labels)
    ax.set_yticks(range(n))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Next State")
    ax.set_ylabel("Current State")
    ax.set_title("TRANSITION COUNT", fontsize=style.base_font_size, pad=8)

    _draw_diagonal_borders(ax, n)
    _annotate_cells(ax, data, lambda v: f"{int(v):,}", im, style)


def _render_probability_panel(
    ax: Axes,
    matrix: TransitionMatrix,
    style: DSPStyleContext,
    fig: Figure,
) -> None:
    """Render the right (probability) heatmap panel with linear Blues palette.

    Each row sums to 1.0 (row-normalised conditional probability), so a linear
    [0, 1] colour scale faithfully represents relative likelihoods.

    :param ax: Target axes (right panel).
    :param matrix: Transition matrix value object.
    :param style: DSPrinter style context.
    :param fig: Parent figure (needed for ``fig.colorbar``).
    """
    labels = list(matrix.state_labels)
    n = matrix.n_states
    data = matrix.prob_matrix

    norm = Normalize(vmin=0.0, vmax=1.0)

    im = ax.imshow(data, cmap="Blues", norm=norm, aspect="auto", origin="upper")
    fig.colorbar(im, ax=ax, label="Transition Probability")

    ax.set_xticks(range(n))
    ax.set_xticklabels(labels)
    ax.set_yticks(range(n))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Next State")
    ax.set_title("TRANSITION PROBABILITY", fontsize=style.base_font_size, pad=8)

    _draw_diagonal_borders(ax, n)
    _annotate_cells(ax, data, lambda v: f"{v:.2f}", im, style)


# ── Public API ────────────────────────────────────────────────────────────────


def render_transition(
    df: pl.DataFrame,
    channel_col: str = "channel",
    time_col: str = "timestamp",
    state_col: str = "state",
    project: str | None = None,
    status: str | None = None,
    context: str | None = None,
    output: Path | None = None,
) -> Path:
    """Render and save a dual-panel state transition matrix heatmap.

    Computes the N×N transition count matrix and the row-normalised probability
    matrix from *df*, then renders both panels on a 14 × 7 inch canvas with the
    DSPrinter scientific style.  The left panel uses a logarithmic colour scale
    (``YlOrRd``) so rare transitions remain visible alongside dominant ones.
    The right panel uses a linear scale (``Blues``) mapping probabilities to
    [0, 1].  Diagonal cells (self-transitions) receive a bold black border on
    both panels.

    :param df: Polars DataFrame containing at minimum *channel_col*, *time_col*,
        and *state_col* columns.
    :param channel_col: Column identifying independent entities / channels.
    :param time_col: Column used for temporal sort (datetime or ISO-8601 string).
    :param state_col: Categorical state label column.
    :param project: Tier-1 brand / project tag for three-tier typography.
    :param status: Tier-2 status label.
    :param context: Tier-3 context string.
    :param output: Output file path.  When ``None``, defaults to
        ``transition_matrix.pdf`` in the current working directory.
    :returns: The resolved output path.
    :rtype: pathlib.Path
    :raises ValueError: If any required column is absent from *df*.
    """
    out: Path = output if output is not None else Path("transition_matrix.pdf")
    out.parent.mkdir(parents=True, exist_ok=True)

    count_matrix, state_labels = compute_transition_matrix(
        df, channel_col, time_col, state_col
    )
    prob_matrix = row_normalize_matrix(count_matrix)
    matrix = TransitionMatrix(
        state_labels=tuple(state_labels),
        count_matrix=count_matrix,
        prob_matrix=prob_matrix,
    )

    with _builder.transition_canvas(
        project=project, status=status, context=context
    ) as (fig, ax_count, ax_prob):
        _render_count_panel(ax_count, matrix, DSP_STYLE_CONTEXT, fig)
        _render_probability_panel(ax_prob, matrix, DSP_STYLE_CONTEXT, fig)
        _builder.autoadjust_xticklabels(ax_count)
        _builder.autoadjust_xticklabels(ax_prob)
        fig.savefig(out)

    return out


__all__ = [
    "TransitionJob",
    "TransitionMatrix",
    "render_transition",
]
