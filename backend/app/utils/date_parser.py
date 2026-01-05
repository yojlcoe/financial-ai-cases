"""統一された日付解析ユーティリティ"""
import re
from datetime import datetime, date
from typing import Optional, List


class DateParser:
    """日付文字列を解析する共通ユーティリティ"""

    # サポートするフォーマット
    FORMATS = [
        "%Y年%m月%d日",
        "%Y.%m.%d",
        "%Y/%m/%d",
        "%Y-%m-%d",
        "%Y%m%d",
    ]

    @classmethod
    def parse(cls, date_text: str, formats: Optional[List[str]] = None) -> Optional[date]:
        """
        日付文字列をdateオブジェクトに変換

        Args:
            date_text: 日付文字列
            formats: カスタムフォーマットリスト（Noneの場合はデフォルト使用）

        Returns:
            dateオブジェクト、または解析失敗時はNone
        """
        if not date_text:
            return None

        # 使用するフォーマット
        parse_formats = formats or cls.FORMATS

        # 数字と日付記号以外を除去
        cleaned = re.sub(r'[^\d年月日/.\-]', '', date_text)

        # フォーマットリストで試行
        for fmt in parse_formats:
            try:
                return datetime.strptime(cleaned, fmt).date()
            except ValueError:
                continue

        # 正規表現で YYYY-MM-DD 形式を抽出
        match = re.search(r'(\d{4})[-/年.](\d{1,2})[-/月.](\d{1,2})', date_text)
        if match:
            try:
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))
                return date(year, month, day)
            except ValueError:
                pass

        return None

    @classmethod
    def extract_from_text(cls, text: str, max_length: int = 500) -> Optional[date]:
        """
        自由文から日付を抽出

        Args:
            text: 検索対象のテキスト
            max_length: 検索する最大文字数

        Returns:
            最初に見つかった日付、または None
        """
        if not text:
            return None

        # 最初の部分だけを検索（パフォーマンス最適化）
        search_text = text[:max_length]

        # パターン1: YYYY年MM月DD日
        match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', search_text)
        if match:
            try:
                return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            except ValueError:
                pass

        # パターン2: YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD
        match = re.search(r'(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})', search_text)
        if match:
            try:
                return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            except ValueError:
                pass

        # パターン3: YYYYMMDD
        match = re.search(r'(\d{8})', search_text)
        if match:
            date_str = match.group(1)
            try:
                return datetime.strptime(date_str, "%Y%m%d").date()
            except ValueError:
                pass

        return None
