# 1. System Context
システム名

GrindGuide

## 目的

JPEG画像またはCSVを入力として、粉体の長さ分布を算出し、CSVとKDEプロットおよび統計値を返す。

得られた粒度分布を、抽出条件の比較やグラインダー設定の検討に活用できるようにする。

## 利用者

バリスタ・コーヒーの一般愛好家

## 主なユースケース

- ユーザが複数サンプルの粒度分布を比較し、抽出条件の違いを確認する
- ユーザが自分のグラインダー環境に合わせて、AIから淹れ方やメモリ設定の提案を受ける

## 入力パターン
### パターンA（画像解析）

複数JPEG

スケール情報

ROI / Fiji条件

### パターンB（既存CSV比較）

複数CSV（Fiji出力など）

## 出力

- 各サンプルのCSV（pixelまたはmm）
- KDEプロット（複数サンプル比較）
- 統計値（サンプル間比較）

# 2. Container
## 2-1. API Container

### 役割
- multipart upload受付
- 入力モード判定（JPEG or CSV）
- 一時処理パイプライン起動
- 結果まとめて返却

### 特徴
- 完全stateless（セッション内のみ）

### 最低限API

- `POST /api/analyze/images`
  - JPEG画像を複数受け取り、Calibration → Fiji → 分布構築 → KDE/統計を実行する
- `POST /api/compare/csv`
  - 既存CSVを複数受け取り、分布構築 → KDE/統計のみを実行する

### `POST /api/analyze/images` の想定リクエスト

- Content-Type: `multipart/form-data`
- form field `payload`
  - リクエスト全体のJSON文字列
- form field `files`
  - JPEGファイルを1..n件

#### `payload` の最低限スキーマ

```json
{
  "samples": [
    {
      "file_key": "sample_01.jpg",
      "sample_name": "Comandante 24 clicks"
    },
    {
      "file_key": "sample_02.jpg",
      "sample_name": "Comandante 20 clicks"
    }
  ],
  "options": {
    "scale_diameter_mm": 50.0,
    "threshold_min": 80,
    "threshold_max": 255,
    "roi_diameter_scale": 0.95,
    "output_unit": "mm"
  }
}
```

#### `samples` の意味

- `file_key`
  - `files` で送った各JPEGと対応付けるキー
  - 当面はファイル名と一致させる運用を想定
- `sample_name`
  - UI表示や結果返却時の識別名

#### `options` の意味

- `scale_diameter_mm`
  - スケール円の実寸直径
- `threshold_min`
  - Fijiに渡す下限threshold
- `threshold_max`
  - Fijiに渡す上限threshold
- `roi_diameter_scale`
  - Calibrationで検出した円から計算するROI直径の係数
- `output_unit`
  - 結果の基準単位。当面は `mm` を優先

### `POST /api/analyze/images` の最低限レスポンス

- Content-Type
  - 当面は `application/json` または `application/zip`
- 返却内容
  - サンプルごとの raw CSV
  - サンプルごとの要約統計
  - 複数サンプル比較用のKDEプロット

#### JSON返却時の最小イメージ

```json
{
  "samples": [
    {
      "sample_name": "Comandante 24 clicks",
      "raw_csv_path": "results/sample_01_raw.csv",
      "particle_count": 995,
      "unit": "mm"
    }
  ],
  "plot_path": "results/kde.png",
  "statistics": {
    "compared_samples": 2
  }
}
```

### `POST /api/compare/csv` の想定リクエスト

- Content-Type: `multipart/form-data`
- form field `payload`
  - 比較対象サンプルのJSON文字列
- form field `files`
  - Fiji出力CSVを1..n件

#### `payload` の最低限スキーマ

```json
{
  "samples": [
    {
      "file_key": "sample_01.csv",
      "sample_name": "Reference A",
      "unit": "mm"
    },
    {
      "file_key": "sample_02.csv",
      "sample_name": "Reference B",
      "unit": "mm"
    }
  ]
}
```

### API設計メモ

- JPEG実体はJSONに埋め込まず、`multipart/form-data` でファイル本体を送る
- ファイルごとの属性は `samples[]` に寄せ、実行条件は `options` に分ける
- ファイルと属性の対応は `file_key` で明示する
- 将来的に `grinder`, `grind_setting`, `brew_method` などの属性を `samples[]` へ追加できる
- 将来的にレスポンスは ZIP 一括返却へ拡張できる

## 2-2. Calibration Container（JPEG時のみ）
- 画像中のスケール円を検出し、pixel と実寸の比率を計算する。

## 2-3. Fiji Worker Container（JPEG時のみ）
- Headless Fiji を使って指定領域内の粉体を pixel 単位で測定する。
- CSVを返却用アーティファクトとして扱う
- DB保存しない

# 2-4. Distribution Builder Container（新規）
## 役割
- CSVまたはFiji結果から分布データを構築する

## 入力
- raw_measurements（複数サンプル）
## 出力
- length array per sample
- density estimation用データ

## 責務
- pixel or mm 正規化
- 欠損値除去
- スケール適用（必要時）

# 2-5. KDE / Statistics Container
## 役割
- KDEプロット生成
- 複数サンプル間統計計算

## 入力
- 各サンプルの length array

## 出力
- KDE plot image（PNG or SVG）
- 統計値

# 2-6. Result Bundle Builder（新規）
## 役割
- 全成果物をまとめて返却形式にする

## 出力
ZIP または JSON + binary

# 3. フロー

## ケースA： JPEG複数入力

```
User
  ↓
API
  ↓
Calibration（各画像）
  ↓
Fiji Worker（各画像）
  ↓
Distribution Builder
  ↓
KDE / Statistics
  ↓
Result Bundle
  ↓
User
```

## ケースB: CSV比較

```
User
  ↓
API
  ↓
Distribution Builder
  ↓
KDE / Statistics
  ↓
Result Bundle
  ↓
User
```
