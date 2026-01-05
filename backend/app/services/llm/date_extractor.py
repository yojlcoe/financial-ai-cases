from typing import Optional
from datetime import date
import json
import re

from app.services.llm.ollama_client import OllamaClient
from app.services.llm.relevance import AiRelevanceClassifier


class DateExtractor:
    """LLMを使って記事から日付を抽出"""

    def __init__(self):
        self.client = OllamaClient()
        self.system_prompt = "You extract published dates from article text."

    async def extract_date(
        self,
        title: str,
        snippet: str = "",
        url: str = "",
        content: str = "",
    ) -> Optional[date]:
        """
        タイトル・スニペット・URL・コンテンツから公開日を抽出

        Args:
            title: 記事タイトル
            snippet: スニペット（検索結果の抜粋など）
            url: 記事URL
            content: 記事本文（最初の部分）

        Returns:
            date object or None
        """
        # まず正規表現で試す（高速）
        for text in [snippet, title, url, content[:200]]:
            extracted = self._extract_date_from_text(text)
            if extracted:
                return extracted

        # LLMで抽出を試みる
        if not await self._is_llm_available():
            return None

        payload = {
            "title": title,
            "snippet": snippet,
            "url": url,
            "content": content[:500],
        }
        prompt = (
            "Return JSON only: {\"date\": \"YYYY-MM-DD\"} or {\"date\": null}.\n"
            f"Article: {json.dumps(payload, ensure_ascii=False)}"
        )

        response = await self.client.generate(
            prompt=prompt,
            system=self.system_prompt,
            temperature=0.0,
            max_tokens=120,
        )

        if not response:
            return None

        data = AiRelevanceClassifier().parse_json_object(response)
        if isinstance(data, dict):
            value = data.get("date")
            if isinstance(value, str):
                try:
                    return date.fromisoformat(value)
                except ValueError:
                    pass

        return None

    def _extract_date_from_text(self, text: str) -> Optional[date]:
        """正規表現でテキストから日付を抽出"""
        if not text:
            return None

        patterns = [
            r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})",
            r"(\d{4})年(\d{1,2})月(\d{1,2})日",
            r"(\d{4})\.(\d{1,2})\.(\d{1,2})",
            r"(\d{4})(\d{2})(\d{2})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if not match:
                continue
            try:
                return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            except ValueError:
                continue
        return None

    async def _is_llm_available(self) -> bool:
        """Ollamaが利用可能かチェック"""
        try:
            return await self.client.is_available()
        except Exception:
            return False
