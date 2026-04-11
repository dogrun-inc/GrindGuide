from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
TMP_DIR = BASE_DIR / "app" / "tmp"
MACRO_PATH = BASE_DIR / "app" / "measure_particles.ijm"

# 開発はmacOSで行うことが多いので、デフォルトのFiji実行ファイルパスはmacOS用に設定しています。必要に応じて環境変数で上書きしてください。
FIJI_EXECUTABLE = os.getenv("FIJI_EXECUTABLE", "/Applications/Fiji/Fiji.app/Contents/MacOS/fiji-macos-arm64")
MAX_UPLOAD_FILES = int(os.getenv("MAX_UPLOAD_FILES", "20"))
DEFAULT_SCALE_DIAMETER_MM = float(os.getenv("DEFAULT_SCALE_DIAMETER_MM", "50.0"))
ROI_DIAMETER_SCALE = float(os.getenv("ROI_DIAMETER_SCALE", "0.95"))
FIJI_HEADLESS = os.getenv("FIJI_HEADLESS", "false").lower() == "true"
