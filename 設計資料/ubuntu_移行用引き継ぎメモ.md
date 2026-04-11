# Ubuntu移行用 引き継ぎメモ

## 目的

- 現在 macOS 上で進めている PoC を、Ubuntu 環境へ移して継続開発できるようにする。
- 特に `calibration.py` と `fiji_runner.py` / `measure_particles.ijm` の現在地を引き継ぐ。
- AWS 本番を見据えて、Fiji 実行系を Linux 前提で再検証する。

## 結論サマリ

- `calibration.py` の PoC は概ね成功している。
- `fiji_runner.py` から `calibration.py` を呼び出し、得られたスケールと円ROIを Fiji macro に渡す流れまでは実装済み。
- ただし Fiji の `Analyze Particles...` は macOS + Fiji アプリ実行環境で不安定。
- 特に `--headless` 実行では `HeadlessGenericDialog` 由来の `NullPointerException` が発生した。
- `--headless` を外しても、`Analyze Particles...` の結果は `nResults=0` で、期待するCSVはまだ得られていない。
- Ubuntu 環境で Fiji 実行条件を再検証する価値が高い。

## calibration PoC の状態

- 対象ファイル: [service/app/calibration.py](/Users/oec/Desktop/docs/Metadog/粒度計測サービス/service/app/calibration.py)
- 対象テスト: [service/app/test_calibration.py](/Users/oec/Desktop/docs/Metadog/粒度計測サービス/service/app/test_calibration.py)

### 実装内容

- OpenCV の `HoughCircles` でスケール円を検出する。
- 画像内に完全に収まる円のみを候補とする。
- そのうち、直径が画像幅の `70%〜95%` に入る候補を優先する。
- 優先候補がなければ、画像内に収まる候補の最大円を採用する。
- `px_per_mm` と `mm_per_px` を返す。

### PoC の判断

- 実画像 `service/tests/IMG_7066.jpg` で、期待直径 `2720px` に対して `2708.96px` を検出。
- 相対誤差は約 `0.4%`。
- 粉体測定用途では実用上ほぼ許容できるという判断。
- calibration の PoC は一旦固定してよい状態。

### メモ

- デバッグ `print` が残っている。
- 後で本番向けにする場合は、`logging` か `debug` フラグへ寄せる余地がある。

## Fiji runner PoC の状態

- 対象ファイル:
  - [service/app/fiji_runner.py](/Users/oec/Desktop/docs/Metadog/粒度計測サービス/service/app/fiji_runner.py)
  - [service/app/measure_particles.ijm](/Users/oec/Desktop/docs/Metadog/粒度計測サービス/service/app/measure_particles.ijm)
  - [service/app/test_fiji_runner.py](/Users/oec/Desktop/docs/Metadog/粒度計測サービス/service/app/test_fiji_runner.py)
  - [service/app/config.py](/Users/oec/Desktop/docs/Metadog/粒度計測サービス/service/app/config.py)

### 実装済みの流れ

- `test_fiji_runner.py` から CLI で画像1枚を流せる。
- `fiji_runner.py` は最初に `detect_scale_circle(...)` を実行する。
- calibration 結果から以下を macro に渡す。
  - `px_per_mm`
  - `roi_x`
  - `roi_y`
  - `roi_w`
  - `roi_h`
- ROI は、検出したスケール円をもとに oval で自動生成している。
- threshold は CLI から任意指定可能。

### 現在の CLI 例

```bash
python service/app/test_fiji_runner.py \
  --input service/tests/IMG_7066.jpg \
  --output service/tests/out.csv \
  --threshold-min 80 \
  --threshold-max 255
```

### 現在の config

- `FIJI_EXECUTABLE`
- `MACRO_PATH`
- `DEFAULT_SCALE_DIAMETER_MM=50.0`
- `ROI_DIAMETER_SCALE=0.95`
- `FIJI_HEADLESS`
  - 現在はデフォルト `false`

## macOS で確認できたこと

### うまくいっている点

- Fiji アプリ自体は起動できる。
- macro に引数を渡して実行できる。
- `out_raw_mask.jpg` は出力される。
- `out_raw_mask.jpg` は、見た目として粒子が良い感じに選択されている。
- よって、少なくとも
  - 画像入力
  - スケール設定
  - ROI 設定
  - threshold
  - mask 作成
  までは概ね成立している。

### 詰まっている点

- `Analyze Particles...` の直前まではログが出る。
- その後に Fiji 内部で以下の例外が出ることがあった。

```text
java.lang.NullPointerException
at net.imagej.patcher.HeadlessGenericDialog...
```

- これは `--headless` 実行時に顕著だった。
- `--headless` を外しても `nResults=0` で、CSV は空ヘッダのみ。

### 現時点の推測

- Fiji / ImageJ の `Analyze Particles...` が headless 実行と相性が悪い可能性がある。
- macOS アプリ版 Fiji 特有の挙動差がある可能性もある。
- mask までは良いので、本質課題は `Analyze Particles...` の実行条件にある。

## 現在の macro の考え方

- グレースケール化
- calibration 結果を用いた `Set Scale`
- threshold 適用
- `Convert to Mask`
- `Invert`
- oval ROI 設定
- `Set Measurements...`
- `Analyze Particles...`
- CSV 保存

## Ubuntu でまず確認したいこと

1. Fiji の CLI 実行が headless で安定するか
2. `Analyze Particles...` が `NullPointerException` なしで実行できるか
3. 同じ `measure_particles.ijm` で `nResults > 0` になるか
4. 期待する列のCSVが出るか

## Ubuntu での優先タスク

1. リポジトリを clone / pull する
2. Python 環境を作る
3. Fiji を配置する
4. Fiji 実行パスを `FIJI_EXECUTABLE` で設定する
5. `test_fiji_runner.py` を実行する
6. `STDOUT/STDERR` と `out_raw_mask.jpg` / `out.csv` を確認する

## Ubuntu 側で期待する改善ポイント

- macOS アプリ版 Fiji ではなく、Linux 用 Fiji を使える
- `headless` 実行の挙動が本番 AWS に近くなる
- `xvfb-run` を含む定石的な自動実行構成が取りやすい

## 次に試す候補

- `FIJI_HEADLESS=true` で Linux 上の挙動を確認
- うまくいかなければ `xvfb-run` 経由で Fiji を実行
- `Analyze Particles...` のオプションを最小構成まで削って差分確認
- ROI あり / なしで比較
- `Set Measurements...` の項目を最小化して問題箇所を切り分け

## 期待するCSVフォーマット

想定出力は次のような形式。

```text
Area,StdDev,Feret,FeretX,FeretY,FeretAngle,MinFeret
1.526,31.685,1.970,1384,946,49.059,1.174
0.167,29.016,0.658,1807,886,60.642,0.376
0.067,29.677,0.387,1840,862,103.392,0.263
...
```

補足:

- 実際の列名は Fiji の出力仕様に依存する可能性がある。
- まずは粒子ごとの行が出ることを優先し、その後で列の厳密な整形を行う。

## 参考ファイル

- [service/app/calibration.py](/Users/oec/Desktop/docs/Metadog/粒度計測サービス/service/app/calibration.py)
- [service/app/test_calibration.py](/Users/oec/Desktop/docs/Metadog/粒度計測サービス/service/app/test_calibration.py)
- [service/app/fiji_runner.py](/Users/oec/Desktop/docs/Metadog/粒度計測サービス/service/app/fiji_runner.py)
- [service/app/test_fiji_runner.py](/Users/oec/Desktop/docs/Metadog/粒度計測サービス/service/app/test_fiji_runner.py)
- [service/app/measure_particles.ijm](/Users/oec/Desktop/docs/Metadog/粒度計測サービス/service/app/measure_particles.ijm)
- [service/app/config.py](/Users/oec/Desktop/docs/Metadog/粒度計測サービス/service/app/config.py)
- [service/tests/IMG_7066.jpg](/Users/oec/Desktop/docs/Metadog/粒度計測サービス/service/tests/IMG_7066.jpg)

## 引き継ぎ時の一言メモ

- calibration PoC は成功扱いでよい。
- Fiji macro は mask 作成までは良いが、`Analyze Particles...` が詰まりどころ。
- Ubuntu で Fiji 実行系を再検証するのが次の主戦場。
