# データベース移行ガイド

job_histories テーブルを除く、すべてのデータを別環境に移行する手順です。

## 📦 エクスポート手順（現在の環境）

1. プロジェクトルートディレクトリで以下のコマンドを実行:

```bash
bash backend/scripts/export_database.sh
```

2. `backend/scripts/database_dump_YYYYMMDD_HHMMSS.sql` が作成されます

3. このSQLファイルを移行先の環境にコピー:
   - USBメモリ
   - クラウドストレージ (Google Drive, Dropbox等)
   - SCP: `scp backend/scripts/database_dump_*.sql user@host:/path/`
   - その他の方法

## 📥 インポート手順（移行先の環境）

1. SQLファイルを移行先の `backend/scripts/` ディレクトリにコピー

2. Docker環境が起動していることを確認:

```bash
docker-compose up -d
```

3. プロジェクトルートディレクトリで以下のコマンドを実行:

```bash
bash backend/scripts/import_database.sh backend/scripts/database_dump_YYYYMMDD_HHMMSS.sql
```

4. 確認メッセージが表示されるので、`yes` と入力

## ⚠️ 注意事項

- **既存データは削除されます** (job_histories を除く)
- 以下のテーブルのデータが移行されます:
  - `companies` (企業)
  - `source_urls` (情報源URL)
  - `articles` (記事)
  - `schedule_settings` (スケジュール設定)
  - `search_settings` (検索設定)
  - `company_search_settings` (企業別検索設定)
- `job_histories` (ジョブ履歴) は**移行されません**

## 🔍 トラブルシューティング

### エクスポート時のエラー

```bash
# Dockerコンテナが起動しているか確認
docker-compose ps

# 起動していない場合は起動
docker-compose up -d
```

### インポート時のエラー

```bash
# ファイルパスが正しいか確認
ls -lh backend/scripts/database_dump_*.sql

# データベースコンテナが起動しているか確認
docker-compose ps db
```

### ファイルサイズの確認

```bash
# エクスポートファイルのサイズを確認
ls -lh backend/scripts/database_dump_*.sql
```

## 📊 データ確認

インポート後、以下のコマンドでデータが正しく移行されたか確認できます:

```bash
# 記事数を確認
docker-compose exec db psql -U casestudy -d casestudy -c "SELECT COUNT(*) FROM articles;"

# 企業数を確認
docker-compose exec db psql -U casestudy -d casestudy -c "SELECT COUNT(*) FROM companies;"
```
