from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

try:
    from ..models import AnalyzeImagesResponse, JobStatusResponse
    from ..services import job_store
except ImportError:
    from models import AnalyzeImagesResponse, JobStatusResponse
    from services import job_store

router = APIRouter(tags=["jobs"])


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get asynchronous job status",
)
async def get_job_status(job_id: str) -> JobStatusResponse:
    try:
        return job_store.build_status_response(job_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}",
        ) from exc


@router.get(
    "/jobs/{job_id}/result",
    response_model=AnalyzeImagesResponse,
    summary="Get asynchronous job result",
)
async def get_job_result(job_id: str) -> AnalyzeImagesResponse:
    try:
        job = job_store.require_job(job_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}",
        ) from exc

    if job.status == "completed" and job.result is not None:
        return job.result
    if job.status == "failed":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=job.error_message or "Job failed.",
        )
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "message": "Job result is not ready yet.",
            "job_id": job_id,
            "status": job.status,
        },
    )
