import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TMP_DIR = BASE_DIR / "app" / "tmp"
MACRO_PATH = BASE_DIR / "app" / "measure_particles.ijm"
JYTHON_SCRIPT_PATH = BASE_DIR / "app" / "measure_particles.py"


def _find_default_fiji_executable() -> str:
    candidates = [
        "/usr/local/bin/Fiji.app/ImageJ-linux64", # 2024-06-01時点でのLinux版Fijiのデフォルトパス
        "/usr/local/bin/Fiji.app/fiji-linux-x64", 
        "/usr/local/bin/ImageJ-linux64",
        "/opt/Fiji.app/ImageJ-linux64",
        "/opt/Fiji/ImageJ-linux64",
        str(BASE_DIR / "tools" / "Fiji.app" / "ImageJ-linux64"),
        "/Applications/Fiji/Fiji.app/Contents/MacOS/fiji-macos-arm64",
        "/Applications/Fiji.app/Contents/MacOS/ImageJ-macosx",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    return candidates[0] if sys.platform.startswith("linux") else candidates[-2]

# Fiji 20220414-1745ビルド使用
# Ubuntu 20.04はGLIBC 2.31のため、GLIBC 2.34+を要求する
# 新しいビルド（fiji-linux-x64）は動作不可。ImageJ-linux64を使うこと。
FIJI_EXECUTABLE = os.getenv("FIJI_EXECUTABLE", _find_default_fiji_executable())
MAX_UPLOAD_FILES = int(os.getenv("MAX_UPLOAD_FILES", "20"))
DEFAULT_SCALE_DIAMETER_MM = float(os.getenv("DEFAULT_SCALE_DIAMETER_MM", "50.0"))
ROI_DIAMETER_SCALE = float(os.getenv("ROI_DIAMETER_SCALE", "0.95"))
DEFAULT_MIN_FERET_MM = float(os.getenv("DEFAULT_MIN_FERET_MM", "0.2"))
DEFAULT_MIN_AREA_MM2 = float(os.getenv("DEFAULT_MIN_AREA_MM2", "0.02"))
DEFAULT_MAX_FERET_MM = float(os.getenv("DEFAULT_MAX_FERET_MM", "3.0"))
FIJI_HEADLESS = os.getenv(
    "FIJI_HEADLESS",
    "true" if sys.platform.startswith("linux") else "false",
).lower() == "true"
FIJI_USE_XVFB = os.getenv("FIJI_USE_XVFB", "false").lower() == "true"
XVFB_RUN_EXECUTABLE = os.getenv("XVFB_RUN_EXECUTABLE", "xvfb-run")
