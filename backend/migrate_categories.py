"""
カテゴリを旧形式から新形式に移行するスクリプト
"""
import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import select, update
from app.models import Article


# 旧カテゴリ → 新カテゴリのマッピング
CATEGORY_MAPPING = {
    "顧客対応・サポート": "活用事例(顧客対応・サポート)",
    "業務効率化・自動化": "活用事例(業務効率化・自動化)",
    "リスク管理・コンプライアンス": "活用事例(リスク管理・コンプライアンス)",
    "商品・サービス開発": "活用事例(商品・サービス開発)",
    "マーケティング・営業": "活用事例(マーケティング・営業)",
    "人事": "活用事例(人事)",
    "IT・システム・セキュリティ": "活用事例(IT・システム・セキュリティ)",
    "データ分析・AI活用": "活用事例(業務効率化・自動化)",  # データ分析・AI活用は業務効率化に統合
    # 以下はそのまま
    "セキュリティ": "セキュリティ",
    "組織・人材": "組織・人材",
    "データ基盤・インフラ": "データ基盤・インフラ",
    "出資": "出資",
    "IR・決算・戦略": "IR・決算・戦略",
    "経済分析": "経済分析",
    "求人": "求人",
    "その他": "その他",
}


async def migrate_categories():
    async with AsyncSessionLocal() as db:
        # 現在のカテゴリ分布を表示
        result = await db.execute(
            select(Article.category).where(Article.category.isnot(None)).distinct()
        )
        current_categories = [row[0] for row in result.all()]

        print("現在のカテゴリ:")
        for cat in sorted(current_categories):
            print(f"  - {cat}")
        print()

        # カテゴリを更新
        updated_count = 0
        for old_cat, new_cat in CATEGORY_MAPPING.items():
            result = await db.execute(
                update(Article)
                .where(Article.category == old_cat)
                .values(category=new_cat)
            )
            if result.rowcount > 0:
                print(f"✓ '{old_cat}' → '{new_cat}' ({result.rowcount}件)")
                updated_count += result.rowcount

        await db.commit()

        print(f"\n合計 {updated_count} 件の記事カテゴリを更新しました")

        # 更新後のカテゴリ分布を表示
        print("\n更新後のカテゴリ分布:")
        from sqlalchemy import func
        result = await db.execute(
            select(Article.category, func.count(Article.id))
            .where(Article.category.isnot(None))
            .group_by(Article.category)
            .order_by(func.count(Article.id).desc())
        )
        categories = result.all()
        for cat, count in categories:
            print(f"  {cat}: {count}件")


if __name__ == "__main__":
    asyncio.run(migrate_categories())