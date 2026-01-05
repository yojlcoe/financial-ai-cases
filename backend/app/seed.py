"""
初期データを登録するシーダースクリプト
実行: python -m app.seed
"""

import asyncio
from datetime import date, timedelta

from app.core.database import AsyncSessionLocal, engine, Base
from app.models import Company, SourceUrl, SearchSetting


# 対象企業データ
COMPANIES = [
    {
        "name": "三井住友銀行",
        "name_en": "Sumitomo Mitsui Banking Corporation",
        "country": "日本",
        "urls": [
            {"url": "https://www.smbc.co.jp/news/", "url_type": "press_release"},
        ]
    },
    {
        "name": "JPMorgan Chase",
        "name_en": "JPMorgan Chase & Co.",
        "country": "米国",
        "urls": [
            {"url": "https://www.jpmorganchase.com/news-stories", "url_type": "press_release"},
        ]
    },
    {
        "name": "Capital One",
        "name_en": "Capital One Financial Corporation",
        "country": "米国",
        "urls": [
            {"url": "https://www.capitalone.com/about/newsroom/", "url_type": "press_release"},
        ]
    },
    {
        "name": "Royal Bank of Canada",
        "name_en": "Royal Bank of Canada",
        "country": "カナダ",
        "urls": [
            {"url": "https://www.rbc.com/newsroom/", "url_type": "press_release"},
        ]
    },
    {
        "name": "Wells Fargo",
        "name_en": "Wells Fargo & Company",
        "country": "米国",
        "urls": [
            {"url": "https://newsroom.wf.com/", "url_type": "press_release"},
        ]
    },
    {
        "name": "Commonwealth Bank of Australia",
        "name_en": "CommBank",
        "country": "オーストラリア",
        "urls": [
            {"url": "https://www.commbank.com.au/about-us/news.html", "url_type": "press_release"},
        ]
    },
    {
        "name": "UBS",
        "name_en": "UBS Group AG",
        "country": "スイス",
        "urls": [
            {"url": "https://www.ubs.com/global/en/media/news.html", "url_type": "press_release"},
        ]
    },
    {
        "name": "HSBC",
        "name_en": "HSBC Holdings plc",
        "country": "英国",
        "urls": [
            {"url": "https://www.hsbc.com/news-and-views", "url_type": "press_release"},
        ]
    },
    {
        "name": "Citigroup",
        "name_en": "Citigroup Inc.",
        "country": "米国",
        "urls": [
            {"url": "https://www.citigroup.com/global/news", "url_type": "press_release"},
        ]
    },
    {
        "name": "TD Bank",
        "name_en": "Toronto-Dominion Bank",
        "country": "カナダ",
        "urls": [
            {"url": "https://newsroom.td.com/", "url_type": "press_release"},
        ]
    },
    {
        "name": "Morgan Stanley",
        "name_en": "Morgan Stanley",
        "country": "米国",
        "urls": [
            {"url": "https://www.morganstanley.com/press-releases", "url_type": "press_release"},
        ]
    },
]


async def seed_database():
    """データベースに初期データを投入"""
    
    # テーブル作成
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as db:
        # 企業データを登録
        for company_data in COMPANIES:
            # 既存チェック
            from sqlalchemy import select
            query = select(Company).where(Company.name == company_data["name"])
            result = await db.execute(query)
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"Skip (already exists): {company_data['name']}")
                continue
            
            # 企業を作成
            company = Company(
                name=company_data["name"],
                name_en=company_data["name_en"],
                country=company_data["country"],
                is_active=True,
            )
            db.add(company)
            await db.flush()
            
            # URLを追加
            for url_data in company_data["urls"]:
                source_url = SourceUrl(
                    company_id=company.id,
                    url=url_data["url"],
                    url_type=url_data["url_type"],
                    is_active=True,
                )
                db.add(source_url)
            
            print(f"Created: {company_data['name']}")
        
        # 検索設定を作成（なければ）
        query = select(SearchSetting)
        result = await db.execute(query)
        existing_setting = result.scalar_one_or_none()
        
        if not existing_setting:
            today = date.today()
            three_months_ago = today - timedelta(days=90)
            
            setting = SearchSetting(
                search_start_date=three_months_ago,
                search_end_date=today,
                schedule_type="weekly",
                schedule_day=1,
                schedule_hour=9,
            )
            db.add(setting)
            print("Created: Search settings")
        
        await db.commit()
        print("\nSeed completed!")


if __name__ == "__main__":
    asyncio.run(seed_database())
