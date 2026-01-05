# Database Migrations

このディレクトリには、データベーススキーマのマイグレーションファイルが含まれています。

## マイグレーションファイル一覧

- **000_initial_schema.sql** - 完全な初期スキーマ（新規データベース用）

## 新規データベースのセットアップ

新しいデータベースを初期化する場合は、`000_initial_schema.sql`のみを実行してください。

### ローカル環境（Docker Compose）

```bash
# Docker Composeでデータベースを起動
docker compose up -d db

# スキーマを作成
docker compose exec backend cat /app/migrations/000_initial_schema.sql | \
  docker compose exec -T db psql -U casestudy -d casestudy
```

### 本番環境（GCP）

```bash
# 本番環境のデータベースコンテナ内で実行
docker compose -f docker-compose.prod.yml exec backend cat /app/migrations/000_initial_schema.sql | \
  docker compose -f docker-compose.prod.yml exec -T db psql -U casestudy -d casestudy
```

## 既存データベースへの新しいマイグレーション適用

将来的にスキーマ変更が必要な場合は、新しいマイグレーションファイルを作成して実行します。

### 新しいマイグレーションの実行

```bash
# ローカル環境
docker compose exec backend cat /app/migrations/001_new_migration.sql | \
  docker compose exec -T db psql -U casestudy -d casestudy

# 本番環境
docker compose -f docker-compose.prod.yml exec backend cat /app/migrations/001_new_migration.sql | \
  docker compose -f docker-compose.prod.yml exec -T db psql -U casestudy -d casestudy
```

## マイグレーションの作成ガイドライン

新しいマイグレーションファイルを作成する場合：

1. **ファイル名**: `XXX_descriptive_name.sql` の形式を使用
   - XXX: 3桁の連番（001から開始）
   - 例: `001_add_user_roles.sql`

2. **ファイル内容**:
   ```sql
   -- Description of what this migration does
   -- Migration: XXX_descriptive_name
   -- Date: YYYY-MM-DD

   -- Your SQL commands here
   ALTER TABLE ...;
   CREATE INDEX ...;
   ```

3. **ベストプラクティス**:
   - `IF NOT EXISTS`や`IF EXISTS`を使用して冪等性を確保
   - ロールバック用のコメントを含める
   - インデックスの作成は`CONCURRENTLY`を検討（本番環境）

## スキーマの確認

現在のデータベーススキーマを確認：

```bash
# テーブル一覧
docker compose exec db psql -U casestudy -d casestudy -c "\dt"

# 特定のテーブルの詳細
docker compose exec db psql -U casestudy -d casestudy -c "\d articles"

# 完全なスキーマのエクスポート
docker compose exec db pg_dump -U casestudy -d casestudy --schema-only --no-owner --no-privileges > current_schema.sql
```

## データベースのバックアップ

マイグレーション前に必ずバックアップを取ってください：

```bash
# データベース全体のバックアップ
docker compose exec db pg_dump -U casestudy casestudy > backup_$(date +%Y%m%d_%H%M%S).sql

# スキーマのみ
docker compose exec db pg_dump -U casestudy -d casestudy --schema-only > schema_backup.sql

# データのみ
docker compose exec db pg_dump -U casestudy -d casestudy --data-only > data_backup.sql
```

## リストア

```bash
# バックアップからリストア
cat backup_YYYYMMDD_HHMMSS.sql | docker compose exec -T db psql -U casestudy casestudy
```

## トラブルシューティング

### マイグレーションが失敗した場合

1. エラーメッセージを確認
2. データベースの状態を確認（`\d`コマンド）
3. 必要に応じてバックアップからリストア
4. マイグレーションファイルを修正して再実行

### ロックの問題

本番環境でマイグレーションを実行する際は、以下に注意：

- アクティブな接続を確認: `SELECT * FROM pg_stat_activity;`
- 長時間実行されるクエリを避ける
- インデックス作成は`CONCURRENTLY`オプションを使用

## 参考

- PostgreSQL公式ドキュメント: https://www.postgresql.org/docs/
- SQLAlchemy Migrations: https://alembic.sqlalchemy.org/
