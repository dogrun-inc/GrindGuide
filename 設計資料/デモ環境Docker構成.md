# デモ環境Docker構成

## 1. 目的

この構成は、GrindGuide の

- JPEG / CSV の入出力
- Fiji を含む計測パイプライン
- 非同期ジョブ API

を、ローカルやクラウド上で再現しやすくするための最小 Docker 構成である。

## 2. 現段階の考え方

現時点では、開発対象を 2 つに分けて考える。

1. 再現性が重要なサービス本体
2. 試行錯誤が多い AI / RAG の探索領域

このため、リポジトリは分けずに 1 つのまま維持しつつ、

- サービス本体は Docker で再現可能にする
- AI 提案や RAG 実験は必要に応じてホスト環境でも進められるようにする

という方針を採る。

## 3. ディレクトリ構成案

```text
GrindGuide/
  compose.demo.yml
  .dockerignore
  docker/
    README.md
    demo/
      Dockerfile
      start-demo.sh
  service/
    app/
    requirements.txt
    tests/
  設計資料/
```

## 4. 各ファイルの役割

### `compose.demo.yml`

- デモ環境の起動定義
- 1 コンテナで API + background job + Fiji を実行する

### `docker/demo/Dockerfile`

- Ubuntu ベース
- Python 3.11
- Java
- Fiji
- Python 依存

をひとまとめにする。

### `docker/demo/start-demo.sh`

- コンテナ起動時に `uvicorn` を実行する

### `.dockerignore`

- `.git`
- `tmp`
- `__pycache__`
- ローカル実行の生成物

などをビルドコンテキストから除外する。

## 5. なぜこの配置にするか

### 5-1. ルート直下に `Dockerfile` を置かない理由

現段階では Docker 化の目的が「デモ環境の再現」であり、

- 本番構成
- API / worker 分離構成
- RAG 専用構成

とはまだ分けて考えたい。

そのため、`docker/demo/` に閉じた配置にして、

- 現在の最小構成
- 将来の拡張構成

を混同しにくくする。

### 5-2. `compose.demo.yml` を分ける理由

今後 `compose.dev.yml` や `compose.worker.yml` を追加しやすくするため。

## 6. 将来の拡張イメージ

必要になれば、次のような分離に進める。

```text
docker/
  demo/
  api/
  worker/
  rag/
```

例:

- `api`: FastAPI のみ
- `worker`: Fiji 実行や重いジョブ処理
- `rag`: Elasticsearch や提案検証用環境

ただし現段階では、`demo` に絞る方が管理しやすい。

## 7. 運用イメージ

### ローカル開発

- ホスト上で設計・探索・スクリプト検証

### デモ

- `docker compose -f compose.demo.yml up --build`

### クラウド試験

- まずは `compose.demo.yml` と同等の 1 コンテナ構成で動作確認
- その後必要に応じて worker 分離を検討
