from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile, status

try:
    from ..config import TMP_DIR
    from ..models import CompareCsvRequest, JobAcceptedResponse
    from ..services import job_store, process_compare_request
except ImportError:
    from config import TMP_DIR
    from models import CompareCsvRequest, JobAcceptedResponse
    from services import job_store, process_compare_request

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


def _build_job_workspace(job_id: str) -> Path:
    workspace = TMP_DIR / "compare" / job_id
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


def _run_compare_job(
    job_id: str,
    request_model: CompareCsvRequest,
    workspace: Path,
    csv_paths_by_name: dict[str, Path],
) -> None:
    try:
        job_store.mark_running(job_id)
        result = process_compare_request(
            request_model=request_model,
            workspace=workspace,
            csv_paths_by_name=csv_paths_by_name,
            progress_callback=lambda completed, current: job_store.update_progress(
                job_id,
                completed_samples=completed,
                current_sample_name=current,
            ),
        )
        job_store.mark_completed(job_id, result)
    except Exception as exc:
        job_store.mark_failed(job_id, str(exc))


@router.post(
    "/compare/csv",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue CSV comparison job",
)
async def compare_csv(
    background_tasks: BackgroundTasks,
    payload: str = Form(..., description="JSON string for CompareCsvRequest"),
    files: list[UploadFile] = File(..., description="Measurement CSV files"),
) -> JobAcceptedResponse:
    try:
        request_model = CompareCsvRequest.model_validate_json(payload)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid payload JSON: {exc}",
        ) from exc

    files_by_name = _validate_csv_files(request_model, files)
    job = job_store.create_job("compare", total_samples=len(request_model.samples))
    workspace = _build_job_workspace(job.job_id)
    csv_paths_by_name = {}

    for file_key, upload in files_by_name.items():
        csv_path = workspace / file_key
        csv_path.write_bytes(await upload.read())
        csv_paths_by_name[file_key] = csv_path

    background_tasks.add_task(
        _run_compare_job,
        job.job_id,
        request_model,
        workspace,
        csv_paths_by_name,
    )

    return JobAcceptedResponse(
        job_id=job.job_id,
        status=job.status,
        status_url=f"/api/jobs/{job.job_id}",
        result_url=f"/api/jobs/{job.job_id}/result",
    )
