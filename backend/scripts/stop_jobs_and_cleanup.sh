#!/bin/bash

# ジョブ停止と2026-01-05の記事削除スクリプト
# 使い方: bash backend/scripts/stop_jobs_and_cleanup.sh

set -e

# Docker Compose V2 detection
COMPOSE_CMD="docker compose"
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
fi

echo "======================================"
echo "ジョブ停止と記事削除"
echo "======================================"
echo ""

# ジョブを停止
echo "実行中のジョブを停止中..."
$COMPOSE_CMD exec -T db psql -U casestudy -d casestudy <<EOF
UPDATE job_histories
SET status = 'cancelled', completed_at = NOW()
WHERE status = 'running';
EOF

echo "✓ ジョブを停止しました"
echo ""

# 2026-01-05の記事を削除
echo "2026-01-05の記事を削除中..."
$COMPOSE_CMD exec -T db psql -U casestudy -d casestudy <<EOF
DELETE FROM articles
WHERE DATE(created_at) = '2026-01-05';
EOF

echo "✓ 記事を削除しました"
echo ""

# 確認
echo "データ確認中..."
$COMPOSE_CMD exec -T db psql -U casestudy -d casestudy -c "SELECT
  (SELECT COUNT(*) FROM job_histories WHERE status = 'running') as running_jobs,
  (SELECT COUNT(*) FROM articles WHERE DATE(created_at) = '2026-01-05') as articles_20260105,
  (SELECT COUNT(*) FROM articles) as total_articles;"

echo ""
echo "======================================"
echo "✓ 完了!"
echo "======================================"
