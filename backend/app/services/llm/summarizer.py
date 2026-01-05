from typing import Optional, Dict
from app.services.llm.ollama_client import OllamaClient
from app.services.llm.prompt_templates import PromptTemplates
from app.utils.json_extractor import JSONExtractor


class ArticleSummarizer:
    """記事の要約を生成"""

    def __init__(self):
        self.client = OllamaClient()
        # 中央管理されたシステムプロンプトを使用
        self.system_prompt = PromptTemplates.SUMMARIZER_SYSTEM_PROMPT

    async def summarize(self, title: str, content: str, company_name: str) -> Optional[Dict]:
        """
        記事を要約

        Args:
            title: 記事タイトル
            content: 記事本文
            company_name: 企業名

        Returns:
            {
                "summary": "要約文",
                "key_points": ["ポイント1", "ポイント2"],
                "outcomes": "成果・効果",
                "technology": "使用技術・仕組み"
            }
        """
        if not content or len(content) < 50:
            return None

        # 中央管理されたプロンプトテンプレートを使用
        prompt = PromptTemplates.build_summarizer_user_prompt(
            title=title,
            content=content,
            company_name=company_name
        )

        response = await self.client.generate(
            prompt=prompt,
            system=self.system_prompt,
            temperature=PromptTemplates.SUMMARIZER_TEMPERATURE,
        )
        
        if not response:
            return None

        # JSONをパース
        result = JSONExtractor.extract_object(response)

        if result:
            return result

        # パース失敗時は簡易形式で返す
        print(f"Summarizer JSON parse error: No valid JSON found in response")
        return {
            "summary": response[:500],
            "key_points": [],
            "outcomes": "記載なし",
            "technology": "記載なし",
        }
