import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

def setup_logging():
    """
    アプリケーション全体のロギング設定
    - 標準出力とファイルの両方に出力
    - ファイルはローテーション（最大100MB、10ファイル保持）
    """
    # ログディレクトリの作成
    log_dir = Path("/app/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # ルートロガーの設定
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # 既存のハンドラをクリア
    root_logger.handlers.clear()

    # フォーマット設定
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 標準出力ハンドラ
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # ファイルハンドラ（ローテーション）
    file_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=100 * 1024 * 1024,  # 100MB
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # ジョブ専用のログファイル
    job_handler = RotatingFileHandler(
        log_dir / "jobs.log",
        maxBytes=100 * 1024 * 1024,  # 100MB
        backupCount=10,
        encoding='utf-8'
    )
    job_handler.setLevel(logging.INFO)
    job_handler.setFormatter(formatter)

    # ジョブロガーの設定
    job_logger = logging.getLogger("app.services.crawler")
    job_logger.addHandler(job_handler)
    job_logger.setLevel(logging.INFO)

    logging.info("Logging configured: console + file (/app/logs/)")
