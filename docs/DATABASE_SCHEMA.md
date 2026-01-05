# データベーススキーマ仕様書

## 概要

このドキュメントは、事例調査AIエージェントシステムのデータベーススキーマを定義します。

最終更新日: 2026-01-02

## データベース構成

- **RDBMS**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0 (async)
- **マイグレーション**: カスタムスクリプト（将来的にAlembicに移行予定）

---

## テーブル一覧

### 1. companies（企業マスタ）

企業情報を管理するマスタテーブル。

| カラム名 | 型 | NULL | デフォルト | 制約 | 説明 |
|---------|-----|------|-----------|------|------|
| id | INTEGER | NO | AUTO | PRIMARY KEY | 企業ID（自動採番） |
| name | VARCHAR(255) | NO | - | - | 企業名（日本語） |
| name_en | VARCHAR(255) | YES | NULL | - | 企業名（英語） |
| country | VARCHAR(100) | YES | NULL | - | 国名 |
| is_active | BOOLEAN | NO | TRUE | - | アクティブフラグ |
| created_at | TIMESTAMP | NO | NOW() | - | 作成日時 |
| updated_at | TIMESTAMP | NO | NOW() | - | 更新日時 |

**インデックス:**
- PRIMARY KEY: `id`
- INDEX: `id` (自動作成)

**リレーションシップ:**
- `source_urls` (1:N) → CASCADE DELETE
- `articles` (1:N) → CASCADE DELETE
- `schedule_settings` (1:1) → CASCADE DELETE

---

### 2. source_urls（情報源URL）

各企業の情報収集元URLを管理。

| カラム名 | 型 | NULL | デフォルト | 制約 | 説明 |
|---------|-----|------|-----------|------|------|
| id | INTEGER | NO | AUTO | PRIMARY KEY | URL ID |
| company_id | INTEGER | NO | - | FOREIGN KEY → companies.id | 企業ID |
| url | VARCHAR(500) | NO | - | - | 情報源URL |
| url_type | VARCHAR(50) | NO | - | - | URLタイプ（press_release, news, blog等） |
| is_active | BOOLEAN | NO | TRUE | - | アクティブフラグ |
| created_at | TIMESTAMP | NO | NOW() | - | 作成日時 |
| updated_at | TIMESTAMP | NO | NOW() | - | 更新日時 |

**インデックス:**
- PRIMARY KEY: `id`
- INDEX: `id`
- **INDEX: `(company_id, is_active)`** ← パフォーマンス最適化

**外部キー:**
- `company_id` REFERENCES `companies(id)` ON DELETE CASCADE

---

### 3. articles（記事）

収集した記事情報を保存。

| カラム名 | 型 | NULL | デフォルト | 制約 | 説明 |
|---------|-----|------|-----------|------|------|
| id | INTEGER | NO | AUTO | PRIMARY KEY | 記事ID |
| company_id | INTEGER | NO | - | FOREIGN KEY → companies.id | 企業ID |
| title | VARCHAR(500) | NO | - | - | 記事タイトル |
| url | VARCHAR(500) | NO | - | UNIQUE | 記事URL |
| published_date | DATE | YES | NULL | - | 公開日 |
| content | TEXT | YES | NULL | - | 本文 |
| summary | TEXT | YES | NULL | - | AI生成の要約 |
| category | VARCHAR(100) | YES | NULL | - | AI分類されたカテゴリ |
| business_area | VARCHAR(100) | YES | NULL | - | AI分類されたビジネス領域 |
| tags | VARCHAR(500) | YES | NULL | - | AIタグ（カンマ区切り） |
| is_inappropriate | BOOLEAN | NO | FALSE | - | 不適切記事フラグ（除外対象） |
| inappropriate_reason | TEXT | YES | NULL | - | 不適切な理由 |
| is_reviewed | BOOLEAN | NO | FALSE | - | 人間による確認済みフラグ |
| created_at | TIMESTAMP | NO | NOW() | - | 作成日時 |
| updated_at | TIMESTAMP | NO | NOW() | - | 更新日時 |

**インデックス:**
- PRIMARY KEY: `id`
- INDEX: `id`
- UNIQUE INDEX: `url`
- **INDEX: `(company_id, published_date DESC)`** ← パフォーマンス最適化
- **INDEX: `created_at DESC`** ← パフォーマンス最適化
- **INDEX: `is_inappropriate`** ← フィルタリング用

**外部キー:**
- `company_id` REFERENCES `companies(id)` ON DELETE CASCADE

**Note:**
- `tags`は将来的に正規化予定（多対多のタグテーブルへ）
- `is_inappropriate`フラグは、AI分析で「調査対象外」と判定された記事をマーク（一覧・分析から除外）
- `is_reviewed`フラグは、人間が確認済みの記事をマーク（レビューワークフロー用）

---

### 4. job_histories（ジョブ実行履歴）

バッチジョブの実行履歴を記録。

| カラム名 | 型 | NULL | デフォルト | 制約 | 説明 |
|---------|-----|------|-----------|------|------|
| id | INTEGER | NO | AUTO | PRIMARY KEY | ジョブID |
| job_type | VARCHAR(50) | NO | - | - | ジョブタイプ（daily, weekly, manual） |
| status | VARCHAR(50) | NO | - | - | ステータス（running, completed, failed） |
| started_at | TIMESTAMP WITH TIME ZONE | NO | - | - | 開始日時 |
| completed_at | TIMESTAMP WITH TIME ZONE | YES | NULL | - | 完了日時 |
| total_companies | INTEGER | NO | 0 | - | 処理対象企業数 |
| processed_companies | INTEGER | NO | 0 | - | 処理完了企業数 |
| total_articles | INTEGER | NO | 0 | - | 収集記事数 |
| error_message | TEXT | YES | NULL | - | エラーメッセージ |

**インデックス:**
- PRIMARY KEY: `id`
- INDEX: `id`
- **INDEX: `(status, started_at DESC)`** ← パフォーマンス最適化

**Note:** タイムゾーン対応のため `TIMESTAMP WITH TIME ZONE` を使用

---

### 5. schedule_settings（スケジュール設定）

検索期間とスケジュール設定を管理。

| カラム名 | 型 | NULL | デフォルト | 制約 | 説明 |
|---------|-----|------|-----------|------|------|
| id | INTEGER | NO | AUTO | PRIMARY KEY | 設定ID |
| search_start_date | DATE | NO | - | - | 検索開始日 |
| search_end_date | DATE | NO | - | - | 検索終了日 |
| schedule_type | VARCHAR(50) | NO | 'weekly' | - | スケジュールタイプ（daily, weekly） |
| schedule_day | INTEGER | NO | 1 | - | 実行日（曜日または日付） |
| schedule_hour | INTEGER | NO | 9 | - | 実行時刻（0-23） |
| created_at | TIMESTAMP | NO | NOW() | - | 作成日時 |
| updated_at | TIMESTAMP | NO | NOW() | - | 更新日時 |

**インデックス:**
- PRIMARY KEY: `id`
- INDEX: `id`

**Note:** シングルトンテーブル（レコードは1件のみ想定）

---

### 6. global_search_settings（グローバル検索設定）

グローバル検索設定を管理。

| カラム名 | 型 | NULL | デフォルト | 制約 | 説明 |
|---------|-----|------|-----------|------|------|
| id | INTEGER | NO | AUTO | PRIMARY KEY | 設定ID |
| default_region | VARCHAR(10) | YES | NULL | - | デフォルト検索リージョン |
| created_at | TIMESTAMP | NO | NOW() | - | 作成日時 |
| updated_at | TIMESTAMP | NO | NOW() | - | 更新日時 |

**インデックス:**
- PRIMARY KEY: `id`

**トリガー:**
- `update_global_search_settings_updated_at`: `updated_at` 自動更新
- `update_search_settings_updated_at`: `updated_at` 自動更新（レガシー）

**Note:**
- シングルトンテーブル（レコードは1件のみ想定）
- 検索キーワードやLLM設定は、アプリケーション設定（プロンプト設定ファイル）に移行

---

### 7. company_search_settings（企業別検索設定）

企業ごとのカスタム検索設定（グローバル設定をオーバーライド）。

| カラム名 | 型 | NULL | デフォルト | 制約 | 説明 |
|---------|-----|------|-----------|------|------|
| id | INTEGER | NO | AUTO | PRIMARY KEY | 設定ID |
| company_id | INTEGER | NO | - | FOREIGN KEY → companies.id, UNIQUE | 企業ID |
| region | VARCHAR(10) | YES | NULL | - | 検索リージョン（企業専用） |
| custom_keywords | TEXT[] | YES | NULL | - | カスタムキーワード配列 |
| created_at | TIMESTAMP | NO | NOW() | - | 作成日時 |
| updated_at | TIMESTAMP | NO | NOW() | - | 更新日時 |

**インデックス:**
- PRIMARY KEY: `id`
- UNIQUE INDEX: `company_id`

**外部キー:**
- `company_id` REFERENCES `companies(id)` ON DELETE CASCADE

**トリガー:**
- `update_company_search_settings_updated_at`: `updated_at` 自動更新

**リレーションシップ:**
- `company` (N:1) → Company

**設定の優先順位:**
1. `custom_keywords` が設定されている場合 → これを使用
2. それ以外 → `global_search_settings.search_keywords` を使用

同様に：
1. `region` が設定されている場合 → これを使用
2. それ以外 → `global_search_settings.default_region` を使用

---

## データベーストリガー

### update_updated_at_column()

テーブルの `updated_at` カラムを自動的に更新。

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';
```

**適用テーブル:**
- `global_search_settings`
- `company_search_settings`

---

## パフォーマンス最適化

### 追加されたインデックス（2025-12-30）

以下のインデックスがパフォーマンス向上のために追加されました：

1. **`idx_articles_company_id_published_date`**
   - テーブル: `articles`
   - カラム: `(company_id, published_date DESC)`
   - 用途: 企業ごとの最新記事取得
   - 期待効果: ~100倍高速化

2. **`idx_articles_created_at`**
   - テーブル: `articles`
   - カラム: `created_at DESC`
   - 用途: 新着記事の取得
   - 期待効果: ~100倍高速化

3. **`idx_source_urls_company_id_active`**
   - テーブル: `source_urls`
   - カラム: `(company_id, is_active)`
   - 用途: 企業のアクティブなソースURL取得
   - 期待効果: ~50倍高速化

4. **`idx_job_histories_status_started_at`**
   - テーブル: `job_histories`
   - カラム: `(status, started_at DESC)`
   - 用途: ジョブステータス別の履歴検索
   - 期待効果: ~50倍高速化

---

## データ整合性制約

### 外部キー制約

| 子テーブル | 子カラム | 親テーブル | 親カラム | ON DELETE |
|-----------|---------|----------|---------|-----------|
| source_urls | company_id | companies | id | CASCADE |
| articles | company_id | companies | id | CASCADE |
| company_search_settings | company_id | companies | id | CASCADE |

### ユニーク制約

| テーブル | カラム | 説明 |
|---------|--------|------|
| articles | url | 記事URLの重複を防止 |
| company_search_settings | company_id | 1企業につき1設定のみ |

---

## 今後の改善予定

### 短期（優先度: 高）

1. **Alembic導入**
   - バージョン管理された自動マイグレーション
   - ロールバック機能

2. **タグの正規化**
   - `articles.tags` を多対多テーブルに分離
   - `tags` テーブルと `article_tags` 中間テーブルの作成

### 中期（優先度: 中）

1. **全文検索の追加**
   - PostgreSQL の `tsvector` を使用
   - `articles.title`, `articles.content` に対する全文検索インデックス

2. **監査ログテーブル**
   - 設定変更履歴の記録
   - WHO/WHEN/WHATの追跡

3. **ORM スタイルの統一**
   - 全モデルで新しい `Mapped` スタイルに統一
   - タイムスタンプ処理の一貫性向上

### 長期（優先度: 低）

1. **パーティショニング**
   - `articles` テーブルの日付ベースパーティショニング
   - 大量データへの対応

2. **レプリケーション**
   - 読み取り専用レプリカの追加
   - 負荷分散

---

## ER図

```
┌─────────────────┐
│   companies     │
│─────────────────│
│ id (PK)         │
│ name            │
│ name_en         │
│ country         │
│ is_active       │
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │
         │ 1:N
         │
    ┌────┴──────────────────────────────┬──────────────────────┐
    │                                   │                      │
┌───▼────────────┐          ┌──────────▼──────┐    ┌─────────▼─────────────────┐
│  source_urls   │          │    articles     │    │ company_search_settings   │
│────────────────│          │─────────────────│    │───────────────────────────│
│ id (PK)        │          │ id (PK)         │    │ id (PK)                   │
│ company_id(FK) │          │ company_id (FK) │    │ company_id (FK, UNIQUE)   │
│ url            │          │ title           │    │ region                    │
│ url_type       │          │ url (UNIQUE)    │    │ custom_keywords           │
│ is_active      │          │ published_date  │    │ created_at                │
│ created_at     │          │ summary         │    │ updated_at                │
│ updated_at     │          │ content         │    └───────────────────────────┘
└────────────────┘          │ tags            │
                            │ source_type     │
                            │ created_at      │
                            │ updated_at      │
                            └─────────────────┘

┌─────────────────────────┐      ┌──────────────────┐
│ global_search_settings  │      │  job_histories   │
│─────────────────────────│      │──────────────────│
│ id (PK)                 │      │ id (PK)          │
│ search_keywords         │      │ job_type         │
│ llm_filter_enabled      │      │ status           │
│ llm_filter_prompt       │      │ started_at       │
│ llm_system_message      │      │ completed_at     │
│ llm_temperature         │      │ total_companies  │
│ llm_max_tokens          │      │ processed_co...  │
│ default_region          │      │ total_articles   │
│ created_at              │      │ error_message    │
│ updated_at              │      └──────────────────┘
└─────────────────────────┘

┌──────────────────────┐
│  schedule_settings   │
│──────────────────────│
│ id (PK)              │
│ search_start_date    │
│ search_end_date      │
│ schedule_type        │
│ schedule_day         │
│ schedule_hour        │
│ created_at           │
│ updated_at           │
└──────────────────────┘
```

---

## 参考資料

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/sql-databases/)

---

**Document Version:** 2.1
**Last Updated:** 2026-01-02
**Author:** AI Case Study Research System Team