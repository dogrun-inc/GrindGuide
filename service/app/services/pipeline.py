from __future__ import annotations

from pathlib import Path
from typing import Callable

try:
    from ..config import DEFAULT_MAX_FERET_MM, DEFAULT_MIN_AREA_MM2, DEFAULT_MIN_FERET_MM
    from ..fiji_runner import run_fiji_measurement
    from ..models import AnalyzeImagesRequest, AnalyzeImagesResponse, CompareCsvRequest, SampleResult, StatisticsSummary
    from .kde_stats import compute_pairwise_tests, compute_sample_statistics
    from .measurement_parser import (
        filter_measurement_dataframe,
        get_measurement_values_from_dataframe,
        read_measurement_csv,
    )
    from .visualization import build_kde_plot_html, render_kde_plot_svg
except ImportError:
    from config import DEFAULT_MAX_FERET_MM, DEFAULT_MIN_AREA_MM2, DEFAULT_MIN_FERET_MM
    from fiji_runner import run_fiji_measurement
    from models import AnalyzeImagesRequest, AnalyzeImagesResponse, CompareCsvRequest, SampleResult, StatisticsSummary
    from services.kde_stats import compute_pairwise_tests, compute_sample_statistics
    from services.measurement_parser import (
        filter_measurement_dataframe,
        get_measurement_values_from_dataframe,
        read_measurement_csv,
    )
    from services.visualization import build_kde_plot_html, render_kde_plot_svg

ProgressCallback = Callable[[int, str | None], None]
DEFAULT_ANALYZE_ATTRIBUTE = "Feret"
DEFAULT_COMPARE_ATTRIBUTE = "Feret"


def _build_pairwise_test_html(samples_by_label: dict[str, object]) -> tuple[str, str | None]:
    if len(samples_by_label) != 2:
        return "", None

    labels = list(samples_by_label.keys())
    values1 = samples_by_label[labels[0]]
    values2 = samples_by_label[labels[1]]
    result = compute_pairwise_tests(values1, values2)
    significance = "有意差あり" if result.levene_significant else "有意差なし"
    html = (
        f"<p><b>Levene検定（分散差）</b>: "
        f"stat={result.levene_statistic:.4f}, "
        f"p={result.levene_p_value:.4f} → {significance}</p>"
        f"<p><b>尖度差（ブートストラップ）</b>: "
        f"差={result.kurtosis_diff_mean:.4f}, "
        f"95%CI=({result.kurtosis_ci_lower:.4f}, {result.kurtosis_ci_upper:.4f})</p>"
    )
    note = (
        "Pairwise comparison available: "
        f"Levene p={result.levene_p_value:.4f}, "
        f"kurtosis diff mean={result.kurtosis_diff_mean:.4f}"
    )
    return html, note


def _build_response(
    *,
    request_count: int,
    sample_results: list[SampleResult],
    plot_path: Path,
    attribute: str,
    pairwise_test_note: str | None,
    min_feret_mm: float,
    min_area_mm2: float,
    max_feret_mm: float,
) -> AnalyzeImagesResponse:
    mean_values = [sample.mean for sample in sample_results if sample.mean is not None]
    median_values = [sample.median for sample in sample_results if sample.median is not None]
    return AnalyzeImagesResponse(
        samples=sample_results,
        plot_path=str(plot_path),
        statistics=StatisticsSummary(
            compared_samples=request_count,
            mean_of_means=(sum(mean_values) / len(mean_values)) if mean_values else None,
            mean_of_medians=(sum(median_values) / len(median_values)) if median_values else None,
            attribute=attribute,
            pairwise_test_note=pairwise_test_note,
            min_feret_mm=min_feret_mm,
            min_area_mm2=min_area_mm2,
            max_feret_mm=max_feret_mm,
        ),
    )


def process_analyze_request(
    *,
    request_model: AnalyzeImagesRequest,
    workspace: Path,
    image_paths_by_name: dict[str, Path],
    progress_callback: ProgressCallback | None = None,
) -> AnalyzeImagesResponse:
    attribute = DEFAULT_ANALYZE_ATTRIBUTE
    min_feret_mm = DEFAULT_MIN_FERET_MM
    min_area_mm2 = DEFAULT_MIN_AREA_MM2
    max_feret_mm = DEFAULT_MAX_FERET_MM
    samples_by_label: dict[str, object] = {}
    sample_results: list[SampleResult] = []

    for index, sample in enumerate(request_model.samples):
        if progress_callback is not None:
            progress_callback(index, sample.sample_name)

        image_path = image_paths_by_name[sample.file_key]
        raw_csv_path = run_fiji_measurement(
            image_path=image_path,
            output_dir=workspace,
            sample_name=Path(sample.file_key).stem,
            scale_diameter_mm=request_model.options.scale_diameter_mm,
            threshold_min=request_model.options.threshold_min,
            threshold_max=request_model.options.threshold_max,
            roi_diameter_scale=request_model.options.roi_diameter_scale,
        )

        raw_df = read_measurement_csv(raw_csv_path)
        filtered_df = filter_measurement_dataframe(
            raw_df,
            min_feret_mm=min_feret_mm,
            max_feret_mm=max_feret_mm,
            min_area_mm2=min_area_mm2,
        )
        values = get_measurement_values_from_dataframe(filtered_df, attribute)
        sample_stats = compute_sample_statistics(values, clip_zero=True)
        samples_by_label[sample.sample_name] = values
        sample_results.append(
            SampleResult(
                sample_name=sample.sample_name,
                particle_count=int(len(raw_df)),
                filtered_particle_count=sample_stats.count,
                unit=request_model.options.output_unit,
                raw_csv_path=str(raw_csv_path),
                mean=sample_stats.mean,
                std=sample_stats.std,
                cv=sample_stats.cv,
                skew=sample_stats.skew,
                kurtosis=sample_stats.kurtosis,
                median=sample_stats.median,
                kde_peak=sample_stats.kde_peak,
            )
        )

        if progress_callback is not None:
            progress_callback(index + 1, sample.sample_name)

    svg_content = render_kde_plot_svg(
        samples=samples_by_label,
        attribute=attribute,
        clip_zero=True,
        title=f"KDE Plot of {attribute}",
    )
    extra_html, pairwise_test_note = _build_pairwise_test_html(samples_by_label)
    html_content = build_kde_plot_html(
        svg_content=svg_content,
        attribute=attribute,
        comment_text="Uploaded image analysis result",
        extra_html=extra_html,
    )
    plot_path = workspace / f"{attribute.lower()}_kde.html"
    plot_path.write_text(html_content, encoding="utf-8")
    return _build_response(
        request_count=len(request_model.samples),
        sample_results=sample_results,
        plot_path=plot_path,
        attribute=attribute,
        pairwise_test_note=pairwise_test_note,
        min_feret_mm=min_feret_mm,
        min_area_mm2=min_area_mm2,
        max_feret_mm=max_feret_mm,
    )


def process_compare_request(
    *,
    request_model: CompareCsvRequest,
    workspace: Path,
    csv_paths_by_name: dict[str, Path],
    progress_callback: ProgressCallback | None = None,
) -> AnalyzeImagesResponse:
    attribute = DEFAULT_COMPARE_ATTRIBUTE
    min_feret_mm = DEFAULT_MIN_FERET_MM
    min_area_mm2 = DEFAULT_MIN_AREA_MM2
    max_feret_mm = DEFAULT_MAX_FERET_MM
    samples_by_label: dict[str, object] = {}
    sample_results: list[SampleResult] = []

    for index, sample in enumerate(request_model.samples):
        if progress_callback is not None:
            progress_callback(index, sample.sample_name)

        saved_path = csv_paths_by_name[sample.file_key]
        raw_df = read_measurement_csv(saved_path)
        filtered_df = filter_measurement_dataframe(
            raw_df,
            min_feret_mm=min_feret_mm,
            max_feret_mm=max_feret_mm,
            min_area_mm2=min_area_mm2,
        )
        values = get_measurement_values_from_dataframe(filtered_df, attribute)
        sample_stats = compute_sample_statistics(values, clip_zero=True)
        samples_by_label[sample.sample_name] = values
        sample_results.append(
            SampleResult(
                sample_name=sample.sample_name,
                particle_count=int(len(raw_df)),
                filtered_particle_count=sample_stats.count,
                unit=sample.unit,
                raw_csv_path=str(saved_path),
                mean=sample_stats.mean,
                std=sample_stats.std,
                cv=sample_stats.cv,
                skew=sample_stats.skew,
                kurtosis=sample_stats.kurtosis,
                median=sample_stats.median,
                kde_peak=sample_stats.kde_peak,
            )
        )

        if progress_callback is not None:
            progress_callback(index + 1, sample.sample_name)

    svg_content = render_kde_plot_svg(
        samples=samples_by_label,
        attribute=attribute,
        clip_zero=True,
        title=f"KDE Plot of {attribute}",
    )
    extra_html, pairwise_test_note = _build_pairwise_test_html(samples_by_label)
    html_content = build_kde_plot_html(
        svg_content=svg_content,
        attribute=attribute,
        comment_text="Uploaded CSV comparison result",
        extra_html=extra_html,
    )
    plot_path = workspace / f"{attribute.lower()}_kde.html"
    plot_path.write_text(html_content, encoding="utf-8")
    return _build_response(
        request_count=len(request_model.samples),
        sample_results=sample_results,
        plot_path=plot_path,
        attribute=attribute,
        pairwise_test_note=pairwise_test_note,
        min_feret_mm=min_feret_mm,
        min_area_mm2=min_area_mm2,
        max_feret_mm=max_feret_mm,
    )
