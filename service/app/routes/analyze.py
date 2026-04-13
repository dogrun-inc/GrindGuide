from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

try:
    from ..models import AnalyzeImagesRequest, AnalyzeImagesResponse, SampleResult, StatisticsSummary
except ImportError:
    from models import AnalyzeImagesRequest, AnalyzeImagesResponse, SampleResult, StatisticsSummary

router = APIRouter(tags=["analyze"])


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

    _validate_image_files(request_model, files)

    # TODO:
    # 1. Save uploaded JPEG files to a temp workspace.
    # 2. Run calibration + Fiji measurement for each sample.
    # 3. Build distributions, KDE plot, and statistics.
    placeholder_samples = [
        SampleResult(
            sample_name=sample.sample_name,
            particle_count=0,
            unit=request_model.options.output_unit,
            raw_csv_path=None,
        )
        for sample in request_model.samples
    ]
    return AnalyzeImagesResponse(
        samples=placeholder_samples,
        plot_path=None,
        statistics=StatisticsSummary(compared_samples=len(request_model.samples)),
    )
