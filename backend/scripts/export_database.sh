#!/bin/bash

# データベースダンプスクリプト (job_histories テーブルを除く)
# 使い方: bash backend/scripts/export_database.sh

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="backend/scripts/database_dump_${TIMESTAMP}.sql"

echo "======================================"
echo "データベースエクスポート"
echo "======================================"
echo "出力ファイル: ${OUTPUT_FILE}"
echo ""

# job_histories 以外のテーブルをダンプ
echo "テーブルをエクスポート中..."
docker-compose exec -T db pg_dump -U casestudy -d casestudy \
  --exclude-table=job_histories \
  --no-owner \
  --no-acl \
  -F p \
  > "${OUTPUT_FILE}"

echo "✓ エクスポート完了: ${OUTPUT_FILE}"
echo ""
echo "======================================"
echo "次のステップ:"
echo "1. ${OUTPUT_FILE} を移行先の環境にコピー"
echo "   例: scp、USB、クラウドストレージなど"
echo "2. 移行先で bash backend/scripts/import_database.sh ${OUTPUT_FILE} を実行"
echo "======================================"
