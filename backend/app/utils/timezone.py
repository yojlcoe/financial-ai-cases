from datetime import datetime
from zoneinfo import ZoneInfo
from app.config import get_settings


def get_jst_now() -> datetime:
    """現在のJST時刻を取得"""
    settings = get_settings()
    tz = ZoneInfo(settings.timezone)
    # UTCの現在時刻を取得してJSTに変換
    utc_now = datetime.now(ZoneInfo("UTC"))
    return utc_now.astimezone(tz)


def utc_to_jst(dt: datetime) -> datetime:
    """UTC時刻をJST時刻に変換"""
    settings = get_settings()
    tz = ZoneInfo(settings.timezone)
    if dt.tzinfo is None:
        # タイムゾーン情報がない場合はUTCと仮定
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(tz)


def jst_to_utc(dt: datetime) -> datetime:
    """JST時刻をUTC時刻に変換"""
    if dt.tzinfo is None:
        # タイムゾーン情報がない場合はJSTと仮定
        settings = get_settings()
        tz = ZoneInfo(settings.timezone)
        dt = dt.replace(tzinfo=tz)
    return dt.astimezone(ZoneInfo("UTC"))