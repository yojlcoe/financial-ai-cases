from typing import Optional

from app.services.llm.ollama_client import OllamaClient
from app.services.llm.prompt_templates import PromptTemplates
from app.settings.search_config import SearchConfig
from app.utils.json_extractor import JSONExtractor


class AiRelevanceClassifier:
    """LLMでAI/DX関連か判定するクラス。"""

    def __init__(self, config: Optional[SearchConfig] = None) -> None:
        self._client = OllamaClient()
        self._available: Optional[bool] = None
        self._config = config or SearchConfig()

    async def is_available(self) -> bool:
        if self._available is None:
            self._available = await self._client.is_available()
        return self._available

    async def classify_text(self, title: str, snippet: str = "") -> Optional[bool]:
        """タイトル/スニペットからAI関連か判定."""
        if not await self.is_available():
            return None

        # Always use prompt templates
        prompt = PromptTemplates.build_ai_relevance_text_prompt(
            title=title,
            snippet=snippet
        )

        response = await self._client.generate(
            prompt=prompt,
            system=PromptTemplates.AI_RELEVANCE_SYSTEM_PROMPT,
            temperature=PromptTemplates.AI_RELEVANCE_TEMPERATURE,
            max_tokens=200,
        )
        return self._extract_ai_flag(response)

    async def classify_article_content(
        self,
        title: str,
        content: str,
        debug: bool = False,
    ) -> Optional[bool]:
        """
        記事本文からAI関連性を詳細に判定（より厳密なフィルター）

        Args:
            title: 記事タイトル
            content: 記事本文（最初の1000文字程度を推奨）
            debug: デバッグログを出力するか

        Returns:
            True: AI関連, False: AI関連でない, None: 判定不可
        """
        if not await self.is_available():
            if debug:
                print("[DEBUG] Ollama not available for article content classification")
            return None

        # 本文は最初の1000文字まで使用
        content_preview = content[:1000] if content else ""

        # プロンプトテンプレートから生成
        prompt = PromptTemplates.build_ai_relevance_content_prompt(
            title=title,
            content_preview=content_preview
        )

        response = await self._client.generate(
            prompt=prompt,
            system=PromptTemplates.AI_RELEVANCE_SYSTEM_PROMPT,
            temperature=PromptTemplates.AI_RELEVANCE_TEMPERATURE,
            max_tokens=200,
        )

        if debug:
            print(f"[DEBUG] Article classification response: {response}")

        result = self._extract_ai_flag(response)

        if debug:
            print(f"[DEBUG] Article AI-related: {result}")
            # 理由も抽出して表示
            try:
                data = self.parse_json_object(response)
                if data and "reason" in data:
                    print(f"[DEBUG] Reason: {data['reason']}")
            except Exception:
                pass

        return result

    def _extract_ai_flag(self, response: Optional[str]) -> Optional[bool]:
        """LLMレスポンスからAI関連フラグを抽出"""
        data = JSONExtractor.extract_object(response)
        if data and isinstance(data.get("ai_related"), bool):
            return data["ai_related"]
        return None

    def parse_json_object(self, text: str):
        """Extract a JSON object from LLM output."""
        return JSONExtractor.extract_object(text)
