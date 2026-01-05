# GCP Compute Engine デプロイガイド

このガイドでは、GCP Compute EngineにCase Study Agentをデプロイする手順を説明します。

## 前提条件

- GCPアカウント
- gcloud CLIのインストール（ローカルマシン）
- SSHキーの設定

## 推奨スペック

**インスタンスタイプ**: e2-medium
- vCPU: 2
- RAM: 4 GB
- ストレージ: 30 GB SSD
- 月額コスト: 約 $24

**より高性能が必要な場合**: e2-standard-2 (4GB RAM) - 月額約$48

## デプロイ手順

### 1. GCPインスタンスの作成

```bash
# gcloud CLIでログイン
gcloud auth login

# プロジェクトを設定
gcloud config set project YOUR_PROJECT_ID

# インスタンスを作成
gcloud compute instances create case-study-agent \
  --zone=asia-northeast1-a \
  --machine-type=e2-medium \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=30GB \
  --boot-disk-type=pd-ssd \
  --tags=http-server,https-server,backend-server
```

### 2. ファイアウォールルールの作成

```bash
# バックエンドAPI用のポート8000を開放
gcloud compute firewall-rules create allow-backend \
  --allow=tcp:8000 \
  --target-tags=backend-server \
  --description="Allow backend API access"
```

### 3. インスタンスにSSH接続

```bash
gcloud compute ssh case-study-agent --zone=asia-northeast1-a
```

### 4. セットアップスクリプトの実行

インスタンスに接続したら:

```bash
# セットアップスクリプトをダウンロード
wget https://raw.githubusercontent.com/YOUR_USERNAME/case-study-agent/main/deployment/setup-gcp.sh

# 実行権限を付与
chmod +x setup-gcp.sh

# スクリプトを実行
sudo bash setup-gcp.sh
```

スクリプトは以下を自動的に実行します:
- システムパッケージの更新
- Docker & Docker Composeのインストール
- Gitのインストール
- アプリケーションのクローン
- 環境変数ファイルの作成

### 5. 環境変数の設定

```bash
cd /opt/case-study-agent
sudo nano .env
```

`.env`ファイルを編集して、本番環境用の値を設定:

```bash
# 強力なパスワードに変更
POSTGRES_USER=casestudy
POSTGRES_PASSWORD=YOUR_SECURE_PASSWORD_HERE
POSTGRES_DB=casestudy

# DATABASE_URLのパスワード部分も更新
DATABASE_URL=postgresql+asyncpg://casestudy:YOUR_SECURE_PASSWORD_HERE@db:5432/casestudy

# Ollama設定
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=gemma3:4b

# アプリケーション設定
DEBUG=false
TIMEZONE=Asia/Tokyo
BACKEND_PORT=8000
```

### 6. アプリケーションの起動

```bash
cd /opt/case-study-agent

# 本番環境用の設定で起動
sudo docker-compose -f docker-compose.prod.yml up -d

# ログを確認
sudo docker-compose -f docker-compose.prod.yml logs -f
```

### 7. Ollamaモデルのダウンロード

```bash
sudo docker-compose -f docker-compose.prod.yml exec ollama ollama pull gemma3:4b
```

これには10-20分程度かかります。

### 8. 動作確認

```bash
# インスタンスの外部IPを確認
gcloud compute instances describe case-study-agent --zone=asia-northeast1-a --format='get(networkInterfaces[0].accessConfigs[0].natIP)'

# ブラウザでアクセス
# http://YOUR_EXTERNAL_IP:8000/health
# http://YOUR_EXTERNAL_IP:8000/docs
```

## Netlifyフロントエンドの設定

1. Netlifyダッシュボードで環境変数を設定:
   - `NEXT_PUBLIC_API_URL`: `http://YOUR_EXTERNAL_IP:8000`

2. 再デプロイしてフロントエンドを更新

## HTTPSの設定（推奨）

本番環境ではHTTPSを使用することを強く推奨します。

### オプション1: Cloudflareを使用（無料）

1. ドメインをCloudflareに追加
2. DNSレコードでGCPインスタンスのIPを指定
3. CloudflareのProxyを有効化（オレンジ色のcloud）
4. SSL/TLSモードを"Full"に設定

### オプション2: Let's Encryptを使用

```bash
# Certbotのインストール
sudo apt-get install certbot

# 証明書の取得
sudo certbot certonly --standalone -d your-domain.com

# Nginxリバースプロキシを設定してHTTPSを有効化
```

## メンテナンス

### アプリケーションの更新

```bash
cd /opt/case-study-agent
sudo git pull
sudo docker-compose -f docker-compose.prod.yml down
sudo docker-compose -f docker-compose.prod.yml up -d --build
```

### ログの確認

```bash
# 全てのサービスのログ
sudo docker-compose -f docker-compose.prod.yml logs -f

# 特定のサービスのログ
sudo docker-compose -f docker-compose.prod.yml logs -f backend
```

### データベースのバックアップ

```bash
# バックアップディレクトリを作成
mkdir -p /opt/backups

# PostgreSQLのバックアップ
sudo docker-compose -f docker-compose.prod.yml exec db pg_dump -U casestudy casestudy > /opt/backups/backup_$(date +%Y%m%d_%H%M%S).sql
```

### リストア

```bash
# バックアップからリストア
cat /opt/backups/backup_YYYYMMDD_HHMMSS.sql | \
  sudo docker-compose -f docker-compose.prod.yml exec -T db psql -U casestudy casestudy
```

## トラブルシューティング

### サービスが起動しない

```bash
# ログを確認
sudo docker-compose -f docker-compose.prod.yml logs

# コンテナの状態を確認
sudo docker-compose -f docker-compose.prod.yml ps

# 再起動
sudo docker-compose -f docker-compose.prod.yml restart
```

### ディスク容量の確認

```bash
df -h
sudo docker system prune -a
```

### メモリ不足

e2-mediumでメモリ不足が発生する場合:
- e2-standard-2 (4GB RAM)にアップグレード
- または不要なサービスを停止

## コスト最適化

### スケジュール停止（開発環境向け）

夜間や週末に停止してコストを削減:

```bash
# インスタンスを停止
gcloud compute instances stop case-study-agent --zone=asia-northeast1-a

# インスタンスを起動
gcloud compute instances start case-study-agent --zone=asia-northeast1-a
```

### プリエンプティブルインスタンス

さらにコストを削減（最大80%オフ）したい場合:

```bash
gcloud compute instances create case-study-agent \
  --preemptible \
  --zone=asia-northeast1-a \
  --machine-type=e2-medium \
  # ... 他のオプション
```

**注意**: プリエンプティブルインスタンスは24時間以内に自動停止される可能性があります。

## セキュリティのベストプラクティス

1. **ファイアウォール**: 必要なポートのみ開放
2. **SSH**: キーベース認証を使用、パスワード認証は無効化
3. **環境変数**: 強力なパスワードを使用
4. **HTTPS**: 本番環境では必須
5. **定期的なアップデート**: セキュリティパッチを適用

## サポート

問題が発生した場合は、GitHubのIssuesで報告してください。
