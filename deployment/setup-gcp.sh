#!/bin/bash
#
# GCP Compute Engine セットアップスクリプト
# 使用方法: sudo bash setup-gcp.sh
#

set -e

echo "======================================"
echo "Case Study Agent - GCP セットアップ"
echo "======================================"

# システム更新
echo "[1/7] システムパッケージを更新中..."
apt-get update
apt-get upgrade -y

# Docker のインストール
echo "[2/7] Docker をインストール中..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
else
    echo "Docker は既にインストールされています"
fi

# Docker Compose のインストール
echo "[3/7] Docker Compose をインストール中..."
if ! command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_VERSION="v2.24.0"
    curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo "Docker Compose は既にインストールされています"
fi

# Git のインストール
echo "[4/7] Git をインストール中..."
apt-get install -y git

# アプリケーションディレクトリの作成
echo "[5/7] アプリケーションディレクトリを作成中..."
APP_DIR="/opt/case-study-agent"
mkdir -p $APP_DIR
cd $APP_DIR

# リポジトリをクローン（既存の場合はプル）
echo "[6/7] リポジトリをクローン/更新中..."
if [ -d ".git" ]; then
    git pull
else
    # TODO: リポジトリURLを実際のURLに置き換えてください
    read -p "GitHub リポジトリの URL を入力してください: " REPO_URL
    git clone $REPO_URL .
fi

# 環境変数ファイルの作成
echo "[7/7] 環境変数ファイルを設定中..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo "⚠️  重要: .env ファイルを編集して、本番環境用の値を設定してください"
    echo "   特に以下の項目を変更する必要があります:"
    echo "   - POSTGRES_PASSWORD (強力なパスワードに変更)"
    echo "   - DATABASE_URL (パスワードを更新)"
    echo ""
    read -p ".env ファイルを今すぐ編集しますか? (y/n): " EDIT_ENV
    if [ "$EDIT_ENV" = "y" ]; then
        nano .env
    fi
fi

# Ollama モデルのダウンロード（初回のみ）
echo ""
echo "======================================"
echo "セットアップ完了！"
echo "======================================"
echo ""
echo "次のステップ:"
echo "1. .env ファイルを編集（まだの場合）: nano .env"
echo "2. アプリケーションを起動: docker-compose -f docker-compose.prod.yml up -d"
echo "3. Ollama モデルをダウンロード: docker-compose -f docker-compose.prod.yml exec ollama ollama pull gemma3:4b"
echo "4. ファイアウォールでポート 8000 を開放"
echo ""
echo "ログの確認: docker-compose -f docker-compose.prod.yml logs -f"
echo ""
