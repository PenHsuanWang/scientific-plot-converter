"""Tests for dsprinter.stats.metrics — calculate_metrics, smart bins, ratio."""

import numpy as np
import pytest
from datetime import datetime, timedelta

from dsprinter.stats.metrics import (
    calculate_metrics,
    calculate_ratio,
    calculate_smart_bins,
    compute_state_bins,
    state_distribution,
    validate_grayscale_contrast,
)


# ── calculate_metrics ─────────────────────────────────────────────────────────


def test_calculate_metrics_empty_array_returns_nan():
    """Empty input must return n=0 and NaN for mean/sigma without crashing."""
    result = calculate_metrics(np.array([]))
    assert result["n"] == 0.0
    assert np.isnan(result["mean"])
    assert np.isnan(result["sigma"])
    assert "cpk" not in result


def test_calculate_metrics_all_nan_treated_as_empty():
    """An array of all NaNs is equivalent to an empty array."""
    result = calculate_metrics(np.array([np.nan, np.nan]))
    assert result["n"] == 0.0


def test_calculate_metrics_single_value_sigma_is_zero():
    """A single-element array must produce sigma=0.0, not raise ddof error."""
    result = calculate_metrics(np.array([42.0]))
    assert result["n"] == 1.0
    assert result["mean"] == pytest.approx(42.0)
    assert result["sigma"] == pytest.approx(0.0)
    assert "cpk" not in result


def test_calculate_metrics_normal_case():
    """Standard N, mean, sigma computation on a small known dataset."""
    data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    result = calculate_metrics(data)
    assert result["n"] == 5.0
    assert result["mean"] == pytest.approx(3.0)
    assert result["sigma"] == pytest.approx(np.std(data, ddof=1))
    assert "cpk" not in result


def test_calculate_metrics_with_cpk():
    """When lsl and usl are provided, cpk must be present and correct."""
    data = np.array([9.8, 10.0, 10.2, 9.9, 10.1])
    result = calculate_metrics(data, lsl=9.0, usl=11.0)
    assert "cpk" in result
    mean = result["mean"]
    sigma = result["sigma"]
    expected_cpk = min((mean - 9.0) / (3 * sigma), (11.0 - mean) / (3 * sigma))
    assert result["cpk"] == pytest.approx(expected_cpk, rel=1e-4)


def test_calculate_metrics_cpk_absent_when_only_lsl():
    """Cpk requires BOTH lsl and usl — providing only lsl produces no cpk."""
    data = np.array([1.0, 2.0, 3.0])
    result = calculate_metrics(data, lsl=0.0)
    assert "cpk" not in result


def test_calculate_metrics_cpk_absent_when_sigma_zero():
    """Cpk is only meaningful when sigma > 0; zero sigma must skip it."""
    data = np.array([5.0, 5.0, 5.0])  # std == 0
    result = calculate_metrics(data, lsl=4.0, usl=6.0)
    assert "cpk" not in result


def test_calculate_metrics_nan_values_are_excluded():
    """Values with NaN must be stripped before computing statistics."""
    data = np.array([1.0, np.nan, 3.0, np.nan, 5.0])
    result = calculate_metrics(data)
    assert result["n"] == 3.0
    assert result["mean"] == pytest.approx(3.0)


# ── calculate_smart_bins ──────────────────────────────────────────────────────


def test_smart_bins_returns_int():
    """Result must always be a Python int (not numpy int64)."""
    data = np.random.normal(0, 1, 100)
    assert isinstance(calculate_smart_bins(data), int)


def test_smart_bins_n_less_than_2_returns_10():
    """Arrays with fewer than 2 valid points must return the fallback of 10."""
    assert calculate_smart_bins(np.array([])) == 10
    assert calculate_smart_bins(np.array([1.0])) == 10
    assert calculate_smart_bins(np.array([np.nan])) == 10


def test_smart_bins_zero_iqr_returns_10():
    """An array of identical values has IQR == 0 — must return fallback 10."""
    data = np.array([5.0] * 50)
    assert calculate_smart_bins(data) == 10


def test_smart_bins_normal_distribution_within_bounds():
    """Freedman-Diaconis result for a normal sample must stay in [10, 200]."""
    rng = np.random.default_rng(42)
    data = rng.normal(loc=10.0, scale=0.5, size=500)
    bins = calculate_smart_bins(data)
    assert 10 <= bins <= 200


def test_smart_bins_large_diverse_dataset_not_clamped_low():
    """A wide-range dataset should produce bins > 10 (non-trivial result)."""
    rng = np.random.default_rng(0)
    data = rng.uniform(0, 100, 1000)
    bins = calculate_smart_bins(data)
    assert bins > 10


def test_smart_bins_clamps_to_max_200():
    """Pathologically narrow IQR with many points must not exceed 200."""
    rng = np.random.default_rng(7)
    # Very small IQR relative to range → many bins before clamp
    data = np.concatenate([
        rng.normal(50.0, 0.001, 5000),
        np.array([0.0, 100.0]),  # outliers to widen range
    ])
    bins = calculate_smart_bins(data)
    assert bins <= 200


# ── calculate_ratio ───────────────────────────────────────────────────────────


def test_calculate_ratio_normal():
    """Normal division produces the expected element-wise ratios."""
    y1 = np.array([2.0, 4.0, 6.0])
    y2 = np.array([1.0, 2.0, 3.0])
    np.testing.assert_array_almost_equal(calculate_ratio(y1, y2), [2.0, 2.0, 2.0])


def test_calculate_ratio_zero_denominator_yields_nan():
    """Zero denominator elements must map to NaN, not raise ZeroDivisionError."""
    y1 = np.array([1.0, 2.0])
    y2 = np.array([0.0, 2.0])
    result = calculate_ratio(y1, y2)
    assert np.isnan(result[0])
    assert result[1] == pytest.approx(1.0)


def test_calculate_ratio_nan_denominator_yields_nan():
    """Denominator elements that are NaN must produce NaN in the result."""
    y1 = np.array([1.0, 2.0])
    y2 = np.array([np.nan, 2.0])
    result = calculate_ratio(y1, y2)
    assert np.isnan(result[0])
    assert result[1] == pytest.approx(1.0)


def test_calculate_ratio_output_dtype_is_float():
    """Output array must be float64 regardless of integer input."""
    y1 = np.array([4, 6], dtype=int)
    y2 = np.array([2, 3], dtype=int)
    result = calculate_ratio(y1, y2)
    assert result.dtype == np.float64


def test_calculate_ratio_all_nan_denominators():
    """All-NaN denominator must produce all-NaN output without errors."""
    y1 = np.array([1.0, 2.0, 3.0])
    y2 = np.full(3, np.nan)
    result = calculate_ratio(y1, y2)
    assert np.all(np.isnan(result))


def test_calculate_ratio_preserves_shape():
    """Output shape must match input shape."""
    y1 = np.ones((5,))
    y2 = np.ones((5,))
    assert calculate_ratio(y1, y2).shape == (5,)


# ── state_distribution ────────────────────────────────────────────────────────


def _dt(offset_secs: float) -> datetime:
    """Return a datetime offset from a fixed epoch for testing."""
    return datetime(2024, 1, 1) + timedelta(seconds=offset_secs)


def test_state_distribution_empty_returns_empty():
    assert state_distribution([]) == {}


def test_state_distribution_single_record():
    rec = [(_dt(0), _dt(100), "running")]
    result = state_distribution(rec)
    assert result == pytest.approx({"running": 100.0})


def test_state_distribution_two_equal_states():
    recs = [(_dt(0), _dt(50), "A"), (_dt(50), _dt(100), "B")]
    result = state_distribution(recs)
    assert result["A"] == pytest.approx(50.0, rel=1e-3)
    assert result["B"] == pytest.approx(50.0, rel=1e-3)


def test_state_distribution_percentage_sums_to_100():
    recs = [
        (_dt(0), _dt(30), "X"),
        (_dt(30), _dt(70), "Y"),
        (_dt(70), _dt(100), "Z"),
    ]
    result = state_distribution(recs)
    assert sum(result.values()) == pytest.approx(100.0, rel=1e-4)


def test_state_distribution_zero_duration_ignored():
    recs = [(_dt(0), _dt(0), "zero"), (_dt(0), _dt(60), "valid")]
    result = state_distribution(recs)
    assert "zero" not in result


# ── compute_state_bins ────────────────────────────────────────────────────────


def test_compute_state_bins_empty_records():
    result = compute_state_bins([], timedelta(hours=1), (_dt(0), _dt(3600)))
    assert result == []


def test_compute_state_bins_single_bucket_full_coverage():
    recs = [(_dt(0), _dt(3600), "on")]
    bins = compute_state_bins(recs, timedelta(hours=1), (_dt(0), _dt(3600)))
    assert len(bins) == 1
    assert bins[0]["on"] == pytest.approx(1.0, rel=1e-4)


def test_compute_state_bins_proportions_sum_lte_one():
    recs = [(_dt(0), _dt(1800), "A"), (_dt(1800), _dt(3600), "B")]
    bins = compute_state_bins(recs, timedelta(hours=1), (_dt(0), _dt(3600)))
    for b in bins:
        assert sum(b.values()) <= 1.0 + 1e-6


def test_compute_state_bins_bucket_count_matches_range():
    recs = [(_dt(0), _dt(7200), "on")]
    bins = compute_state_bins(recs, timedelta(hours=1), (_dt(0), _dt(7200)))
    assert len(bins) == 2


# ── validate_grayscale_contrast ───────────────────────────────────────────────


def test_validate_grayscale_contrast_identical_colors_fail():
    # Two identical colors → ratio 1.0 < 3.0
    violations = validate_grayscale_contrast(["#000000", "#000000"])
    assert len(violations) == 1


def test_validate_grayscale_contrast_black_white_pass():
    violations = validate_grayscale_contrast(["#000000", "#ffffff"])
    assert violations == []


def test_validate_grayscale_contrast_empty_and_single():
    assert validate_grayscale_contrast([]) == []
    assert validate_grayscale_contrast(["#aabbcc"]) == []


def test_validate_grayscale_contrast_malformed_hex_skipped():
    # Malformed entries must not raise — they should be skipped
    violations = validate_grayscale_contrast(["#zzzzzz", "#ffffff"])
    assert isinstance(violations, list)
