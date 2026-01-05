# API仕様書

## 概要

事例調査AIエージェントシステムのREST API仕様書です。

**Base URL:** `http://localhost:8000/api/v1`

**最終更新日:** 2025-12-30

---

## 認証

現在、認証は実装されていません（将来的に追加予定）。

---

## エラーレスポンス

すべてのエンドポイントは、エラー時に以下の形式でレスポンスを返します：

```json
{
  "detail": "エラーメッセージ"
}
```

**HTTPステータスコード:**
- `200`: 成功
- `404`: リソースが見つからない
- `422`: バリデーションエラー
- `500`: サーバーエラー

---

## エンドポイント一覧

### 1. Companies（企業管理）

#### 1.1 企業一覧取得

```
GET /companies
```

**レスポンス:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "サンプル銀行",
      "name_en": "Sample Bank Corporation",
      "country": "Japan",
      "is_active": true,
      "created_at": "2025-01-01T00:00:00",
      "updated_at": "2025-01-01T00:00:00",
      "source_urls": [...]
    }
  ],
  "total": 10
}
```

---

#### 1.2 企業詳細取得

```
GET /companies/{company_id}
```

**レスポンス:** 企業オブジェクト

---

#### 1.3 企業作成

```
POST /companies
```

**リクエストボディ:**
```json
{
  "name": "サンプル銀行",
  "name_en": "Sample Bank Corporation",
  "country": "Japan",
  "is_active": true,
  "source_urls": [
    {
      "url": "https://example.com/press/",
      "url_type": "press_release",
      "is_active": true
    }
  ]
}
```

**レスポンス:** 作成された企業オブジェクト

---

#### 1.4 企業更新

```
PUT /companies/{company_id}
```

**リクエストボディ:**
```json
{
  "name": "サンプル銀行",
  "name_en": "Sample Bank Corporation",
  "country": "Japan",
  "is_active": true
}
```

**レスポンス:** 更新された企業オブジェクト

---

#### 1.5 企業削除

```
DELETE /companies/{company_id}
```

**レスポンス:**
```json
{
  "message": "Company deleted successfully"
}
```

**Note:** CASCADE削除により、関連する `source_urls`, `articles`, `company_search_settings` も同時に削除されます。

---

#### 1.6 ソースURL追加

```
POST /companies/{company_id}/urls
```

**リクエストボディ:**
```json
{
  "url": "https://example.com/press/",
  "url_type": "press_release",
  "is_active": true
}
```

**レスポンス:** 作成されたソースURLオブジェクト

---

#### 1.7 ソースURL更新

```
PUT /companies/{company_id}/urls/{url_id}
```

**リクエストボディ:**
```json
{
  "url": "https://example.com/press/",
  "url_type": "press_release",
  "is_active": true
}
```

**レスポンス:** 更新されたソースURLオブジェクト

---

#### 1.8 ソースURL削除

```
DELETE /companies/{company_id}/urls/{url_id}
```

**レスポンス:**
```json
{
  "message": "URL deleted successfully"
}
```

---

### 2. Articles（記事管理）

#### 2.1 記事一覧取得

```
GET /articles?company_id={company_id}&skip={skip}&limit={limit}
```

**クエリパラメータ:**
- `company_id` (optional): 企業IDでフィルタリング
- `skip` (optional): スキップ数（デフォルト: 0）
- `limit` (optional): 取得件数（デフォルト: 100）
- `category` (optional): カテゴリでフィルタリング
- `business_area` (optional): 業務領域でフィルタリング
- `tags` (optional): タグでフィルタリング
- `start_date` (optional): 開始日でフィルタリング（YYYY-MM-DD）
- `end_date` (optional): 終了日でフィルタリング（YYYY-MM-DD）
- `is_reviewed` (optional): レビュー状態でフィルタリング

**レスポンス:**
```json
{
  "items": [
    {
      "id": 1,
      "company_id": 1,
      "title": "AIを活用した新サービス開始",
      "url": "https://example.com/article/1",
      "published_date": "2025-01-15",
      "summary": "要約テキスト...",
      "content": "本文...",
      "category": "顧客対応",
      "business_area": "リテールバンキング",
      "tags": "AI,DX,自動化",
      "is_inappropriate": false,
      "inappropriate_reason": null,
      "is_reviewed": false,
      "created_at": "2025-01-16T00:00:00"
    }
  ],
  "total": 50
}
```

---

#### 2.2 記事更新

```
PUT /articles/{article_id}
```

**リクエストボディ:**
```json
{
  "title": "AIを活用した新サービス開始",
  "summary": "要約テキスト...",
  "published_date": "2025-01-15",
  "category": "顧客対応",
  "business_area": "リテールバンキング",
  "tags": "AI,DX,自動化",
  "is_inappropriate": false,
  "inappropriate_reason": null,
  "is_reviewed": true
}
```

**レスポンス:** 更新された記事オブジェクト

---

#### 2.3 記事分析サマリー取得

```
GET /articles/analysis-stats?company_id={company_id}
```

**クエリパラメータ:**
- `company_id` (optional): 企業IDでフィルタリング

**レスポンス:**
```json
{
  "total": 120,
  "analyzed": 80,
  "coefficient": 66.7
}
```

---

#### 2.4 記事分析係数取得

```
GET /articles/analysis-coefficients?company_id={company_id}
```

**クエリパラメータ:**
- `company_id` (optional): 企業IDでフィルタリング

**レスポンス:**
```json
{
  "total": 120,
  "by_category": [{"label": "顧客対応", "count": 30}],
  "by_business_area": [{"label": "リテールバンキング", "count": 25}],
  "by_region": [{"label": "jp", "count": 40}],
  "by_month": [{"period": "2025-01", "count": 10}]
}
```

---

#### 2.5 単一URLから記事追加

```
POST /articles/from-url
```

**リクエストボディ:**
```json
{
  "url": "https://example.com/article/1",
  "company_id": 1
}
```

**レスポンス:**
```json
{
  "job_id": 1,
  "message": "URL addition job started for Sample Bank"
}
```

**エラー:**
- `400`: URLが重複している
- `404`: 企業が見つからない

---

#### 2.6 複数URLから記事追加

```
POST /articles/from-urls
```

**リクエストボディ:**
```json
{
  "urls": [
    "https://example.com/article/1",
    "https://example.com/article/2"
  ],
  "company_id": 1
}
```

**レスポンス:**
```json
{
  "job_id": 1,
  "message": "2 URL(s) addition job started for Sample Bank"
}
```

**エラー:**
- `400`: URLが重複している、またはURLが空
- `404`: 企業が見つからない

### 3. Jobs（ジョブ管理）

#### 3.1 ジョブ履歴一覧取得

```
GET /jobs
```

**レスポンス:**
```json
{
  "items": [
    {
      "id": 1,
      "job_type": "manual",
      "status": "completed",
      "started_at": "2025-01-15T09:00:00+09:00",
      "completed_at": "2025-01-15T09:30:00+09:00",
      "total_companies": 10,
      "processed_companies": 10,
      "total_articles": 50,
      "error_message": null
    }
  ],
  "total": 20
}
```

---

#### 3.2 ジョブ開始

```
POST /jobs/start
```

**リクエストボディ:**
```json
{
  "job_type": "manual"
}
```

**job_type:**
- `manual`: 手動実行
- `daily`: 日次実行
- `weekly`: 週次実行

**レスポンス:**
```json
{
  "job_id": 1,
  "message": "Job started with 10 companies"
}
```

---

### 4. Settings（設定管理）

#### 4.1 スケジュール設定取得

```
GET /settings
```

**レスポンス:**
```json
{
  "id": 1,
  "search_start_date": "2025-01-01",
  "search_end_date": "2025-12-31",
  "schedule_type": "weekly",
  "schedule_day": 1,
  "schedule_hour": 9,
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-01-01T00:00:00"
}
```

**schedule_day の意味:**
- `schedule_type="weekly"` の場合: 0=月曜, 1=火曜, ..., 6=日曜
- `schedule_type="daily"` の場合: 1-28（月の日付）

---

#### 4.2 スケジュール設定更新

```
POST /settings
```

**リクエストボディ:**
```json
{
  "search_start_date": "2025-01-01",
  "search_end_date": "2025-12-31",
  "schedule_type": "weekly",
  "schedule_day": 1,
  "schedule_hour": 9
}
```

**レスポンス:** 更新された設定オブジェクト

---

### 5. Search Settings（検索設定管理）

#### 5.1 グローバル検索設定取得

```
GET /search-settings/global
```

**レスポンス:**
```json
{
  "id": 1,
  "default_region": null
}
```

---

#### 5.2 グローバル検索設定更新

```
PUT /search-settings/global
```

**リクエストボディ:**
```json
{
  "default_region": "jp"
}
```

**レスポンス:** 更新された設定オブジェクト

---

#### 5.3 企業別検索設定取得

```
GET /search-settings/company/{company_name}
```

**パスパラメータ:**
- `company_name`: 企業名（URLエンコード必須）

**レスポンス:**
```json
{
  "id": 1,
  "company_id": 5,
  "company_name": "JPMorgan Chase",
  "region": "us-en",
  "custom_keywords": [
    "AI",
    "artificial intelligence",
    "machine learning",
    "automation",
    "fintech AI"
  ]
}
```

**エラー:**
- `404`: 企業が見つからない、または設定が存在しない

---

#### 5.4 企業別検索設定更新

```
PUT /search-settings/company/{company_name}
```

**パスパラメータ:**
- `company_name`: 企業名（URLエンコード必須）

**リクエストボディ:**
```json
{
  "region": "us-en",
  "custom_keywords": ["AI", "fintech AI"]
}
```

**Note:**
- `region`, `custom_keywords` はオプショナル
- `null` または空配列を設定すると、グローバル設定にフォールバック

**レスポンス:**
```json
{
  "id": 1,
  "company_id": 5,
  "company_name": "JPMorgan Chase",
  "region": "us-en",
  "custom_keywords": ["AI", "fintech AI"]
}
```

**エラー:**
- `404`: 企業が見つからない

---

#### 5.5 企業別検索設定削除

```
DELETE /search-settings/company/{company_name}
```

**パスパラメータ:**
- `company_name`: 企業名（URLエンコード必須）

**レスポンス:**
```json
{
  "message": "Settings for company 'JPMorgan Chase' deleted successfully"
}
```

**エラー:**
- `404`: 設定が見つからない

**Note:** 削除後は自動的にグローバル設定が適用されます。

---

#### 5.6 リージョン別キーワード取得

```
GET /search-settings/keywords/{region}
```

**パスパラメータ:**
- `region`: リージョン（`global` 指定時はグローバル扱い）

**レスポンス:**
```json
{
  "region": "jp",
  "keywords": ["AI", "生成AI", "DX"]
}
```

### 6. Prompts（プロンプト管理）

#### 6.1 プロンプト取得

```
GET /prompts
```

**レスポンス:**
```json
{
  "classifier": {
    "system_prompt": "分類用システムプロンプト...",
    "user_prompt_template": "ユーザープロンプトテンプレート...",
    "categories": ["顧客対応", "与信", "不正検知"],
    "business_areas": ["リテールバンキング", "法人向け"],
    "temperature": 0.0
  },
  "summarizer": {
    "system_prompt": "要約用システムプロンプト...",
    "user_prompt_template": "要約テンプレート...",
    "temperature": 0.2
  },
  "ai_relevance": {
    "system_prompt": "AI関連判定用システムプロンプト...",
    "content_prompt_template": "本文用テンプレート...",
    "text_prompt_template": "テキスト用テンプレート...",
    "temperature": 0.0
  }
}
```

---

### 7. Reports（レポート管理）

#### 6.1 レポート一覧取得

```
GET /reports
```

**レスポンス:**
```json
{
  "reports": [
    {
      "filename": "report_2025-01-15.md",
      "size": 10240,
      "created_at": 1736899200.0
    }
  ]
}
```

---

#### 6.2 レポート生成

```
POST /reports/generate?start_date={start_date}&end_date={end_date}
```

**クエリパラメータ:**
- `start_date`: 開始日（YYYY-MM-DD）
- `end_date`: 終了日（YYYY-MM-DD）

**レスポンス:**
```json
{
  "message": "Report generated successfully",
  "filepath": "/app/reports/report_2025-01-15.md",
  "filename": "report_2025-01-15.md"
}
```

---

#### 6.3 レポートダウンロード

```
GET /reports/download/{filename}
```

**パスパラメータ:**
- `filename`: レポートのファイル名

**レスポンス:** Markdownファイル

## 検索設定の優先順位

検索実行時の設定値は以下の優先順位で決定されます：

### リージョン
1. `company_search_settings.region` （企業別設定）
2. `global_search_settings.default_region` （グローバル設定）
3. `null`（グローバル検索）

### キーワード
- リージョンに応じて内部のキーワードセットを使用
- `company_search_settings.custom_keywords` が設定されている場合はそれを優先

---

## データベース変更の影響

### 企業削除時の CASCADE DELETE

企業を削除すると、以下のデータも自動的に削除されます：

1. `source_urls`（その企業の情報源URL）
2. `articles`（その企業の記事）
3. `company_search_settings`（その企業の検索設定）

**例:**
```bash
DELETE /companies/5
```

上記を実行すると、`company_id=5` に紐づくすべての関連データが削除されます。

---

## ベストプラクティス

### 1. 企業名のURLエンコード

企業名に特殊文字が含まれる場合、必ずURLエンコードしてください。

**悪い例:**
```
GET /search-settings/company/JPMorgan Chase
```

**良い例:**
```
GET /search-settings/company/JPMorgan%20Chase
```

---

### 2. 検索設定のテスト

新しい検索設定を適用する前に、テストスクリプトで動作確認することを推奨します。

```bash
docker compose run --rm backend python scripts/print_duckduckgo_search_results.py \
  --company-name "JPMorgan Chase" \
  --timelimit d \
  --num-results 10 \
  --ai-only-llm
```

---

## リクエスト例

### cURLでの企業別設定作成

```bash
curl -X PUT "http://localhost:8000/api/v1/search-settings/company/JPMorgan%20Chase" \
  -H "Content-Type: application/json" \
  -d '{
    "region": "us-en",
    "custom_keywords": ["AI", "artificial intelligence", "fintech AI"]
  }'
```

### JavaScriptでのグローバル設定取得

```javascript
const response = await fetch('http://localhost:8000/api/v1/search-settings/global');
const settings = await response.json();
console.log(settings.default_region);
```

### Pythonでのジョブ開始

```python
import requests

response = requests.post(
    'http://localhost:8000/api/v1/jobs/start',
    json={'job_type': 'manual'}
)
print(response.json())
```

---

## 変更履歴

### v2.0 (2025-12-30)

**Breaking Changes:**
- `CompanySearchSettingsResponse` に `company_id` フィールドを追加
- 内部的に `company_name` ではなく `company_id` でデータ管理

**新機能:**
- パフォーマンス最適化済みのクエリ
- CASCADE DELETE による整合性向上

**非推奨:**
- なし（後方互換性あり）

### v1.0 (2025-01-01)

- 初期リリース

---

## サポート

問題が発生した場合は、以下をご確認ください：

1. バックエンドログ: `docker compose logs backend`
2. データベース接続: `docker compose ps`
3. API仕様書（本ドキュメント）

---

**Document Version:** 2.0
**Last Updated:** 2025-12-30
**Author:** AI Case Study Research System Team
