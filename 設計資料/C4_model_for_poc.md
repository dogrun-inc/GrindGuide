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
