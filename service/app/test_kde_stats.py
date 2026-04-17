import numpy as np

from service.app.services.kde_stats import (
    bootstrap_kurtosis_diff,
    compute_pairwise_tests,
    compute_sample_statistics,
)
from service.app.services.visualization import build_kde_plot_html, render_kde_plot_svg


def test_compute_sample_statistics_returns_expected_fields():
    values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

    result = compute_sample_statistics(values)

    assert result.count == 5
    assert result.mean == 3.0
    assert result.median == 3.0
    assert np.isfinite(result.kde_peak)


def test_bootstrap_kurtosis_diff_returns_confidence_interval():
    data1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    data2 = np.array([1.5, 2.5, 3.5, 4.5, 5.5])

    diff_mean, lower, upper = bootstrap_kurtosis_diff(data1, data2, n_iterations=200)

    assert np.isfinite(diff_mean)
    assert lower <= upper


def test_compute_pairwise_tests_returns_levene_and_kurtosis_info():
    data1 = np.array([1.0, 2.0, 3.0, 4.0, 8.0])
    data2 = np.array([1.1, 2.1, 3.1, 4.1, 5.1])

    result = compute_pairwise_tests(data1, data2)

    assert np.isfinite(result.levene_p_value)
    assert np.isfinite(result.kurtosis_diff_mean)


def test_render_kde_plot_svg_returns_svg_document():
    svg = render_kde_plot_svg(
        {
            "Sample A": np.array([1.0, 2.0, 3.0, 4.0]),
            "Sample B": np.array([1.5, 2.5, 3.5, 4.5]),
        },
        attribute="Feret",
        clip_zero=True,
    )

    assert "<svg" in svg
    assert "Sample A" in svg


def test_build_kde_plot_html_wraps_svg_and_comment():
    html = build_kde_plot_html("<svg></svg>", attribute="Feret", comment_text="example comment")

    assert "<html>" in html
    assert "example comment" in html
