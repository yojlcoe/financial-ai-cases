"""リトライロジックのユーティリティ"""
import asyncio
from typing import TypeVar, Callable, Optional, List, Type
from functools import wraps

from app.utils.service_error import RetryableError, NonRetryableError, ServiceError

T = TypeVar('T')


class RetryConfig:
    """リトライ設定"""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 10.0,
        exponential_base: float = 2.0,
        retryable_errors: Optional[List[Type[Exception]]] = None
    ):
        """
        Args:
            max_attempts: 最大試行回数
            initial_delay: 初回待機時間（秒）
            max_delay: 最大待機時間（秒）
            exponential_base: 指数バックオフの基数
            retryable_errors: リトライ対象の例外クラスリスト
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_errors = retryable_errors or [RetryableError, TimeoutError, ConnectionError]


async def retry_async(
    func: Callable[..., T],
    config: Optional[RetryConfig] = None,
    *args,
    **kwargs
) -> T:
    """
    非同期関数をリトライ実行

    Args:
        func: 実行する非同期関数
        config: リトライ設定（Noneの場合はデフォルト）
        *args: 関数の位置引数
        **kwargs: 関数のキーワード引数

    Returns:
        関数の戻り値

    Raises:
        最後の試行で発生した例外
    """
    if config is None:
        config = RetryConfig()

    last_error = None

    for attempt in range(config.max_attempts):
        try:
            return await func(*args, **kwargs)
        except NonRetryableError:
            # リトライ不可のエラーは即座に再スロー
            raise
        except tuple(config.retryable_errors) as e:
            last_error = e
            if attempt < config.max_attempts - 1:
                # 指数バックオフで待機
                delay = min(
                    config.initial_delay * (config.exponential_base ** attempt),
                    config.max_delay
                )
                print(f"[RETRY] Attempt {attempt + 1}/{config.max_attempts} failed: {e}. Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
            else:
                # 最後の試行
                print(f"[RETRY] All {config.max_attempts} attempts failed")
        except Exception as e:
            # 予期しないエラー
            print(f"[ERROR] Unexpected error (not retryable): {e}")
            raise

    # すべての試行が失敗
    if last_error:
        raise last_error
    raise ServiceError(
        service_name="RetryHandler",
        error_code="UNKNOWN_ERROR",
        message="All retry attempts exhausted without success"
    )


def with_retry(config: Optional[RetryConfig] = None):
    """
    非同期関数にリトライ機能を追加するデコレータ

    Usage:
        @with_retry(RetryConfig(max_attempts=5))
        async def fetch_data():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_async(func, config, *args, **kwargs)
        return wrapper
    return decorator
