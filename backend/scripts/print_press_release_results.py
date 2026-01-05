"""
Print press release list results for a given URL without using the DB.

Usage:
    python scripts/print_press_release_results.py \
        --url "https://www.smbc.co.jp/news/" \
        --start-date 2025-10-01 \
        --end-date 2025-10-31 \
        --max-results 500
"""

import argparse
import asyncio
import sys
from datetime import date
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.crawler.press_scraper import PressScraper


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print press release list results")
    parser.add_argument("--url", type=str, required=True, help="Press release list URL")
    parser.add_argument("--start-date", type=str, default=None, help="YYYY-MM-DD")
    parser.add_argument("--end-date", type=str, default=None, help="YYYY-MM-DD")
    parser.add_argument("--max-results", type=int, default=500, help="Max results to print")
    parser.add_argument(
        "--debug-html",
        action="store_true",
        help="Print HTTP status and the first 1000 chars of HTML",
    )
    parser.add_argument(
        "--no-use-llm",
        action="store_false",
        dest="use_llm",
        help="Disable LLM fallback for press links",
    )
    parser.add_argument(
        "--no-date-llm",
        action="store_false",
        dest="date_llm",
        help="Disable LLM date extraction",
    )
    parser.set_defaults(use_llm=True, date_llm=True)
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    start_date = date.fromisoformat(args.start_date) if args.start_date else None
    end_date = date.fromisoformat(args.end_date) if args.end_date else None

    scraper = PressScraper()
    results = await scraper.fetch_press_list(
        args.url,
        start_date,
        end_date,
        debug=args.debug_html,
        use_llm_fallback=args.use_llm,
        extract_date_with_llm=args.date_llm,
    )

    print(f"Press list results: {len(results)}")
    for i, item in enumerate(results[: args.max_results], 1):
        title = (item.get("title") or "").strip()
        url = (item.get("url") or "").strip()
        print(f"{i:02d}. {title}")
        print(f"    {url}")

    if len(results) > args.max_results:
        print(f"... ({len(results) - args.max_results} more not shown)")


if __name__ == "__main__":
    asyncio.run(main())
