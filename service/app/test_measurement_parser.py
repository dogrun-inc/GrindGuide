from pathlib import Path

import pandas as pd
import pytest

from service.app.services.measurement_parser import (
    get_measurement_values,
    normalize_measurement_dataframe,
    read_measurement_csv,
)


def test_normalize_measurement_dataframe_drops_index_like_column():
    df = pd.DataFrame(
        {
            " ": [1, 2],
            "Feret": [0.5, 0.7],
            "Area": [1.2, 1.4],
        }
    )

    normalized = normalize_measurement_dataframe(df)

    assert list(normalized.columns) == ["Feret", "Area"]


def test_read_measurement_csv_supports_legacy_results_file():
    df = read_measurement_csv(Path("service/app/tmp/Results_7084.csv"))

    assert "Feret" in df.columns
    assert "Area" in df.columns
    assert " " not in df.columns


def test_get_measurement_values_returns_numeric_array():
    values = get_measurement_values(Path("service/app/tmp/Results_7084.csv"), "Feret")

    assert values.size > 0
    assert values.dtype.kind == "f"


def test_get_measurement_values_rejects_missing_attribute():
    with pytest.raises(ValueError, match="Attribute 'Round' not found"):
        get_measurement_values(Path("service/app/tmp/Results_7084.csv"), "Round")
