import pytest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import cv2

try:
    from . import calibration
except ImportError:
    import calibration


class TestDetectScaleCircle:
    """
    TestDetectScaleCircle - detect_scale_circle 関数のユニットテストクラス
    ## 概要
    `calibration.detect_scale_circle` 関数の動作を検証するテストスイート。
    OpenCV の `imread` および `HoughCircles` をモック化することで、
    実際の画像ファイルを使用せずに各シナリオをテストする。
    ## テスト対象
    - `calibration.detect_scale_circle(image_path: Path, scale_diameter_mm: float) -> dict`
        - `image_path`: 画像ファイルのパス
        - `scale_diameter_mm`: スケール円の実寸直径（mm）
        - 戻り値: 以下のキーを持つ辞書
            - `circle_center_x` (float): 検出円の中心X座標（px）
            - `circle_center_y` (float): 検出円の中心Y座標（px）
            - `circle_radius_px` (float): 検出円の半径（px）
            - `circle_diameter_px` (float): 検出円の直径（px）
            - `px_per_mm` (float): 1mmあたりのピクセル数
            - `mm_per_px` (float): 1pxあたりのmm数
    ## テストケース
    | メソッド名 | 検証内容 |
    |---|---|
    | `test_detect_scale_circle_success` | 正常系: 有効な画像から円を検出し、キャリブレーション値を正確に算出できること |
    | `test_detect_scale_circle_image_read_failure` | 異常系: 画像読み込み失敗時に `ValueError("Failed to read image")` が送出されること |
    | `test_detect_scale_circle_no_circle_detected` | 異常系: 円が検出されない場合に `ValueError("No scale circle detected")` が送出されること |
    | `test_detect_scale_circle_selects_largest` | 正常系: 複数の円が検出された場合、最大半径の円が選択されること |
    | `test_detect_scale_circle_different_scale_diameter` | 正常系: 異なるスケール直径（mm）を指定した場合にキャリブレーション値が正確に算出されること |
    """

    def test_detect_scale_circle_success(self):
        """Test successful circle detection with valid image."""
        mock_image = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_image = cv2.circle(mock_image, (320, 240), 50, (255, 255, 255), -1)
        
        with patch.object(calibration.cv2, 'imread', return_value=mock_image):
            with patch.object(calibration.cv2, 'HoughCircles') as mock_hough:
                mock_circles = np.array([[[320.0, 240.0, 50.0]]])
                mock_hough.return_value = mock_circles
                
                result = calibration.detect_scale_circle(Path("test.jpg"), 25.0)
                
                assert result["circle_center_x"] == 320.0
                assert result["circle_center_y"] == 240.0
                assert result["circle_radius_px"] == 50.0
                assert result["circle_diameter_px"] == 100.0
                assert result["px_per_mm"] == 4.0
                assert result["mm_per_px"] == 0.25

    def test_detect_scale_circle_image_read_failure(self):
        """Test that ValueError is raised when image cannot be read."""
        with patch.object(calibration.cv2, 'imread', return_value=None):
            with pytest.raises(ValueError, match="Failed to read image"):
                calibration.detect_scale_circle(Path("nonexistent.jpg"), 25.0)

    def test_detect_scale_circle_no_circle_detected(self):
        """Test that ValueError is raised when no circle is detected."""
        mock_image = np.zeros((480, 640, 3), dtype=np.uint8)
        
        with patch.object(calibration.cv2, 'imread', return_value=mock_image):
            with patch.object(calibration.cv2, 'HoughCircles', return_value=None):
                with pytest.raises(ValueError, match="No scale circle detected"):
                    calibration.detect_scale_circle(Path("test.jpg"), 25.0)

    def test_detect_scale_circle_selects_largest(self):
        """Test that the largest circle is selected when multiple circles are detected."""
        mock_image = np.zeros((480, 640, 3), dtype=np.uint8)
        
        with patch.object(calibration.cv2, 'imread', return_value=mock_image):
            with patch.object(calibration.cv2, 'HoughCircles') as mock_hough:
                mock_circles = np.array([[[100.0, 100.0, 30.0], [320.0, 240.0, 60.0], [200.0, 200.0, 40.0]]])
                mock_hough.return_value = mock_circles
                
                result = calibration.detect_scale_circle(Path("test.jpg"), 25.0)
                
                assert result["circle_center_x"] == 320.0
                assert result["circle_center_y"] == 240.0
                assert result["circle_radius_px"] == 60.0
                assert result["circle_diameter_px"] == 120.0

    def test_detect_scale_circle_different_scale_diameter(self):
        """Test calibration with different scale diameters."""
        mock_image = np.zeros((480, 640, 3), dtype=np.uint8)
        
        with patch.object(calibration.cv2, 'imread', return_value=mock_image):
            with patch.object(calibration.cv2, 'HoughCircles') as mock_hough:
                mock_circles = np.array([[[320.0, 240.0, 50.0]]])
                mock_hough.return_value = mock_circles
                result = calibration.detect_scale_circle(Path("test.jpg"), 50.0)
                
                assert result["px_per_mm"] == 2.0
                assert result["mm_per_px"] == 0.5

    def test_detect_scale_circle_with_real_image(self):
        """Test that the real sample image detects the expected 50 mm scale circle."""
        image_path = Path("service/tests/IMG_7066.jpg")
        result = calibration.detect_scale_circle(image_path, 50.0)

        assert result["circle_diameter_px"] == pytest.approx(2720.0, rel=0.03)
        assert result["px_per_mm"] == pytest.approx(54.4, rel=0.03)
        assert result["mm_per_px"] == pytest.approx(1.0 / 54.4, rel=0.03)
