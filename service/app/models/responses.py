from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SampleResult(BaseModel):
    sample_name: str = Field(..., min_length=1)
    particle_count: int = Field(..., ge=0)
    filtered_particle_count: int | None = Field(default=None, ge=0)
    unit: Literal["mm", "px"]
    raw_csv_path: str | None = None
    mean: float | None = None
    std: float | None = None
    cv: float | None = None
    skew: float | None = None
    kurtosis: float | None = None
    median: float | None = None
    kde_peak: float | None = None


class StatisticsSummary(BaseModel):
    compared_samples: int = Field(..., ge=0)
    mean_of_means: float | None = None
    mean_of_medians: float | None = None
    attribute: str | None = None
    pairwise_test_note: str | None = None
    min_feret_mm: float | None = None
    min_area_mm2: float | None = None
    max_feret_mm: float | None = None


class AnalyzeImagesResponse(BaseModel):
    samples: list[SampleResult] = Field(default_factory=list)
    plot_path: str | None = None
    statistics: StatisticsSummary


JobState = Literal["queued", "running", "completed", "failed"]
JobType = Literal["analyze", "compare"]


class JobAcceptedResponse(BaseModel):
    job_id: str = Field(..., min_length=1)
    status: JobState
    status_url: str = Field(..., min_length=1)
    result_url: str = Field(..., min_length=1)


class JobStatusResponse(BaseModel):
    job_id: str = Field(..., min_length=1)
    job_type: JobType
    status: JobState
    total_samples: int = Field(..., ge=0)
    completed_samples: int = Field(..., ge=0)
    current_sample_name: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
