#!/usr/bin/env bash
set -euo pipefail

cd /workspace/service
exec python3.11 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
