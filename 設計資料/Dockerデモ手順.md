# Dockerデモ手順

## 1. 目的

この手順書は、GrindGuide のデモ環境を Docker で起動し、

- API が起動すること
- `compare/csv` が動作すること
- `analyze/images` が動作すること
- 非同期ジョブ API が動作すること

を確認するための実行メモである。

## 2. 参照ファイル

- [compose.demo.yml](/mnt/meta-dog/GrindGuide/compose.demo.yml)
- [docker/demo/Dockerfile](/mnt/meta-dog/GrindGuide/docker/demo/Dockerfile)
- [docker/demo/start-demo.sh](/mnt/meta-dog/GrindGuide/docker/demo/start-demo.sh)
- [設計資料/デモ環境Docker構成.md](/mnt/meta-dog/GrindGuide/%E8%A8%AD%E8%A8%88%E8%B3%87%E6%96%99/%E3%83%87%E3%83%A2%E7%92%B0%E5%A2%83Docker%E6%A7%8B%E6%88%90.md)

## 3. 前提

- Docker / Docker Compose が利用できること
- リポジトリルートでコマンドを実行すること
- `service/tests/` にデモ用画像・CSVが存在すること

## 4. 起動

### 初回起動または build を含める場合

```bash
docker compose -f compose.demo.yml up --build
```

### バックグラウンド起動

```bash
docker compose -f compose.demo.yml up --build -d
```

## 5. 状態確認

### コンテナ状態確認

```bash
docker compose -f compose.demo.yml ps
```

### ログ確認

```bash
docker compose -f compose.demo.yml logs -f
```

### API が起動しているか確認

```bash
curl http://127.0.0.1:8000/openapi.json
```

JSON が返れば、FastAPI 自体は起動している。

## 6. デモ確認の順番

おすすめの確認順は次の通り。

1. `openapi.json`
2. `compare/csv`
3. `analyze/images`

理由:

- `compare/csv` は Fiji を使わないため、API / 非同期ジョブ / 統計処理の確認に向く
- `analyze/images` は Fiji を含むため、本命の end-to-end 確認になる

## 7. compare/csv の確認

### ジョブ受付

```bash
curl -X POST "http://127.0.0.1:8000/api/compare/csv" \
  -H "accept: application/json" \
  -F 'payload={
    "samples": [
      {"file_key": "out.csv", "sample_name": "Sample A", "unit": "mm"}
    ]
  }' \
  -F "files=@service/tests/out.csv;type=text/csv"
```

期待レスポンス例:

```json
{
  "job_id": "compare_20260426T010000Z_abcdef12",
  "status": "queued",
  "status_url": "/api/jobs/compare_20260426T010000Z_abcdef12",
  "result_url": "/api/jobs/compare_20260426T010000Z_abcdef12/result"
}
```

### ジョブ状態確認

```bash
curl "http://127.0.0.1:8000/api/jobs/compare_20260426T010000Z_abcdef12"
```

### 結果取得

```bash
curl "http://127.0.0.1:8000/api/jobs/compare_20260426T010000Z_abcdef12/result"
```

## 8. analyze/images の確認

### ジョブ受付

```bash
curl -X POST "http://127.0.0.1:8000/api/analyze/images" \
  -H "accept: application/json" \
  -F 'payload={
    "samples": [
      {"file_key": "IMG_7066.jpg", "sample_name": "Sample A"}
    ],
    "options": {
      "scale_diameter_mm": 50.0,
      "threshold_min": 80,
      "threshold_max": 255,
      "roi_diameter_scale": 0.95,
      "output_unit": "mm"
    }
  }' \
  -F "files=@service/tests/IMG_7066.jpg;type=image/jpeg"
```

期待レスポンス例:

```json
{
  "job_id": "analyze_20260426T010500Z_1234abcd",
  "status": "queued",
  "status_url": "/api/jobs/analyze_20260426T010500Z_1234abcd",
  "result_url": "/api/jobs/analyze_20260426T010500Z_1234abcd/result"
}
```

### ジョブ状態確認

```bash
curl "http://127.0.0.1:8000/api/jobs/analyze_20260426T010500Z_1234abcd"
```

### 結果取得

```bash
curl "http://127.0.0.1:8000/api/jobs/analyze_20260426T010500Z_1234abcd/result"
```

## 9. 結果の見方

確認したい主な項目:

- `particle_count`
- `filtered_particle_count`
- `mean`
- `median`
- `kde_peak`
- `min_feret_mm`
- `min_area_mm2`
- `max_feret_mm`

また、`raw_csv_path` や `plot_path` は volume 越しにホスト側からも確認できる。

例:

- `service/app/tmp/analyze/<job_id>/...`
- `service/app/tmp/compare/<job_id>/...`

## 10. コンテナ停止

### フォアグラウンド起動時

```bash
Ctrl + C
```

### バックグラウンド起動時

```bash
docker compose -f compose.demo.yml down
```

## 11. 再 build について

```bash
docker compose -f compose.demo.yml up --build
```

を実行しても、通常は毎回すべてゼロから再 build されるわけではない。Docker のレイヤーキャッシュが有効であれば、

- アプリコード変更
- 依存変更
- Dockerfile 変更

の位置に応じて再利用される。

現状の `docker/demo/Dockerfile` では、アプリコード変更だけなら Fiji のダウンロードレイヤーは再利用されやすい。

## 12. よくある詰まりどころ

### `openapi.json` は通るが `analyze/images` が失敗する

- Fiji / Java 側の問題の可能性が高い
- コンテナログと job の `error_message` を確認する

### `POST` が 501 になる

- FastAPI ではなく別の簡易 HTTP サーバに投げている可能性がある
- 対象ポートを確認する

### 画像や CSV が見つからない

- `curl` 実行位置がリポジトリルートか確認する
- `service/tests/...` の相対パスを見直す

### `result` がすぐ取れない

- 非同期ジョブ方式なので正常
- 先に `GET /api/jobs/{job_id}` で `completed` になるのを確認する

## 13. 将来の見直し候補

- `result` の `plot_path` / `raw_csv_path` を artifact API に寄せる
- ZIP ダウンロード API を追加する
- API / worker 分離構成に移行する
- `compare` / `analyze` のデモ用スクリプトを `scripts/` に置く
