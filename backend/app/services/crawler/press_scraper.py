import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import date
import asyncio
import re
import json
from urllib.parse import urljoin

from app.services.llm.ollama_client import OllamaClient
from app.services.llm.relevance import AiRelevanceClassifier

class PressScraper:
    """企業の公式プレスリリース一覧をスクレイピング"""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
        }

        # プレスリリース一覧ページのスクレイピング設定
        self.site_configs = {
            "smbc.co.jp": {
                "list_selector": "div.news-list a, ul.news-list a, .newslist a",
                "date_selector": ".date, .news-date, time",
                "date_format": ["%Y年%m月%d日", "%Y.%m.%d", "%Y/%m/%d"],
            },
            "default": {
                "list_selector": "a[href*='news'], a[href*='press'], a[href*='release']",
                "date_selector": ".date, time, .published",
                "date_format": ["%Y-%m-%d", "%Y年%m月%d日", "%Y.%m.%d", "%Y/%m/%d"],
            }
        }
    
    def _get_config(self, url: str) -> Dict:
        """URLに対応する設定を取得"""
        for domain, config in self.site_configs.items():
            if domain in url:
                return config
        return self.site_configs["default"]
    
    async def fetch_press_list(
        self,
        url: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        debug: bool = False,
        use_llm_fallback: bool = False,
        extract_date_with_llm: bool = False,
    ) -> List[Dict]:
        """プレスリリース一覧を取得"""
        config = self._get_config(url)
        results = []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()

                html = self._decode_html(response)
                if debug:
                    print(f"[debug] status={response.status_code} url={response.url}")
                    print("[debug] response head:")
                    print(html[:1000])
                
                soup = BeautifulSoup(html, "lxml")
                
                # リンクを取得
                links = soup.select(config["list_selector"])
                if debug:
                    print(f"[debug] list_selector={config['list_selector']}")
                    print(f"[debug] links_found={len(links)}")

                if not links:
                    # Fallback: collect all anchors and filter by common news patterns
                    candidates = soup.select("a[href]")
                    if debug:
                        print(f"[debug] fallback_candidates={len(candidates)}")
                    links = [
                        a for a in candidates
                        if "/news/" in a.get("href", "")
                        or a.get("href", "").endswith(".pdf")
                    ]
                    if debug:
                        print(f"[debug] fallback_links={len(links)}")
                
                if not links and use_llm_fallback:
                    candidates = self._build_llm_candidates(soup)
                    if debug:
                        print(f"[debug] llm_candidates={len(candidates)}")
                    llm_links = await self._select_links_with_llm(url, candidates, debug=debug)
                    links = llm_links
                
                llm_client = None
                if extract_date_with_llm:
                    llm_client = await self._get_llm_client(debug=debug)

                for link in links[:500]:  # 最大500件
                    href = link.get("href", "") if hasattr(link, "get") else link.get("url", "")
                    if not href:
                        continue
                    
                    # 相対URLを絶対URLに変換
                    full_url = urljoin(url, href)
                    
                    # タイトル取得
                    title = ""
                    if hasattr(link, "get_text"):
                        title = link.get_text(strip=True)
                    if not title and hasattr(link, "get"):
                        title = link.get("title", "").strip()
                    if not title:
                        if hasattr(link, "get"):
                            title = link.get("aria-label", "").strip()
                    if not title:
                        title = full_url

                    extracted_date = self._extract_date_from_link(link, title, full_url)
                    if not extracted_date and extract_date_with_llm and llm_client:
                        extracted_date = await self._extract_date_with_llm(
                            llm_client,
                            link=link,
                            title=title,
                            url=full_url,
                            debug=debug,
                        )

                    if start_date or end_date:
                        if not extracted_date:
                            continue
                        if start_date and extracted_date < start_date:
                            continue
                        if end_date and extracted_date > end_date:
                            continue

                    if title and full_url:
                        results.append({
                            "title": title,
                            "url": full_url,
                            "published_date": extracted_date,
                            "date_validated": bool(start_date or end_date),
                            "source": "press_list",
                        })
                
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"Press list fetch error: {e}")
        
        return results

    def _decode_html(self, response: httpx.Response) -> str:
        """Decode HTML with charset hints from meta tags."""
        content = response.content
        charset = None
        match = re.search(br'charset=["\']?([a-zA-Z0-9_-]+)', content[:1000])
        if match:
            charset = match.group(1).decode("ascii", errors="ignore")
        if not charset:
            charset = response.encoding or "utf-8"
        try:
            return content.decode(charset, errors="replace")
        except LookupError:
            return content.decode("utf-8", errors="replace")

    def _build_llm_candidates(self, soup: BeautifulSoup, limit: int = 200) -> List[Dict]:
        """Collect anchor candidates for LLM filtering."""
        candidates = []
        for anchor in soup.select("a[href]"):
            href = anchor.get("href", "").strip()
            if not href or href.startswith("#") or href.lower().startswith("javascript:"):
                continue

            text = anchor.get_text(" ", strip=True)
            if not text:
                text = anchor.get("aria-label", "").strip()
            if not text:
                text = anchor.get("title", "").strip()
            candidates.append({
                "text": text[:120],
                "href": href,
            })
            if len(candidates) >= limit:
                break
        return candidates

    async def _select_links_with_llm(
        self,
        base_url: str,
        candidates: List[Dict],
        debug: bool = False,
    ) -> List[Dict]:
        """Use LLM to select likely press release links."""
        if not candidates:
            return []

        client = OllamaClient()
        if not await client.is_available():
            if debug:
                print("[debug] Ollama not available; skipping LLM fallback")
            return []

        system = (
            "You extract press release list items. "
            "Return only JSON array, no prose."
        )
        prompt = (
            "From the candidates, select likely press release list entries. "
            "Return a JSON array of objects with 'title' and 'url'. "
            f"Base URL: {base_url}\n"
            f"Candidates:\n{json.dumps(candidates, ensure_ascii=False)}"
        )

        response = await client.generate(prompt=prompt, system=system, temperature=0.1, max_tokens=1200)
        if not response:
            return []

        data = self._parse_json_array(response)
        if not isinstance(data, list):
            return []

        results = []
        for item in data:
            if not isinstance(item, dict):
                continue
            title = (item.get("title") or "").strip()
            url = (item.get("url") or "").strip()
            if not url:
                continue
            results.append({
                "title": title or url,
                "url": url,
            })
        return results

    def _parse_json_array(self, text: str):
        """Extract a JSON array from LLM output."""
        start = text.find("[")
        end = text.rfind("]")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            return None

    async def _get_llm_client(self, debug: bool = False) -> Optional[OllamaClient]:
        """Return an available LLM client."""
        client = OllamaClient()
        if not await client.is_available():
            if debug:
                print("[debug] Ollama not available; skipping LLM features")
            return None
        return client

    async def _extract_date_with_llm(
        self,
        client: OllamaClient,
        link,
        title: str,
        url: str,
        debug: bool = False,
    ) -> Optional[date]:
        """Ask LLM to extract date from nearby HTML text."""
        if hasattr(link, "find_parent"):
            parent = link.find_parent()
            context = parent.get_text(" ", strip=True) if parent else ""
        else:
            context = ""

        payload = {
            "title": title,
            "url": url,
            "context": context[:800],
        }
        system = "You extract published dates from press release list items."
        prompt = (
            "Return JSON only: {\"date\": \"YYYY-MM-DD\"} or {\"date\": null}.\n"
            f"Item: {json.dumps(payload, ensure_ascii=False)}"
        )
        response = await client.generate(prompt=prompt, system=system, temperature=0.0, max_tokens=120)
        if not response:
            return None

        data = AiRelevanceClassifier().parse_json_object(response)
        if isinstance(data, dict):
            value = data.get("date")
            if isinstance(value, str):
                try:
                    return date.fromisoformat(value)
                except ValueError:
                    if debug:
                        print("[debug] LLM date parse failed")
        return None


    def _extract_date_from_text(self, text: str) -> Optional[date]:
        """Extract a date from text if present."""
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

    def _extract_date_from_link(
        self,
        link,
        title: str,
        url: str,
    ) -> Optional[date]:
        """Try to extract a date near the link or from title/url."""
        text_candidates = []

        if hasattr(link, "get_text"):
            parent = link.find_parent()
            if parent:
                text_candidates.append(parent.get_text(" ", strip=True))
            text_candidates.append(link.get_text(" ", strip=True))

        text_candidates.append(title)
        text_candidates.append(url)

        url_date = self._extract_date_from_url(url)
        if url_date:
            return url_date

        for text in text_candidates:
            extracted = self._extract_date_from_text(text)
            if extracted:
                return extracted
        return None

    def _extract_date_from_url(self, url: str) -> Optional[date]:
        """Extract a date from common URL patterns."""
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
