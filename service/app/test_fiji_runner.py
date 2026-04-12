from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import shutil
import sys

try:
    from .config import (
        DEFAULT_SCALE_DIAMETER_MM,
        FIJI_EXECUTABLE,
        FIJI_HEADLESS,
        MACRO_PATH,
        ROI_DIAMETER_SCALE,
    )
    from .fiji_runner import run_fiji_measurement
except ImportError:
    from config import (
        DEFAULT_SCALE_DIAMETER_MM,
        FIJI_EXECUTABLE,
        FIJI_HEADLESS,
        MACRO_PATH,
        ROI_DIAMETER_SCALE,
    )
    from fiji_runner import run_fiji_measurement


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Run the Fiji particle-measurement PoC for a single image."
    )
    parser.add_argument("--input", required=True, help="Path to the input image.")
    parser.add_argument("--output", required=True, help="Path to the output CSV.")
    parser.add_argument(
        "--scale-diameter-mm",
        type=float,
        default=DEFAULT_SCALE_DIAMETER_MM,
        help="Actual diameter of the scale circle in millimeters.",
    )
    parser.add_argument(
        "--threshold-min",
        type=float,
        default=None,
        help="Lower threshold value passed to Fiji. If omitted, auto threshold is used.",
    )
    parser.add_argument(
        "--threshold-max",
        type=float,
        default=None,
        help="Upper threshold value passed to Fiji. If omitted, auto threshold is used.",
    )
    parser.add_argument(
        "--roi-diameter-scale",
        type=float,
        default=ROI_DIAMETER_SCALE,
        help="Scale factor applied to the detected calibration circle when building the oval ROI.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not input_path.exists():
        parser.error(f"input image does not exist: {input_path}")

    if not Path(FIJI_EXECUTABLE).exists():
        parser.error(f"Fiji executable does not exist: {FIJI_EXECUTABLE}")

    if not MACRO_PATH.exists():
        parser.error(f"Fiji macro does not exist: {MACRO_PATH}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    sample_name = output_path.stem
    temp_output_dir = output_path.parent

    print(f"[test_fiji_runner] input={input_path}")
    print(f"[test_fiji_runner] output={output_path}")
    print(f"[test_fiji_runner] fiji_executable={FIJI_EXECUTABLE}")
    print(f"[test_fiji_runner] fiji_headless={FIJI_HEADLESS}")
    print(f"[test_fiji_runner] macro_path={MACRO_PATH}")
    print(f"[test_fiji_runner] scale_diameter_mm={args.scale_diameter_mm}")
    print(f"[test_fiji_runner] threshold_min={args.threshold_min}")
    print(f"[test_fiji_runner] threshold_max={args.threshold_max}")
    print(f"[test_fiji_runner] roi_diameter_scale={args.roi_diameter_scale}")

    result_csv = run_fiji_measurement(
        image_path=input_path,
        output_dir=temp_output_dir,
        sample_name=sample_name,
        scale_diameter_mm=args.scale_diameter_mm,
        threshold_min=args.threshold_min,
        threshold_max=args.threshold_max,
        roi_diameter_scale=args.roi_diameter_scale,
    )

    if result_csv != output_path:
        shutil.move(str(result_csv), str(output_path))

    print(f"[test_fiji_runner] completed: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
