from __future__ import annotations

from pathlib import Path
import subprocess

try:
    from .config import (
        DEFAULT_SCALE_DIAMETER_MM,
        FIJI_EXECUTABLE,
        FIJI_HEADLESS,
        FIJI_USE_XVFB,
        MACRO_PATH,
        ROI_DIAMETER_SCALE,
        XVFB_RUN_EXECUTABLE,
    )
except ImportError:
    from config import (
        DEFAULT_SCALE_DIAMETER_MM,
        FIJI_EXECUTABLE,
        FIJI_HEADLESS,
        FIJI_USE_XVFB,
        MACRO_PATH,
        ROI_DIAMETER_SCALE,
        XVFB_RUN_EXECUTABLE,
    )


def _format_macro_arg(key: str, value: object) -> str:
    return f"{key}={value}"


def _build_roi_from_calibration(calibration_result: dict, roi_diameter_scale: float) -> dict:
    scaled_diameter = calibration_result["circle_diameter_px"] * roi_diameter_scale
    scaled_radius = scaled_diameter / 2.0
    center_x = calibration_result["circle_center_x"]
    center_y = calibration_result["circle_center_y"]
    return {
        "roi_x": center_x - scaled_radius,
        "roi_y": center_y - scaled_radius,
        "roi_w": scaled_diameter,
        "roi_h": scaled_diameter,
    }


def _detect_scale_circle(image_path: Path, scale_diameter_mm: float) -> dict:
    try:
        from .calibration import detect_scale_circle
    except ImportError:
        from calibration import detect_scale_circle

    return detect_scale_circle(image_path, scale_diameter_mm)


def _build_macro_argument(
    image_path: Path,
    output_csv: Path,
    calibration_result: dict,
    roi: dict,
    threshold_min: float | None,
    threshold_max: float | None,
) -> str:
    args = [
        _format_macro_arg("image", image_path),
        _format_macro_arg("output", output_csv),
        _format_macro_arg("px_per_mm", calibration_result["px_per_mm"]),
        _format_macro_arg("roi_x", roi["roi_x"]),
        _format_macro_arg("roi_y", roi["roi_y"]),
        _format_macro_arg("roi_w", roi["roi_w"]),
        _format_macro_arg("roi_h", roi["roi_h"]),
    ]
    if (threshold_min is None) != (threshold_max is None):
        raise ValueError("threshold_min and threshold_max must be provided together")
    if threshold_min is not None and threshold_max is not None:
        args.append(_format_macro_arg("threshold_min", threshold_min))
        args.append(_format_macro_arg("threshold_max", threshold_max))
    return ";".join(str(item) for item in args)


def _build_fiji_command(macro_arg: str) -> list[str]:
    cmd = [
        FIJI_EXECUTABLE,
        "--console",
        "-macro",
        str(MACRO_PATH),
        macro_arg,
    ]
    if FIJI_HEADLESS:
        cmd.insert(1, "--headless")
    if FIJI_USE_XVFB:
        cmd = [XVFB_RUN_EXECUTABLE, "-a", *cmd]
    return cmd


def run_fiji_measurement(
    image_path: Path,
    output_dir: Path,
    sample_name: str,
    scale_diameter_mm: float = DEFAULT_SCALE_DIAMETER_MM,
    threshold_min: float | None = None,
    threshold_max: float | None = None,
    roi_diameter_scale: float = ROI_DIAMETER_SCALE,
) -> Path:
    output_csv = output_dir / f"{sample_name}_raw.csv"
    calibration_result = _detect_scale_circle(image_path, scale_diameter_mm)
    roi = _build_roi_from_calibration(calibration_result, roi_diameter_scale)
    print(f"[fiji_runner] calibration_result={calibration_result}")
    print(f"[fiji_runner] roi={roi}")
    arg = _build_macro_argument(
        image_path=image_path,
        output_csv=output_csv,
        calibration_result=calibration_result,
        roi=roi,
        threshold_min=threshold_min,
        threshold_max=threshold_max,
    )
    cmd = _build_fiji_command(arg)
    print(f"[fiji_runner] cmd={cmd}")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.stdout:
        print(f"[fiji_runner] Fiji STDOUT:\n{result.stdout}")
    if result.stderr:
        print(f"[fiji_runner] Fiji STDERR:\n{result.stderr}")

    if result.returncode != 0:
        raise RuntimeError(
            f"Fiji failed for {image_path.name}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    if not output_csv.exists():
        raise RuntimeError(
            f"Fiji did not produce output CSV: {output_csv}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    return output_csv
