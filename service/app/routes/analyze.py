from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

try:
    from ..config import TMP_DIR
    from ..fiji_runner import run_fiji_measurement
    from ..models import AnalyzeImagesRequest, AnalyzeImagesResponse, SampleResult, StatisticsSummary
    from ..services import (
        build_kde_plot_html,
        compute_pairwise_tests,
        compute_sample_statistics,
        get_measurement_values,
        render_kde_plot_svg,
    )
except ImportError:
    from config import TMP_DIR
    from fiji_runner import run_fiji_measurement
    from models import AnalyzeImagesRequest, AnalyzeImagesResponse, SampleResult, StatisticsSummary
    from services import (
        build_kde_plot_html,
        compute_pairwise_tests,
        compute_sample_statistics,
        get_measurement_values,
        render_kde_plot_svg,
    )

router = APIRouter(tags=["analyze"])
DEFAULT_ANALYZE_ATTRIBUTE = "Feret"


def _validate_image_files(
    payload: AnalyzeImagesRequest,
    files: list[UploadFile],
) -> dict[str, UploadFile]:
    files_by_name = {}
    for upload in files:
        if not upload.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All uploaded files must have a filename.",
            )
        files_by_name[upload.filename] = upload

    expected_keys = {sample.file_key for sample in payload.samples}
    actual_keys = set(files_by_name.keys())
    if expected_keys != actual_keys:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Uploaded files do not match payload.samples[].file_key.",
                "expected_file_keys": sorted(expected_keys),
                "actual_filenames": sorted(actual_keys),
            },
        )
    return files_by_name


def _build_analyze_workspace() -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    workspace = TMP_DIR / "analyze" / f"{timestamp}_{uuid4().hex[:8]}"
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


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


@router.post(
    "/analyze/images",
    response_model=AnalyzeImagesResponse,
    summary="Analyze uploaded JPEG images",
)
async def analyze_images(
    payload: str = Form(..., description="JSON string for AnalyzeImagesRequest"),
    files: list[UploadFile] = File(..., description="JPEG files"),
) -> AnalyzeImagesResponse:
    try:
        request_model = AnalyzeImagesRequest.model_validate_json(payload)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid payload JSON: {exc}",
        ) from exc

    files_by_name = _validate_image_files(request_model, files)
    workspace = _build_analyze_workspace()
    attribute = DEFAULT_ANALYZE_ATTRIBUTE

    try:
        samples_by_label = {}
        sample_results = []

        for sample in request_model.samples:
            upload = files_by_name[sample.file_key]
            image_path = workspace / sample.file_key
            image_path.write_bytes(await upload.read())

            raw_csv_path = run_fiji_measurement(
                image_path=image_path,
                output_dir=workspace,
                sample_name=Path(sample.file_key).stem,
                scale_diameter_mm=request_model.options.scale_diameter_mm,
                threshold_min=request_model.options.threshold_min,
                threshold_max=request_model.options.threshold_max,
                roi_diameter_scale=request_model.options.roi_diameter_scale,
            )

            values = get_measurement_values(raw_csv_path, attribute)
            sample_stats = compute_sample_statistics(values, clip_zero=True)
            samples_by_label[sample.sample_name] = values
            sample_results.append(
                SampleResult(
                    sample_name=sample.sample_name,
                    particle_count=sample_stats.count,
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
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    mean_values = [sample.mean for sample in sample_results if sample.mean is not None]
    median_values = [sample.median for sample in sample_results if sample.median is not None]
    return AnalyzeImagesResponse(
        samples=sample_results,
        plot_path=str(plot_path),
        statistics=StatisticsSummary(
            compared_samples=len(request_model.samples),
            mean_of_means=(sum(mean_values) / len(mean_values)) if mean_values else None,
            mean_of_medians=(sum(median_values) / len(median_values)) if median_values else None,
            attribute=attribute,
            pairwise_test_note=pairwise_test_note,
        ),
    )
