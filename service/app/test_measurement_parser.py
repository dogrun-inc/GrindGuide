from pathlib import Path

import pandas as pd
import pytest

from service.app.services.measurement_parser import (
    convert_feret_px_bounds_to_mm,
    filter_measurement_dataframe,
    filter_measurement_values,
    get_measurement_values_from_dataframe,
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


def test_get_measurement_values_from_dataframe_returns_numeric_array():
    df = pd.DataFrame({"Feret": [0.2, 0.3, 0.4]})

    values = get_measurement_values_from_dataframe(df, "Feret")

    assert values.tolist() == [0.2, 0.3, 0.4]


def test_convert_feret_px_bounds_to_mm_returns_expected_thresholds():
    min_mm, max_mm = convert_feret_px_bounds_to_mm(px_per_mm=54.0, min_feret_px=10, max_feret_px=20)

    assert min_mm == pytest.approx(10 / 54.0)
    assert max_mm == pytest.approx(20 / 54.0)


def test_filter_measurement_values_applies_bounds():
    values = filter_measurement_values(
        values=[0.1, 0.2, 0.3, 0.4],
        min_value=0.15,
        max_value=0.35,
    )

    assert values.tolist() == [0.2, 0.3]


def test_filter_measurement_dataframe_applies_feret_and_area_bounds():
    df = pd.DataFrame(
        {
            "Feret": [0.1, 0.2, 0.3, 0.4],
            "Area": [0.01, 0.02, 0.03, 0.04],
        }
    )

    filtered = filter_measurement_dataframe(
        df,
        min_feret_mm=0.2,
        min_area_mm2=0.02,
    )

    assert filtered["Feret"].tolist() == [0.2, 0.3, 0.4]
