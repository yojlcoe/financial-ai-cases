#!/bin/bash
#
# データベースマイグレーション実行スクリプト
# 使用方法: bash migrate.sh [environment]
#   environment: local (デフォルト) または prod
#

set -e

ENVIRONMENT=${1:-local}
COMPOSE_FILE="docker-compose.yml"

if [ "$ENVIRONMENT" = "prod" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    echo "🚀 本番環境のマイグレーションを実行します"
    echo "⚠️  警告: 本番データベースに変更を加えます。バックアップを取得済みですか？"
    read -p "続行しますか? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo "マイグレーション中止"
        exit 0
    fi
else
    echo "🔧 ローカル環境のマイグレーションを実行します"
fi

# データベースが稼働中か確認
echo ""
echo "[1/3] データベース接続を確認中..."
if docker compose -f $COMPOSE_FILE exec db pg_isready -U casestudy > /dev/null 2>&1; then
    echo "✓ データベース接続OK"
else
    echo "✗ データベースに接続できません"
    echo "  docker compose -f $COMPOSE_FILE up -d db を実行してください"
    exit 1
fi

# バックアップを作成
echo ""
echo "[2/3] バックアップを作成中..."
BACKUP_DIR="./backups"
mkdir -p $BACKUP_DIR
BACKUP_FILE="${BACKUP_DIR}/backup_$(date +%Y%m%d_%H%M%S).sql"

docker compose -f $COMPOSE_FILE exec db pg_dump -U casestudy casestudy > $BACKUP_FILE
echo "✓ バックアップ作成完了: $BACKUP_FILE"

# マイグレーション実行
echo ""
echo "[3/3] マイグレーションを実行中..."

# 新規データベースかチェック
TABLE_COUNT=$(docker compose -f $COMPOSE_FILE exec db psql -U casestudy -d casestudy -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')

if [ "$TABLE_COUNT" -eq "0" ]; then
    echo "新規データベースを検出 - 初期スキーマを適用します"
    docker compose -f $COMPOSE_FILE exec backend cat /app/migrations/000_initial_schema.sql | \
        docker compose -f $COMPOSE_FILE exec -T db psql -U casestudy -d casestudy
    echo "✓ 初期スキーマの適用完了"
else
    echo "既存のデータベースを検出 - テーブル数: $TABLE_COUNT"
    echo ""
    echo "適用可能なマイグレーション:"
    echo "  - 新しいマイグレーションファイルがある場合は手動で実行してください"
    echo "  - 例: bash migrate.sh prod 008_new_migration.sql"

    # 特定のマイグレーションファイルが指定された場合
    if [ -n "$2" ]; then
        MIGRATION_FILE="$2"
        if [ -f "../backend/migrations/$MIGRATION_FILE" ]; then
            echo ""
            echo "マイグレーション $MIGRATION_FILE を実行中..."
            docker compose -f $COMPOSE_FILE exec backend cat /app/migrations/$MIGRATION_FILE | \
                docker compose -f $COMPOSE_FILE exec -T db psql -U casestudy -d casestudy
            echo "✓ マイグレーション完了"
        else
            echo "✗ マイグレーションファイルが見つかりません: $MIGRATION_FILE"
            exit 1
        fi
    fi
fi

echo ""
echo "======================================"
echo "マイグレーション処理完了"
echo "======================================"
echo ""
echo "バックアップファイル: $BACKUP_FILE"
echo ""
echo "データベース状態を確認:"
echo "  docker compose -f $COMPOSE_FILE exec db psql -U casestudy -d casestudy -c '\dt'"
echo ""
