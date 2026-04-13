from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ImageSampleInput(BaseModel):
    file_key: str = Field(
        ...,
        min_length=1,
        description="JPEGファイルとの対応キー。当面はアップロード時のファイル名と一致させる。",
    )
    sample_name: str = Field(
        ...,
        min_length=1,
        description="表示や結果返却に使うサンプル名。",
    )
    grinder: str | None = Field(default=None, description="任意。グラインダー名。")
    grind_setting: str | None = Field(default=None, description="任意。メモリやクリック数。")
    brew_method: str | None = Field(default=None, description="任意。V60, Espressoなど。")
    notes: str | None = Field(default=None, description="任意メモ。")


class AnalyzeImagesOptions(BaseModel):
    scale_diameter_mm: float = Field(default=50.0, gt=0)
    threshold_min: float | None = Field(default=None, ge=0, le=255)
    threshold_max: float | None = Field(default=None, ge=0, le=255)
    roi_diameter_scale: float = Field(default=0.95, gt=0)
    output_unit: Literal["mm", "px"] = "mm"

    @model_validator(mode="after")
    def validate_threshold_pair(self) -> AnalyzeImagesOptions:
        if (self.threshold_min is None) != (self.threshold_max is None):
            raise ValueError("threshold_min and threshold_max must be provided together")
        if (
            self.threshold_min is not None
            and self.threshold_max is not None
            and self.threshold_min > self.threshold_max
        ):
            raise ValueError("threshold_min must be <= threshold_max")
        return self


class AnalyzeImagesRequest(BaseModel):
    samples: list[ImageSampleInput] = Field(..., min_length=1)
    options: AnalyzeImagesOptions = Field(default_factory=AnalyzeImagesOptions)

    @model_validator(mode="after")
    def validate_unique_file_keys(self) -> AnalyzeImagesRequest:
        file_keys = [sample.file_key for sample in self.samples]
        if len(file_keys) != len(set(file_keys)):
            raise ValueError("file_key must be unique")
        return self


class CsvSampleInput(BaseModel):
    file_key: str = Field(
        ...,
        min_length=1,
        description="CSVファイルとの対応キー。当面はアップロード時のファイル名と一致させる。",
    )
    sample_name: str = Field(
        ...,
        min_length=1,
        description="表示や結果返却に使うサンプル名。",
    )
    unit: Literal["mm", "px"] = "mm"
    grinder: str | None = Field(default=None, description="任意。グラインダー名。")
    grind_setting: str | None = Field(default=None, description="任意。メモリやクリック数。")
    brew_method: str | None = Field(default=None, description="任意。V60, Espressoなど。")
    notes: str | None = Field(default=None, description="任意メモ。")


class CompareCsvRequest(BaseModel):
    samples: list[CsvSampleInput] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_unique_file_keys(self) -> CompareCsvRequest:
        file_keys = [sample.file_key for sample in self.samples]
        if len(file_keys) != len(set(file_keys)):
            raise ValueError("file_key must be unique")
        return self
