import asyncio
import logging
from datetime import date
from typing import List, Dict, Optional
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models import Company, Article
from app.crud import company as crud_company
from app.crud import article as crud_article
from app.crud import job as crud_job
from app.crud import schedule_setting as crud_schedule_setting
from app.services.crawler.duckduckgo_search import DuckDuckGoSearcher
from app.services.crawler.press_scraper import PressScraper
from app.services.parser.article_fetcher import ArticleFetcher
from app.services.llm.summarizer import ArticleSummarizer
from app.services.llm.classifier import ArticleClassifier
from app.services.llm.date_extractor import DateExtractor
from app.services.llm.relevance import AiRelevanceClassifier
from app.utils.region_keywords import get_keywords_by_region

logger = logging.getLogger(__name__)


class ResearchAgent:
    """事例調査AIエージェント"""

    # タイムアウト設定（秒）
    FETCH_TIMEOUT = 300  # 記事取得のタイムアウト（5分）
    LLM_TIMEOUT = 300    # LLM処理のタイムアウト（5分）

    def __init__(self):
        self.ddg_searcher = DuckDuckGoSearcher()
        self.press_scraper = PressScraper()
        self.article_fetcher = ArticleFetcher()
        self.summarizer = ArticleSummarizer()
        self.classifier = ArticleClassifier()
        self.date_extractor = DateExtractor()
        self.ai_classifier = AiRelevanceClassifier()
    
    async def run(self, job_id: int) -> None:
        """
        調査ジョブを実行
        
        Args:
            job_id: ジョブID
        """
        async with AsyncSessionLocal() as db:
            try:
                # 検索設定を取得
                setting = await crud_schedule_setting.get_schedule_setting(db)
                if not setting:
                    await crud_job.complete_job(db, job_id, "failed", "検索設定が見つかりません")
                    return
                
                start_date = setting.search_start_date
                end_date = setting.search_end_date
                
                # アクティブな企業を取得
                companies, total = await crud_company.get_companies(db, is_active=True)
                
                if total == 0:
                    await crud_job.complete_job(db, job_id, "failed", "対象企業がありません")
                    return
                
                # ジョブの総企業数を更新
                await crud_job.update_job_progress(db, job_id, 0, 0)
                
                total_articles = 0
                
                # 企業ごとに順番に処理
                for i, company in enumerate(companies):
                    logger.info(f"Processing {i+1}/{total}: {company.name}")

                    try:
                        # 企業処理を実行（タイムアウトなし）
                        # job_id, company_index, current_total_articlesを渡す
                        articles = await self._process_company(
                            db, company, start_date, end_date, job_id, i + 1, total_articles
                        )
                        total_articles += len(articles)

                        # 企業処理完了後に進捗更新
                        await crud_job.update_job_progress(
                            db, job_id, i + 1, total_articles
                        )

                    except Exception as e:
                        logger.info(f"Error processing {company.name}: {e}")
                        # エラーが発生しても続行
                        await crud_job.update_job_progress(
                            db, job_id, i + 1, total_articles
                        )
                        continue

                    # レート制限対策
                    await asyncio.sleep(3)
                
                # ジョブ完了
                await crud_job.complete_job(db, job_id, "completed")
                logger.info(f"Job completed: {total_articles} articles processed")
                
            except Exception as e:
                logger.info(f"Job failed: {e}")
                await crud_job.complete_job(db, job_id, "failed", str(e))
    
    async def _process_company(
        self,
        db: AsyncSession,
        company: Company,
        start_date: date,
        end_date: date,
        job_id: int,
        company_index: int,
        base_article_count: int,
    ) -> List[Article]:
        """
        1企業の調査を実行

        Args:
            db: DBセッション
            company: 企業
            start_date: 検索開始日
            end_date: 検索終了日
            job_id: ジョブID
            company_index: 現在の企業インデックス（1-based）
            base_article_count: この企業処理開始時点の記事数

        Returns:
            取得した記事リスト
        """
        articles = []

        # 1. DuckDuckGo検索
        logger.info(f"[STEP] Starting DuckDuckGo search for {company.name}")
        search_results = await self._search_duckduckgo(company, start_date, end_date)
        logger.info(f"[STEP] DuckDuckGo search completed for {company.name}, processing {len(search_results)} items")
        articles.extend(
            await self._process_items_in_order(
                db, company, search_results, start_date, end_date, job_id, company_index, base_article_count
            )
        )
        logger.info(f"[STEP] DuckDuckGo items processed for {company.name}, {len(articles)} articles saved")

        # 2. 公式プレスリリース
        logger.info(f"[STEP] Starting press release fetch for {company.name}")
        press_results = await self._fetch_press_releases(company, start_date, end_date)
        logger.info(f"[STEP] Press release fetch completed for {company.name}, processing {len(press_results)} items")
        press_articles = await self._process_items_in_order(
            db, company, press_results, start_date, end_date, job_id, company_index, base_article_count + len(articles)
        )
        articles.extend(press_articles)
        logger.info(f"[STEP] Press items processed for {company.name}, {len(press_articles)} articles saved")

        logger.info(f"[STEP] Company {company.name} processing completed, total {len(articles)} articles")
        return articles

    async def _process_items_in_order(
        self,
        db: AsyncSession,
        company: Company,
        items: List[Dict],
        start_date: date,
        end_date: date,
        job_id: int,
        company_index: int,
        base_article_count: int,
    ) -> List[Article]:
        """Process items in the given order, de-duplicating by normalized URL."""
        collected = []
        seen = set()

        for idx, item in enumerate(items, 1):
            raw_url = item.get("url", "")
            title = item.get("title", "")
            logger.info(f"[ITEM {idx}/{len(items)}] Processing: {title[:50]}...")

            normalized_url = self._normalize_url(raw_url)
            if not normalized_url:
                logger.info(f"[ITEM {idx}/{len(items)}] Skipped: invalid URL")
                continue
            if normalized_url in seen:
                logger.info(f"[ITEM {idx}/{len(items)}] Skipped: duplicate URL")
                continue
            seen.add(normalized_url)
            item["normalized_url"] = normalized_url

            existing = await crud_article.get_article_by_url(db, normalized_url)
            if not existing:
                if raw_url and raw_url != normalized_url:
                    existing = await crud_article.get_article_by_url(db, raw_url)
            if existing:
                logger.info(f"[ITEM {idx}/{len(items)}] Skipped: already exists in DB")
                continue

            logger.info(f"[ITEM {idx}/{len(items)}] Fetching and processing article...")
            article_data = await self._fetch_and_process_article(
                db, company, item, start_date, end_date
            )
            if article_data:
                collected.append(article_data)
                # 記事が保存されたら即座に進捗を更新
                current_total = base_article_count + len(collected)
                await crud_job.update_job_progress(db, job_id, company_index, current_total)
                logger.info(f"[ITEM {idx}/{len(items)}] ✓ Article saved (total: {current_total})")
            else:
                logger.info(f"[ITEM {idx}/{len(items)}] ✗ Article not saved (filtered or error)")

            await asyncio.sleep(1)

        return collected
    

    async def _search_duckduckgo(
        self,
        company: Company,
        start_date: date,
        end_date: date,
    ) -> List[Dict]:
        """DuckDuckGo検索を実行"""
        results: List[Dict] = []

        # 企業別の検索リージョン設定を取得
        region = None
        if company.search_settings and company.search_settings.region:
            # リージョンをそのまま使用（sg-en形式）
            region = company.search_settings.region

        # リージョンに応じたキーワードを取得
        keywords = get_keywords_by_region(region)

        # ログ出力
        logger.info(f"[DuckDuckGo Search] Company: {company.name}")
        logger.info(f"  Region: {region or 'None (default)'}")
        logger.info(f"  Keywords: {keywords}")

        query = self.ddg_searcher.build_company_query(
            company.name,
            keywords=keywords,
        )
        logger.info(f"  Query (native): {query}")

        # 本文チェックで判定するため、タイトル+スニペットチェックは不要
        ddg_results = await self.ddg_searcher.search(
            query, start_date, end_date, num_results=10, gl=region
        )
        # DuckDuckGo検索結果にソースタグを付ける
        for item in ddg_results:
            item["source"] = "duckduckgo"
        results.extend(ddg_results)

        if company.name_en:
            # 英語名での検索は英語キーワードを使用
            query_en = self.ddg_searcher.build_company_query(
                company.name_en,
                keywords=["AI", "generative AI", "agentic AI", "digital transformation", "automation", "case study"],
            )
            logger.info(f"  Query (English): {query_en}")

            # 本文チェックで判定するため、タイトル+スニペットチェックは不要
            ddg_results_en = await self.ddg_searcher.search(
                query_en, start_date, end_date, num_results=5, gl=region
            )
            # DuckDuckGo検索結果にソースタグを付ける
            for item in ddg_results_en:
                item["source"] = "duckduckgo"
            results.extend(ddg_results_en)

        logger.info(f"  Found {len(results)} results from DuckDuckGo")

        return results

    
    async def _fetch_press_releases(
        self,
        company: Company,
        start_date: date,
        end_date: date,
    ) -> List[Dict]:
        """公式プレスリリースを取得"""
        results = []
        
        for source_url in company.source_urls:
            if not source_url.is_active:
                continue
            
            press_items = await self.press_scraper.fetch_press_list(
                source_url.url,
                start_date,
                end_date,
                use_llm_fallback=True,
                extract_date_with_llm=True,
            )
            results.extend(press_items)
            
            await asyncio.sleep(1)
        
        return results
    
    async def _fetch_and_process_article(
        self,
        db: AsyncSession,
        company: Company,
        item: Dict,
        start_date: date,
        end_date: date,
    ) -> Optional[Article]:
        """記事を取得して処理"""
        url = item.get("url", "")
        normalized_url = item.get("normalized_url", url)
        title = item.get("title", "")

        # 記事内容を取得（タイムアウト付き）
        try:
            article_data = await asyncio.wait_for(
                self.article_fetcher.fetch_content(url),
                timeout=self.FETCH_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.warning(f"[TIMEOUT] Article fetch timed out after {self.FETCH_TIMEOUT}s: {url}")
            article_data = None
        except Exception as e:
            logger.info(f"[ERROR] Article fetch failed: {url} - {e}")
            article_data = None

        # AI関連性チェック（本文優先、失敗時はタイトル+スニペット）
        content = ""
        if article_data and article_data.get("content"):
            # 本文取得成功 → 本文でAI判定（厳密、タイムアウト付き）
            content = article_data.get("content", "")
            try:
                is_ai_related = await asyncio.wait_for(
                    self.ai_classifier.classify_article_content(
                        title=article_data.get("title", title),
                        content=content,
                        debug=False,
                    ),
                    timeout=self.LLM_TIMEOUT
                )
            except asyncio.TimeoutError:
                logger.warning(f"[TIMEOUT] AI classification timed out after {self.LLM_TIMEOUT}s: {title}")
                is_ai_related = None
            except Exception as e:
                logger.info(f"[ERROR] AI classification failed: {title} - {e}")
                is_ai_related = None

            if is_ai_related is False:
                logger.info(f"[FILTERED] Not AI-related (content check): {title}")
                return None
            elif is_ai_related is None:
                logger.info(f"[WARN] Could not determine AI relevance (content check): {title}")
        else:
            # 本文取得失敗 → タイトル+スニペットでフォールバック判定（タイムアウト付き）
            logger.info(f"[INFO] Content fetch failed, using title+snippet for AI check: {url}")
            snippet = item.get("snippet", "")
            try:
                is_ai_related = await asyncio.wait_for(
                    self.ai_classifier.classify_text(
                        title=title,
                        snippet=snippet,
                    ),
                    timeout=self.LLM_TIMEOUT
                )
            except asyncio.TimeoutError:
                logger.warning(f"[TIMEOUT] AI classification (title+snippet) timed out after {self.LLM_TIMEOUT}s: {title}")
                is_ai_related = None
            except Exception as e:
                logger.info(f"[ERROR] AI classification (title+snippet) failed: {title} - {e}")
                is_ai_related = None

            if is_ai_related is False:
                logger.info(f"[FILTERED] Not AI-related (title+snippet check): {title}")
                return None
            elif is_ai_related is None:
                logger.info(f"[WARN] Could not determine AI relevance (title+snippet check): {title}")

            # AI関連と判定されたが本文なし → タイトルだけでも保存
            logger.info(f"[INFO] AI-related article but no content available, saving with title only: {title}")
            # article_dataがNoneまたは空の場合の初期化
            if not article_data:
                article_data = {
                    "title": title,
                    "content": "",
                    "url": url,
                    "published_date": None,
                }

        # 日付検証（発行日不明は保存しない）
        pub_date = article_data.get("published_date") or item.get("published_date")
        if not pub_date:
            try:
                pub_date = await asyncio.wait_for(
                    self.date_extractor.extract_date(
                        title=article_data.get("title", title),
                        snippet=item.get("snippet", ""),
                        url=url,
                        content=content,
                    ),
                    timeout=self.LLM_TIMEOUT
                )
            except asyncio.TimeoutError:
                logger.warning(f"[TIMEOUT] Date extraction timed out after {self.LLM_TIMEOUT}s: {title}")
                pub_date = None
        if not pub_date:
            # 日付が取得できない場合は今日の日付を使用
            from datetime import datetime
            pub_date = datetime.now().date()
            logger.info(f"Using today's date for article without published_date: {title}")

        # 日付範囲チェック
        # - 手動追加(manual)は常に保存
        # - DuckDuckGo検索も常に保存
        # - プレス一覧で日付検証済みの場合は再検証しない
        # - それ以外は日付範囲内のみ保存
        if item.get("source") not in ("manual", "duckduckgo"):
            if not (item.get("source") == "press_list" and item.get("date_validated")):
                if pub_date < start_date or pub_date > end_date:
                    logger.info(f"Skipping article outside date range: {title}")
                    return None
        
        # LLMで要約
        try:
            summary_data = await asyncio.wait_for(
                self.summarizer.summarize(
                    title=article_data.get("title", title),
                    content=content,
                    company_name=company.name,
                ),
                timeout=self.LLM_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.warning(f"[TIMEOUT] Summarization timed out after {self.LLM_TIMEOUT}s: {title}")
            summary_data = None
        
        # LLMで分類
        try:
            classify_data = await asyncio.wait_for(
                self.classifier.classify(
                    title=article_data.get("title", title),
                    content=content,
                    summary=summary_data.get("summary", "") if summary_data else "",
                    company_name=company.name,
                ),
                timeout=self.LLM_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.warning(f"[TIMEOUT] Classification timed out after {self.LLM_TIMEOUT}s: {title}")
            classify_data = None

        # 要約を整形
        summary_text = ""
        if summary_data:
            summary_text = f"""## 概要
{summary_data.get('summary', '')}

## 主要ポイント
{chr(10).join(['- ' + p for p in summary_data.get('key_points', [])])}

## 成果・効果
{summary_data.get('outcomes', '記載なし')}

## 技術・仕組み
{summary_data.get('technology', '記載なし')}"""

        # 不適切フラグと理由を設定
        is_inappropriate = classify_data.get("is_inappropriate", False)
        inappropriate_reason = None
        if is_inappropriate:
            inappropriate_reason = "調査済・対象外"
            logger.info(f"[FILTERED] Inappropriate article, saving with flag: {title}")

        # DBに保存
        from app.schemas import ArticleCreate
        article_create = ArticleCreate(
            company_id=company.id,
            title=article_data.get("title", title),
            content=content[:5000],
            summary=summary_text,
            url=normalized_url,
            published_date=pub_date,
            category=classify_data.get("category", "その他"),
            business_area=classify_data.get("business_area", "その他"),
            tags=",".join(classify_data.get("tags", [])),
            is_inappropriate=is_inappropriate,
            inappropriate_reason=inappropriate_reason,
        )

        article = await crud_article.create_article(db, article_create)
        if is_inappropriate:
            logger.info(f"Saved inappropriate article: {title}")
        else:
            logger.info(f"Saved article: {title}")

        return article

    def _normalize_url(self, url: str) -> str:
        """重複排除用にURLを正規化（追跡パラメータ除去 + フラグメント削除）"""
        if not url:
            return ""
        try:
            parts = urlsplit(url)
        except ValueError:
            return url

        tracking_params = {
            "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "utm_id",
            "gclid", "fbclid", "msclkid", "igshid", "mc_cid", "mc_eid", "_ga", "_gl",
        }

        query_items = [
            (k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
            if k not in tracking_params and not k.startswith("utm_")
        ]
        normalized_query = urlencode(query_items, doseq=True)

        # パスの末尾スラッシュを統一（ルート以外）
        path = parts.path or ""
        if path.endswith("/") and path != "/":
            path = path.rstrip("/")

        normalized = urlunsplit((
            parts.scheme.lower(),
            parts.netloc.lower(),
            path,
            normalized_query,
            "",  # fragment removed
        ))
        return normalized or url
    
