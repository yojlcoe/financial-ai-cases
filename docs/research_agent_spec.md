# ResearchAgent 仕様書

**最終更新**: 2026-01-12
**バージョン**: 3.0

---

## 目次

1. [概要](#概要)
2. [アーキテクチャ](#アーキテクチャ)
3. [処理フロー](#処理フロー)
4. [AI関連性判定ロジック](#AI関連性判定ロジック)
5. [データフロー](#データフロー)
6. [エラーハンドリング](#エラーハンドリング)
7. [パフォーマンス特性](#パフォーマンス特性)
8. [設定項目](#設定項目)
9. [API仕様](#API仕様)
10. [改善履歴](#改善履歴)

---

## 概要

### 目的

ResearchAgentは、金融機関のAI事例を自動収集・分析するシステムのコアコンポーネントです。複数の情報源（Web検索、プレスリリース）から記事を取得し、LLMを用いてAI関連性を判定、分類、要約を行います。

### 主要機能

1. **多源情報収集**
   - DuckDuckGo Web検索（日本語・英語クエリ）
   - 企業公式プレスリリースの自動スクレイピング

2. **AI関連性フィルタリング**
   - 2段階判定: 本文 → タイトル+スニペット（フォールバック）
   - LLM不可時は判定を保留し、記事処理を継続

3. **記事処理パイプライン**
   - PDF/HTML自動判別・抽出
   - 日付自動抽出（HTML解析 → LLM → 当日フォールバック）
   - カテゴリ分類・要約生成
   - 重複排除（URL正規化 + 既存URLチェック）

4. **ジョブ管理**
   - 非同期バックグラウンド実行
   - 進捗トラッキング（企業数・記事数）
   - エラー時の部分的継続

---

## アーキテクチャ

### システム構成

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer                               │
│  POST /jobs/start, POST /articles/from-url, etc.            │
└────────────────────┬───────────────────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │   ResearchAgent         │
        │  (Orchestrator)         │
        └────────────┬────────────┘
                     │
        ┌────────────┴────────────────────────────┐
        │                                         │
        ▼                                         ▼
┌───────────────┐                       ┌────────────────┐
│ Crawler Layer │                       │  Parser Layer  │
├───────────────┤                       ├────────────────┤
│ - DuckDuckGo  │                       │ - ArticleFetch │
│ - PressScrape │                       │ - PdfExtractor │
└───────┬───────┘                       └────────┬───────┘
        │                                        │
        └────────────────┬───────────────────────┘
                         │
                ┌────────▼──────────┐
                │    LLM Layer      │
                ├───────────────────┤
                │ - Relevance       │
                │ - Classifier      │
                │ - Summarizer      │
                │ - DateExtractor   │
                └────────┬──────────┘
                         │
                ┌────────▼──────────┐
                │  Database Layer   │
                │  (CRUD + Models)  │
                └───────────────────┘
```

### 依存サービス

| サービス | 役割 | ファイル |
|---------|------|---------|
| **DuckDuckGoSearcher** | Web検索実行 | `app/services/crawler/duckduckgo_search.py` |
| **PressScraper** | プレスリリース取得 | `app/services/crawler/press_scraper.py` |
| **ArticleFetcher** | 記事コンテンツ取得（HTML/PDF） | `app/services/parser/article_fetcher.py` |
| **PdfExtractor** | PDF解析 | `app/services/parser/pdf_extractor.py` |
| **AiRelevanceClassifier** | AI関連性判定 | `app/services/llm/relevance.py` |
| **ArticleClassifier** | カテゴリ・タグ分類 | `app/services/llm/classifier.py` |
| **ArticleSummarizer** | 要約生成 | `app/services/llm/summarizer.py` |
| **DateExtractor** | 日付抽出 | `app/services/llm/date_extractor.py` |
| **OllamaClient** | LLM API通信基盤 | `app/services/llm/ollama_client.py` |
| **PromptTemplates** | プロンプト管理 | `app/services/llm/prompt_templates.py` |

---

## 処理フロー

### ジョブ実行フロー全体

```mermaid
graph TD
    A[POST /jobs/start] --> B[run_research_job]
    B --> C[ResearchAgent.run job_id]
    C --> D{スケジュール設定取得}
    D -->|成功| E{アクティブ企業取得}
    D -->|失敗| Z[ジョブ失敗]
    E -->|0件| Z
    E -->|1件以上| F[ジョブ進捗初期化]
    F --> G[FOR EACH 企業]
    G --> H[_process_company]
    H --> I[DuckDuckGo検索]
    H --> J[プレスリリース取得]
    I --> K[_process_items_in_order]
    J --> K
    K --> L[URL正規化・重複排除]
    L --> M[_fetch_and_process_article]
    M --> N{AI関連?}
    N -->|No| O[スキップ]
    N -->|Yes| P[分類・要約]
    P --> Q[DB保存]
    Q --> R[進捗更新]
    R --> G
    G -->|全企業完了| S[ジョブ完了]
```

### _fetch_and_process_article の詳細フロー

```
1. 記事内容取得
   ArticleFetcher.fetch_content(url)
   ├─ HTTP GET
   ├─ Content-Type判定
   ├─ PDF → PdfExtractor.extract_from_bytes()
   └─ HTML → BeautifulSoup解析

2. AI関連性判定（2段階）
   ┌─────────────────────────────────┐
   │ if article_data.content exists: │
   │   ├─ classify_article_content() │ ← 本文ベース（厳密）
   │   │   → False: return None      │
   │   │   → None:  警告のみ継続     │
   │   └─ True: 次へ                 │
   │ else:                           │
   │   ├─ classify_text()            │ ← タイトル+スニペット（軽量）
   │   │   → False: return None      │
   │   │   → None:  警告のみ継続     │
   │   └─ True: 空contentで保存      │
   └─────────────────────────────────┘

3. 日付検証
   published_date 取得優先順位:
   1. article_data.published_date
   2. item.published_date (検索結果)
   3. DateExtractor.extract_date() (LLM)
   4. datetime.now().date() (最終フォールバック)

   日付範囲チェック:
   - source="manual" → 常に保存
   - source="duckduckgo" → 常に保存
   - source="press_list" かつ date_validated=true → 再検証しない
   - その他 → start_date ≤ published_date ≤ end_date

4. LLM処理（逐次実行）
   ├─ summarizer.summarize()
   │   → summary, key_points, outcomes, technology
   │
   └─ classifier.classify()
       → category, business_area, tags, is_inappropriate

5. DB保存
   ArticleCreate → crud_article.create_article()
   content は 5000文字まで切り詰め
```

---

## AI関連性判定ロジック

### 多層フィルタリング・アーキテクチャ (v3.0)

ResearchAgentは **3層のフィルタリング** を採用し、不適切な記事を段階的に除外します:

```
検索結果取得
    │
    ▼
┌────────────────────────────────────┐
│ 1. URLレベルフィルタ（即時除外）    │ ← v3.0 新規追加
│   - リスト記事パターン検出          │
│   - 信頼性の低いソース検出          │
│   - URL正規化・重複チェック         │
└───────────┬────────────────────────┘
            │
            ▼
┌────────────────────────────────────┐
│ 2. AI関連性判定（LLM）             │ ← v3.0 厳格化
│   - 本文ベース判定（優先）          │
│   - タイトル+スニペット判定（FB）   │
│   - 厳格な基準で非AI記事を除外      │
└───────────┬────────────────────────┘
            │
            ▼
┌────────────────────────────────────┐
│ 3. 記事分類・適切性判定（LLM）     │ ← v3.0 4ステップ化
│   - 4ステップ検証プロセス          │
│   - 企業関連性・AI/DX内容チェック   │
│   - カテゴリ・業務領域・タグ付与    │
└───────────┬────────────────────────┘
            │
            ▼
      データベース保存
```

### 1. URLレベルフィルタ (v3.0 新規追加)

**実装箇所:** `_process_items_in_order()` → `_is_list_article_url()`, `_is_unreliable_source()`

#### リスト記事検出

データベース分析（17件のリスト記事）から抽出した実際のパターン:

```python
list_patterns = [
    '/tags/',       # タグ一覧 (https://www.ncblibrary.com/tags/247)
    '/tag/',        # タグページ (https://tech.eu/tag/agentic-ai)
    '/theme/',      # テーマ別一覧 (https://xtech.nikkei.com/theme/ai)
    '/keyword/',    # キーワード一覧 (https://www.yomiuri.co.jp/keyword/135446)
    '/category/',   # カテゴリ一覧 (https://mobiili.fi/category/muut)
    '/corner/',     # コーナー一覧 (https://markezine.jp/article/corner/1164)
    '/case',        # 事例一覧 (https://www.consulting-headwaters.co.jp/case)
    '/events',      # イベント一覧 (https://whatson.cityofsydney.nsw.gov.au/events)
    '/insights',    # インサイト一覧 (https://www.expat.hsbc.com/wealth/insights)
]

# ドメインルート（/ のみ）も検出
if path == "/" or path == "":
    return True
```

**効果:** LLM呼び出し前に記事一覧ページを除外、コスト削減

#### 信頼性の低いソース検出

個人ブログなど信頼性が不明なドメインを除外:

```python
unreliable_domains = [
    'note.com',    # 日本の個人ブログ (実データ10件確認)
    'medium.com',  # 個人ブログ (実データ10件確認)
]
```

**効果:** 信頼性の低い情報源を事前除外

### 2. AI関連性判定（LLM） (v3.0 厳格化)

ResearchAgentは **本文優先・フォールバック型** の2段階判定を採用しています。

#### 段階1: 本文ベース判定（推奨）

```python
if article_data and article_data.get("content"):
    is_ai_related = await ai_classifier.classify_article_content(
        title=article_data.get("title", title),
        content=content
    )
```

- **使用タイミング**: 記事本文の取得に成功した場合
- **精度**: 高（本文の内容を分析）
- **処理時間**: LLMの推論時間に依存
- **プロンプト**: `AI_RELEVANCE_CONTENT_PROMPT` (prompt_templates.py)
- **備考**: 判定時は本文の先頭1000文字を使用

#### 段階2: タイトル+スニペット判定（フォールバック）

```python
else:
    is_ai_related = await ai_classifier.classify_text(
        title=title,
        snippet=snippet
    )
```

- **使用タイミング**: 本文取得失敗時
- **精度**: 中（タイトルとスニペットのみ）
- **処理時間**: LLMの推論時間に依存
- **プロンプト**: `AI_RELEVANCE_TEXT_PROMPT` (prompt_templates.py)

#### 判定結果の処理

| 戻り値 | 意味 | 処理 |
|--------|------|------|
| `True` | AI関連 | 処理継続（分類・要約） |
| `False` | AI関連でない | 記事を破棄（return None） |
| `None` | 判定不可（LLMエラー等） | 警告ログ出力 + 処理継続（保守的） |

#### 判定基準（LLM側） - v3.0 詳細化

**TRUE（AI関連と判定）:**

1. 生成AI技術の実装・活用
   - ChatGPT, Claude, GPT-3/4/o1, LLM, 大規模言語モデル
   - Gemini, Copilot, Bard, Llama, Anthropic
   - RAG, プロンプトエンジニアリング
   - 文章生成, コード生成, 画像生成

2. 機械学習・深層学習の実装
   - ニューラルネットワーク, CNN, RNN, Transformer
   - 教師あり/なし学習, 強化学習
   - モデル訓練, AI推論, MLOps
   - TensorFlow, PyTorch, scikit-learn

3. AI主導の自動化・意思決定
   - AIエージェント, AIアシスタント, 対話型AI
   - AI予測モデル, 異常検知AI, レコメンデーションAI
   - AIによる自動分類, 自動判定, 自動応答

4. 具体的なAI活用領域
   - 画像認識, 物体検出, 顔認識
   - 自然言語処理(NLP), 感情分析, テキストマイニング
   - 音声認識, 音声合成
   - AIチャットボット, 不正検知AI, リスク予測AI

**FALSE（非AI記事）:**

1. DX・デジタル化のみ（AI技術の具体的記載なし）
2. 一般的なIT技術（クラウド, データベース, API等）
3. AI要素のない自動化（ルールベースRPA, マクロ, スクリプト等）
4. 曖昧な「AI」言及のみ（「AI時代」「AI活用を検討」等）
5. その他（IoT, ブロックチェーン, 仮想通貨等でAI要素なし）

### 3. 記事分類・適切性判定（LLM） - v3.0 4ステップ化

**実装箇所:** `ArticleClassifier.classify()`

#### 4ステップ検証プロセス

```
ステップ1: 対象企業の関連性チェック（最優先）
   ├─ 対象企業名が記事本文に明示的に登場するか？
   ├─ 対象企業の具体的な活動・発表・取り組みが主題か？
   └─ NO → is_inappropriate: true（理由: "対象企業への具体的な言及なし"）

ステップ2: AI/DX関連性チェック
   ├─ AI、機械学習、生成AI、LLM、自動化等の具体的技術が実装されているか？
   └─ NO → is_inappropriate: true（理由: "AI/DX技術の具体的な実装なし"）

ステップ3: 記事タイプチェック
   ├─ リスト記事、まとめ記事、一覧ページではないか？
   └─ YES → is_inappropriate: true（理由: "リスト・まとめ記事"）

ステップ4: アクセス・品質チェック
   ├─ 記事本文が取得できているか？
   ├─ 有償サイトやアクセス制限はないか？
   └─ 問題あり → is_inappropriate: true（理由: "本文取得不可/アクセス制限"）

すべてクリア → is_inappropriate: false
```

#### 不適切な記事の判定基準（優先度順）

**a) 企業無関係（最重要）** - 306件 (48.2%)
- 対象企業名が記事本文に1回も出現しない
- 対象企業への言及が脚注や参考程度のみ
- 他の企業の事例のみ
- 業界全体の話題で対象企業が第三者的・客観的にしか登場しない

**b) AI/DX内容なし** - 55件 (8.7%)
- AI、機械学習、生成AI、LLM、自動化、デジタル化などの具体的技術への言及がない
- 単なる「スマート」「デジタル」「IT」のみ
- 一般的なシステム更新やインフラ整備のみ

**c) リスト・まとめ記事** - 17件 (2.7%)
- URLに「list」「ranking」「matome」「summary」が含まれる
- 複数企業の事例を羅列しているだけ
- 記事一覧ページ、ニュースサイトのトップページ

**d) アクセス・信頼性の問題** - 20件 (3.1%)
- 有償会員限定、ペイウォール
- Mediumなどの個人ブログで信頼性が不明
- 404エラー、アクセス不可
- 動画のみで文字コンテンツなし

**e) 重複・既知**
- 明らかに同じ内容の記事

**f) その他の不適切** - 141件 (22.2%)
- 金融業界と無関係な業界の話題
- 求人情報のみ（AI人材の求人は対象）

**データベース分析結果（635件の不適切記事）:**
上記の分布は実データ分析に基づき、各フィルタ層の設計根拠となっています。

---

## データフロー

### 検索結果のデータ構造

#### DuckDuckGo検索結果

```python
{
    "url": "https://example.com/article",
    "title": "記事タイトル",
    "snippet": "記事の概要...",
    "source": "duckduckgo"  # ResearchAgentが付与
}
```

#### プレスリリース結果

```python
{
    "url": "https://company.com/press/2025/01/news.html",
    "title": "プレスリリースタイトル",
    "snippet": "",
    "published_date": date(2025, 1, 15),
    "date_validated": True,  # 日付範囲チェック済み
    "source": "press_list"
}
```

### ArticleFetcher の返り値

```python
{
    "title": "抽出されたタイトル",
    "content": "本文テキスト（最大5000文字）",
    "url": "元のURL",
    "published_date": date(2025, 1, 15) | None
}
```

- **PDF**: `PdfExtractor` でテキスト抽出 + タイトル自動検出
- **HTML**: BeautifulSoupでセレクタベース抽出

### URL正規化ルール

`_normalize_url()` で以下を実施:

1. **追跡パラメータの削除**
   ```
   utm_source, utm_medium, gclid, fbclid, _ga など
   ```

2. **フラグメント削除**
   ```
   https://example.com/article#section1
   → https://example.com/article
   ```

3. **パスの統一**
   ```
   https://example.com/page/
   → https://example.com/page
   ```

4. **大文字小文字の統一**
   ```
   scheme と netloc を小文字化
   ```

---

## エラーハンドリング

### エラーハンドリング方針（v2.0以降）

#### 導入済みのエラーハンドリング機構

1. **ServiceError 階層**
   - `ServiceError`: 基底クラス（service_name, error_code, message, details）
   - `RetryableError`: リトライ可能なエラー
   - `NonRetryableError`: リトライ不可のエラー

2. **ErrorCode 列挙型**
   ```python
   ErrorCode.FETCH_TIMEOUT
   ErrorCode.LLM_UNAVAILABLE
   ErrorCode.PDF_EXTRACT_ERROR
   ```

3. **リトライロジック**
   - `retry_async()` + `RetryConfig` を `ArticleFetcher.fetch_content()` で使用
   - 例外種別に応じて指数バックオフで再試行

#### エラー発生時の挙動

| エラー箇所 | 挙動 | 影響範囲 |
|-----------|------|---------|
| 検索設定取得失敗 | ジョブ全体を失敗 | 全企業 |
| 企業処理エラー | 該当企業をスキップ | 1企業のみ |
| 記事取得エラー | タイトル+スニペット判定にフォールバック | 1記事のみ |
| LLM判定エラー (None) | 警告ログ + 処理継続 | 1記事のみ |
| DB保存エラー | 当該企業の処理を中断し次の企業へ | 1企業のみ |

### ログ出力

現在のログレベル:

- `[INFO]`: 正常フロー（企業処理開始、記事保存成功）
- `[WARN]`: 潜在的問題（LLM判定None、日付抽出失敗）
- `[FILTERED]`: フィルタリング（AI関連でない記事）
- `[ERROR]`: エラー（HTTP失敗、DB保存失敗）
- `[RETRY]`: リトライ実行

---

## パフォーマンス特性

### 処理時間の傾向

- LLM呼び出し（AI関連判定・分類・要約）が支配的
- 要約は本文が短い場合はスキップされる
- 要約 → 分類の順で逐次実行

### レート制限

```python
await asyncio.sleep(3)  # 企業ごと
await asyncio.sleep(1)  # 記事ごと
```

### 最適化の余地

1. **LLM呼び出しの並列化**
   - 現在: 要約・分類は逐次実行
   - 改善: `asyncio.gather()` で並列実行

2. **バッチ処理**
   - 現在: 記事ごとにDB保存
   - 改善: バッチインサート → DB負荷軽減

---

## 設定項目

### ScheduleSetting (DB)

```python
class ScheduleSetting:
    search_start_date: date    # 検索対象の開始日
    search_end_date: date      # 検索対象の終了日
    schedule_type: str         # daily / weekly
    schedule_day: int          # weekly: 0-6, daily: 1-28
    schedule_hour: int         # 0-23
```

### CompanySearchSettings (DB)

```python
class CompanySearchSettings:
    company_id: int
    region: str                # 検索リージョン（例: "jp-jp", "sg-en"）
    custom_keywords: List[str] # カスタムキーワード（ResearchAgentでは未使用）
```

### SearchConfig (app/settings/search_config.py)

```python
class SearchConfig:
    search_keywords: List[str]          # デフォルトキーワード
    default_region: Optional[str]       # デフォルトリージョン

### RegionKeywords (app/utils/region_keywords.py)

```python
def get_keywords_by_region(region: Optional[str]) -> List[str]:
    ...
```
```

---

## API仕様

### POST /jobs/start

**Request:**
```json
{
  "job_type": "manual"
}
```

**Response:**
```json
{
  "job_id": 123,
  "message": "Job started with 10 companies"
}
```

### POST /articles/from-url

手動URL追加（ResearchAgentを部分的に使用）

**Request:**
```json
{
  "company_id": 14,
  "url": "https://example.com/article"
}
```

**Response:**
```json
{
  "job_id": 230,
  "message": "URL addition job started for Sample Bank"
}
```

### POST /articles/from-urls

**Request:**
```json
{
  "company_id": 14,
  "urls": ["https://example.com/article-1", "https://example.com/article-2"]
}
```

**Response:**
```json
{
  "job_id": 231,
  "message": "2 URL(s) addition job started for Sample Bank"
}
```

---

## 改善履歴

### v3.0 (2026-01-12)

**新機能:**
- ✅ **3層フィルタリング・アーキテクチャの実装**
  - URLレベルフィルタ（即時除外）
  - AI関連性判定（LLM、厳格化）
  - 記事分類・適切性判定（LLM、4ステップ化）

- ✅ **URLレベルフィルタ追加** (`_is_list_article_url()`, `_is_unreliable_source()`)
  - リスト記事パターン検出（9パターン: /tags/, /tag/, /theme/, /keyword/, /category/, /corner/, /case, /events, /insights）
  - ドメインルート（/ のみ）検出
  - 信頼性の低いソース検出（note.com, medium.com）
  - LLM呼び出し前に不適切記事を除外 → コスト削減

- ✅ **AI関連性判定の厳格化** (`prompt_templates.py`)
  - TRUE判定基準を4カテゴリに整理（生成AI、機械学習、AI自動化、具体的活用領域）
  - FALSE判定基準を5カテゴリに整理（DX/デジタル化のみ、一般IT、非AI自動化、曖昧なAI言及、その他）
  - 判定方法の3ステップを追加
  - 具体的AI技術名・製品名の明示を要求

- ✅ **記事分類の4ステップ検証プロセス** (`prompt_templates.py`)
  - ステップ1: 対象企業の関連性チェック（最優先）
  - ステップ2: AI/DX関連性チェック
  - ステップ3: 記事タイプチェック
  - ステップ4: アクセス・品質チェック
  - 不適切な記事の判定基準を6カテゴリに優先度付け（a-f）

**データベース分析に基づく改善:**
- 📊 635件の不適切記事を分析し、パターン分布を特定:
  - 企業無関係: 306件 (48.2%)
  - その他: 141件 (22.2%)
  - 理由なし: 63件 (9.9%)
  - AI内容なし: 55件 (8.7%)
  - 調査済・対象外: 33件 (5.2%)
  - アクセス不可: 20件 (3.1%)
  - リスト記事: 17件 (2.7%)

**パフォーマンス:**
- ⚡ LLM呼び出し削減: URLレベルフィルタで事前除外
- ⚡ コスト削減: 不要なAPI呼び出しを回避
- ⚡ 処理時間短縮: 早期除外により全体の処理時間を削減
- ⚡ データ品質向上: 高精度な判定により適切な記事のみを保存

**ドキュメント:**
- 📝 3層フィルタリング・アーキテクチャの詳細図を追加
- 📝 URLレベルフィルタの実装詳細を追加
- 📝 AI関連性判定基準を詳細化（v2.0の2倍以上の詳細度）
- 📝 4ステップ検証プロセスの明記
- 📝 データベース分析結果の追加

### v2.0 (2025-01-05)

**新機能:**
- ✅ 共通ユーティリティクラス追加
  - `DateParser`: 日付解析統一
  - `JSONExtractor`: JSON抽出統一
  - `HTTPClient`: HTTPリクエスト統一
- ✅ エラーハンドリング統一
  - `ServiceError`, `RetryableError`, `NonRetryableError`
  - `ErrorCode` 列挙型
  - `retry_async()`, `@with_retry` デコレータ
- ✅ AI関連性判定の明確化
  - 本文優先・フォールバック型の2段階判定を文書化

**バグ修正:**
- 🐛 PDF抽出後のAI判定が動作しない問題を修正
- 🐛 prompt_templates.py の重複プロンプト削除

**ドキュメント:**
- 📝 本仕様書を新規作成
- 📝 処理フローの詳細図を追加
- 📝 パフォーマンス特性を明記

### v1.0 (2025-12)

**初期リリース:**
- DuckDuckGo + プレスリリース統合
- LLM分類・要約機能
- URL正規化・重複排除

---

## 付録

### 関連ファイルマップ

```
backend/
├── app/
│   ├── api/v1/
│   │   └── jobs.py                        # ジョブAPI
│   ├── services/
│   │   ├── crawler/
│   │   │   ├── research_agent.py          # ★ メインオーケストレーター
│   │   │   ├── duckduckgo_search.py       # Web検索
│   │   │   └── press_scraper.py           # プレスリリース
│   │   ├── parser/
│   │   │   ├── article_fetcher.py         # コンテンツ取得
│   │   │   └── pdf_extractor.py           # PDF解析
│   │   └── llm/
│   │       ├── ollama_client.py           # LLM基盤
│   │       ├── relevance.py               # AI判定
│   │       ├── classifier.py              # 分類
│   │       ├── summarizer.py              # 要約
│   │       ├── date_extractor.py          # 日付抽出
│   │       └── prompt_templates.py        # プロンプト管理
│   ├── utils/                              # ★ v2.0 新規追加
│   │   ├── date_parser.py                 # 日付解析統一
│   │   ├── json_extractor.py              # JSON抽出統一
│   │   ├── http_client.py                 # HTTP統一
│   │   ├── service_error.py               # エラー定義
│   │   └── retry_handler.py               # リトライ機構
│   ├── crud/
│   │   ├── company.py
│   │   ├── article.py
│   │   ├── job.py
│   │   └── schedule_setting.py
│   └── schemas/
│       └── article.py                     # ArticleCreate, ArticleUpdate
└── scripts/
    └── test_mufg_job.py                   # テストスクリプト
```

### 今後の改善予定

1. **パフォーマンス最適化**
   - [ ] LLM呼び出しの並列化（asyncio.gather）
   - [ ] DBバッチ保存
   - [ ] LLM応答のキャッシング

2. **機能追加**
   - [ ] 構造化ログシステム（JSON形式）
   - [ ] 記事の類似度判定（重複記事排除）
   - [ ] 段階的ジョブ再開機能

3. **コード品質**
   - [ ] ユニットテストカバレッジ向上
   - [ ] 型ヒントの完全化
   - [ ] Docstring の充実

---

**Document Version:** 3.0
**Last Updated:** 2026-01-12
**Maintained by:** Development Team
