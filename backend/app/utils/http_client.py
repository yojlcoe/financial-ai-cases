"""共通HTTPクライアントユーティリティ"""
import httpx
from typing import Dict, Optional


class HTTPClient:
    """HTTPリクエストの共通設定と実行"""

    # 共通User-Agent
    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    # 共通ヘッダー
    DEFAULT_HEADERS = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
    }

    @classmethod
    def get_headers(cls, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        HTTPヘッダーを取得

        Args:
            additional_headers: 追加ヘッダー

        Returns:
            マージされたヘッダー辞書
        """
        headers = cls.DEFAULT_HEADERS.copy()
        if additional_headers:
            headers.update(additional_headers)
        return headers

    @classmethod
    def create_client(
        cls,
        timeout: float = 30.0,
        follow_redirects: bool = True,
        additional_headers: Optional[Dict[str, str]] = None
    ) -> httpx.AsyncClient:
        """
        AsyncClientを作成

        Args:
            timeout: タイムアウト秒数
            follow_redirects: リダイレクトを追跡するか
            additional_headers: 追加ヘッダー

        Returns:
            設定済みのAsyncClient
        """
        return httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=follow_redirects,
            headers=cls.get_headers(additional_headers)
        )
