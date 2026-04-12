"""Statistical metrics for semiconductor process analysis."""

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
