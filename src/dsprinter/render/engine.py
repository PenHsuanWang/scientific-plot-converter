"""Matplotlib rendering engine enforcing the scientific layout standard.

Implements the ``DSPStyleContext`` value object and ``CanvasBuilder`` class
that together enforce the three-tier typography hierarchy, golden margin
layout, four-sided mirror ticks, and the Petroff-compliant color palette
across all DSPrinter output.
"""

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Final, Generator

import matplotlib as mpl
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
from cycler import cycler as make_cycler
from matplotlib.axes import Axes
from matplotlib.figure import Figure


@dataclass(frozen=True)
class DSPStyleContext:
    """Immutable value object holding all DSPrinter styling constants.

    All fields are frozen at class definition. Changing any constant
    requires a versioned library release — runtime mutation is prohibited
    by the ``frozen=True`` constraint.
    """

    # ── Typography ────────────────────────────────────────────────────────
    font_family: tuple[str, ...] = ("Arial", "Helvetica", "DejaVu Sans")
    # base_font_size (10 pt) → tick labels, legend text, stats box.
    # title_font_size (12 pt) → X/Y axis label titles AND plot title
    #   (≈ CMS/HEP 5 % canvas-height rule for axis titles; 4 % for tick labels).
    base_font_size: float = 10.0
    title_font_size: float = 12.0
    # Three-tier annotation base (Tier-1 = 1.0 ×, i.e. 14 pt).
    # Tier-3 at 60 % → 8.4 pt, above the 8 pt legibility floor.
    annotation_font_size: float = 14.0

    # Three-tier size ratios (locked — do not override)
    tier1_size_ratio: float = 1.00   # Bold  — brand / project tag
    tier2_size_ratio: float = 0.77   # Italic — status tag (75–80 %)
    tier3_size_ratio: float = 0.60   # Regular — context info

    # ── Golden margins (fraction of figure size) ──────────────────────────
    margin_left: float = 0.15
    margin_right: float = 0.05   # right plot edge at 1 − 0.05 = 0.95
    margin_top: float = 0.09     # top plot edge at  1 − 0.09 = 0.91
    margin_bottom: float = 0.12

    # ── Petroff-compliant color palette ───────────────────────────────────
    petroff_palette: tuple[str, ...] = (
        "#3f90da",  # dark blue  (primary)
        "#ffa90e",  # orange
        "#bd1f01",  # dark red
        "#94a4a2",  # gray
        "#832db6",  # purple
        "#a96b59",  # brown
        "#e76300",  # dark orange
        "#b9ac70",  # tan
        "#717581",  # dark gray
        "#92dadd",  # light blue
    )

    # ── Axis styling ──────────────────────────────────────────────────────
    tick_direction: str = "in"
    # X-axis title pad: 1.1 × base_font_size (= 11 pt).
    # Y-axis title pad: 1.4 × base_font_size (= 14 pt) — extra room for
    # scientific-notation exponents (e.g., ×10³) that sit outside tick labels.
    axis_x_label_pad: float = 11.0
    axis_y_label_pad: float = 14.0

    # ── Tick label overflow guard ──────────────────────────────────────────
    # X-axis labels longer than this (chars) trigger 45° auto-rotation,
    # preventing datetime strings and other long tokens from crowding.
    tick_label_rotation_threshold: int = 6
    tick_label_max_rotation: float = 45.0


#: Module-level singleton — the one authoritative style instance.
DSP_STYLE_CONTEXT: Final[DSPStyleContext] = DSPStyleContext()


class CanvasBuilder:
    """Applies ``DSPStyleContext`` rules to Matplotlib figures.

    Responsible for:

    * Activating the Petroff color cycle and locked typography via
      ``rcParams``.
    * Applying the golden margin ratios via ``fig.subplots_adjust``.
    * Configuring four-sided, inward mirror ticks and axis label padding.
    * Rendering the three-tier typography annotation layer.
    * Providing context managers for single-panel and 7:3 composite
      figure layouts.
    """

    def __init__(self, style: DSPStyleContext = DSP_STYLE_CONTEXT) -> None:
        """Initialise the builder with the given style context."""
        self._style = style

    # ── Private helpers ───────────────────────────────────────────────────

    def _apply_global_style(self) -> None:
        """Push locked rcParams: Petroff cycle, fonts, vector output."""
        s = self._style
        mpl.rcParams.update({
            "font.family": "sans-serif",
            "font.sans-serif": list(s.font_family),
            # Global fallback; overridden by the specific keys below.
            "font.size": s.base_font_size,
            # Plot title above the axes frame — 12 pt (≈ CMS 5 %).
            "axes.titlesize": s.title_font_size,
            "axes.titleweight": "normal",    # Regular; Bold reserved for Tier-1
            # X/Y axis label titles — 12 pt (≈ CMS 5 %).
            "axes.labelsize": s.title_font_size,
            "axes.labelweight": "normal",    # Regular; Bold reserved for Tier-1
            # Tick mark numbers — 10 pt (≈ CMS 4 %).
            "xtick.labelsize": s.base_font_size,
            "ytick.labelsize": s.base_font_size,
            # Legend and figure title — 10 pt / Regular.
            "legend.fontsize": s.base_font_size,
            "figure.titlesize": s.title_font_size,
            "figure.titleweight": "normal",  # Regular; Bold reserved for Tier-1
            "axes.prop_cycle": make_cycler(color=list(s.petroff_palette)),
            "axes.linewidth": 1.2,
            "lines.linewidth": 1.5,
            "grid.alpha": 0.4,
            "grid.linestyle": "--",
            "savefig.format": "pdf",
            "pdf.fonttype": 42,    # TrueType — vector-safe
            "svg.fonttype": "none",
            "legend.frameon": False,
        })

    def _apply_margins(self, fig: Figure, hspace: float = 0.0) -> None:
        """Set golden margin ratios on the figure via ``subplots_adjust``."""
        s = self._style
        fig.subplots_adjust(
            left=s.margin_left,
            right=1.0 - s.margin_right,
            bottom=s.margin_bottom,
            top=1.0 - s.margin_top,
            hspace=hspace,
        )

    def _apply_axis_styling(self, ax: Axes) -> None:
        """Enable four-sided inward mirror ticks and pad axis titles."""
        s = self._style
        ax.tick_params(
            which="both",
            direction=s.tick_direction,
            top=True, right=True, bottom=True, left=True,
        )
        ax.xaxis.labelpad = s.axis_x_label_pad
        ax.yaxis.labelpad = s.axis_y_label_pad

    # ── Public API ────────────────────────────────────────────────────────

    def autoadjust_xticklabels(self, ax: Axes) -> None:
        """Rotate X-axis tick labels when they would overlap or are too long.

        Triggers a canvas draw to finalise tick positions, then checks
        two conditions — bounding-box overlap between adjacent labels and
        label character count — and rotates all X-tick labels to
        ``tick_label_max_rotation`` degrees (right-aligned) when either
        condition is met.  Y-axis labels are never modified.

        Call this method after all plot data and axis limits have been set,
        immediately before ``fig.savefig()``.

        :param ax: The axes whose X tick labels to inspect and adjust.
        :type ax: matplotlib.axes.Axes
        """
        fig = ax.get_figure()
        if fig is None:
            return

        fig.canvas.draw()   # finalise tick label text and pixel positions

        labels = [lbl for lbl in ax.get_xticklabels() if lbl.get_text()]
        if len(labels) < 2:
            return

        s = self._style
        max_chars = max(len(lbl.get_text()) for lbl in labels)

        bboxes = [lbl.get_window_extent() for lbl in labels]
        overlapping = any(
            bboxes[i].x1 > bboxes[i + 1].x0
            for i in range(len(bboxes) - 1)
        )

        if overlapping or max_chars > s.tick_label_rotation_threshold:
            plt.setp(labels, rotation=s.tick_label_max_rotation, ha="right")

    def add_three_tier_typography(
        self,
        fig: Figure,
        project: str | None = None,
        status: str | None = None,
        context: str | None = None,
    ) -> None:
        """Render the three-tier annotation layer in the reserved top margin.

        * **Tier 1** (Bold, top-left): brand / project identifier.
        * **Tier 2** (Italic, ~77 % size, same line): data status tag.
        * **Tier 3** (Regular, ~60 % size, top-right): context metadata.

        :param fig: The figure to annotate.
        :param project: Tier-1 brand or project name.
        :param status: Tier-2 status label (e.g. ``"Internal Use Only"``).
        :param context: Tier-3 context string (e.g. ``"2024-Q3 | N=1000"``).
        """
        s = self._style
        tier1_fs = s.annotation_font_size * s.tier1_size_ratio
        tier2_fs = s.annotation_font_size * s.tier2_size_ratio
        tier3_fs = s.annotation_font_size * s.tier3_size_ratio

        # Vertical centre of the reserved top margin in figure coordinates
        y_mid = 1.0 - s.margin_top / 2.0
        x_left = s.margin_left
        x_right = 1.0 - s.margin_right

        if project:
            t1 = fig.text(
                x_left, y_mid, project,
                fontsize=tier1_fs, fontweight="bold",
                ha="left", va="center",
            )
            if status:
                # Draw to resolve font metrics, then measure Tier-1 right edge
                fig.canvas.draw()
                renderer = fig.canvas.get_renderer()  # type: ignore[attr-defined]
                bb = t1.get_window_extent(renderer=renderer)
                bb_fig = bb.transformed(fig.transFigure.inverted())
                fig.text(
                    bb_fig.x1 + 0.008, y_mid, status,
                    fontsize=tier2_fs, fontstyle="italic",
                    ha="left", va="center", color="dimgray",
                )

        if context:
            fig.text(
                x_right, y_mid, context,
                fontsize=tier3_fs, fontweight="normal",
                ha="right", va="center", color="dimgray",
            )

    @contextmanager
    def single_canvas(
        self,
        figsize: tuple[float, float] = (8, 6),
        project: str | None = None,
        status: str | None = None,
        context: str | None = None,
    ) -> Generator[tuple[Figure, Axes], None, None]:
        """Yield a single-panel figure with golden margins and mirror ticks.

        :param figsize: Figure width and height in inches.
        :param project: Tier-1 brand / project tag.
        :param status: Tier-2 status label.
        :param context: Tier-3 context string.
        :yields: ``(Figure, Axes)`` ready for plot construction.
        """
        self._apply_global_style()
        fig, ax = plt.subplots(figsize=figsize)
        self._apply_margins(fig)
        self._apply_axis_styling(ax)
        # Annotations must be added BEFORE yield so that fig.savefig() called
        # inside the `with` block captures them.  The canvas.draw() inside
        # add_three_tier_typography uses the renderer on the (already-margined)
        # empty axes to measure Tier-1 text width — this is correct and safe.
        self.add_three_tier_typography(fig, project, status, context)
        try:
            yield fig, ax
        finally:
            plt.close(fig)

    @contextmanager
    def composite_canvas(
        self,
        figsize: tuple[float, float] = (8, 9),
        project: str | None = None,
        status: str | None = None,
        context: str | None = None,
    ) -> Generator[tuple[Figure, Axes, Axes], None, None]:
        """Yield a 7:3 two-panel composite figure with a shared X-axis.

        The upper axes occupies 70 % of the plot area height; the lower
        axes occupies the remaining 30 %.  The shared X-axis ensures
        pixel-perfect horizontal alignment.  Upper panel X-tick labels
        are hidden so the two panels appear visually fused.

        :param figsize: Figure width and height in inches.
        :param project: Tier-1 brand / project tag.
        :param status: Tier-2 status label.
        :param context: Tier-3 context string.
        :yields: ``(Figure, ax_main, ax_ratio)`` ready for plot construction.
        """
        self._apply_global_style()
        fig = plt.figure(figsize=figsize)
        gs = gridspec.GridSpec(
            2, 1, height_ratios=[7, 3], hspace=0, figure=fig
        )
        ax_main = fig.add_subplot(gs[0])
        ax_ratio = fig.add_subplot(gs[1], sharex=ax_main)

        self._apply_margins(fig, hspace=0.0)
        self._apply_axis_styling(ax_main)
        self._apply_axis_styling(ax_ratio)

        # Fuse panels: hide upper X-tick labels, keep tick lines
        ax_main.tick_params(labelbottom=False)

        # Annotations before yield — same reason as single_canvas.
        self.add_three_tier_typography(fig, project, status, context)
        try:
            yield fig, ax_main, ax_ratio
        finally:
            plt.close(fig)


def add_stats_legend(ax: Axes, stats: dict[str, float]) -> None:
    """Add a frameless stats legend box (N, μ, σ, Cpk) to the axes.

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
        0.97, 0.97, textstr, transform=ax.transAxes,
        fontsize=DSP_STYLE_CONTEXT.base_font_size,
        verticalalignment="top", horizontalalignment="right", bbox=props,
    )
