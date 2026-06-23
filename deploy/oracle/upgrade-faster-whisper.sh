#!/usr/bin/env bash
# Oracle VM: rebuild API with faster-whisper large-v3 and restart stack.
# Run on the server from repo root: bash deploy/oracle/upgrade-faster-whisper.sh
set -euo pipefail

cd "$(dirname "$0")/../.."

echo "==> Pull latest code"
git pull --ff-only origin "$(git branch --show-current)"

echo "==> Ensure .env has faster-whisper settings"
grep -q '^WHISPER_MODEL_SIZE=' .env 2>/dev/null && \
  sed -i 's/^WHISPER_MODEL_SIZE=.*/WHISPER_MODEL_SIZE=large-v3/' .env || \
  echo 'WHISPER_MODEL_SIZE=large-v3' >> .env
grep -q '^WHISPER_COMPUTE_TYPE=' .env 2>/dev/null && \
  sed -i 's/^WHISPER_COMPUTE_TYPE=.*/WHISPER_COMPUTE_TYPE=int8/' .env || \
  echo 'WHISPER_COMPUTE_TYPE=int8' >> .env
grep -q '^WEB_CONCURRENCY=' .env 2>/dev/null && \
  sed -i 's/^WEB_CONCURRENCY=.*/WEB_CONCURRENCY=1/' .env || \
  echo 'WEB_CONCURRENCY=1' >> .env
grep -q '^WHISPER_ENABLED=' .env 2>/dev/null && \
  sed -i 's/^WHISPER_ENABLED=.*/WHISPER_ENABLED=true/' .env || \
  echo 'WHISPER_ENABLED=true' >> .env

echo "==> Rebuild API image (faster-whisper, no openai-whisper)"
docker compose -f docker-compose.yml -f docker-compose.oracle.yml build api --no-cache

echo "==> Restart API (first Speaking request downloads ~3GB model into hf_cache volume)"
docker compose -f docker-compose.yml -f docker-compose.oracle.yml up -d api

echo "==> Health check"
sleep 5
docker compose -f docker-compose.yml -f docker-compose.oracle.yml exec -T api curl -sf http://localhost:8000/health
echo ""
echo "OK. Test Speaking on https://linguaielts.site — first transcription may take 1–3 min (model download)."
