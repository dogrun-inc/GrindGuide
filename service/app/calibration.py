from pathlib import Path
import cv2


def detect_scale_circle(image_path: Path, scale_diameter_mm: float) -> dict:
    """
    Detect a circular scale marker in an image and calculate pixel-to-millimeter conversion factors.
    
    This function reads an image, applies preprocessing filters, and uses the Hough Circle Transform
    to detect circular objects. It identifies the largest circle (assumed to be the scale marker)
    and calculates calibration parameters for converting pixel measurements to real-world millimeters.
    
    Args:
        image_path (Path): File path to the input image.
        scale_diameter_mm (float): The actual diameter of the scale circle in millimeters.
    
    Returns:
        dict: A dictionary containing the following keys:
            - circle_center_x (float): X-coordinate of the detected circle's center in pixels.
            - circle_center_y (float): Y-coordinate of the detected circle's center in pixels.
            - circle_radius_px (float): Radius of the detected circle in pixels.
            - circle_diameter_px (float): Diameter of the detected circle in pixels.
            - px_per_mm (float): Conversion factor from millimeters to pixels.
            - mm_per_px (float): Conversion factor from pixels to millimeters.
    
    Raises:
        ValueError: If the image cannot be read from the specified path or if no circle is detected.
    
    Notes:
        - cv2.imread(): Reads the image from the file path in BGR color format.
        - cv2.cvtColor(): Converts the BGR image to grayscale for circle detection.
        - cv2.medianBlur(): Applies median filtering (kernel size 5x5) to reduce noise.
        - cv2.HoughCircles(): Detects circles using the Hough Circle Transform with HOUGH_GRADIENT method.
          Parameters: dp=1.2 (inverse ratio of accumulator resolution), minDist=100 (minimum distance
          between circles), param1=100 (Canny edge detection threshold), param2=30 (accumulator threshold),
          minRadius=10 (minimum circle radius), maxRadius=0 (no maximum radius limit).
        - The largest detected circle is selected as the scale marker (Proof of Concept approach).
    """
    
    print(f"[calibration] image_path={image_path}, scale_diameter_mm={scale_diameter_mm}")

    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Failed to read image: {image_path}")
    image_height, image_width = image.shape[:2]
    print(f"[calibration] image_size=(width={image_width}, height={image_height})")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)

    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=100,
        param1=100,
        param2=30,
        minRadius=10,
        maxRadius=0,
    )

    if circles is None:
        raise ValueError("No scale circle detected")

    circles = circles[0]
    print(f"[calibration] detected_circles={len(circles)}")
    valid_circles = []
    for idx, candidate in enumerate(circles):
        center_x = float(candidate[0])
        center_y = float(candidate[1])
        radius_px = float(candidate[2])
        is_inside_image = (
            center_x - radius_px >= 0
            and center_y - radius_px >= 0
            and center_x + radius_px <= image_width
            and center_y + radius_px <= image_height
        )
        print(
            "[calibration] "
            f"candidate[{idx}]=(x={center_x}, y={center_y}, radius={radius_px}, "
            f"diameter={radius_px * 2.0}, inside_image={is_inside_image})"
        )
        if is_inside_image:
            valid_circles.append(candidate)

    if not valid_circles:
        raise ValueError("No valid scale circle detected inside image bounds")

    print(f"[calibration] valid_circles={len(valid_circles)}")
    # スケール円は画像幅の大半を占める想定のため、
    # まず「画像幅の70〜95%の直径を持つ候補」を優先する。
    # こうすることで、粉体や文字などの小さな円形ノイズを採用しにくくする。
    # この条件に合う候補がない場合は、撮影条件のばらつきを考慮して
    # 画像内に収まる候補全体から最大円をフォールバック採用する。
    min_preferred_diameter = image_width * 0.70
    max_preferred_diameter = image_width * 0.95
    preferred_circles = [
        candidate
        for candidate in valid_circles
        if min_preferred_diameter <= float(candidate[2]) * 2.0 <= max_preferred_diameter
    ]
    print(
        "[calibration] "
        f"preferred_diameter_range=({min_preferred_diameter}, {max_preferred_diameter}), "
        f"preferred_circles={len(preferred_circles)}"
    )

    candidate_pool = preferred_circles if preferred_circles else valid_circles
    if preferred_circles:
        print("[calibration] selecting from preferred_circles")
    else:
        print("[calibration] preferred_circles empty, falling back to valid_circles")

    # 現行実装では優先候補群のうち最大円を採用
    circle = max(candidate_pool, key=lambda c: c[2])
    radius_px = float(circle[2])
    diameter_px = radius_px * 2.0
    px_per_mm = diameter_px / scale_diameter_mm
    print(
        "[calibration] "
        f"selected_circle=(x={float(circle[0])}, y={float(circle[1])}, radius={radius_px}), "
        f"diameter_px={diameter_px}, px_per_mm={px_per_mm}, mm_per_px={1.0 / px_per_mm}"
    )

    return {
        "circle_center_x": float(circle[0]),
        "circle_center_y": float(circle[1]),
        "circle_radius_px": radius_px,
        "circle_diameter_px": diameter_px,
        "px_per_mm": px_per_mm,
        "mm_per_px": 1.0 / px_per_mm,
    }
