arg = getArgument();
setBatchMode(true);

function getValueFromArg(argText, key) {
    parts = split(argText, ";");
    for (i = 0; i < parts.length; i++) {
        kv = split(parts[i], "=");
        if (kv.length == 2 && kv[0] == key) return kv[1];
    }
    return "";
}

imagePath = getValueFromArg(arg, "image");
outputPath = getValueFromArg(arg, "output");
pxPerMm = getValueFromArg(arg, "px_per_mm");
thresholdMin = getValueFromArg(arg, "threshold_min");
thresholdMax = getValueFromArg(arg, "threshold_max");
roiX = getValueFromArg(arg, "roi_x");
roiY = getValueFromArg(arg, "roi_y");
roiW = getValueFromArg(arg, "roi_w");
roiH = getValueFromArg(arg, "roi_h");

outlinePath = replace(outputPath, ".csv", "_outlines.jpg");
maskPath = replace(outputPath, ".csv", "_mask.jpg");

print("[measure_particles] imagePath=" + imagePath);
print("[measure_particles] outputPath=" + outputPath);
print("[measure_particles] pxPerMm=" + pxPerMm);
print("[measure_particles] thresholdMin=" + thresholdMin + ", thresholdMax=" + thresholdMax);
print("[measure_particles] roi=(" + roiX + ", " + roiY + ", " + roiW + ", " + roiH + ")");

open(imagePath);
originalTitle = getTitle();

// 1. Gray scale に変換
run("8-bit");
run("Duplicate...", "title=measurement_source");
measurementSourceTitle = getTitle();
selectWindow(originalTitle);

// 2-3. Python 側で求めた px_per_mm を使ってスケール設定
if (pxPerMm != "") {
    run("Set Scale...", "distance=" + pxPerMm + " known=1 unit=mm global");
    selectWindow(measurementSourceTitle);
    run("Set Scale...", "distance=" + pxPerMm + " known=1 unit=mm global");
    selectWindow(originalTitle);
}

// 4. Threshold 設定
if (thresholdMin != "" && thresholdMax != "") {
    setThreshold(parseFloat(thresholdMin), parseFloat(thresholdMax));
} else {
    setAutoThreshold("Default");
}
run("Convert to Mask");
run("Invert");
saveAs("Jpeg", maskPath);

// 5. 対象領域を oval ROI で制限
if (roiX != "" && roiY != "" && roiW != "" && roiH != "") {
    makeOval(parseFloat(roiX), parseFloat(roiY), parseFloat(roiW), parseFloat(roiH));
}

// 6. 測定項目の設定
print("[measure_particles] before Set Measurements");
run(
    "Set Measurements...",
    "area standard center feret's redirect=[" + measurementSourceTitle + "] decimal=3"
);
print("[measure_particles] after Set Measurements");

// 7. 粒子解析
// PoCではまず粒子抽出そのものを確認したいので、サイズ条件は広めに取る。
// 安定して抽出できるのを確認した後に、実運用向けの最小・最大面積へ絞り込む。
print("[measure_particles] before Analyze Particles");
run(
    "Analyze Particles...",
    "size=0-999999 circularity=0.00-1.00 show=Nothing clear"
);
print("[measure_particles] after Analyze Particles title=" + getTitle());

print("[measure_particles] nResults=" + nResults);
if (nResults > 0) {
    saveAs("Results", outputPath);
} else {
    File.saveString("Area,StdDev,XM,YM,Feret,FeretX,FeretY,FeretAngle,MinFeret\n", outputPath);
}

if (isOpen("Results")) {
    selectWindow("Results");
    run("Close");
}

if (isOpen(originalTitle)) {
    selectWindow(originalTitle);
    close();
}

if (isOpen(measurementSourceTitle)) {
    selectWindow(measurementSourceTitle);
    close();
}

setBatchMode(false);
