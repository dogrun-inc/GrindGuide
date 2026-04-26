# Docker Layout

このディレクトリは、開発環境全体を Docker 前提へ固定するのではなく、

- デモ環境
- 共有しやすい再現環境
- クラウド試験環境

を切り出すための配置として使う。

## 方針

- リポジトリは引き続き 1 つのまま運用する
- Fiji / FastAPI / 非同期ジョブの再現性が必要な部分を Docker 化する
- RAG 実験や設計検討は、必要に応じてホスト環境でも継続できるようにする

## 配置

```text
docker/
  README.md
  demo/
    Dockerfile
    start-demo.sh
compose.demo.yml
```

## 役割

- `compose.demo.yml`
  - デモ環境の起動定義
- `docker/demo/Dockerfile`
  - API + background job + Fiji を 1 コンテナで動かす最小構成
- `docker/demo/start-demo.sh`
  - コンテナ内起動スクリプト

## 今後の拡張余地

将来的に必要になれば、次のように増やせる。

```text
docker/
  demo/
  api/
  worker/
  nginx/
```

ただし現段階では、`demo/` に閉じた最小構成を維持する。
