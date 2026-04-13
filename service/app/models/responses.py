from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SampleResult(BaseModel):
    sample_name: str = Field(..., min_length=1)
    particle_count: int = Field(..., ge=0)
    unit: Literal["mm", "px"]
    raw_csv_path: str | None = None


class StatisticsSummary(BaseModel):
    compared_samples: int = Field(..., ge=0)
    mean_of_means: float | None = None
    mean_of_medians: float | None = None


class AnalyzeImagesResponse(BaseModel):
    samples: list[SampleResult] = Field(default_factory=list)
    plot_path: str | None = None
    statistics: StatisticsSummary
