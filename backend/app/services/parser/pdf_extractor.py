import io
from typing import Optional, Dict
from datetime import date
import re

try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class PdfExtractor:
    """PDFからテキストを抽出する共通クラス"""

    @staticmethod
    def is_available() -> bool:
        """PyPDF2が利用可能かチェック"""
        return PDF_AVAILABLE

    async def extract_from_bytes(self, url: str, pdf_bytes: bytes) -> Optional[Dict]:
        """
        PDFバイトデータからテキストを抽出

        Args:
            url: PDF URL（ログとメタデータ用）
            pdf_bytes: PDFのバイトデータ

        Returns:
            抽出結果 {title, content, url, published_date} または None
        """
        if not PDF_AVAILABLE:
            error_msg = f"PyPDF2 not available, cannot read PDF: {url}"
            print(f"[ERROR] {error_msg}")
            print("[INFO] Install PyPDF2 with: pip install PyPDF2")
            return None

        if not pdf_bytes:
            print(f"[ERROR] Empty PDF bytes for URL: {url}")
            return None

        try:
            # PDFを読み込み
            pdf_file = io.BytesIO(pdf_bytes)
            reader = PdfReader(pdf_file)

            # PDFページ数をログ
            num_pages = len(reader.pages)
            print(f"[INFO] PDF has {num_pages} pages: {url}")

            # 全ページのテキストを抽出
            text_content = []
            for i, page in enumerate(reader.pages):
                try:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
                except Exception as page_error:
                    print(f"[WARN] Failed to extract text from page {i+1}: {page_error}")

            full_text = "\n".join(text_content)

            if not full_text.strip():
                print(f"[WARN] No text extracted from PDF (might be image-based): {url}")
                # 画像ベースのPDFの場合でも基本情報は返す
                full_text = f"[PDF content could not be extracted - may be image-based PDF]\nURL: {url}"

            # タイトルを推測（最初の行または PDFメタデータから）
            title = ""
            if reader.metadata and reader.metadata.title:
                title = reader.metadata.title
            elif full_text:
                # 最初の非空白行をタイトルとする
                lines = [line.strip() for line in full_text.split('\n') if line.strip()]
                if lines:
                    title = lines[0][:200]  # 最大200文字

            if not title:
                title = f"PDF Document - {url.split('/')[-1]}"

            # URLから日付を抽出を試みる
            published_date = self._extract_date_from_url(url)

            print(f"[SUCCESS] PDF extracted: {len(full_text)} characters, title: {title[:50]}...")

            return {
                "title": title,
                "content": full_text[:10000],  # PDFは最大10000文字
                "url": url,
                "published_date": published_date,
            }

        except Exception as e:
            import traceback
            print(f"[ERROR] PDF extraction error ({url}): {e}")
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            return None

    def _extract_date_from_url(self, url: str) -> Optional[date]:
        """URLから日付を抽出"""
        if not url:
            return None

        # Pattern: /newsYYYY/.../newsMMDD(.pdf)
        match = re.search(r"/news(20\d{2})/.+?/news(\d{4})", url)
        if match:
            year = int(match.group(1))
            month = int(match.group(2)[:2])
            day = int(match.group(2)[2:])
            try:
                return date(year, month, day)
            except ValueError:
                return None

        # Pattern: YYYYMMDD in URL
        return self._extract_date_from_text(url)

    def _extract_date_from_text(self, text: str) -> Optional[date]:
        """テキストから日付を抽出"""
        if not text:
            return None

        patterns = [
            r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})",
            r"(\d{4})年(\d{1,2})月(\d{1,2})日",
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
