"""
Print DuckDuckGo search results without using the DB.

Usage:
    python scripts/print_duckduckgo_search_results.py \
        --company-name "三井住友銀行" \
        --start-date 2025-10-06 \
        --end-date 2025-10-06 \
        --num-results 10
"""

import argparse
import asyncio
import sys
from datetime import date
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import get_db
from app.services.crawler.duckduckgo_search import DuckDuckGoSearcher
from app.services.llm.relevance import AiRelevanceClassifier
from app.settings.search_config import SearchConfig, load_search_config_from_db


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print DuckDuckGo search results")
    parser.add_argument("--company-name", type=str, required=True, help="Company name")
    parser.add_argument("--start-date", type=str, default=None, help="YYYY-MM-DD")
    parser.add_argument("--end-date", type=str, default=None, help="YYYY-MM-DD")
    parser.add_argument("--num-results", type=int, default=10, help="Max results to fetch")
    parser.add_argument("--gl", type=str, default=None, help="Country code (e.g. jp)")
    parser.add_argument(
        "--timelimit",
        type=str,
        default=None,
        help="d/w/m/y (overrides date-based timelimit)",
    )
    parser.add_argument(
        "--debug-html",
        action="store_true",
        help="Print HTTP status and the first 1000 chars of HTML",
    )
    parser.add_argument(
        "--ai-only-llm",
        action="store_true",
        help="Filter results with LLM AI/DX classification",
    )
    return parser.parse_args()


async def _filter_with_llm(results: list[dict], config: SearchConfig) -> list[dict]:
    if not results:
        return results

    classifier = AiRelevanceClassifier(config=config)
    if not await classifier.is_available():
        print("LLM is not available; skipping AI filter.")
        return results

    print("\n" + "=" * 80)
    print("AI RELEVANCE CLASSIFICATION")
    print("=" * 80 + "\n")

    filtered = []
    for i, item in enumerate(results, 1):
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        if not title and not snippet:
            continue

        result = await classifier.classify_text(title=title, snippet=snippet)
        status = "✓ AI RELATED" if result is True else "✗ NOT AI RELATED"

        print(f"{i:02d}. [{status}] {title}")
        print(f"    {item.get('url', '')}")
        if snippet:
            print(f"    {snippet}")
        print()

        if result is True:
            filtered.append(item)

    print(f"\nFiltered: {len(filtered)}/{len(results)} results are AI-related\n")
    return filtered


async def main() -> None:
    args = parse_args()

    # Load configuration from database
    async for db in get_db():
        config = await load_search_config_from_db(db, company_name=args.company_name)
        break

    print(f"Configuration loaded for: {args.company_name}")
    print(f"Search keywords: {', '.join(config.search_keywords[:3])}... (total: {len(config.search_keywords)})")
    print(f"LLM filter enabled: {config.llm_filter_enabled}")
    print(f"Default region: {config.default_region or 'global'}")
    print()

    # Create searcher with config
    searcher = DuckDuckGoSearcher(config=config)

    if not args.start_date or not args.end_date:
        if not args.timelimit:
            raise SystemExit("start-date and end-date are required unless --timelimit is set.")
        start_date = None
        end_date = None
    else:
        start_date = date.fromisoformat(args.start_date)
        end_date = date.fromisoformat(args.end_date)

    # Build query using config keywords (or override if specified)
    query = searcher.build_company_query(args.company_name)

    print(query)

    # Use region from config if not specified in args
    region = args.gl or config.default_region

    results = await searcher.search(
        query,
        start_date,
        end_date,
        num_results=args.num_results,
        gl=region,
        timelimit_override=args.timelimit,
        debug=args.debug_html,
    )

    # Show original results
    print("\n" + "=" * 80)
    print(f"ORIGINAL DDG SEARCH RESULTS: {len(results)} items")
    print("=" * 80 + "\n")
    for i, item in enumerate(results, 1):
        title = (item.get("title") or "").strip()
        url = (item.get("url") or "").strip()
        snippet = (item.get("snippet") or "").strip()
        print(f"{i:02d}. {title}")
        print(f"    {url}")
        if snippet:
            print(f"    {snippet}")
        print()

    # Apply LLM filtering if requested
    if args.ai_only_llm:
        filtered_results = await _filter_with_llm(results, config)
        print("\n" + "=" * 80)
        print(f"FINAL FILTERED RESULTS: {len(filtered_results)} items")
        print("=" * 80 + "\n")
        for i, item in enumerate(filtered_results, 1):
            title = (item.get("title") or "").strip()
            url = (item.get("url") or "").strip()
            snippet = (item.get("snippet") or "").strip()
            print(f"{i:02d}. {title}")
            print(f"    {url}")
            if snippet:
                print(f"    {snippet}")
            print()


if __name__ == "__main__":
    asyncio.run(main())
