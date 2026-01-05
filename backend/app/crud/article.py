from sqlalchemy import select, func, and_, case, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import date

from app.models import Article, Company
from app.schemas import ArticleCreate, ArticleUpdate


async def get_articles(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    company_id: Optional[int] = None,
    category: Optional[str] = None,
    business_area: Optional[str] = None,
    tags: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    include_unknown_dates: Optional[bool] = None,
    is_reviewed: Optional[bool] = None,
) -> tuple[List[Article], int]:
    query = select(Article)
    count_query = select(func.count(Article.id))

    # 不適切フラグがついた記事を除外
    query = query.where(Article.is_inappropriate == False)
    count_query = count_query.where(Article.is_inappropriate == False)

    if company_id:
        query = query.where(Article.company_id == company_id)
        count_query = count_query.where(Article.company_id == company_id)

    if category:
        query = query.where(Article.category == category)
        count_query = count_query.where(Article.category == category)

    if business_area:
        query = query.where(Article.business_area == business_area)
        count_query = count_query.where(Article.business_area == business_area)

    if tags:
        # タグは部分一致で検索（カンマ区切りのリストに含まれるか）
        query = query.where(Article.tags.contains(tags))
        count_query = count_query.where(Article.tags.contains(tags))

    # 日付フィルタリング
    if start_date or end_date:
        # 日付範囲が指定されている場合
        if include_unknown_dates:
            # 日付不明を含む場合は、日付がNULLまたは範囲内のものを取得
            date_conditions = []
            if start_date and end_date:
                date_conditions.append(
                    and_(Article.published_date >= start_date, Article.published_date <= end_date)
                )
            elif start_date:
                date_conditions.append(Article.published_date >= start_date)
            elif end_date:
                date_conditions.append(Article.published_date <= end_date)

            # NULLまたは日付範囲内の条件
            date_conditions.append(Article.published_date.is_(None))
            query = query.where(or_(*date_conditions))
            count_query = count_query.where(or_(*date_conditions))
        else:
            # 日付不明を含まない場合は、範囲内のもののみ
            if start_date:
                query = query.where(Article.published_date >= start_date)
                count_query = count_query.where(Article.published_date >= start_date)
            if end_date:
                query = query.where(Article.published_date <= end_date)
                count_query = count_query.where(Article.published_date <= end_date)
    elif include_unknown_dates:
        # 日付範囲の指定なしで、日付不明のみを取得
        query = query.where(Article.published_date.is_(None))
        count_query = count_query.where(Article.published_date.is_(None))

    if is_reviewed is not None:
        query = query.where(Article.is_reviewed == is_reviewed)
        count_query = count_query.where(Article.is_reviewed == is_reviewed)

    # 日付降順、ただしNULL（日付なし）は最後
    # 同じ日付の場合はID降順（追加順）でソート
    query = query.order_by(
        case((Article.published_date.is_(None), 1), else_=0),
        Article.published_date.desc(),
        Article.id.desc()
    ).offset(skip).limit(limit)

    result = await db.execute(query)
    articles = result.scalars().all()

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return articles, total


async def get_article_by_url(db: AsyncSession, url: str) -> Optional[Article]:
    query = select(Article).where(Article.url == url)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_article(db: AsyncSession, article: ArticleCreate) -> Article:
    db_article = Article(**article.model_dump())
    db.add(db_article)
    await db.commit()
    await db.refresh(db_article)
    return db_article


async def update_article(
    db: AsyncSession,
    article_id: int,
    article_update: ArticleUpdate,
) -> Optional[Article]:
    query = select(Article).where(Article.id == article_id)
    result = await db.execute(query)
    db_article = result.scalar_one_or_none()

    if not db_article:
        return None

    update_data = article_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_article, field, value)

    await db.commit()
    await db.refresh(db_article)
    return db_article


async def get_analysis_stats(
    db: AsyncSession,
    company_id: Optional[int] = None,
) -> tuple[int, int]:
    filters = [Article.is_inappropriate == False]
    if company_id:
        filters.append(Article.company_id == company_id)

    total_query = select(func.count(Article.id))
    analyzed_query = select(func.count(Article.id)).where(
        and_(
            Article.summary.isnot(None),
            Article.summary != "",
            Article.category.isnot(None),
            Article.category != "",
            Article.business_area.isnot(None),
            Article.business_area != "",
            Article.tags.isnot(None),
            Article.tags != "",
        )
    )

    if filters:
        total_query = total_query.where(*filters)
        analyzed_query = analyzed_query.where(*filters)

    total_result = await db.execute(total_query)
    analyzed_result = await db.execute(analyzed_query)

    total = total_result.scalar() or 0
    analyzed = analyzed_result.scalar() or 0

    return total, analyzed


async def get_analysis_coefficients(
    db: AsyncSession,
    company_id: Optional[int] = None,
) -> dict:
    query = select(
        Article.category,
        Article.business_area,
        Article.published_date,
        Company.country,
    ).join(Company, Article.company_id == Company.id).where(Article.is_inappropriate == False)

    if company_id:
        query = query.where(Article.company_id == company_id)

    result = await db.execute(query)
    rows = result.all()

    total = len(rows)
    category_counts: dict[str, int] = {}
    business_area_counts: dict[str, int] = {}
    region_counts: dict[str, int] = {}
    month_counts: dict[str, int] = {}

    for category, business_area, published_date, country in rows:
        category_label = category or "未分類"
        business_area_label = business_area or "未分類"
        region_label = country or "不明"
        if published_date:
            month_label = published_date.strftime("%Y-%m")
        else:
            month_label = "不明"

        category_counts[category_label] = category_counts.get(category_label, 0) + 1
        business_area_counts[business_area_label] = business_area_counts.get(business_area_label, 0) + 1
        region_counts[region_label] = region_counts.get(region_label, 0) + 1
        month_counts[month_label] = month_counts.get(month_label, 0) + 1

    def to_sorted_list(items: dict[str, int]) -> list[dict]:
        return [
            {"label": label, "count": count}
            for label, count in sorted(items.items(), key=lambda x: (-x[1], x[0]))
        ]

    def to_month_list(items: dict[str, int]) -> list[dict]:
        def sort_key(item: tuple[str, int]) -> tuple[int, str]:
            label, _ = item
            return (1, label) if label == "不明" else (0, label)

        return [{"period": label, "count": count} for label, count in sorted(items.items(), key=sort_key)]

    return {
        "total": total,
        "by_category": to_sorted_list(category_counts),
        "by_business_area": to_sorted_list(business_area_counts),
        "by_region": to_sorted_list(region_counts),
        "by_month": to_month_list(month_counts),
    }


async def update_article_summary(
    db: AsyncSession,
    article_id: int,
    summary: str,
    category: str,
    business_area: str,
    tags: str
) -> Optional[Article]:
    query = select(Article).where(Article.id == article_id)
    result = await db.execute(query)
    db_article = result.scalar_one_or_none()
    
    if not db_article:
        return None
    
    db_article.summary = summary
    db_article.category = category
    db_article.business_area = business_area
    db_article.tags = tags
    
    await db.commit()
    await db.refresh(db_article)
    return db_article
