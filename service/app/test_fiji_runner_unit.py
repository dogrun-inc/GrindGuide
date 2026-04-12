from pathlib import Path

from service.app import fiji_runner


def test_build_roi_from_calibration():
    calibration_result = {
        "circle_center_x": 100.0,
        "circle_center_y": 120.0,
        "circle_diameter_px": 80.0,
    }

    roi = fiji_runner._build_roi_from_calibration(calibration_result, 0.95)

    assert roi == {
        "roi_x": 62.0,
        "roi_y": 82.0,
        "roi_w": 76.0,
        "roi_h": 76.0,
    }


def test_build_macro_argument_with_thresholds():
    arg = fiji_runner._build_macro_argument(
        image_path=Path("/tmp/input.jpg"),
        output_csv=Path("/tmp/out.csv"),
        calibration_result={"px_per_mm": 54.4},
        roi={"roi_x": 1.0, "roi_y": 2.0, "roi_w": 3.0, "roi_h": 4.0},
        threshold_min=80.0,
        threshold_max=255.0,
    )

    assert "image=/tmp/input.jpg" in arg
    assert "output=/tmp/out.csv" in arg
    assert "px_per_mm=54.4" in arg
    assert "threshold_min=80.0" in arg
    assert "threshold_max=255.0" in arg


def test_build_macro_argument_rejects_partial_thresholds():
    try:
        fiji_runner._build_macro_argument(
            image_path=Path("/tmp/input.jpg"),
            output_csv=Path("/tmp/out.csv"),
            calibration_result={"px_per_mm": 54.4},
            roi={"roi_x": 1.0, "roi_y": 2.0, "roi_w": 3.0, "roi_h": 4.0},
            threshold_min=80.0,
            threshold_max=None,
        )
    except ValueError as exc:
        assert "provided together" in str(exc)
    else:
        raise AssertionError("expected ValueError for partial thresholds")


def test_build_fiji_command_headless_and_xvfb(monkeypatch):
    monkeypatch.setattr(fiji_runner, "FIJI_EXECUTABLE", "/opt/Fiji.app/ImageJ-linux64")
    monkeypatch.setattr(fiji_runner, "MACRO_PATH", Path("/repo/service/app/measure_particles.ijm"))
    monkeypatch.setattr(fiji_runner, "FIJI_HEADLESS", True)
    monkeypatch.setattr(fiji_runner, "FIJI_USE_XVFB", True)
    monkeypatch.setattr(fiji_runner, "XVFB_RUN_EXECUTABLE", "xvfb-run")

    cmd = fiji_runner._build_fiji_command("image=/tmp/input.jpg")

    assert cmd == [
        "xvfb-run",
        "-a",
        "/opt/Fiji.app/ImageJ-linux64",
        "--headless",
        "--console",
        "-macro",
        "/repo/service/app/measure_particles.ijm",
        "image=/tmp/input.jpg",
    ]
