from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats


@dataclass
class SampleStatistics:
    count: int
    mean: float
    std: float
    cv: float
    skew: float
    kurtosis: float
    median: float
    kde_peak: float


@dataclass
class PairwiseTestResult:
    levene_statistic: float
    levene_p_value: float
    levene_significant: bool
    kurtosis_diff_mean: float
    kurtosis_ci_lower: float
    kurtosis_ci_upper: float


def _safe_stat(value: float) -> float:
    if np.isnan(value) or np.isinf(value):
        return float("nan")
    return float(value)


def find_kde_peak(values: np.ndarray, clip_zero: bool = False, grid_size: int = 1024) -> float:
    if values.size == 0:
        return float("nan")
    lower = max(0.0, float(values.min())) if clip_zero else float(values.min())
    upper = float(values.max())
    if lower == upper:
        return lower
    kde = stats.gaussian_kde(values, bw_method="scott")
    grid = np.linspace(lower, upper, grid_size)
    densities = kde(grid)
    return float(grid[np.argmax(densities)])


def compute_sample_statistics(values: np.ndarray, clip_zero: bool = False) -> SampleStatistics:
    array = np.asarray(values, dtype=float)
    if array.size == 0:
        raise ValueError("values must not be empty")

    mean = float(np.mean(array))
    std = float(np.std(array, ddof=1)) if array.size > 1 else 0.0
    cv = std / mean if mean != 0 else float("nan")
    skew = _safe_stat(stats.skew(array)) if array.size > 2 else float("nan")
    kurt = _safe_stat(stats.kurtosis(array)) if array.size > 3 else float("nan")
    median = float(np.median(array))
    kde_peak = find_kde_peak(array, clip_zero=clip_zero)
    return SampleStatistics(
        count=int(array.size),
        mean=mean,
        std=std,
        cv=float(cv),
        skew=skew,
        kurtosis=kurt,
        median=median,
        kde_peak=kde_peak,
    )


def bootstrap_kurtosis_diff(
    data1: np.ndarray,
    data2: np.ndarray,
    n_iterations: int = 5000,
    ci: int = 95,
    seed: int = 42,
) -> tuple[float, float, float]:
    values1 = np.asarray(data1, dtype=float)
    values2 = np.asarray(data2, dtype=float)
    if values1.size == 0 or values2.size == 0:
        raise ValueError("bootstrap inputs must not be empty")

    rng = np.random.RandomState(seed)
    diffs = np.empty(n_iterations, dtype=float)
    for idx in range(n_iterations):
        sample1 = rng.choice(values1, size=values1.size, replace=True)
        sample2 = rng.choice(values2, size=values2.size, replace=True)
        diffs[idx] = stats.kurtosis(sample1) - stats.kurtosis(sample2)

    lower = float(np.percentile(diffs, (100 - ci) / 2))
    upper = float(np.percentile(diffs, 100 - (100 - ci) / 2))
    return float(np.mean(diffs)), lower, upper


def compute_pairwise_tests(
    data1: np.ndarray,
    data2: np.ndarray,
    alpha: float = 0.05,
) -> PairwiseTestResult:
    values1 = np.asarray(data1, dtype=float)
    values2 = np.asarray(data2, dtype=float)
    if values1.size == 0 or values2.size == 0:
        raise ValueError("pairwise test inputs must not be empty")

    levene_statistic, levene_p_value = stats.levene(values1, values2)
    kurtosis_diff_mean, kurtosis_ci_lower, kurtosis_ci_upper = bootstrap_kurtosis_diff(
        values1,
        values2,
    )
    return PairwiseTestResult(
        levene_statistic=float(levene_statistic),
        levene_p_value=float(levene_p_value),
        levene_significant=bool(levene_p_value < alpha),
        kurtosis_diff_mean=kurtosis_diff_mean,
        kurtosis_ci_lower=kurtosis_ci_lower,
        kurtosis_ci_upper=kurtosis_ci_upper,
    )
