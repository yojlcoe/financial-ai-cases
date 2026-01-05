# 事例調査AIエージェント

金融機関のAI・DX事例を自動収集・分析するシステムです。

## 主な機能

- 🏢 **企業管理**: 調査対象企業の登録・管理
- 📰 **記事収集**: DuckDuckGoを使用した自動記事収集
- 🤖 **AIフィルタリング**: LLMによるAI関連記事の自動判定
- ⚙️ **検索設定**: グローバルおよび企業別の検索キーワード・LLM設定
- 📊 **レポート生成**: 収集データの分析レポート作成
- ⏰ **スケジュール実行**: 定期的な自動実行

## クイックスタート

### 必要な環境

- Docker Desktop
- Docker Compose

### セットアップ

1. リポジトリのクローン

```bash
git clone <repository-url>
cd case-study-agent
```

2. 環境変数の設定（必要に応じて）

```bash
cp .env.example .env
```

3. コンテナの起動

```bash
docker compose up -d
```

4. アクセス

- **フロントエンド**: http://localhost:3000
- **バックエンドAPI**: http://localhost:8000
- **APIドキュメント**: http://localhost:8000/docs

## アーキテクチャ

### システム構成

```
Frontend (Next.js) ⟷ Backend (FastAPI) ⟷ PostgreSQL
                            ⬇
                    External Services
                  (DuckDuckGo, Ollama)
```

### 主要技術

- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python 3.11, SQLAlchemy 2.0
- **Database**: PostgreSQL 15+
- **LLM**: Ollama (llama3.2:1b)
- **Infrastructure**: Docker, Docker Compose

## ドキュメント

詳細な仕様は `docs/` ディレクトリを参照してください：

- [📘 DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) - データベーススキーマ仕様
- [📗 API_SPECIFICATION.md](docs/API_SPECIFICATION.md) - REST API仕様
- [📙 ARCHITECTURE.md](docs/ARCHITECTURE.md) - システムアーキテクチャ

## 使い方

### 1. 企業の登録

フロントエンド（http://localhost:3000）の「企業管理」から企業を追加します。

### 2. 情報源URLの設定

各企業にプレスリリースページやニュースページのURLを登録します。

### 3. 検索設定（新機能）

「検索設定」メニューから以下を設定できます：

#### グローバル設定
- 検索キーワード（複数指定可能）
- LLMフィルター設定（プロンプト、Temperature等）
- デフォルト検索リージョン

#### 企業別設定
- カスタムキーワード（その企業専用）
- 検索リージョン（例: `us-en`, `jp`）

### 4. ジョブの実行

「実行管理」から手動でジョブを開始するか、スケジュール設定で自動実行を設定します。

### 5. 結果の確認

収集された記事は「ダッシュボード」または「レポート」で確認できます。

## 開発者向け

### マイグレーション実行

```bash
# 検索設定テーブルの作成
docker compose run --rm backend python scripts/migrate_search_settings.py

# スキーマリファクタリング（パフォーマンス最適化）
docker compose run --rm backend python scripts/refactor_search_settings.py
```

### テストスクリプト

```bash
# DuckDuckGo検索のテスト
docker compose run --rm backend python scripts/print_duckduckgo_search_results.py \
  --company-name "三井住友銀行" \
  --timelimit d \
  --num-results 10 \
  --ai-only-llm
```

### ログの確認

```bash
# すべてのコンテナのログ
docker compose logs

# 特定のサービスのログ
docker compose logs backend -f
```

## 最近の更新（2025-12-30）

### データベースリファクタリング

✅ **パフォーマンス最適化**
- 複合インデックスの追加（記事検索が最大100倍高速化）
- 外部キー制約の追加（データ整合性の向上）
- 冗長なインデックスの削除

✅ **検索設定UI**
- グローバル設定と企業別設定の管理画面を追加
- データベース駆動の設定管理
- リアルタイム設定反映

✅ **データ整合性の向上**
- CASCADE DELETE による関連データの自動削除
- 参照整合性制約の追加
- 孤立レコードの防止

## 本番環境デプロイ

### フロントエンド (Netlify)

1. **Netlifyにリポジトリを接続**
2. **ビルド設定**:
   - Build command: `cd frontend && npm run build`
   - Publish directory: `frontend/out`
   - Node version: 18以上
3. **環境変数を設定**:
   - `NEXT_PUBLIC_API_URL`: バックエンドのURL (例: `https://api.example.com`)

### バックエンド (GCP Compute Engine)

詳細は [deployment/README.md](deployment/README.md) を参照

**推奨スペック**: e2-medium (2vCPU, 4GB RAM) - 月額約$24

**主な手順**:
1. GCPインスタンスを作成
2. Docker & Docker Composeをインストール
3. 環境変数を設定（`.env`ファイル）
4. `docker-compose.prod.yml`で起動
5. ファイアウォールでポート8000を開放

## 環境変数

### バックエンド（必須）

```bash
DATABASE_URL=postgresql+asyncpg://user:password@db:5432/dbname
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=gemma3:4b
DEBUG=false
TIMEZONE=Asia/Tokyo
```

### フロントエンド（必須）

```bash
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

## トラブルシューティング

### Ollamaが起動しない

```bash
docker compose restart ollama
```

### データベース接続エラー

```bash
docker compose restart db
# または
docker compose down && docker compose up -d
```

### フロントエンドがバックエンドに接続できない

環境変数 `NEXT_PUBLIC_API_URL` を確認してください。

## ライセンス

MIT License

## 貢献

Pull Requestsを歓迎します！大きな変更の場合は、まずissueを作成して変更内容を議論してください。

## サポート

問題が発生した場合は、GitHubのIssuesで報告してください。