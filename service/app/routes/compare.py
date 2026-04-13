from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

try:
    from ..models import AnalyzeImagesResponse, CompareCsvRequest, SampleResult, StatisticsSummary
except ImportError:
    from models import AnalyzeImagesResponse, CompareCsvRequest, SampleResult, StatisticsSummary

router = APIRouter(tags=["compare"])


def _validate_csv_files(
    payload: CompareCsvRequest,
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
    "/compare/csv",
    response_model=AnalyzeImagesResponse,
    summary="Compare uploaded CSV measurement files",
)
async def compare_csv(
    payload: str = Form(..., description="JSON string for CompareCsvRequest"),
    files: list[UploadFile] = File(..., description="Measurement CSV files"),
) -> AnalyzeImagesResponse:
    try:
        request_model = CompareCsvRequest.model_validate_json(payload)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid payload JSON: {exc}",
        ) from exc

    _validate_csv_files(request_model, files)

    # TODO:
    # 1. Parse uploaded CSV files.
    # 2. Build distributions, KDE plot, and statistics.
    placeholder_samples = [
        SampleResult(
            sample_name=sample.sample_name,
            particle_count=0,
            unit=sample.unit,
            raw_csv_path=None,
        )
        for sample in request_model.samples
    ]
    return AnalyzeImagesResponse(
        samples=placeholder_samples,
        plot_path=None,
        statistics=StatisticsSummary(compared_samples=len(request_model.samples)),
    )
