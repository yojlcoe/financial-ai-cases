#!/bin/bash

# データベースリストアスクリプト
# 使い方: bash backend/scripts/import_database.sh backend/scripts/database_dump_YYYYMMDD_HHMMSS.sql

set -e

if [ $# -eq 0 ]; then
    echo "エラー: SQLファイルを指定してください"
    echo "使い方: bash backend/scripts/import_database.sh backend/scripts/database_dump_YYYYMMDD_HHMMSS.sql"
    exit 1
fi

DUMP_FILE=$1

if [ ! -f "${DUMP_FILE}" ]; then
    echo "エラー: ファイルが見つかりません: ${DUMP_FILE}"
    exit 1
fi

echo "======================================"
echo "データベースインポート"
echo "======================================"
echo "ファイル: ${DUMP_FILE}"
echo ""
echo "警告: 既存のデータは削除されます (job_histories を除く)"
read -p "続行しますか? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "インポートをキャンセルしました"
    exit 0
fi

echo ""
echo "既存データをクリア中..."

# job_histories 以外のテーブルをクリア
docker-compose exec -T db psql -U casestudy -d casestudy <<EOF
TRUNCATE TABLE company_search_settings CASCADE;
TRUNCATE TABLE search_settings CASCADE;
TRUNCATE TABLE schedule_settings CASCADE;
TRUNCATE TABLE articles CASCADE;
TRUNCATE TABLE source_urls CASCADE;
TRUNCATE TABLE companies CASCADE;
EOF

echo "✓ データクリア完了"
echo ""
echo "データをインポート中..."

# SQLファイルをインポート
cat "${DUMP_FILE}" | docker-compose exec -T db psql -U casestudy -d casestudy

echo ""
echo "======================================"
echo "✓ インポート完了!"
echo "======================================"
