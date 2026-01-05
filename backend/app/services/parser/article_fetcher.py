from bs4 import BeautifulSoup
from typing import Dict, Optional
from datetime import date
import asyncio
import httpx

from app.services.parser.pdf_extractor import PdfExtractor
from app.utils.http_client import HTTPClient
from app.utils.date_parser import DateParser
from app.utils.retry_handler import retry_async, RetryConfig
from app.utils.service_error import RetryableError, ErrorCode


class ArticleFetcher:
    """記事コンテンツを取得する共通クラス（HTML/PDF両対応）"""

    def __init__(self):
        self.pdf_extractor = PdfExtractor()

        # サイト別のHTML抽出設定
        self.site_configs = {
            "smbc.co.jp": {
                "title_selector": "h1, .news-title, .title",
                "content_selector": "div.news-content, .content, article, main",
                "date_selector": ".date, .news-date, time",
                "date_format": ["%Y年%m月%d日", "%Y.%m.%d", "%Y/%m/%d"],
            },
            "default": {
                "title_selector": "h1, .title, .headline",
                "content_selector": "article, .content, main, .body",
                "date_selector": ".date, time, .published",
                "date_format": ["%Y-%m-%d", "%Y年%m月%d日", "%Y.%m.%d", "%Y/%m/%d"],
            }
        }

    def _get_config(self, url: str) -> Dict:
        """URLに対応する設定を取得"""
        for domain, config in self.site_configs.items():
            if domain in url:
                return config
        return self.site_configs["default"]

    async def fetch_content(self, url: str) -> Optional[Dict]:
        """
        記事の詳細を取得（HTML or PDF）- リトライ機構付き

        Args:
            url: 記事のURL

        Returns:
            記事データ {title, content, url, published_date} または None
        """
        # リトライ設定（最大3回、タイムアウトとコネクションエラーのみ）
        retry_config = RetryConfig(
            max_attempts=3,
            initial_delay=2.0,
            retryable_errors=[httpx.TimeoutException, httpx.ConnectError, RetryableError]
        )

        try:
            return await retry_async(self._fetch_content_internal, retry_config, url)
        except Exception as e:
            print(f"Article fetch error ({url}): {e}")
            return None

    async def _fetch_content_internal(self, url: str) -> Optional[Dict]:
        """内部実装: 記事コンテンツ取得"""
        config = self._get_config(url)

        async with HTTPClient.create_client(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()

            content_type = response.headers.get('content-type', '').lower()

            # PDFの場合（複数の条件でチェック）
            is_pdf = (
                url.lower().endswith('.pdf') or
                'application/pdf' in content_type or
                'pdf' in content_type
            )

            if is_pdf:
                print(f"Detected PDF: {url} (content-type: {content_type})")
                return await self.pdf_extractor.extract_from_bytes(url, response.content)

            # HTMLの場合
            soup = BeautifulSoup(response.text, "lxml")

            # タイトル
            title_elem = soup.select_one(config["title_selector"])
            title = title_elem.get_text(strip=True) if title_elem else ""

            # 本文
            content_elem = soup.select_one(config["content_selector"])
            content = ""
            if content_elem:
                # スクリプトとスタイルを除去
                for tag in content_elem.select("script, style, nav, footer, header"):
                    tag.decompose()
                content = content_elem.get_text(separator="\n", strip=True)

            # 日付
            published_date = None
            date_elem = soup.select_one(config["date_selector"])
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                published_date = DateParser.parse(date_text, config["date_format"])

            await asyncio.sleep(1)

            return {
                "title": title,
                "content": content[:5000],  # 最大5000文字
                "url": url,
                "published_date": published_date,
            }
