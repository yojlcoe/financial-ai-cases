from typing import Optional, Dict, List
from app.services.llm.ollama_client import OllamaClient
from app.services.llm.prompt_templates import PromptTemplates
from app.utils.json_extractor import JSONExtractor


class ArticleClassifier:
    """記事のカテゴリ・タグ分類"""

    def __init__(self):
        self.client = OllamaClient()

        # 中央管理されたカテゴリと業務領域を使用
        self.categories = PromptTemplates.CATEGORIES
        self.business_areas = PromptTemplates.BUSINESS_AREAS
        self.system_prompt = PromptTemplates.CLASSIFIER_SYSTEM_PROMPT

    async def classify(self, title: str, content: str, summary: str = "", company_name: str = "") -> Optional[Dict]:
        """
        記事を分類

        Args:
            title: 記事タイトル
            content: 記事本文
            summary: 要約（あれば）
            company_name: 企業名（関連性チェック用）

        Returns:
            {
                "is_inappropriate": bool,  # 金融業界と無関係または内容不明な記事の場合True
                "category": "カテゴリ",
                "business_area": "業務領域",
                "tags": ["タグ1", "タグ2"]
            }
        """
        text_to_analyze = f"{title}\n{summary}\n{content[:1500]}"

        # 中央管理されたプロンプトテンプレートを使用
        prompt = PromptTemplates.build_classifier_user_prompt(
            text=text_to_analyze,
            company_name=company_name
        )

        response = await self.client.generate(
            prompt=prompt,
            system=self.system_prompt,
            temperature=PromptTemplates.CLASSIFIER_TEMPERATURE,
        )
        
        if not response:
            return self._default_classification()
        
        # JSONをパース
        result = JSONExtractor.extract_object(response)

        if result:
            # カテゴリの検証
            if result.get("category") not in self.categories:
                result["category"] = "その他"
            if result.get("business_area") not in self.business_areas:
                result["business_area"] = "その他"
            return result

        print(f"Classification JSON parse error: No valid JSON found in response")
        return self._default_classification()
    
    def _default_classification(self) -> Dict:
        """デフォルト分類"""
        return {
            "is_inappropriate": False,
            "category": "その他",
            "business_area": "その他",
            "tags": [],
        }
