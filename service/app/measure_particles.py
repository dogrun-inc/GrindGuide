# measure_particles.py  (Fiji --headless --run で実行する Jython スクリプト)
from ij import IJ, ImagePlus
from ij.plugin.filter import ParticleAnalyzer
from ij.measure import ResultsTable, Measurements
from ij.process import ImageProcessor
from ij.plugin import Duplicator
from ij.gui import OvalRoi
from java.lang import Double
import os

# ---- 引数パース ------------------------------------------------
def get_arg(args, key, default=""):
    for token in args.split(";"):
        kv = token.split("=", 1)
        if len(kv) == 2 and kv[0].strip() == key:
            return kv[1].strip()
    return default

from ij.macro import Interpreter
arg = Interpreter.getDefaultMacroOptions() or ""

image_path      = get_arg(arg, "image")
output_path     = get_arg(arg, "output")
px_per_mm       = get_arg(arg, "px_per_mm")
threshold_min   = get_arg(arg, "threshold_min")
threshold_max   = get_arg(arg, "threshold_max")
roi_x           = get_arg(arg, "roi_x")
roi_y           = get_arg(arg, "roi_y")
roi_w           = get_arg(arg, "roi_w")
roi_h           = get_arg(arg, "roi_h")

outline_path         = output_path.replace(".csv", "_outlines.jpg")
mask_path            = output_path.replace(".csv", "_mask.jpg")
analysis_mask_path   = output_path.replace(".csv", "_analysis_mask.jpg")
measurement_src_path = output_path.replace(".csv", "_measurement_source.jpg")

print("[measure_particles] imagePath="      + image_path)
print("[measure_particles] outputPath="     + output_path)
print("[measure_particles] pxPerMm="        + px_per_mm)
print("[measure_particles] thresholdMin="   + threshold_min + ", thresholdMax=" + threshold_max)
print("[measure_particles] roi=(%s, %s, %s, %s)" % (roi_x, roi_y, roi_w, roi_h))

# ---- 1. 画像を開いて8-bit化 ------------------------------------
imp = IJ.openImage(image_path)
IJ.run(imp, "8-bit", "")

# ---- 2-3. スケール設定 -----------------------------------------
if px_per_mm:
    cal = imp.getCalibration()
    cal.pixelWidth  = 1.0 / float(px_per_mm)
    cal.pixelHeight = 1.0 / float(px_per_mm)
    cal.setUnit("mm")
    imp.setCalibration(cal)

# ---- measurement_source（グレースケール原画）を保存 -------------
src_imp = imp.duplicate()
src_imp.setTitle("measurement_source")
if px_per_mm:
    src_imp.setCalibration(imp.getCalibration())
IJ.saveAs(src_imp, "Jpeg", measurement_src_path)

# ---- 4. Threshold → Convert to Mask → Invert ------------------
ip = imp.getProcessor()
t_min = float(threshold_min) if threshold_min else None
t_max = float(threshold_max) if threshold_max else None

if t_min is not None and t_max is not None:
    ip.setThreshold(t_min, t_max, ImageProcessor.RED_LUT)
else:
    IJ.run(imp, "Auto Threshold", "method=Default")

IJ.run(imp, "Convert to Mask", "")
IJ.run(imp, "Invert", "")
IJ.saveAs(imp, "Jpeg", mask_path)

# ---- 5. analysis_mask（oval ROI で範囲制限） -------------------
mask_imp = imp.duplicate()
mask_imp.setTitle("analysis_mask")

if roi_x and roi_y and roi_w and roi_h:
    oval = OvalRoi(
        int(float(roi_x)), int(float(roi_y)),
        int(float(roi_w)), int(float(roi_h))
    )
    mask_imp.setRoi(oval)
    IJ.run(mask_imp, "Clear Outside", "")
    mask_imp.killRoi()

IJ.saveAs(mask_imp, "Jpeg", analysis_mask_path)

# ---- 6-7. Analyze Particles（Java API 直接呼び出し）-----------
# JPEG保存でthresholdが失われるため、ここで2値画像として再設定
mask_ip = mask_imp.getProcessor()
mask_ip.setThreshold(1, 255, ImageProcessor.NO_LUT_UPDATE)

rt = ResultsTable()

flags = (
    ParticleAnalyzer.DISPLAY_RESULTS |
    ParticleAnalyzer.CLEAR_WORKSHEET
)
measurements = (
    Measurements.AREA       |
    Measurements.STD_DEV    |
    Measurements.CENTER_OF_MASS |
    Measurements.FERET
)

# redirect先をsrc_impに設定
ParticleAnalyzer.setRoiManager(None)
pa = ParticleAnalyzer(
    flags,
    measurements,
    rt,
    0.0,            # min size
    Double.MAX_VALUE,  # max size
    0.0,            # min circularity
    1.0             # max circularity
)
pa.setHideOutputImage(True)

# redirect（measurement_source から輝度を計測）
imp_for_measure = src_imp
pa.analyze(mask_imp, imp_for_measure)  # mask で粒子検出、輝度はsrc_impから

n = rt.size()
print("[measure_particles] nResults=" + str(n))

if n > 0:
    rt.saveAs(output_path)
else:
    with open(output_path, "w") as f:
        f.write("Area,StdDev,XM,YM,Feret,FeretX,FeretY,FeretAngle,MinFeret\n")

print("[measure_particles] done")