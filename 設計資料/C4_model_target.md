# 1. System Context
システム名

GrindGuide

## 目的

JPEG画像またはCSVを入力として、粉体の長さ分布を算出し、CSVとKDEプロットおよび統計値を返す。

得られた粒度分布を、抽出条件の比較やグラインダー設定の検討に活用できるようにする。

将来的には、既知の粒度分布データ、抽出レシピ、グラインダー設定データを参照しながら、AIが抽出方法やグラインダー設定の提案を返せるようにする。

## 利用者

- バリスタ・コーヒーの一般愛好家
- 自宅で抽出条件を調整したいユーザ
- 自分のグラインダー設定と抽出結果の関係を継続的に把握したいユーザ

## 提供価値

- 画像から粒度分布を可視化できる
- 複数サンプルを比較できる
- 粒度分布と抽出条件の関係を蓄積できる
- 将来的にAIによる最適な設定の提案を受けられる
- 長時間処理でもジョブ受付・進捗確認・結果取得を分けて扱える

## 現行実装との関係

- 現行実装の中心は `Calibration` と `Fiji Worker` による粒度計測である
- 本資料はその先の API、比較、AI提案、RAG まで含めた完成形の設計方針をまとめる
- 現行実装の詳細は [C4_model_for_poc.md](/mnt/meta-dog/GrindGuide/%E8%A8%AD%E8%A8%88%E8%B3%87%E6%96%99/C4_model_for_poc.md) を参照する

# 2. Scope
## 現在実装済みの範囲

- 画像中のスケール円検出
- Fiji による粒子計測
- 単画像に対する CLI ベースの測定実行
- API の request / response モデルの土台
- API route の受け口の土台

## 今後対象とする範囲

- JPEG複数入力 API
- CSV比較 API
- 非同期ジョブ管理
- 分布構築
- KDEプロット / 統計値計算
- 結果返却形式の整備
- AI提案
- RAG用データベースの設計と利用

## 対象外

- ユーザアカウント管理
- 長期保存前提の大規模データ基盤
- 本格的な学習パイプライン
- 医療や食品安全のような高リスク用途の自動意思決定

# 3. User Journey / Use Cases
## ケースA: JPEG画像から粒度分布を得る

1. ユーザがJPEG画像とサンプル名をアップロードする
2. システムがスケール検出と粒子計測を行う
3. 粒度分布、CSV、KDE、統計値を返す

## ケースB: 既存CSVを比較する

1. ユーザが複数の既存CSVをアップロードする
2. システムが分布構築と比較を行う
3. KDEと統計値を返す

## ケースC: 抽出条件の調整案を得る

1. ユーザが現在の粒度分布と抽出方法を入力する
2. システムが既知データと比較する
3. AIがグラインダー設定や抽出条件の候補を返す

# 4. Container Overview
## 現行コンテナ

- API Container
- Calibration Container
- Fiji Worker Container
- Distribution Builder Container
- KDE / Statistics Container
- Result Bundle Builder

## 将来追加コンテナ

- AI Advisor Container
- Retrieval / Knowledge Access Container
- Knowledge DB
- Feedback Store
- Recommendation Policy Layer
- Job Management Container

# 5. Current Containers
## 5-1. API Container

### 役割
- multipart upload受付
- 入力モード判定（JPEG or CSV）
- ジョブ受付
- 一時処理パイプライン起動
- ジョブ状態返却
- 結果取得導線の返却

### 特徴
- 完全stateless（セッション内のみ）
- 長時間処理は同期完了を待たず、ジョブIDを返す

### 最低限API

- `POST /api/analyze/images`
  - JPEG画像を複数受け取り、ジョブを受け付ける
- `POST /api/compare/csv`
  - 既存CSVを複数受け取り、ジョブを受け付ける
- `GET /api/jobs/{job_id}`
  - ジョブ状態と進捗を返す
- `GET /api/jobs/{job_id}/result`
  - 完了済みジョブの結果を返す

## 5-2. Calibration Container（JPEG時のみ）
- 画像中のスケール円を検出し、pixel と実寸の比率を計算する

## 5-3. Fiji Worker Container（JPEG時のみ）
- Headless Fiji を使って指定領域内の粉体を pixel 単位で測定する
- CSVを返却用アーティファクトとして扱う
- DB保存しない

## 5-4. Distribution Builder Container
### 役割
- CSVまたはFiji結果から分布データを構築する

### 入力
- raw_measurements（複数サンプル）

### 出力
- length array per sample
- density estimation用データ

### 責務
- pixel or mm 正規化
- 欠損値除去
- スケール適用（必要時）
- raw measurement を保持したまま、後処理フィルタでノイズ除去できるようにする
- スマホ撮影時は `min_feret_px` を基準に下限を決め、`px_per_mm` から mm へ換算して適用する

## 5-5. KDE / Statistics Container
### 役割
- KDEプロット生成
- 複数サンプル間統計計算

### 入力
- 各サンプルの length array

### 出力
- KDE plot image（PNG or SVG）
- 統計値

## 5-6. Result Bundle Builder
### 役割
- 全成果物をまとめて返却形式にする

### 出力
- ZIP または JSON + binary

## 5-7. Job Management Container
### 役割
- ジョブID発行
- ジョブ状態管理
- 進捗管理
- 完了後の結果参照先管理

### 状態
- `queued`
- `running`
- `completed`
- `failed`

### 管理したい情報
- `job_id`
- `job_type`
- `submitted_at`
- `total_samples`
- `completed_samples`
- `current_sample_name`
- `result_location`
- `error_message`

# 6. Future Containers
## 6-1. AI Advisor Container

### 役割
- 粒度分布、抽出条件、既知データをもとに提案文を生成する

### 入力
- 測定済み粒度分布
- ユーザの抽出条件
- Retrieval Layer が返した候補知識

### 出力
- 推奨グラインダー設定
- 推奨抽出方法
- 提案理由
- 参照した知識の要約

## 6-2. Retrieval / Knowledge Access Container

### 役割
- 粒度分布や条件に近い既知データを検索する

### 入力
- 測定結果
- メタデータ
- 推奨対象の条件

### 出力
- 類似サンプル候補
- 既知メッシュ候補
- 抽出レシピ候補

## 6-3. Knowledge DB

### 役割
- 提案の根拠となる既知データを保持する

### 内容候補
- 既知メッシュ分布
- グラインダー設定ごとの代表分布
- 抽出方法ごとの推奨レンジ
- 手動で整備したノウハウ

## 6-4. Feedback Store

### 役割
- ユーザが提案をどう評価したかを保存する

### 用途
- 提案品質の改善
- 類似条件への再利用

## 6-5. Recommendation Policy Layer

### 役割
- ルールベース判定とLLM生成の責務分離を行う

### 方針
- 根拠の薄い提案は返しすぎない
- 必要な条件が足りないときは不足情報を返す
- 提案には必ず根拠を添える

# 7. Data Flow
## ケースA: JPEG複数入力

```
User
  ↓
API
  ↓
Job Accepted
  ↓
Job Management
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
Job Accepted
  ↓
Job Management
  ↓
Distribution Builder
  ↓
KDE / Statistics
  ↓
Result Bundle
  ↓
User
```

## ケースC: AI提案

```
User
  ↓
API
  ↓
Measurement Result / CSV
  ↓
Retrieval / Knowledge Access
  ↓
AI Advisor
  ↓
Recommendation Response
  ↓
User
```

## ケースD: ジョブ状態確認と結果取得

```
User
  ↓
GET /api/jobs/{job_id}
  ↓
Job Management
  ↓
Status Response

User
  ↓
GET /api/jobs/{job_id}/result
  ↓
Result Bundle
  ↓
Completed Result
```

# 8. API Surface
## 現行API

- `POST /api/analyze/images`
- `POST /api/compare/csv`

## 将来追加API候補

- `GET /api/jobs/{job_id}`
- `GET /api/jobs/{job_id}/result`
- `POST /api/recommend`
- `POST /api/feedback`

## request / response の基本方針

- JPEG実体は JSON に埋め込まず、`multipart/form-data` で送る
- ファイルごとの属性は `samples[]` にまとめる
- 実行条件は `options` に分ける
- 将来的に recommendation 系 API でも同様の入力設計を踏襲する
- 長時間処理の初回レスポンスでは、結果本体ではなくジョブ受付結果を返す
- クライアントは `job_id` を使って進捗確認と結果取得を行う

## 将来拡張メモ: measurement filter

- raw CSV は Fiji の出力をできるだけそのまま保持する
- ノイズ除去は Fiji 側で強く削るより、後処理フィルタで調整できるようにする
- 特にスマホ撮影では、解像力より明確に細かい粒子はノイズとして扱う
- 当面のデフォルト方針は `min_feret_px = 10` を候補とし、`px_per_mm` から `min_feret_mm` へ換算して適用する
- `max` は当面デフォルト無しとし、必要時のみ指定する

## 将来拡張メモ: replicate grouping

- 将来的に、複数の測定ファイルを1つの代表サンプルとして束ねるオプションを追加できるようにする
- 主な用途は、同一条件で複数回測定した結果を1サンプル群として比較すること
- 実装する場合は、統計量の単純平均ではなく、生データを結合して1つの distribution として扱う方式を優先する
- API では `file_key` の単一指定に加えて、`file_keys` の複数指定や `replicates` のような表現を検討する
- KDE / 統計 / AI提案の downstream は、束ねた distribution を通常の1サンプルと同様に扱える構成を維持する

## ジョブ受付レスポンスの方針

- `POST /api/analyze/images`
- `POST /api/compare/csv`
  は処理完了を待たずに `202 Accepted` を返す

### ジョブ受付レスポンス例

```json
{
  "job_id": "job_20260414_001",
  "status": "queued",
  "status_url": "/api/jobs/job_20260414_001",
  "result_url": "/api/jobs/job_20260414_001/result"
}
```

### ジョブ状態レスポンス例

```json
{
  "job_id": "job_20260414_001",
  "status": "running",
  "total_samples": 5,
  "completed_samples": 2,
  "current_sample_name": "Comandante 24 clicks"
}
```

# 9. Data Model
## Sample metadata

- `sample_name`
- `file_key`
- `file_keys` or `replicates` (将来拡張)
- `grinder`
- `grind_setting`
- `brew_method`
- `bean_name`
- `roast_level`
- `notes`

## Raw measurement

- Fiji出力CSV
- `Area`
- `StdDev`
- `Feret`
- `FeretAngle`
- `MinFeret`
- `Circ.`
- `AR`
- `Round`
- 補助列

### 補足

- `Feret`, `MinFeret`, `AR` は粒子の大きさや細長さを見るための基礎特徴とする
- `FeretAngle` は粒子の向きや形状の偏りをみるための候補特徴とする
- `Circ.` と `Round` は粒子の丸さをみるための特徴とする
- 将来的に raw measurement から派生特徴量を計算する
  - 例: `AR` の平均、`Circ.` の分布、`Round` の中央値、`FeretAngle` のばらつき

## Distribution data

- sampleごとの length array
- 正規化済み単位
- 外れ値処理結果
- 形状特徴量 summary
  - 例: `AR`, `Circ.`, `Round`, `FeretAngle` の代表値や分布要約
- 将来的に replicate を束ねた combined distribution も扱えるようにする
- raw distribution と filtered distribution を区別して扱えるようにする

## KDE / statistics result

- KDE plot
- 平均
- 中央値
- 分散
- 比較結果

## Recommendation request

- sample metadata
- distribution summary
- shape feature summary
- applied filter metadata
- job or result reference
- comparison target
- desired brew profile

## Recommendation response

- 推奨設定
- 説明文
- 根拠データ
- 類似サンプル
- 参照した形状特徴
- 注意点

## Knowledge record

- record_id
- source_type
- grinder
- grind_setting
- brew_method
- representative_distribution
- representative_shape_features
- notes
- evidence_level

# 10. Knowledge Base / RAG Design
## 保持したい知識

- 既知メッシュ分布
- グラインダー設定と粒度分布の対応
- 形状特徴と抽出傾向の対応
- 抽出方法ごとの推奨粒度傾向
- 特定条件での味の傾向

## 初期方針

- 最初は構造化データ中心で始める
- 近傍検索や条件フィルタで十分なら、ベクトルDBは急いで入れない
- LLM は説明生成に使い、判定の土台は明示的に持つ

## 将来の拡張

- 類似分布検索
- 自然言語メモの検索
- 埋め込みベースの retrieval

# 11. Recommendation Policy
## 役割分担

- ルールベース
  - 最低限の安全判定
  - データ不足時のガード
  - 推奨候補の絞り込み
- LLM
  - 理由説明
  - 比較要約
  - ユーザ向け表現の整形

## 提案時の原則

- 根拠のある提案だけを返す
- 根拠データを明記する
- 粒径だけでなく形状特徴も必要に応じて使う
- 推奨と断定を区別する
- 測定結果の不確実性を隠さない

# 12. Storage / Runtime
## 開発環境

- Ubuntu + micromamba
- Fiji.app
- Python 3.11

## 本番候補

- Docker 化
- API コンテナ
- Fiji 実行コンテナ
- Job 管理コンテナ
- 将来的な DB コンテナ

## 一時ファイル

- 画像
- raw CSV
- plot
- debug artifact

## 保存方針

- セッション単位の一時保存を基本とする
- 長期保存が必要なデータだけ別ストアへ移す
- ジョブ進捗と結果参照情報は、API再試行や結果取得に耐えられる形で保持する

# 13. Non-Functional Requirements
## 性能

- 画像1枚あたりの処理時間を実用範囲に収める
- 複数サンプル処理でも過度に待たせない
- 長時間処理でもクライアントを同期ブロックしない

## 再現性

- 同じ入力から近い結果を再現できること
- しきい値やスケール条件を明示できること

## 説明可能性

- AI提案に根拠を添える
- 比較対象や類似データを明示できること

## 保守性

- Calibration / Fiji / Distribution / AI を疎結合に保つ
- コンテナ単位に入れ替え可能にする
- API と長時間処理ワーカーの責務を分ける

# 14. Risks / Open Questions
- Fiji実行の安定性をどこまで担保できるか
- 粒度指標として何を中心に扱うか
- `Circ.`, `AR`, `Round`, `FeretAngle` が抽出効率にどの程度寄与するか
- KDEの見せ方をどうするか
- 非同期ジョブ状態をどこに保持するか
- `min_feret_px` のデフォルト値をどこで妥当とみなすか
- replicate grouping を導入する場合、どの単位で1サンプルとみなすか
- AI提案の品質をどう評価するか
- 既知データをどう収集し、どう信頼度付けするか
- RAG がどの段階で必要になるか

# 15. Roadmap
## Phase 1
- JPEG解析 API を完成させる
- CSV比較 API を完成させる
- 非同期ジョブ受付と状態確認 API を用意する

## Phase 2
- Distribution Builder と KDE / Statistics を実装する
- Result Bundle の返却形式を固める

## Phase 3
- 知識データのスキーマを決める
- 既知データを手動整備する

## Phase 4
- 初期版 Recommendation API を作る
- ルールベース + LLM の役割分担を固める

## Phase 5
- Retrieval の改善
- 評価と改善サイクルの整備
