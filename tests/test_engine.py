"""Tests for dsprinter.render.engine — CanvasBuilder, DSPStyleContext, helpers."""

import matplotlib
matplotlib.use("Agg")  # noqa: E402 — must be set before any other mpl import

import matplotlib.pyplot as plt  # noqa: E402
import pytest  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402

from dsprinter.render.engine import (  # noqa: E402
    DSP_STYLE_CONTEXT,
    CanvasBuilder,
    DSPStyleContext,
    add_stats_legend,
)


# ── DSPStyleContext value-object tests ────────────────────────────────────────


def test_fab_style_context_is_frozen():
    """Mutations on the frozen dataclass must raise AttributeError."""
    with pytest.raises((AttributeError, TypeError)):
        DSP_STYLE_CONTEXT.margin_left = 0.99  # type: ignore[misc]


def test_fab_style_context_tier_size_ratios_within_spec():
    """Tier-2 must be 75–80 % of Tier-1; Tier-3 must be ~60 %."""
    ctx = DSPStyleContext()
    assert 0.75 <= ctx.tier2_size_ratio <= 0.80
    assert ctx.tier3_size_ratio == pytest.approx(0.60, abs=0.01)


def test_fab_style_context_golden_margins():
    """Margin constants must match the layout specification exactly."""
    ctx = DSPStyleContext()
    assert ctx.margin_left == pytest.approx(0.15)
    assert ctx.margin_right == pytest.approx(0.05)
    assert 0.08 <= ctx.margin_top <= 0.10
    assert ctx.margin_bottom == pytest.approx(0.12)


def test_fab_style_context_petroff_palette_length():
    """Petroff palette must have exactly 10 entries."""
    assert len(DSP_STYLE_CONTEXT.petroff_palette) == 10


def test_fab_style_context_petroff_no_pure_red_or_green_at_front():
    """Primary slots must not be pure #ff0000 or #00ff00."""
    c1, c2 = DSP_STYLE_CONTEXT.petroff_palette[:2]
    assert c1.lower() not in ("#ff0000", "#00ff00")
    assert c2.lower() not in ("#ff0000", "#00ff00")


def test_fab_style_context_tick_direction_is_inward():
    """Tick direction must be 'in' to produce four-sided mirror ticks."""
    assert DSP_STYLE_CONTEXT.tick_direction == "in"


def test_fab_style_context_axis_label_pads_differentiated():
    """Y-axis label pad must be larger than X to accommodate sci-notation exponents."""
    ctx = DSPStyleContext()
    # X: 1.1 × base (11 pt); Y: 1.4 × base (14 pt)
    assert ctx.axis_x_label_pad == pytest.approx(11.0)
    assert ctx.axis_y_label_pad == pytest.approx(14.0)
    assert ctx.axis_y_label_pad > ctx.axis_x_label_pad


def test_single_canvas_applies_differentiated_axis_pads():
    """Axes must use separate x/y label pads after single_canvas setup."""
    builder = CanvasBuilder()
    s = builder._style
    with builder.single_canvas() as (fig, ax):
        assert ax.xaxis.labelpad == pytest.approx(s.axis_x_label_pad)
        assert ax.yaxis.labelpad == pytest.approx(s.axis_y_label_pad)


def test_fab_style_context_font_family_contains_standard_fonts():
    """Font family tuple must include at least one standard sans-serif font."""
    fonts = {f.lower() for f in DSP_STYLE_CONTEXT.font_family}
    assert fonts & {"arial", "helvetica", "dejavu sans"}


def test_fab_style_context_singleton_is_same_instance():
    """DSP_STYLE_CONTEXT must be the module-level singleton."""
    from dsprinter.render.engine import DSP_STYLE_CONTEXT as ctx2
    assert DSP_STYLE_CONTEXT is ctx2


def test_fab_style_context_axis_label_size_larger_than_tick_size():
    """Axis label size (12 pt) must exceed tick label size (10 pt) per US-2.6."""
    ctx = DSPStyleContext()
    assert ctx.title_font_size > ctx.base_font_size


# ── CanvasBuilder rcParam enforcement ────────────────────────────────────────


def test_global_style_axis_label_size_is_title_font_size():
    """axes.labelsize (X/Y axis titles) must be title_font_size (12 pt), not base."""
    builder = CanvasBuilder()
    with builder.single_canvas() as (fig, ax):
        import matplotlib as _mpl
        assert _mpl.rcParams["axes.labelsize"] == pytest.approx(
            builder._style.title_font_size
        )


def test_global_style_tick_label_size_is_base_font_size():
    """xtick.labelsize and ytick.labelsize must be base_font_size (10 pt)."""
    builder = CanvasBuilder()
    with builder.single_canvas() as (fig, ax):
        import matplotlib as _mpl
        assert _mpl.rcParams["xtick.labelsize"] == pytest.approx(
            builder._style.base_font_size
        )
        assert _mpl.rcParams["ytick.labelsize"] == pytest.approx(
            builder._style.base_font_size
        )


def test_global_style_axis_label_weight_is_regular():
    """Axis label and title weights must be 'normal' — Bold is exclusive to Tier-1."""
    builder = CanvasBuilder()
    with builder.single_canvas() as (fig, ax):
        import matplotlib as _mpl
        assert _mpl.rcParams["axes.labelweight"] == "normal"
        assert _mpl.rcParams["axes.titleweight"] == "normal"


# ── CanvasBuilder — single_canvas ─────────────────────────────────────────────


def test_single_canvas_yields_figure_and_axes():
    """single_canvas must yield a (Figure, Axes) tuple."""
    builder = CanvasBuilder()
    with builder.single_canvas() as (fig, ax):
        assert isinstance(fig, plt.Figure)
        assert hasattr(ax, "plot")


def test_single_canvas_axes_has_inward_ticks():
    """After entering single_canvas the axes tick direction must be 'in'."""
    builder = CanvasBuilder()
    with builder.single_canvas() as (fig, ax):
        params = ax.yaxis.get_tick_params(which="major")
        assert params.get("direction") == "in"


def test_single_canvas_margins_are_applied():
    """subplots_adjust must reflect the golden-margin constants."""
    builder = CanvasBuilder()
    s = builder._style
    with builder.single_canvas() as (fig, ax):
        sp = fig.subplotpars
        assert sp.left == pytest.approx(s.margin_left, abs=0.001)
        assert sp.right == pytest.approx(1.0 - s.margin_right, abs=0.001)
        assert sp.bottom == pytest.approx(s.margin_bottom, abs=0.001)
        assert sp.top == pytest.approx(1.0 - s.margin_top, abs=0.001)


def test_single_canvas_figure_is_closed_after_context():
    """Figure must be closed (not leaked) after exiting single_canvas."""
    builder = CanvasBuilder()
    captured = {}
    with builder.single_canvas() as (fig, ax):
        captured["fig"] = fig
    assert not plt.fignum_exists(captured["fig"].number)


# ── CanvasBuilder — composite_canvas ─────────────────────────────────────────


def test_composite_canvas_yields_figure_and_two_axes():
    """composite_canvas must yield (Figure, ax_main, ax_ratio)."""
    builder = CanvasBuilder()
    with builder.composite_canvas() as (fig, ax_main, ax_ratio):
        assert isinstance(fig, plt.Figure)
        assert ax_main is not ax_ratio


def test_composite_canvas_upper_x_labels_hidden():
    """Upper panel X-tick labels must be hidden (labelbottom=False)."""
    builder = CanvasBuilder()
    with builder.composite_canvas() as (fig, ax_main, ax_ratio):
        params = ax_main.xaxis.get_tick_params(which="major")
        assert params.get("labelbottom") is False


def test_composite_canvas_figure_is_closed_after_context():
    """Figure must be closed after exiting composite_canvas."""
    builder = CanvasBuilder()
    captured = {}
    with builder.composite_canvas() as (fig, ax_main, ax_ratio):
        captured["fig"] = fig
    assert not plt.fignum_exists(captured["fig"].number)


# ── Three-tier typography — before-yield placement (Bug 2 regression) ─────────


def test_single_canvas_all_three_tiers_present_before_savefig():
    """All three annotation tiers must be in fig.texts BEFORE savefig.

    Regression: previously add_three_tier_typography() was called in the
    ``finally`` block, which runs AFTER fig.savefig() inside the ``with``.
    """
    builder = CanvasBuilder()
    with builder.single_canvas(
        project="ACME", status="Draft", context="N=500"
    ) as (fig, ax):
        ax.plot([1, 2], [1, 2])
        texts = [t.get_text() for t in fig.texts]
        assert "ACME" in texts, "Tier-1 project tag missing before savefig"
        assert "Draft" in texts, "Tier-2 status tag missing before savefig"
        assert "N=500" in texts, "Tier-3 context tag missing before savefig"


def test_composite_canvas_all_three_tiers_present_before_savefig():
    """Same regression check for composite_canvas."""
    builder = CanvasBuilder()
    with builder.composite_canvas(
        project="FabCo", status="Simulation", context="Q3-2025"
    ) as (fig, ax_main, ax_ratio):
        ax_main.plot([1, 2], [1, 2])
        texts = [t.get_text() for t in fig.texts]
        assert "FabCo" in texts
        assert "Simulation" in texts
        assert "Q3-2025" in texts


def test_tier1_only_no_crash_no_tier2():
    """Providing only project (no status) must render Tier-1 alone."""
    builder = CanvasBuilder()
    with builder.single_canvas(project="Solo") as (fig, ax):
        texts = [t.get_text() for t in fig.texts]
        assert "Solo" in texts
        assert len(texts) == 1  # only Tier-1; no Tier-2, no Tier-3


def test_status_without_project_not_rendered():
    """Status alone (no project) must NOT be rendered — Tier-2 needs Tier-1."""
    builder = CanvasBuilder()
    with builder.single_canvas(status="Orphan") as (fig, ax):
        texts = [t.get_text() for t in fig.texts]
        assert "Orphan" not in texts


def test_context_only_renders_tier3():
    """Providing only context must render Tier-3 without errors."""
    builder = CanvasBuilder()
    with builder.single_canvas(context="N=42") as (fig, ax):
        texts = [t.get_text() for t in fig.texts]
        assert "N=42" in texts


def test_no_annotations_when_all_none():
    """No annotations should appear when all three params are None."""
    builder = CanvasBuilder()
    with builder.single_canvas() as (fig, ax):
        assert fig.texts == []


def test_tier1_fontweight_is_bold():
    """Tier-1 text element must have fontweight='bold'."""
    builder = CanvasBuilder()
    with builder.single_canvas(project="BoldCheck") as (fig, ax):
        t1 = next(t for t in fig.texts if t.get_text() == "BoldCheck")
        assert t1.get_fontweight() in ("bold", 700)


def test_tier2_fontstyle_is_italic():
    """Tier-2 text element must use italic style."""
    builder = CanvasBuilder()
    with builder.single_canvas(project="P", status="ItalicCheck") as (fig, ax):
        t2 = next(t for t in fig.texts if t.get_text() == "ItalicCheck")
        assert t2.get_fontstyle() == "italic"


def test_tier2_fontsize_smaller_than_tier1():
    """Tier-2 font size must be strictly smaller than Tier-1."""
    builder = CanvasBuilder()
    with builder.single_canvas(project="Big", status="Small") as (fig, ax):
        t1 = next(t for t in fig.texts if t.get_text() == "Big")
        t2 = next(t for t in fig.texts if t.get_text() == "Small")
        assert t2.get_fontsize() < t1.get_fontsize()


def test_tier3_horizontal_alignment_is_right():
    """Tier-3 context label must be right-aligned."""
    builder = CanvasBuilder()
    with builder.single_canvas(context="right-align-check") as (fig, ax):
        t3 = next(t for t in fig.texts if t.get_text() == "right-align-check")
        assert t3.get_ha() == "right"


# ── add_stats_legend ──────────────────────────────────────────────────────────


def test_add_stats_legend_basic_text_present():
    """N, μ, σ text blocks must appear in the axes annotations."""
    fig, ax = plt.subplots()
    stats = {"n": 100.0, "mean": 9.87, "sigma": 0.42}
    add_stats_legend(ax, stats)
    # The text is a single annotation object — check its string content
    annotations = [c for c in ax.get_children()
                   if hasattr(c, "get_text")]
    combined = " ".join(a.get_text() for a in annotations)
    assert "100" in combined
    plt.close(fig)


def test_add_stats_legend_with_cpk_shows_cpk():
    """When stats dict contains 'cpk', the legend must include Cpk text."""
    fig, ax = plt.subplots()
    stats = {"n": 50.0, "mean": 10.0, "sigma": 0.1, "cpk": 1.67}
    add_stats_legend(ax, stats)
    annotations = [c for c in ax.get_children()
                   if hasattr(c, "get_text")]
    combined = " ".join(a.get_text() for a in annotations)
    assert "1.67" in combined
    plt.close(fig)


def test_add_stats_legend_without_cpk_key():
    """Without 'cpk' in stats the legend renders normally, no KeyError."""
    fig, ax = plt.subplots()
    stats = {"n": 20.0, "mean": 5.0, "sigma": 0.5}
    add_stats_legend(ax, stats)  # must not raise
    plt.close(fig)


def test_add_stats_legend_empty_stats_no_crash():
    """An empty stats dict must not raise — defaults to zero."""
    fig, ax = plt.subplots()
    add_stats_legend(ax, {})
    plt.close(fig)


# ── autoadjust_xticklabels ────────────────────────────────────────────────────


def test_fab_style_context_tick_rotation_constants_exist():
    """Style context must expose tick-label rotation threshold and max angle."""
    ctx = DSPStyleContext()
    assert ctx.tick_label_rotation_threshold == 6
    assert ctx.tick_label_max_rotation == pytest.approx(45.0)


def test_autoadjust_xticklabels_rotates_long_labels():
    """Datetime-length labels (> 6 chars) must be auto-rotated to 45°."""
    builder = CanvasBuilder()
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(["2024-01-01", "2024-02-01", "2024-03-01"])
    builder.autoadjust_xticklabels(ax)
    labels = [lbl for lbl in ax.get_xticklabels() if lbl.get_text()]
    assert labels[0].get_rotation() == pytest.approx(45.0)
    plt.close(fig)


def test_autoadjust_xticklabels_no_rotation_for_short_labels():
    """Single-digit numeric labels must stay at 0° — no unnecessary rotation."""
    builder = CanvasBuilder()
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(["1", "2", "3"])
    builder.autoadjust_xticklabels(ax)
    labels = [lbl for lbl in ax.get_xticklabels() if lbl.get_text()]
    assert labels[0].get_rotation() == pytest.approx(0.0)
    plt.close(fig)


def test_autoadjust_xticklabels_single_label_is_noop():
    """A single tick label must not raise and must not be rotated."""
    builder = CanvasBuilder()
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_xticks([1])
    ax.set_xticklabels(["only-one-long-label"])
    builder.autoadjust_xticklabels(ax)   # must not raise
    plt.close(fig)


# ── DSPStyleContext Gantt fields ───────────────────────────────────────────────


def test_gantt_min_px_width_default_value():
    """Default gantt_min_px_width must equal 2.0 as per spec."""
    ctx = DSPStyleContext()
    assert ctx.gantt_min_px_width == pytest.approx(2.0)


def test_gantt_min_px_width_is_immutable():
    """gantt_min_px_width must be immutable (frozen dataclass)."""
    ctx = DSPStyleContext()
    with pytest.raises((AttributeError, TypeError)):
        ctx.gantt_min_px_width = 5.0  # type: ignore[misc]


# ── gantt_canvas context manager ──────────────────────────────────────────────


def test_gantt_canvas_yields_correct_panel_count():
    """gantt_canvas should yield exactly n_channels Axes."""
    builder = CanvasBuilder(DSPStyleContext())
    with builder.gantt_canvas(n_channels=3) as (fig, axes):
        assert len(axes) == 3
        plt.close(fig)


def test_gantt_canvas_only_bottom_panel_has_xticklabels():
    """Upper panels must have X-tick labels suppressed."""
    builder = CanvasBuilder(DSPStyleContext())
    with builder.gantt_canvas(n_channels=3) as (fig, axes):
        for ax in axes[:-1]:
            assert not ax.get_xticklabels(minor=False) or all(
                t.get_visible() is False or t.get_text() == ""
                for t in ax.get_xticklabels()
            )
        plt.close(fig)


def test_gantt_canvas_raises_on_zero_channels():
    """n_channels < 1 must raise ValueError."""
    builder = CanvasBuilder(DSPStyleContext())
    with pytest.raises(ValueError, match="n_channels"):
        with builder.gantt_canvas(n_channels=0):
            pass


def test_gantt_canvas_warns_on_too_many_channels():
    """n_channels > 20 must emit UserWarning."""
    builder = CanvasBuilder(DSPStyleContext())
    with pytest.warns(UserWarning, match="exceeds 20"):
        with builder.gantt_canvas(n_channels=21) as (fig, _):
            plt.close(fig)


def test_gantt_canvas_single_channel():
    """A single-channel gantt canvas must succeed and close cleanly."""
    builder = CanvasBuilder(DSPStyleContext())
    with builder.gantt_canvas(n_channels=1) as (fig, axes):
        assert len(axes) == 1
        plt.close(fig)


# ── transition_canvas ─────────────────────────────────────────────────────────


def test_transition_canvas_yields_two_axes():
    """transition_canvas must yield exactly two Axes instances."""
    builder = CanvasBuilder(DSPStyleContext())
    with builder.transition_canvas() as (fig, ax_count, ax_prob):
        assert isinstance(ax_count, Axes)
        assert isinstance(ax_prob, Axes)
        assert ax_count is not ax_prob
        plt.close(fig)


def test_transition_canvas_default_figsize():
    """Default figure width must be 14 inches."""
    builder = CanvasBuilder(DSPStyleContext())
    with builder.transition_canvas() as (fig, _, __):
        assert fig.get_figwidth() == pytest.approx(14.0, rel=1e-3)
        plt.close(fig)


def test_transition_canvas_figure_closed_after_exit():
    """Figure must be closed after the context manager exits."""
    import matplotlib.pyplot as _plt

    builder = CanvasBuilder(DSPStyleContext())
    with builder.transition_canvas() as (fig, _, __):
        fig_num = fig.number

    assert fig_num not in [f.number for f in _plt.get_fignums()]


def test_transition_canvas_golden_margins():
    """Golden margin parameters must be applied to the figure."""
    style = DSPStyleContext()
    builder = CanvasBuilder(style)
    with builder.transition_canvas() as (fig, _, __):
        sp = fig.subplotpars
        assert sp.left == pytest.approx(style.margin_left, rel=1e-4)
        assert sp.right == pytest.approx(1.0 - style.margin_right, rel=1e-4)
        assert sp.bottom == pytest.approx(style.margin_bottom, rel=1e-4)
        assert sp.top == pytest.approx(1.0 - style.margin_top, rel=1e-4)
        plt.close(fig)


def test_transition_canvas_typography_applied():
    """Three-tier typography must add figure-level text when args are supplied."""
    builder = CanvasBuilder(DSPStyleContext())
    with builder.transition_canvas(project="TestProject") as (fig, _, __):
        # add_three_tier_typography calls fig.text() for Tier-1
        assert len(fig.texts) > 0
        plt.close(fig)
