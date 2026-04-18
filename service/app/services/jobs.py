from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Literal
from uuid import uuid4

from ..models import AnalyzeImagesResponse, JobStatusResponse

JobState = Literal["queued", "running", "completed", "failed"]
JobType = Literal["analyze", "compare"]


@dataclass
class JobRecord:
    job_id: str
    job_type: JobType
    status: JobState
    total_samples: int
    completed_samples: int
    current_sample_name: str | None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    result: AnalyzeImagesResponse | None = None


class InMemoryJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._lock = Lock()

    def create_job(self, job_type: JobType, total_samples: int) -> JobRecord:
        now = datetime.now(timezone.utc)
        job = JobRecord(
            job_id=f"{job_type}_{now.strftime('%Y%m%dT%H%M%SZ')}_{uuid4().hex[:8]}",
            job_type=job_type,
            status="queued",
            total_samples=total_samples,
            completed_samples=0,
            current_sample_name=None,
            created_at=now,
        )
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get_job(self, job_id: str) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)

    def require_job(self, job_id: str) -> JobRecord:
        job = self.get_job(job_id)
        if job is None:
            raise KeyError(job_id)
        return job

    def mark_running(self, job_id: str) -> None:
        now = datetime.now(timezone.utc)
        with self._lock:
            job = self._jobs[job_id]
            job.status = "running"
            job.started_at = now

    def update_progress(
        self,
        job_id: str,
        *,
        completed_samples: int,
        current_sample_name: str | None,
    ) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.completed_samples = completed_samples
            job.current_sample_name = current_sample_name

    def mark_completed(self, job_id: str, result: AnalyzeImagesResponse) -> None:
        now = datetime.now(timezone.utc)
        with self._lock:
            job = self._jobs[job_id]
            job.status = "completed"
            job.completed_at = now
            job.completed_samples = job.total_samples
            job.current_sample_name = None
            job.result = result

    def mark_failed(self, job_id: str, error_message: str) -> None:
        now = datetime.now(timezone.utc)
        with self._lock:
            job = self._jobs[job_id]
            job.status = "failed"
            job.completed_at = now
            job.error_message = error_message
            job.current_sample_name = None

    def build_status_response(self, job_id: str) -> JobStatusResponse:
        job = self.require_job(job_id)
        return JobStatusResponse(
            job_id=job.job_id,
            job_type=job.job_type,
            status=job.status,
            total_samples=job.total_samples,
            completed_samples=job.completed_samples,
            current_sample_name=job.current_sample_name,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error_message=job.error_message,
        )


job_store = InMemoryJobStore()
