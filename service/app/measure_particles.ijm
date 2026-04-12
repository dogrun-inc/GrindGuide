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

function closeIfOpen(title) {
    if (isOpen(title)) {
        selectWindow(title);
        close();
    }
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
analysisMaskPath = replace(outputPath, ".csv", "_analysis_mask.jpg");
measurementSourcePath = replace(outputPath, ".csv", "_measurement_source.jpg");

print("[measure_particles] imagePath=" + imagePath);
print("[measure_particles] outputPath=" + outputPath);
print("[measure_particles] pxPerMm=" + pxPerMm);
print("[measure_particles] thresholdMin=" + thresholdMin + ", thresholdMax=" + thresholdMax);
print("[measure_particles] roi=(" + roiX + ", " + roiY + ", " + roiW + ", " + roiH + ")");

closeIfOpen("Results");
run("Clear Results");
setOption("BlackBackground", false);

open(imagePath);
originalTitle = getTitle();

// 1. Gray scale に変換
run("8-bit");
run("Duplicate...", "title=measurement_source");
measurementSourceTitle = getTitle();
saveAs("Jpeg", measurementSourcePath);
selectWindow(originalTitle);

// 2-3. Python 側で求めた px_per_mm を使ってスケール設定
if (pxPerMm != "") {
    run("Set Scale...", "distance=" + pxPerMm + " known=1 unit=mm global");
    selectWindow(measurementSourceTitle);
    run("Set Scale...", "distance=" + pxPerMm + " known=1 unit=mm global");
    selectWindow(originalTitle);
}

// 4. Threshold 設定・2値化
if (thresholdMin != "" && thresholdMax != "") {
    setThreshold(parseFloat(thresholdMin), parseFloat(thresholdMax));
} else {
    setAutoThreshold("Default");
}
print("[DEBUG] threshold set on: " + getTitle());
run("Convert to Mask");
run("Invert");
saveAs("Jpeg", maskPath);  // 確認用保存はそのままでOK

// 5. 対象領域を oval ROI で制限した専用画像を作る
// ↓ Duplicateは現在アクティブな2値画像（Convert to Mask済み）から作る → これはOK
run("Duplicate...", "title=analysis_mask");
analysisMaskTitle = getTitle();  // "analysis_mask" のはずだが後続でJPEG再オープンになっていないか注意
if (roiX != "" && roiY != "" && roiW != "" && roiH != "") {
    makeOval(parseFloat(roiX), parseFloat(roiY), parseFloat(roiW), parseFloat(roiH));
    run("Clear Outside");
}
run("Select None");
// ↓ JPEGで保存するのは確認用のみ。analysisMaskTitleはメモリ上のウィンドウを使う
saveAs("Jpeg", analysisMaskPath);
// saveAs の後にタイトルが変わる可能性があるので再取得
analysisMaskTitle = getTitle();
print("[DEBUG] analysisMaskTitle after saveAs: " + analysisMaskTitle);

// 6. 測定項目の設定
print("[measure_particles] before Set Measurements");
run("Set Measurements...",
    "area standard center feret's redirect=[" + measurementSourceTitle + "] decimal=3");
print("[measure_particles] after Set Measurements");

// 7. 粒子解析
print("[measure_particles] before Analyze Particles");
if (!isOpen(analysisMaskTitle)) {
    print("[ERROR] window not found: " + analysisMaskTitle);
    exit("abort");
}
selectWindow(analysisMaskTitle);

// ↓ saveAs("Jpeg") でthresholdとLUTがリセットされるため、ここで再設定
if (is("Inverting LUT")) {
    run("Invert LUT");
}
setThreshold(1, 255);  // Convert to Mask済みなので粒子=255、背景=0

// batch modeを一時的に抜ける
setBatchMode(false);
print("[DEBUG] bitDepth=" + bitDepth());
print("[DEBUG] imageType=" + getImageInfo());
run("Analyze Particles...", "size=0-Infinity circularity=0.00-1.00 display clear");
print("[measure_particles] after Analyze Particles title=" + getTitle());



print("[measure_particles] nResults=" + nResults);
if (nResults > 0) {
    saveAs("Results", outputPath);
} else {
    File.saveString("Area,StdDev,XM,YM,Feret,FeretX,FeretY,FeretAngle,MinFeret\n", outputPath);
}

if (isOpen("Drawing of " + analysisMaskTitle)) {
    selectWindow("Drawing of " + analysisMaskTitle);
    saveAs("Jpeg", outlinePath);
    close();
}

closeIfOpen("Results");
closeIfOpen(originalTitle);
closeIfOpen(measurementSourceTitle);
closeIfOpen(analysisMaskTitle);

setBatchMode(false);
