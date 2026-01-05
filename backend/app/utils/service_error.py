"""サービス層の統一的なエラーハンドリング"""
from typing import Optional, Dict, Any
from enum import Enum


class ErrorCode(str, Enum):
    """エラーコード定義"""
    # HTTP関連
    FETCH_TIMEOUT = "FETCH_TIMEOUT"
    FETCH_FAILED = "FETCH_FAILED"
    HTTP_ERROR = "HTTP_ERROR"

    # LLM関連
    LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_PARSE_ERROR = "LLM_PARSE_ERROR"
    LLM_RESPONSE_ERROR = "LLM_RESPONSE_ERROR"

    # コンテンツ解析関連
    PDF_EXTRACT_ERROR = "PDF_EXTRACT_ERROR"
    HTML_PARSE_ERROR = "HTML_PARSE_ERROR"
    DATE_EXTRACT_ERROR = "DATE_EXTRACT_ERROR"

    # データベース関連
    DB_CONNECTION_ERROR = "DB_CONNECTION_ERROR"
    DB_QUERY_ERROR = "DB_QUERY_ERROR"

    # その他
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class ServiceError(Exception):
    """サービス層の基本例外クラス"""

    def __init__(
        self,
        service_name: str,
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """
        Args:
            service_name: サービス名（例: "ArticleFetcher"）
            error_code: エラーコード
            message: エラーメッセージ
            details: 追加詳細情報
            original_error: 元の例外
        """
        self.service_name = service_name
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.original_error = original_error

        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """エラーメッセージをフォーマット"""
        msg = f"[{self.service_name}] {self.error_code.value}: {self.message}"
        if self.details:
            msg += f" | Details: {self.details}"
        if self.original_error:
            msg += f" | Original: {str(self.original_error)}"
        return msg

    def to_dict(self) -> Dict[str, Any]:
        """エラー情報を辞書に変換（ログ記録用）"""
        return {
            "service_name": self.service_name,
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details,
            "original_error": str(self.original_error) if self.original_error else None,
        }


class RetryableError(ServiceError):
    """リトライ可能なエラー"""
    pass


class NonRetryableError(ServiceError):
    """リトライ不可のエラー"""
    pass
