"""Statistical metrics for semiconductor process analysis."""

from collections.abc import Sequence
from datetime import datetime, timedelta

import numpy as np


def calculate_metrics(
    data: np.ndarray,
    lsl: float | None = None,
    usl: float | None = None,
) -> dict[str, float]:
    """Calculate statistical indicators N, Mean, Sigma, and Cpk.

    :param data: 1D numpy array of numerical data.
    :type data: numpy.ndarray
    :param lsl: Lower Specification Limit (optional).
    :type lsl: float or None
    :param usl: Upper Specification Limit (optional).
    :type usl: float or None
    :returns: Dictionary with keys ``n``, ``mean``, ``sigma``,
        and optionally ``cpk``.
    :rtype: dict[str, float]
    """
    valid_data = data[~np.isnan(data)]
    n = len(valid_data)

    if n == 0:
        return {"n": 0.0, "mean": float("nan"), "sigma": float("nan")}

    mean = float(np.mean(valid_data))
    sigma = float(np.std(valid_data, ddof=1)) if n > 1 else 0.0

    metrics: dict[str, float] = {"n": float(n), "mean": mean, "sigma": sigma}

    if lsl is not None and usl is not None and sigma > 0:
        cpk_lower = (mean - lsl) / (3 * sigma)
        cpk_upper = (usl - mean) / (3 * sigma)
        metrics["cpk"] = min(cpk_lower, cpk_upper)

    return metrics


def calculate_smart_bins(data: np.ndarray) -> int:
    """Calculate the optimal number of histogram bins for semiconductor data.

    Uses the Freedman-Diaconis rule to avoid aliasing in continuous
    distributions.

    :param data: 1D numpy array of numerical data.
    :type data: numpy.ndarray
    :returns: Recommended bin count, clamped between 10 and 200.
    :rtype: int
    """
    valid_data = data[~np.isnan(data)]
    n = len(valid_data)

    if n < 2:
        return 10

    q75, q25 = np.percentile(valid_data, [75, 25])
    iqr = q75 - q25

    if iqr == 0:
        return 10

    bin_width = 2 * iqr * (n ** (-1 / 3))

    if bin_width == 0:
        return 10

    data_range = np.max(valid_data) - np.min(valid_data)
    bins = int(np.ceil(data_range / bin_width))

    return max(10, min(bins, 200))


def calculate_ratio(
    y1: "np.ndarray",
    y2: "np.ndarray",
) -> "np.ndarray":
    """Calculate element-wise ratio ``y1 / y2`` for the compare panel.

    Zero or NaN denominators produce ``NaN`` entries without raising
    a ``ZeroDivisionError``.

    :param y1: Numerator array (e.g. measured data).
    :type y1: numpy.ndarray
    :param y2: Denominator array (e.g. simulation / reference).
    :type y2: numpy.ndarray
    :returns: Array of ratio values; ``NaN`` where ``y2`` is zero or NaN.
    :rtype: numpy.ndarray
    """
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where((y2 != 0) & ~np.isnan(y2), y1 / y2, np.nan)
    return ratio.astype(float)


def state_distribution(
    records: Sequence[tuple[datetime, datetime, str]],
) -> dict[str, float]:
    """Compute per-state time percentage for a single channel.

    Each record represents a half-open interval ``[start, end)`` with a
    categorical state label.  Durations are accumulated and converted to
    percentages of the total covered time.  Overlapping intervals are
    accumulated independently (no union merging); for disjoint Gantt
    records this is exact.

    :param records: Sequence of ``(start, end, state)`` tuples.
    :type records: Sequence[tuple[datetime, datetime, str]]
    :returns: Mapping of ``{state: percentage}`` where values sum to ≈ 100.0
        when intervals are non-overlapping.
    :rtype: dict[str, float]
    """
    if not records:
        return {}

    state_seconds: dict[str, float] = {}
    for start, end, state in records:
        secs = (end - start).total_seconds()
        if secs > 0:
            state_seconds[state] = state_seconds.get(state, 0.0) + secs

    total = sum(state_seconds.values())
    if total <= 0:
        return {}

    return {state: (secs / total) * 100.0 for state, secs in state_seconds.items()}


def compute_state_bins(
    records: Sequence[tuple[datetime, datetime, str]],
    bucket_size: timedelta,
    time_range: tuple[datetime, datetime],
) -> list[dict[str, float]]:
    """Divide *time_range* into fixed buckets and compute state proportions.

    For each bucket ``[bucket_start, bucket_end)``, the overlap of every
    record with that bucket is measured and returned as a proportion of the
    bucket's total duration.  Proportions sum to ≤ 1.0 per bucket (< 1.0
    when no record covers part of the bucket).

    :param records: Sequence of ``(start, end, state)`` tuples.
    :type records: Sequence[tuple[datetime, datetime, str]]
    :param bucket_size: Width of each time bucket (e.g. ``timedelta(hours=1)``).
    :type bucket_size: timedelta
    :param time_range: ``(global_start, global_end)`` bounding the dataset.
    :type time_range: tuple[datetime, datetime]
    :returns: One dict per bucket in chronological order; each dict maps
        ``{state: proportion}`` where proportion ∈ [0, 1].
    :rtype: list[dict[str, float]]
    """
    global_start, global_end = time_range
    if (global_end - global_start).total_seconds() <= 0 or not records:
        return []

    result: list[dict[str, float]] = []
    bucket_start = global_start
    while bucket_start < global_end:
        bucket_end = min(bucket_start + bucket_size, global_end)
        bucket_seconds = (bucket_end - bucket_start).total_seconds()

        state_seconds: dict[str, float] = {}
        for rec_start, rec_end, state in records:
            overlap_start = max(rec_start, bucket_start)
            overlap_end = min(rec_end, bucket_end)
            if overlap_end > overlap_start:
                secs = (overlap_end - overlap_start).total_seconds()
                state_seconds[state] = state_seconds.get(state, 0.0) + secs

        bin_proportions: dict[str, float] = {}
        if bucket_seconds > 0:
            for state, secs in state_seconds.items():
                bin_proportions[state] = secs / bucket_seconds

        result.append(bin_proportions)
        bucket_start = bucket_end

    return result


def validate_grayscale_contrast(
    colors: Sequence[str],
) -> list[tuple[str, str, float]]:
    """Identify adjacent color pairs that fail the 3:1 grayscale contrast ratio.

    Uses the WCAG 2.1 relative luminance formula to convert each ``#RRGGBB``
    hex color to a perceptual luminance value, then computes the contrast
    ratio for every consecutive pair in *colors*.  Pairs with a ratio below
    3.0 are returned as violations.

    :param colors: Sequence of ``#RRGGBB`` hex color strings.
    :type colors: Sequence[str]
    :returns: List of ``(colorA, colorB, ratio)`` for each violating pair.
    :rtype: list[tuple[str, str, float]]
    """

    def _luminance(hex_color: str) -> float:
        """WCAG 2.1 relative luminance for a single ``#RRGGBB`` color."""
        h = hex_color.lstrip("#")
        r_raw = int(h[0:2], 16) / 255
        g_raw = int(h[2:4], 16) / 255
        b_raw = int(h[4:6], 16) / 255

        def _lin(c: float) -> float:
            return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

        return 0.2126 * _lin(r_raw) + 0.7152 * _lin(g_raw) + 0.0722 * _lin(b_raw)

    violations: list[tuple[str, str, float]] = []
    for i in range(len(colors) - 1):
        c1, c2 = colors[i], colors[i + 1]
        try:
            l1 = _luminance(c1)
            l2 = _luminance(c2)
            lighter, darker = max(l1, l2), min(l1, l2)
            ratio = (lighter + 0.05) / (darker + 0.05)
            if ratio < 3.0:
                violations.append((c1, c2, ratio))
        except (ValueError, IndexError):
            pass  # silently skip malformed hex strings

    return violations
