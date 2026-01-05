"""LLMレスポンスからJSONを抽出する共通ユーティリティ"""
import json
from typing import Optional, Dict, List, Any


class JSONExtractor:
    """LLMの出力からJSONオブジェクト/配列を抽出"""

    @staticmethod
    def extract_object(text: str) -> Optional[Dict[str, Any]]:
        """
        テキストからJSONオブジェクトを抽出

        Args:
            text: LLMレスポンステキスト

        Returns:
            抽出されたdict、または失敗時はNone
        """
        if not text:
            return None

        # 最初の { から最後の } までを抽出
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1 or end <= start:
            return None

        try:
            json_str = text[start:end + 1]
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def extract_array(text: str) -> Optional[List[Any]]:
        """
        テキストからJSON配列を抽出

        Args:
            text: LLMレスポンステキスト

        Returns:
            抽出されたlist、または失敗時はNone
        """
        if not text:
            return None

        # 最初の [ から最後の ] までを抽出
        start = text.find("[")
        end = text.rfind("]")

        if start == -1 or end == -1 or end <= start:
            return None

        try:
            json_str = text[start:end + 1]
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def extract_value(data: Optional[Dict], key: str, default: Any = None) -> Any:
        """
        辞書から安全に値を取得

        Args:
            data: 対象の辞書
            key: キー
            default: デフォルト値

        Returns:
            取得した値、または default
        """
        if not data or not isinstance(data, dict):
            return default
        return data.get(key, default)
