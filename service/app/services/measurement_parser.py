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


def get_measurement_values(path: str | Path, attribute: str) -> np.ndarray:
    df = read_measurement_csv(path)
    if attribute not in df.columns:
        raise ValueError(f"Attribute '{attribute}' not found in measurement CSV: {path}")
    values = df[attribute].dropna().values.astype(float)
    if values.size == 0:
        raise ValueError(f"Attribute '{attribute}' contains no usable values: {path}")
    return values
