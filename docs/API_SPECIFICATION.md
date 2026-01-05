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
      "name": "三井住友銀行",
      "name_en": "Sumitomo Mitsui Banking Corporation",
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

#### 1.2 企業作成

```
POST /companies
```

**リクエストボディ:**
```json
{
  "name": "三井住友銀行",
  "name_en": "Sumitomo Mitsui Banking Corporation",
  "country": "Japan",
  "is_active": true
}
```

**レスポンス:** 作成された企業オブジェクト

---

#### 1.3 企業更新

```
PUT /companies/{company_id}
```

**リクエストボディ:**
```json
{
  "name": "三井住友銀行",
  "name_en": "Sumitomo Mitsui Banking Corporation",
  "country": "Japan",
  "is_active": true
}
```

**レスポンス:** 更新された企業オブジェクト

---

#### 1.4 企業削除

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

#### 1.5 ソースURL追加

```
POST /companies/{company_id}/urls
```

**リクエストボディ:**
```json
{
  "url": "https://www.smbc.co.jp/news/",
  "url_type": "press_release",
  "is_active": true
}
```

**レスポンス:** 作成されたソースURLオブジェクト

---

#### 1.6 ソースURL削除

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
      "tags": "AI,DX,自動化",
      "source_type": "press_release",
      "created_at": "2025-01-16T00:00:00",
      "updated_at": "2025-01-16T00:00:00"
    }
  ],
  "total": 50
}
```

---

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
  "message": "Job started successfully"
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
  "search_keywords": [
    "AI",
    "artificial intelligence",
    "generative AI",
    "machine learning",
    "DX",
    "digital transformation",
    "automation",
    "生成AI",
    "デジタル",
    "自動化",
    "事例"
  ],
  "llm_filter_enabled": true,
  "llm_filter_prompt": "Answer with JSON only: {\"ai_related\": true|false}.\nDetermine if the content is specifically related to AI...",
  "llm_system_message": "AI relevance classifier (strict mode: AI-only, excluding general DX/digitalization)",
  "llm_temperature": 0.0,
  "llm_max_tokens": 120,
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
  "search_keywords": ["AI", "machine learning", "生成AI"],
  "llm_filter_enabled": true,
  "llm_filter_prompt": "プロンプトテキスト...",
  "llm_system_message": "システムメッセージ",
  "llm_temperature": 0.0,
  "llm_max_tokens": 120,
  "default_region": "jp"
}
```

**バリデーション:**
- `search_keywords`: 最低1件以上
- `llm_filter_prompt`: 最低10文字以上
- `llm_system_message`: 5文字以上500文字以下
- `llm_temperature`: 0.0 ~ 2.0
- `llm_max_tokens`: 10 ~ 1000
- `default_region`: 最大10文字

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

### 6. Reports（レポート管理）

#### 6.1 レポート一覧取得

```
GET /reports
```

**レスポンス:**
```json
{
  "reports": [
    {
      "id": "report_2025-01-15",
      "start_date": "2025-01-01",
      "end_date": "2025-01-15",
      "generated_at": "2025-01-16T00:00:00",
      "file_path": "/path/to/report.pdf"
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
  "report_id": "report_2025-01-15",
  "file_path": "/path/to/report.pdf"
}
```

---

## 検索設定の優先順位

検索実行時の設定値は以下の優先順位で決定されます：

### キーワード
1. `company_search_settings.custom_keywords` （企業別設定）
2. `global_search_settings.search_keywords` （グローバル設定）
3. YAMLファイルのフォールバック
4. ハードコードされたデフォルト値

### リージョン
1. `company_search_settings.region` （企業別設定）
2. `global_search_settings.default_region` （グローバル設定）
3. YAMLファイルのフォールバック
4. `null`（グローバル検索）

### LLMフィルター設定
- 常に `global_search_settings` の値を使用
- 企業別のカスタマイズは不可

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

### 3. LLMフィルターのチューニング

`llm_temperature` と `llm_max_tokens` は以下の値から開始することを推奨します：

- **厳密なフィルタリング**: `temperature=0.0`, `max_tokens=120`
- **柔軟なフィルタリング**: `temperature=0.3`, `max_tokens=200`

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
console.log(settings.search_keywords);
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
