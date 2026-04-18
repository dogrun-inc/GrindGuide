from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

INDEX_LIKE_COLUMNS = {"", " ", "Unnamed: 0"}


def normalize_measurement_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    if not normalized.columns.empty and str(normalized.columns[0]).strip() in INDEX_LIKE_COLUMNS:
        normalized = normalized.iloc[:, 1:]
    return normalized


def read_measurement_csv(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    return normalize_measurement_dataframe(df)


def get_measurement_values_from_dataframe(df: pd.DataFrame, attribute: str) -> np.ndarray:
    if attribute not in df.columns:
        raise ValueError(f"Attribute '{attribute}' not found in measurement DataFrame")
    values = df[attribute].dropna().values.astype(float)
    if values.size == 0:
        raise ValueError(f"Attribute '{attribute}' contains no usable values")
    return values


def get_measurement_values(path: str | Path, attribute: str) -> np.ndarray:
    df = read_measurement_csv(path)
    try:
        return get_measurement_values_from_dataframe(df, attribute)
    except ValueError as exc:
        message = str(exc)
        if "not found" in message:
            raise ValueError(f"Attribute '{attribute}' not found in measurement CSV: {path}") from exc
        raise ValueError(f"Attribute '{attribute}' contains no usable values: {path}") from exc


def convert_feret_px_bounds_to_mm(
    px_per_mm: float,
    min_feret_px: float | None = None,
    max_feret_px: float | None = None,
) -> tuple[float | None, float | None]:
    if px_per_mm <= 0:
        raise ValueError("px_per_mm must be greater than zero")

    min_feret_mm = None if min_feret_px is None else float(min_feret_px) / float(px_per_mm)
    max_feret_mm = None if max_feret_px is None else float(max_feret_px) / float(px_per_mm)
    return min_feret_mm, max_feret_mm


def filter_measurement_values(
    values: np.ndarray,
    min_value: float | None = None,
    max_value: float | None = None,
) -> np.ndarray:
    filtered = np.asarray(values, dtype=float)
    if filtered.size == 0:
        return filtered
    if min_value is not None:
        filtered = filtered[filtered >= float(min_value)]
    if max_value is not None:
        filtered = filtered[filtered <= float(max_value)]
    return filtered


def filter_measurement_dataframe(
    df: pd.DataFrame,
    min_feret_mm: float | None = None,
    max_feret_mm: float | None = None,
    min_area_mm2: float | None = None,
    max_area_mm2: float | None = None,
) -> pd.DataFrame:
    filtered = df.copy()
    if min_feret_mm is not None:
        if "Feret" not in filtered.columns:
            raise ValueError("Feret column is required for min_feret_mm filtering")
        filtered = filtered[filtered["Feret"] >= float(min_feret_mm)]
    if max_feret_mm is not None:
        if "Feret" not in filtered.columns:
            raise ValueError("Feret column is required for max_feret_mm filtering")
        filtered = filtered[filtered["Feret"] <= float(max_feret_mm)]
    if min_area_mm2 is not None:
        if "Area" not in filtered.columns:
            raise ValueError("Area column is required for min_area_mm2 filtering")
        filtered = filtered[filtered["Area"] >= float(min_area_mm2)]
    if max_area_mm2 is not None:
        if "Area" not in filtered.columns:
            raise ValueError("Area column is required for max_area_mm2 filtering")
        filtered = filtered[filtered["Area"] <= float(max_area_mm2)]
    return filtered
