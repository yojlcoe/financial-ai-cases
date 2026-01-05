import asyncio
from datetime import date
from typing import Dict, List, Optional

from ddgs import DDGS
from app.services.llm.relevance import AiRelevanceClassifier
from app.settings.search_config import SearchConfig


class DuckDuckGoSearcher:
    """DuckDuckGo Search APIを使った検索クラス"""

    def __init__(self, config: Optional[SearchConfig] = None):
        """
        Initialize DuckDuckGo searcher.

        Args:
            config: SearchConfig instance. If None, loads default config.
        """
        self._config = config or SearchConfig()
    
    async def search(
        self,
        query: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        num_results: int = 10,
        gl: Optional[str] = None,
        timelimit_override: Optional[str] = None,
        debug: bool = False,
    ) -> List[Dict]:
        """
        DuckDuckGo検索を実行

        Args:
            query: 検索クエリ
            start_date: 検索開始日
            end_date: 検索終了日
            num_results: 取得件数
            gl: リージョン指定 (sg-en形式で指定)

        Returns:
            検索結果のリスト [{title, url, snippet}, ...]
        """
        if timelimit_override:
            timelimit = timelimit_override
        else:
            timelimit = self._calculate_timelimit(start_date, end_date)

        # glパラメータをそのまま使用（sg-en, jp-jp等の形式）
        region = gl if gl else "wt-wt"

        def _run_search() -> List[Dict]:
            with DDGS() as ddgs:
                return list(
                    ddgs.text(
                        query=query,
                        region=region,
                        safesearch="off",
                        timelimit=timelimit,
                        max_results=num_results,
                    )
                )

        def _run_search_no_timelimit() -> List[Dict]:
            with DDGS() as ddgs:
                return list(
                    ddgs.text(
                        query=query,
                        region=region,
                        safesearch="off",
                        timelimit=None,
                        max_results=num_results,
                    )
                )

        results = []

        try:
            items = await asyncio.to_thread(_run_search)
            if debug:
                print(f"[debug] region={region} timelimit={timelimit} query={query}")
                print(f"[debug] results={len(items)}")
            for item in items:
                title = item.get("title") or ""
                url = item.get("href") or ""
                snippet = item.get("body") or ""
                if title and url:
                    results.append({
                        "title": title,
                        "url": url,
                        "snippet": snippet,
                    })
        except Exception as e:
            if timelimit:
                try:
                    if debug:
                        print(f"[debug] timelimit failed ({e}), retrying without timelimit")
                    items = await asyncio.to_thread(_run_search_no_timelimit)
                    for item in items:
                        title = item.get("title") or ""
                        url = item.get("href") or ""
                        snippet = item.get("body") or ""
                        if title and url:
                            results.append({
                                "title": title,
                                "url": url,
                                "snippet": snippet,
                            })
                except Exception as inner:
                    print(f"DuckDuckGo search error: {inner}")
            else:
                print(f"DuckDuckGo search error: {e}")

        await asyncio.sleep(1)
        return results

    async def search_ai_related(
        self,
        query: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        num_results: int = 10,
        gl: Optional[str] = None,
        timelimit_override: Optional[str] = None,
        debug: bool = False,
    ) -> List[Dict]:
        """Search and filter results with LLM AI/DX relevance check."""
        results = await self.search(
            query,
            start_date,
            end_date,
            num_results=num_results,
            gl=gl,
            timelimit_override=timelimit_override,
            debug=debug,
        )
        return await self._filter_with_llm(results, debug=debug)
    
    def build_company_query(self, company_name: str, keywords: List[str] = None) -> str:
        """企業名と検索キーワードからクエリを構築"""
        if keywords is None:
            # Use keywords from config
            keywords = self._config.search_keywords

        keyword_str = " OR ".join(keywords)
        return f'"{company_name}" ({keyword_str})'

    async def _filter_with_llm(self, results: List[Dict], debug: bool = False) -> List[Dict]:
        if not results:
            return results

        # Check if LLM filtering is enabled in config
        if not self._config.llm_filter_enabled:
            if debug:
                print("[debug] LLM filtering is disabled in config")
            return results

        classifier = AiRelevanceClassifier(config=self._config)
        if not await classifier.is_available():
            if debug:
                print("[debug] Ollama not available; skipping LLM AI filter")
            return results

        filtered = []
        for item in results:
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            if not title and not snippet:
                continue
            result = await classifier.classify_text(title=title, snippet=snippet)
            if result is True:
                filtered.append(item)
        return filtered

    def _calculate_timelimit(
        self,
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> Optional[str]:
        """
        ddgsのtimelimitは d/w/m のみを受け付ける。
        指定期間が直近の場合だけ近似的に適用する。
        """
        if not start_date or not end_date:
            return None

        if end_date < start_date:
            return None

        span_days = (end_date - start_date).days
        if span_days <= 1:
            return "d"
        if span_days <= 7:
            return "w"
        if span_days <= 31:
            return "m"
        if span_days <= 366:
            return "y"
        return None
